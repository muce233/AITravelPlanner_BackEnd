"""语音识别服务类 - 兼容fun-asr-realtime和Qwen-ASR-Realtime模型"""
import asyncio
import base64
import json
import logging
import time
from typing import Optional, Dict, Any, Callable
from enum import Enum

import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback
from dashscope.audio.qwen_omni import MultiModality, AudioFormat

from ..schemas.speech import (
    ASRModelType, AudioFormat as SpeechAudioFormat, LanguageCode, 
    VADConfig, TranscriptionParams, ASRConfig, RealtimeTranscriptionResponse,
    AudioChunkData
)


class SpeechRecognitionMode(str, Enum):
    """语音识别模式"""
    SYNC = "sync"  # 同步识别
    REALTIME = "realtime"  # 实时识别


class ASRServiceError(Exception):
    """语音识别服务异常"""
    pass


class FunASRCallback(RecognitionCallback):
    """Fun-ASR实时识别回调类"""
    
    def __init__(self, on_transcription: Callable[[str], None]):
        self.on_transcription = on_transcription
        self.last_text = ""
    
    def on_event(self, message):
        """处理识别事件"""
        try:
            if hasattr(message, 'sentence'):
                text = message.sentence
                if text and text != self.last_text:
                    self.on_transcription(text)
                    self.last_text = text
        except Exception as e:
            logging.error(f"Fun-ASR回调处理错误: {e}")
    
    def on_complete(self):
        """识别完成"""
        logging.info("Fun-ASR识别完成")
    
    def on_error(self, error):
        """识别错误"""
        logging.error(f"Fun-ASR识别错误: {error}")


class QwenASRCallback(OmniRealtimeCallback):
    """Qwen-ASR实时识别回调类"""
    
    def __init__(self, on_transcription: Callable[[str], None]):
        self.on_transcription = on_transcription
        self.last_text = ""
    
    def on_event(self, event):
        """处理识别事件"""
        try:
            # 处理语音识别结果事件
            if event.get('type') == 'conversation.item.input_audio_transcription.text':
                text = event.get('text', '')
                if text and text != self.last_text:
                    self.on_transcription(text)
                    self.last_text = text
            # 处理语音停止事件
            elif event.get('type') == 'input_audio_buffer.speech_stopped':
                # 可以在这里处理语音结束后的逻辑
                pass
            # 处理错误事件
            elif event.get('type') == 'error':
                error_info = event.get('error', {})
                logging.error(f"Qwen-ASR错误: {error_info.get('message', '未知错误')}")
                        
        except Exception as e:
            logging.error(f"Qwen-ASR回调处理错误: {e}")
    
    def on_complete(self):
        """识别完成"""
        logging.info("Qwen-ASR识别完成")
    
    def on_error(self, error):
        """识别错误"""
        try:
            if isinstance(error, dict):
                error_msg = error.get('message', '未知错误')
                error_code = error.get('code', 'unknown')
                logging.error(f"Qwen-ASR识别错误 [{error_code}]: {error_msg}")
            else:
                logging.error(f"Qwen-ASR识别错误: {error}")
        except Exception as e:
            logging.error(f"Qwen-ASR错误处理失败: {e}")


