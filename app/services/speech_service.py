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
    
    def __init__(self, on_transcription: Callable[[str, bool], None]):
        self.on_transcription = on_transcription
        self.last_text = ""
    
    def on_event(self, message):
        """处理识别事件"""
        try:
            if hasattr(message, 'sentence'):
                text = message.sentence
                is_final = True  # Fun-ASR通常返回最终结果
                if text and text != self.last_text:
                    self.on_transcription(text, is_final)
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
    
    def __init__(self, on_transcription: Callable[[str, bool], None]):
        self.on_transcription = on_transcription
        self.last_text = ""
    
    def on_event(self, event):
        """处理识别事件"""
        try:
            if event.get('type') == 'transcription.text.delta':
                text = event.get('delta', '')
                is_final = event.get('is_final', False)
                
                if text and (text != self.last_text or is_final):
                    self.on_transcription(text, is_final)
                    if is_final:
                        self.last_text = text
                        
        except Exception as e:
            logging.error(f"Qwen-ASR回调处理错误: {e}")
    
    def on_complete(self):
        """识别完成"""
        logging.info("Qwen-ASR识别完成")
    
    def on_error(self, error):
        """识别错误"""
        logging.error(f"Qwen-ASR识别错误: {error}")


class SpeechRecognitionService:
    """语音识别服务类"""
    
    def __init__(self, config: ASRConfig):
        self.config = config
        self.active_sessions: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
        # 配置DashScope API Key
        dashscope.api_key = config.api_key
        
        # 根据区域配置WebSocket URL
        if config.region == "cn-beijing":
            dashscope.base_websocket_api_url = 'wss://dashscope.aliyuncs.com/api-ws/v1/inference'
        else:  # 新加坡或其他区域
            dashscope.base_websocket_api_url = 'wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference'
    
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
    
    async def sync_recognition(self, audio_data: bytes, 
                             model_type: ASRModelType = None,
                             language: LanguageCode = None,
                             sample_rate: int = None) -> Dict[str, Any]:
        """同步语音识别"""
        try:
            model_type = model_type or self.config.model_type
            language = language or self.config.transcription_params.language
            sample_rate = sample_rate or self.config.transcription_params.sample_rate
            
            if model_type == ASRModelType.FUN_ASR_REALTIME:
                return await self._fun_asr_sync_recognition(audio_data, language, sample_rate)
            elif model_type == ASRModelType.QWEN_ASR_REALTIME:
                return await self._qwen_asr_sync_recognition(audio_data, language, sample_rate)
            else:
                raise ASRServiceError(f"不支持的模型类型: {model_type}")
                
        except Exception as e:
            self.logger.error(f"同步语音识别失败: {e}")
            raise ASRServiceError(f"语音识别失败: {str(e)}")
    
    async def _fun_asr_sync_recognition(self, audio_data: bytes, 
                                      language: LanguageCode, sample_rate: int) -> Dict[str, Any]:
        """Fun-ASR同步识别"""
        # 将音频数据保存为临时文件
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # 这里需要将音频数据转换为WAV格式
            # 简化实现，实际应该使用音频处理库
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            recognition = Recognition(
                model='fun-asr-realtime',
                format='wav',
                sample_rate=sample_rate
            )
            
            result = recognition.call(temp_file_path)
            
            if result.status_code == 200:
                return {
                    "text": result.get_sentence(),
                    "confidence": 0.95,  # Fun-ASR不直接提供置信度
                    "is_final": True,
                    "model_type": ASRModelType.FUN_ASR_REALTIME,
                    "language": language
                }
            else:
                raise ASRServiceError(f"Fun-ASR识别失败: {result.message}")
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    async def _qwen_asr_sync_recognition(self, audio_data: bytes, 
                                       language: LanguageCode, sample_rate: int) -> Dict[str, Any]:
        """Qwen-ASR同步识别"""
        # Qwen-ASR主要通过实时接口实现，这里使用实时接口模拟同步识别
        # 实际项目中应该使用专门的同步接口
        
        result_text = ""
        is_completed = False
        
        def on_transcription(text: str, is_final: bool):
            nonlocal result_text, is_completed
            result_text = text
            if is_final:
                is_completed = True
        
        # 创建实时会话
        session_id = f"sync_{int(time.time())}"
        await self.start_realtime_session(session_id, model_type=ASRModelType.QWEN_ASR_REALTIME, 
                                        on_transcription=on_transcription)
        
        # 发送音频数据
        await self.send_audio_data(session_id, audio_data, is_final=True)
        
        # 等待识别完成
        max_wait_time = 10  # 最大等待10秒
        start_time = time.time()
        while not is_completed and (time.time() - start_time) < max_wait_time:
            await asyncio.sleep(0.1)
        
        # 关闭会话
        await self.stop_realtime_session(session_id)
        
        return {
            "text": result_text,
            "confidence": 0.95,
            "is_final": True,
            "model_type": ASRModelType.QWEN_ASR_REALTIME,
            "language": language
        }
    
    async def start_realtime_session(self, session_id: str, 
                                   model_type: ASRModelType = None,
                                   on_transcription: Callable[[str, bool], None] = None) -> bool:
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
                                   on_transcription: Callable[[str, bool], None]) -> Recognition:
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
                                    on_transcription: Callable[[str, bool], None]) -> OmniRealtimeConversation:
        """启动Qwen-ASR实时会话"""
        callback = QwenASRCallback(on_transcription)
        
        conversation = OmniRealtimeConversation(
            model='qwen-audio-turbo',
            callback=callback
        )
        
        # 连接并配置会话
        conversation.connect()
        
        # 更新会话配置
        conversation.update_session(
            output_modalities=[MultiModality.TEXT],
            enable_turn_detection=self.config.vad_config.enabled,
            turn_detection_type=self.config.vad_config.type,
            turn_detection_threshold=self.config.vad_config.threshold,
            turn_detection_silence_duration_ms=self.config.vad_config.silence_duration_ms,
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            enable_input_audio_transcription=True
        )
        
        return conversation
    
    async def send_audio_data(self, session_id: str, audio_data: bytes, is_final: bool = False) -> bool:
        """发送音频数据到实时会话"""
        try:
            if session_id not in self.active_sessions:
                self.logger.error(f"会话 {session_id} 不存在")
                return False
            
            session_info = self.active_sessions[session_id]
            model_type = session_info["model_type"]
            
            if model_type == ASRModelType.FUN_ASR_REALTIME:
                return await self._send_fun_asr_audio(session_info["session"], audio_data, is_final)
            elif model_type == ASRModelType.QWEN_ASR_REALTIME:
                return await self._send_qwen_asr_audio(session_info["session"], audio_data, is_final)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"发送音频数据失败: {e}")
            return False
    
    async def _send_fun_asr_audio(self, recognition: Recognition, audio_data: bytes, is_final: bool) -> bool:
        """发送音频数据到Fun-ASR - 直接使用二进制数据"""
        try:
            # Fun-ASR通过send_audio_frame方法发送二进制音频数据
            recognition.send_audio_frame(audio_data)
            if is_final:
                recognition.stop()
            return True
        except Exception as e:
            self.logger.error(f"Fun-ASR发送音频失败: {e}")
            return False

    async def _send_qwen_asr_audio(self, conversation: OmniRealtimeConversation, 
                                 audio_data: bytes, is_final: bool) -> bool:
        """发送音频数据到Qwen-ASR - 将二进制转为base64传输"""
        try:
            # 将二进制音频数据转换为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 追加音频数据
            conversation.append_audio(audio_base64)
            
            if is_final:
                # 提交音频数据
                conversation.commit()
            
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
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        if session_id in self.active_sessions:
            session_info = self.active_sessions[session_id].copy()
            # 移除回调函数等敏感信息
            session_info.pop("on_transcription", None)
            session_info.pop("session", None)
            return session_info
        return None
    
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