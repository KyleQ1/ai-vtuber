"""
TTS Factory - Easy switching between different TTS providers
"""

from typing import Optional
from tts_interface import TTSInterface
from tts_service import TikTokTTSService
from tts_elevenlabs import ElevenLabsTTSService, ELEVENLABS_AVAILABLE


class TTSFactory:
    """Factory class for creating TTS service instances."""
    
    PROVIDERS = {
        "tiktok": TikTokTTSService,
        "elevenlabs": ElevenLabsTTSService,
    }
    
    @staticmethod
    def create(provider: str = "tiktok", **kwargs) -> TTSInterface:
        """
        Create a TTS service instance.
        
        Args:
            provider: Provider name ("tiktok" or "elevenlabs")
            **kwargs: Provider-specific configuration
                - For ElevenLabs: api_key (optional, uses env var if not provided)
        
        Returns:
            TTSInterface instance
        
        Raises:
            ValueError: If provider is unknown or unavailable
        
        Examples:
            # Use TikTok TTS
            tts = TTSFactory.create("tiktok")
            
            # Use ElevenLabs
            tts = TTSFactory.create("elevenlabs")
            tts = TTSFactory.create("elevenlabs", api_key="your-key-here")
        """
        provider = provider.lower()
        
        if provider not in TTSFactory.PROVIDERS:
            available = ", ".join(TTSFactory.PROVIDERS.keys())
            raise ValueError(f"Unknown TTS provider: {provider}. Available: {available}")
        
        # Special checks for providers with dependencies
        if provider == "elevenlabs" and not ELEVENLABS_AVAILABLE:
            raise ValueError(
                "ElevenLabs provider not available. "
                "Install with: pip install elevenlabs"
            )
        
        # Create instance
        provider_class = TTSFactory.PROVIDERS[provider]
        
        try:
            return provider_class(**kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create {provider} TTS service: {e}")
    
    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available provider names."""
        available = ["tiktok"]  # TikTok is always available
        
        if ELEVENLABS_AVAILABLE:
            available.append("elevenlabs")
        
        return available