class SpeechRecognitionService:
    """语音识别服务类"""
    
    def __init__(self, config: ASRConfig):
        self.config = config
        self.active_sessions: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
        # 配置DashScope API Key
        dashscope.api_key = config.api_key
        
        # 根据区域配置WebSocket URL
        dashscope.base_websocket_api_url = config.fun_asr_url
    
    def _map_audio_format(self, format: SpeechAudioFormat) -> str:
        """映射音频格式到DashScope格式"""
        format_map = {
            SpeechAudioFormat.PCM: "pcm",
            SpeechAudioFormat.OPUS: "opus",
            SpeechAudioFormat.WAV: "wav",
            SpeechAudioFormat.MP3: "mp3",
            SpeechAudioFormat.AAC: "aac",
            SpeechAudioFormat.AMR: "amr",
            SpeechAudioFormat.SPEEX: "speex"
        }
        return format_map.get(format, "pcm")
    
    def _map_language_code(self, language: LanguageCode) -> str:
        """映射语言代码到DashScope格式"""
        language_map = {
            LanguageCode.ZH: "zh",
            LanguageCode.YUE: "yue",
            LanguageCode.EN: "en",
            LanguageCode.JA: "ja",
            LanguageCode.DE: "de",
            LanguageCode.KO: "ko",
            LanguageCode.RU: "ru",
            LanguageCode.FR: "fr",
            LanguageCode.PT: "pt",
            LanguageCode.AR: "ar",
            LanguageCode.IT: "it",
            LanguageCode.ES: "es",
            LanguageCode.HI: "hi",
            LanguageCode.ID: "id",
            LanguageCode.TH: "th",
            LanguageCode.TR: "tr",
            LanguageCode.UK: "uk",
            LanguageCode.VI: "vi"
        }
        return language_map.get(language, "zh")
    

    

    

    
    async def start_realtime_session(self, session_id: str, 
                                   model_type: ASRModelType = None,
                                   on_transcription: Callable[[str], None] = None) -> bool:
        """启动实时语音识别会话"""
        try:
            model_type = model_type or self.config.model_type
            
            if session_id in self.active_sessions:
                self.logger.warning(f"会话 {session_id} 已存在")
                return False
            
            if model_type == ASRModelType.FUN_ASR_REALTIME:
                session = await self._start_fun_asr_session(session_id, on_transcription)
            elif model_type == ASRModelType.QWEN_ASR_REALTIME:
                session = await self._start_qwen_asr_session(session_id, on_transcription)
            else:
                raise ASRServiceError(f"不支持的模型类型: {model_type}")
            
            self.active_sessions[session_id] = {
                "session": session,
                "model_type": model_type,
                "start_time": time.time(),
                "on_transcription": on_transcription
            }
            
            self.logger.info(f"启动实时语音识别会话: {session_id}, 模型: {model_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动实时会话失败: {e}")
            raise ASRServiceError(f"启动实时会话失败: {str(e)}")
    
    async def _start_fun_asr_session(self, session_id: str, 
                                   on_transcription: Callable[[str], None]) -> Recognition:
        """启动Fun-ASR实时会话"""
        callback = FunASRCallback(on_transcription)
        
        recognition = Recognition(
            model='fun-asr-realtime',
            format=self._map_audio_format(self.config.transcription_params.input_audio_format),
            sample_rate=self.config.transcription_params.sample_rate,
            callback=callback
        )
        
        # 启动识别
        recognition.start()
        return recognition
    
    async def _start_qwen_asr_session(self, session_id: str, 
                                    on_transcription: Callable[[str], None]) -> OmniRealtimeConversation:
        """启动Qwen-ASR实时会话"""
        callback = QwenASRCallback(on_transcription)
        
        conversation = OmniRealtimeConversation(
            model='qwen3-asr-flash-realtime',
            callback=callback
        )
        
        # 连接并配置会话
        conversation.connect()
        
        # 根据配置获取音频格式
        audio_format_map = {
            SpeechAudioFormat.PCM: AudioFormat.PCM_16000HZ_MONO_16BIT,
            SpeechAudioFormat.OPUS: AudioFormat.OPUS_16000HZ_MONO
        }
        audio_format = audio_format_map.get(
            self.config.transcription_params.input_audio_format,
            AudioFormat.PCM_16000HZ_MONO_16BIT
        )
        
        # 更新会话配置
        vad_threshold = max(-1.0, min(1.0, self.config.vad_config.threshold))
        vad_silence_duration = max(200, min(6000, self.config.vad_config.silence_duration_ms))
        
        conversation.update_session(
            output_modalities=[MultiModality.TEXT],
            enable_turn_detection=self.config.vad_config.enabled,
            turn_detection_type='server_vad',  # 固定为server_vad
            turn_detection_threshold=vad_threshold,
            turn_detection_silence_duration_ms=vad_silence_duration,
            input_audio_format=audio_format,
            enable_input_audio_transcription=True
        )
        
        return conversation
    
    async def send_audio_data(self, session_id: str, audio_data: bytes) -> bool:
        """发送音频数据到实时会话"""
        try:
            if session_id not in self.active_sessions:
                self.logger.error(f"会话 {session_id} 不存在")
                return False
            
            session_info = self.active_sessions[session_id]
            model_type = session_info["model_type"]
            
            if model_type == ASRModelType.FUN_ASR_REALTIME:
                return await self._send_fun_asr_audio(session_info["session"], audio_data)
            elif model_type == ASRModelType.QWEN_ASR_REALTIME:
                return await self._send_qwen_asr_audio(session_info["session"], audio_data)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"发送音频数据失败: {e}")
            return False
    
    async def _send_fun_asr_audio(self, recognition: Recognition, audio_data: bytes) -> bool:
        """发送音频数据到Fun-ASR - 直接使用二进制数据"""
        try:
            # Fun-ASR通过send_audio_frame方法发送二进制音频数据
            recognition.send_audio_frame(audio_data)
            return True
        except Exception as e:
            self.logger.error(f"Fun-ASR发送音频失败: {e}")
            return False

    async def _send_qwen_asr_audio(self, conversation: OmniRealtimeConversation, 
                                 audio_data: bytes) -> bool:
        """发送音频数据到Qwen-ASR - 将二进制转为base64传输"""
        try:
            # 处理大音频数据分片发送
            max_chunk_size = 1024 * 1024  # 1MB分片
            chunks = [audio_data[i:i+max_chunk_size] for i in range(0, len(audio_data), max_chunk_size)]
            
            for chunk in chunks:
                # 将二进制音频数据转换为base64
                audio_base64 = base64.b64encode(chunk).decode('utf-8')
                
                # 追加音频数据
                conversation.append_audio(audio_base64)
                
                # 小延迟避免发送过快
                await asyncio.sleep(0.01)
            
            return True
        except Exception as e:
            self.logger.error(f"Qwen-ASR发送音频失败: {e}")
            return False
    
    async def stop_realtime_session(self, session_id: str) -> bool:
        """停止实时语音识别会话"""
        try:
            if session_id not in self.active_sessions:
                self.logger.warning(f"会话 {session_id} 不存在")
                return False
            
            session_info = self.active_sessions[session_id]
            model_type = session_info["model_type"]
            
            if model_type == ASRModelType.FUN_ASR_REALTIME:
                session_info["session"].stop()
            elif model_type == ASRModelType.QWEN_ASR_REALTIME:
                # Qwen-ASR会自动关闭连接
                pass
            
            # 从活跃会话中移除
            del self.active_sessions[session_id]
            
            self.logger.info(f"停止实时语音识别会话: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"停止实时会话失败: {e}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_info in self.active_sessions.items():
            if current_time - session_info["start_time"] > self.config.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.stop_realtime_session(session_id)
        
        return len(expired_sessions)
    
    def get_active_session_count(self) -> int:
        """获取活跃会话数量"""
        return len(self.active_sessions)