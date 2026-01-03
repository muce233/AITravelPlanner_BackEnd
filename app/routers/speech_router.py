"""语音识别路由 - 兼容fun-asr-realtime和Qwen-ASR-Realtime模型"""
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..schemas.speech import (
    RealtimeTranscriptionResponse,
    ASRConfig, VADConfig, TranscriptionParams
)
from ..services.speech_service import SpeechRecognitionService
from ..config import settings

router = APIRouter(prefix="/api/speech", tags=["speech"])

# 全局语音识别服务实例
_speech_service: SpeechRecognitionService = None


def get_speech_service() -> SpeechRecognitionService:
    """获取语音识别服务实例"""
    global _speech_service
    if _speech_service is None:
        config = ASRConfig(
            api_key=settings.dashscope_api_key,
            model_type=settings.dashscope_speech_model,
            fun_asr_url=settings.fun_asr_url,
            vad_config=VADConfig(
                enabled=settings.vad_enabled,
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
        async def on_transcription(text: str):
            response = RealtimeTranscriptionResponse(
                session_id=session_id,
                text=text,
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
                    audio_data=data
                )
                
                if not success:
                    await websocket.send_text(json.dumps({
                        "error": "发送音频数据失败"
                    }))
                    
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
