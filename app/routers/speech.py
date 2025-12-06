from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import get_current_active_user
from ..schemas.speech import SpeechRecognitionRequest, SpeechRecognitionResponse

router = APIRouter(prefix="/api/speech", tags=["speech"])


@router.post("/recognize", response_model=SpeechRecognitionResponse)
async def speech_recognize(
    request: SpeechRecognitionRequest,
    current_user = Depends(get_current_active_user)
):
    """语音识别（暂为占位实现）"""
    # TODO: 集成科大讯飞或其他语音识别服务
    # 这里返回一个模拟的识别结果
    return SpeechRecognitionResponse(
        text="这是语音识别的模拟结果，实际需要集成语音识别API",
        confidence=0.95
    )


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