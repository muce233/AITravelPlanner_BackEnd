"""语音识别相关数据模型"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ASRModelType(str, Enum):
    """语音识别模型类型"""
    FUN_ASR_REALTIME = "fun-asr-realtime"
    QWEN_ASR_REALTIME = "qwen-asr-realtime"


class AudioFormat(str, Enum):
    """音频格式"""
    PCM = "pcm"
    OPUS = "opus"
    WAV = "wav"
    MP3 = "mp3"
    AAC = "aac"
    AMR = "amr"
    SPEEX = "speex"


class LanguageCode(str, Enum):
    """支持的语言代码"""
    ZH = "zh"  # 中文（普通话及方言）
    YUE = "yue"  # 粤语
    EN = "en"  # 英文
    JA = "ja"  # 日语
    DE = "de"  # 德语
    KO = "ko"  # 韩语
    RU = "ru"  # 俄语
    FR = "fr"  # 法语
    PT = "pt"  # 葡萄牙语
    AR = "ar"  # 阿拉伯语
    IT = "it"  # 意大利语
    ES = "es"  # 西班牙语
    HI = "hi"  # 印地语
    ID = "id"  # 印尼语
    TH = "th"  # 泰语
    TR = "tr"  # 土耳其语
    UK = "uk"  # 乌克兰语
    VI = "vi"  # 越南语


class VADConfig(BaseModel):
    """语音活动检测配置"""
    enabled: bool = Field(default=True, description="是否启用VAD")
    threshold: float = Field(default=0.2, ge=-1, le=1, description="VAD检测阈值")
    silence_duration_ms: int = Field(default=800, ge=200, le=6000, description="静音断句阈值（毫秒）")
    type: str = Field(default="server_vad", description="VAD类型")


class TranscriptionParams(BaseModel):
    """语音识别参数配置"""
    language: LanguageCode = Field(default=LanguageCode.ZH, description="音频源语言")
    sample_rate: int = Field(default=16000, description="音频采样率（Hz）")
    input_audio_format: AudioFormat = Field(default=AudioFormat.PCM, description="音频格式")
    corpus_text: Optional[str] = Field(default=None, max_length=10000, description="上下文增强文本")


class ASRConfig(BaseModel):
    """语音识别服务配置"""
    model_type: ASRModelType = Field(default=ASRModelType.FUN_ASR_REALTIME, description="模型类型")
    api_key: str = Field(description="阿里云API Key")
    region: str = Field(default="cn-beijing", description="服务区域")
    vad_config: VADConfig = Field(default_factory=VADConfig, description="VAD配置")
    transcription_params: TranscriptionParams = Field(default_factory=TranscriptionParams, description="识别参数")
    max_duration: int = Field(default=60, ge=1, le=300, description="最大录音时长（秒）")


class SpeechRecognitionRequest(BaseModel):
    """语音识别请求"""
    audio_data: str = Field(description="base64编码的音频数据")
    model_type: ASRModelType = Field(default=ASRModelType.FUN_ASR_REALTIME, description="模型类型")
    language: LanguageCode = Field(default=LanguageCode.ZH, description="语言代码")
    sample_rate: int = Field(default=16000, description="采样率")
    audio_format: AudioFormat = Field(default=AudioFormat.PCM, description="音频格式")


class SpeechRecognitionResponse(BaseModel):
    """语音识别响应"""
    text: str = Field(description="识别文本")
    confidence: Optional[float] = Field(default=None, description="置信度")
    is_final: bool = Field(default=True, description="是否为最终结果")
    model_type: ASRModelType = Field(description="使用的模型类型")
    language: LanguageCode = Field(description="识别语言")


class RealtimeTranscriptionRequest(BaseModel):
    """实时语音识别请求"""
    session_id: str = Field(description="会话ID")
    model_type: ASRModelType = Field(default=ASRModelType.FUN_ASR_REALTIME, description="模型类型")
    vad_config: VADConfig = Field(default_factory=VADConfig, description="VAD配置")
    transcription_params: TranscriptionParams = Field(default_factory=TranscriptionParams, description="识别参数")


class AudioChunkData(BaseModel):
    """音频数据块"""
    session_id: str = Field(description="会话ID")
    audio_data: str = Field(description="base64编码的音频数据")
    is_final: bool = Field(default=False, description="是否为最终数据块")
    timestamp: int = Field(description="时间戳")


class RealtimeTranscriptionResponse(BaseModel):
    """实时语音识别响应"""
    session_id: str = Field(description="会话ID")
    text: str = Field(description="识别文本")
    is_final: bool = Field(default=False, description="是否为最终结果")
    confidence: Optional[float] = Field(default=None, description="置信度")
    model_type: ASRModelType = Field(description="使用的模型类型")


class SpeechServiceConfig(BaseModel):
    """语音服务配置"""
    enabled_models: List[ASRModelType] = Field(default_factory=list, description="启用的模型列表")
    default_model: ASRModelType = Field(default=ASRModelType.FUN_ASR_REALTIME, description="默认模型")
    max_concurrent_sessions: int = Field(default=10, description="最大并发会话数")
    session_timeout: int = Field(default=300, description="会话超时时间（秒）")