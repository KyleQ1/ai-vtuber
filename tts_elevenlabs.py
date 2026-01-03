"""
ElevenLabs TTS Service
Handles text-to-speech generation using ElevenLabs API.
"""

import asyncio
import os
from typing import Optional
from tts_interface import TTSInterface

try:
    from elevenlabs import ElevenLabs, VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("⚠️ elevenlabs not installed. Install with: pip install elevenlabs")


# Popular ElevenLabs voice IDs (you can customize these)
ELEVENLABS_VOICES = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "domi": "AZnzlk1XvdvUeBnXmlld",
    "bella": "EXAVITQu4vr4xnSDxMaL",
    "antoni": "ErXwobaYiN019PkySvjV",
    "elli": "MF3mGyEYCl7XYWbV9V6O",
    "josh": "TxGEqnHWrfWFTfGW9XjX",
    "arnold": "VR6AewLTigWG4xSOukaG",
    "adam": "pNInz6obpgDQGcFmaJgB",
    "sam": "yoZ06aMxZJJ28mfd3POQ",
}


class ElevenLabsTTSService(TTSInterface):
    """Handles ElevenLabs TTS API calls."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs TTS service.
        
        Args:
            api_key: ElevenLabs API key. If None, reads from ELEVENLABS_API_KEY env var.
        """
        if not ELEVENLABS_AVAILABLE:
            raise ImportError("elevenlabs package not installed. Install with: pip install elevenlabs")
        
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables or constructor")
        
        self.client = ElevenLabs(api_key=self.api_key)
        
        # Voice settings for optimal streaming
        self.voice_settings = VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True
        )
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "ElevenLabs"
    
    def get_available_voices(self) -> list[str]:
        """Get available ElevenLabs voice names."""
        return list(ELEVENLABS_VOICES.keys())
    
    def get_max_text_length(self) -> int:
        """ElevenLabs supports longer texts."""
        return 5000
    
    async def generate(self, text: str, voice: str) -> Optional[bytes]:
        """
        Generate TTS audio from text using ElevenLabs API.
        
        Args:
            text: Text to convert to speech
            voice: Voice name (e.g., 'rachel', 'bella') or voice ID
            
        Returns:
            Audio data as MP3 bytes, or None if failed
        """
        # Truncate if too long
        if len(text) > self.get_max_text_length():
            text = text[:self.get_max_text_length()]
        
        # Map voice name to voice ID if needed
        voice_id = ELEVENLABS_VOICES.get(voice.lower(), voice)
        
        # Use asyncio.to_thread to avoid blocking the event loop
        return await asyncio.to_thread(self._generate_sync, text, voice_id)
    
    def _generate_sync(self, text: str, voice_id: str) -> Optional[bytes]:
        """Synchronous generation method (called via to_thread)."""
        try:
            # Generate audio
            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",  # Fast model for streaming
                voice_settings=self.voice_settings,
            )
            
            # Collect all audio chunks
            audio_chunks = []
            for chunk in audio_generator:
                if chunk:
                    audio_chunks.append(chunk)
            
            # Combine chunks into single bytes object
            audio_data = b''.join(audio_chunks)
            
            if audio_data:
                return audio_data
            else:
                print("❌ ElevenLabs returned empty audio")
                return None
                
        except Exception as e:
            print(f"❌ ElevenLabs API error: {e}")
            return None

