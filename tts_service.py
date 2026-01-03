"""
TikTok TTS Service
Handles text-to-speech generation using TikTok API endpoints.
"""

import requests
import base64
from typing import Optional


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


class TikTokTTSService:
    """Handles TikTok TTS API calls with automatic fallback."""
    
    @staticmethod
    def generate(text_speaker: str, req_text: str) -> Optional[bytes]:
        """Generate TTS audio from text using TikTok API."""
        # TikTok has a ~300 character limit per request
        if len(req_text) > 290:
            req_text = req_text[:290]
        
        # Try each endpoint until one works
        for endpoint in TIKTOK_TTS_ENDPOINTS:
            try:
                payload = {"text": req_text, "voice": text_speaker}
                response = requests.post(
                    endpoint["url"],
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                response_json = response.json()
                
                # Handle different response formats
                audio_data = TikTokTTSService._extract_audio(response_json, endpoint["response_type"])
                if audio_data:
                    return audio_data
                    
            except Exception as e:
                print(f"⚠️ Endpoint {endpoint['url']} failed: {e}")
                continue
        
        print("❌ All TTS endpoints failed")
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

