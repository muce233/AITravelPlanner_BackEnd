"""语音识别相关数据模型"""
from pydantic import BaseModel


class SpeechRecognitionRequest(BaseModel):
    audio_data: str  # base64编码的音频数据
    language: str = "zh-CN"


class SpeechRecognitionResponse(BaseModel):
    text: str
    confidence: float