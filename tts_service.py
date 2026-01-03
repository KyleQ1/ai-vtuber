"""
TikTok TTS Service
Handles text-to-speech generation using TikTok API endpoints.
"""

import asyncio
import requests
import base64
from typing import Optional
from tts_interface import TTSInterface


# TikTok TTS API Endpoints (proxy services - no session ID needed!)
TIKTOK_TTS_ENDPOINTS = [
    {
        "url": "https://tiktok-tts.weilnet.workers.dev/api/generation",
        "response_type": "data"
    },
    {
        "url": "https://gesserit.co/api/tiktok-tts",
        "response_type": "base64"
    }
]


# Available TikTok voices from: https://github.com/mark-rez/TikTok-Voice-TTS
TIKTOK_VOICES = [
    'en_us_001',  # Cute energetic female voice
    'en_us_002',  # Male voice
    'en_us_006',  # Male 2
    'en_us_007',  # Female
    'en_us_009',  # Male 3
    'en_us_010',  # Male 4
]


class TikTokTTSService(TTSInterface):
    """Handles TikTok TTS API calls with automatic fallback."""
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "TikTok TTS"
    
    def get_available_voices(self) -> list[str]:
        """Get available TikTok voices."""
        return TIKTOK_VOICES
    
    def get_max_text_length(self) -> int:
        """TikTok has a 300 character limit."""
        return 290
    
    async def generate(self, text: str, voice: str) -> Optional[bytes]:
        """
        Generate TTS audio from text using TikTok API.
        
        Args:
            text: Text to convert to speech
            voice: TikTok voice identifier (e.g., 'en_us_001')
            
        Returns:
            Audio data as MP3 bytes, or None if failed
        """
        # TikTok has a ~300 character limit per request
        if len(text) > self.get_max_text_length():
            text = text[:self.get_max_text_length()]
        
        # Use asyncio.to_thread to avoid blocking the event loop
        return await asyncio.to_thread(self._generate_sync, voice, text)
    
    def _generate_sync(self, voice: str, text: str) -> Optional[bytes]:
        """Synchronous generation method (called via to_thread)."""
        # Try each endpoint until one works
        for endpoint in TIKTOK_TTS_ENDPOINTS:
            try:
                payload = {"text": text, "voice": voice}
                response = requests.post(
                    endpoint["url"],
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                response_json = response.json()
                
                # Handle different response formats
                audio_data = self._extract_audio(response_json, endpoint["response_type"])
                if audio_data:
                    return audio_data
                    
            except Exception as e:
                print(f"⚠️ Endpoint {endpoint['url']} failed: {e}")
                continue
        
        print("❌ All TikTok TTS endpoints failed")
        return None
    
    @staticmethod
    def _extract_audio(response_json: dict, response_type: str) -> Optional[bytes]:
        """Extract audio data from API response."""
        try:
            if response_type == "data":
                if "data" in response_json:
                    audio_data = response_json["data"]
                    if isinstance(audio_data, str):
                        return base64.b64decode(audio_data)
                    return audio_data
            else:  # base64
                if response_json.get("success") and "base64" in response_json:
                    return base64.b64decode(response_json["base64"])
                elif "data" in response_json:
                    return base64.b64decode(response_json["data"])
        except Exception as e:
            print(f"⚠️ Error extracting audio: {e}")
        return None

