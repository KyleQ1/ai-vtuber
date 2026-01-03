"""
TTS Interface - Abstract base class for TTS providers
Allows easy switching between different TTS implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional


class TTSInterface(ABC):
    """Abstract base class for all TTS providers."""
    
    @abstractmethod
    async def generate(self, text: str, voice: str) -> Optional[bytes]:
        """
        Generate TTS audio from text.
        
        Args:
            text: Text to convert to speech
            voice: Voice identifier (provider-specific)
            
        Returns:
            Audio data as bytes (MP3 format), or None if generation failed
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> list[str]:
        """
        Get list of available voice identifiers for this provider.
        
        Returns:
            List of voice identifier strings
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this TTS provider.
        
        Returns:
            Provider name string
        """
        pass
    
    def get_max_text_length(self) -> int:
        """
        Get maximum text length supported by this provider.
        
        Returns:
            Maximum character count (default: 5000)
        """
        return 5000

