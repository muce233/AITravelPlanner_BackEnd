"""语音识别路由 - 兼容fun-asr-realtime和Qwen-ASR-Realtime模型"""
import base64
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import JSONResponse

from ..auth import get_current_active_user
from ..schemas.speech import (
    ASRModelType, SpeechRecognitionRequest, SpeechRecognitionResponse,
    RealtimeTranscriptionRequest, AudioChunkData, RealtimeTranscriptionResponse,
    ASRConfig, VADConfig, TranscriptionParams, SpeechServiceConfig
)
from ..services.speech_service import SpeechRecognitionService, ASRServiceError

router = APIRouter(prefix="/api/speech", tags=["speech"])

# 全局语音识别服务实例
_speech_service: SpeechRecognitionService = None


def get_speech_service() -> SpeechRecognitionService:
    """获取语音识别服务实例"""
    global _speech_service
    if _speech_service is None:
        # 从环境变量获取配置
        import os
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            raise RuntimeError("未配置DASHSCOPE_API_KEY环境变量")
        
        config = ASRConfig(
            api_key=api_key,
            model_type=ASRModelType.FUN_ASR_REALTIME,
            region=os.getenv('ASR_REGION', 'cn-beijing'),
            vad_config=VADConfig(
                enabled=True,
                threshold=0.2,
                silence_duration_ms=800
            ),
            transcription_params=TranscriptionParams(
                language="zh",
                sample_rate=16000,
                input_audio_format="pcm"
            ),
            max_duration=60
        )
        
        _speech_service = SpeechRecognitionService(config)
    
    return _speech_service


@router.get("/config")
async def get_speech_config():
    """获取语音识别服务配置"""
    service = get_speech_service()
    
    return {
        "enabled_models": [ASRModelType.FUN_ASR_REALTIME, ASRModelType.QWEN_ASR_REALTIME],
        "default_model": ASRModelType.FUN_ASR_REALTIME,
        "max_duration": service.config.max_duration,
        "sample_rate": service.config.transcription_params.sample_rate,
        "supported_languages": [lang.value for lang in service.config.transcription_params.language.__class__],
        "supported_formats": [fmt.value for fmt in service.config.transcription_params.input_audio_format.__class__]
    }


@router.websocket("/realtime/{session_id}")
async def websocket_realtime_speech(
    websocket: WebSocket,
    session_id: str
):
    """实时语音识别WebSocket接口"""
    await websocket.accept()
    
    try:
        service = get_speech_service()
        
        # 使用后端配置的默认模型类型
        model_type = service.config.model_type
        
        # 定义转录回调函数
        async def on_transcription(text: str, is_final: bool):
            response = RealtimeTranscriptionResponse(
                session_id=session_id,
                text=text,
                is_final=is_final,
                model_type=model_type
            )
            await websocket.send_text(response.json())
        
        # 启动实时会话
        success = await service.start_realtime_session(
            session_id=session_id,
            model_type=model_type,
            on_transcription=on_transcription
        )
        
        if not success:
            await websocket.send_text(json.dumps({
                "error": "无法启动实时语音识别会话"
            }))
            return
        
        # 处理音频数据流
        while True:
            try:
                # 接收二进制音频数据
                data = await websocket.receive_bytes()
                
                # 发送音频数据到识别服务
                success = await service.send_audio_data(
                    session_id=session_id,
                    audio_data=data,
                    is_final=False  # 实时流中通常不是最终数据块
                )
                
                if not success:
                    await websocket.send_text(json.dumps({
                        "error": "发送音频数据失败"
                    }))
                
                # 如果是最终数据块，准备结束会话
                if audio_chunk.is_final:
                    break
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logging.error(f"处理WebSocket消息错误: {e}")
                await websocket.send_text(json.dumps({
                    "error": f"处理消息失败: {str(e)}"
                }))
        
    except Exception as e:
        logging.error(f"WebSocket实时语音识别错误: {e}")
        await websocket.send_text(json.dumps({
            "error": f"实时语音识别失败: {str(e)}"
        }))
    
    finally:
        # 清理会话
        try:
            await service.stop_realtime_session(session_id)
        except Exception as e:
            logging.error(f"清理会话失败: {e}")


@router.post("/realtime/start")
async def start_realtime_session(
    request: RealtimeTranscriptionRequest,
    current_user = Depends(get_current_active_user)
):
    """启动实时语音识别会话"""
    try:
        service = get_speech_service()
        
        # 检查会话是否已存在
        session_info = await service.get_session_info(request.session_id)
        if session_info:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会话已存在")
        
        # 启动会话（这里需要传入回调函数，但HTTP接口无法实时返回结果）
        # 实时识别主要通过WebSocket接口实现
        success = await service.start_realtime_session(
            session_id=request.session_id,
            model_type=service.config.model_type
        )
        
        if success:
            return {"message": "会话启动成功", "session_id": request.session_id}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="会话启动失败")
            
    except ASRServiceError as e:
        logging.error(f"启动实时会话失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/realtime/{session_id}/audio")
async def send_audio_data(
    session_id: str,
    audio_data: bytes = Body(..., media_type="application/octet-stream"),
    is_final: bool = Body(default=False),
    current_user = Depends(get_current_active_user)
):
    """发送音频数据到实时会话"""
    try:
        service = get_speech_service()
        
        # 发送音频数据
        success = await service.send_audio_data(
            session_id=session_id,
            audio_data=audio_data,
            is_final=is_final
        )
        
        if success:
            return {"message": "音频数据发送成功"}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="音频数据发送失败")
            
    except ASRServiceError as e:
        logging.error(f"发送音频数据失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/realtime/{session_id}/stop")
async def stop_realtime_session(
    session_id: str,
    current_user = Depends(get_current_active_user)
):
    """停止实时语音识别会话"""
    try:
        service = get_speech_service()
        
        success = await service.stop_realtime_session(session_id)
        
        if success:
            return {"message": "会话停止成功"}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="会话停止失败")
            
    except ASRServiceError as e:
        logging.error(f"停止实时会话失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/realtime/{session_id}/info")
async def get_realtime_session_info(
    session_id: str,
    current_user = Depends(get_current_active_user)
):
    """获取实时会话信息"""
    try:
        service = get_speech_service()
        
        session_info = await service.get_session_info(session_id)
        
        if session_info:
            return session_info
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
            
    except ASRServiceError as e:
        logging.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/status")
async def get_speech_service_status():
    """获取语音识别服务状态"""
    try:
        service = get_speech_service()
        
        # 清理过期会话
        expired_count = await service.cleanup_expired_sessions()
        
        return {
            "active_sessions": service.get_active_session_count(),
            "expired_sessions_cleaned": expired_count,
            "service_status": "running"
        }
        
    except Exception as e:
        logging.error(f"获取服务状态失败: {e}")
        return {
            "active_sessions": 0,
            "expired_sessions_cleaned": 0,
            "service_status": "error",
            "error": str(e)
        }


@router.post("/synthesize")
async def speech_synthesize(
    text: str,
    current_user = Depends(get_current_active_user)
):
    """语音合成（暂为占位实现）"""
    # TODO: 集成语音合成服务
    return {
        "message": "语音合成功能待实现",
        "text": text,
        "audio_url": None
    }