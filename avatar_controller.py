"""
Live2D Avatar Controller for VTube Studio Integration
Analyzes audio streams and controls lip-sync and expressions in real-time.
"""

import asyncio
import json
import os
import numpy as np
from typing import Optional, Dict
from pathlib import Path

try:
    import pyvts
except ImportError:
    print("⚠️ pyvts not installed. Install with: pip install pyvts")
    pyvts = None


class AvatarController:
    """
    Controls Live2D model in VTube Studio using audio analysis.
    
    Features:
    - RMS-based mouth movement from audio amplitude
    - Temporal smoothing for fluid animations
    - Token persistence for seamless reconnection
    - Async operation to prevent audio blocking
    - Emotion/expression control
    """
    
    # Audio processing constants
    SAMPLE_RATE = 24000  # TikTok TTS sample rate
    CHUNK_SIZE = 2048    # Audio chunk size for processing
    
    # Mouth animation constants
    GAIN = 2.5           # Amplification factor for mouth movement sensitivity
    SMOOTHING_FACTOR = 0.7  # EMA smoothing (0-1, higher = smoother but slower response)
    SILENCE_THRESHOLD = 0.01  # Below this RMS, mouth stays closed
    
    # VTube Studio parameter names
    PARAM_MOUTH_OPEN = "MouthOpen"
    PARAM_MOUTH_FORM = "MouthForm"
    
    def __init__(self, 
                 plugin_name: str = "Neuro-sama TTS Controller",
                 plugin_developer: str = "AI Livestreamer",
                 token_path: str = "vts_token.json",
                 gain: float = GAIN,
                 smoothing: float = SMOOTHING_FACTOR):
        """
        Initialize the Avatar Controller.
        
        Args:
            plugin_name: Name displayed in VTube Studio
            plugin_developer: Developer name for VTube Studio
            token_path: Path to save/load authentication token
            gain: Sensitivity multiplier for mouth movement
            smoothing: Smoothing factor for temporal smoothing (0-1)
        """
        if pyvts is None:
            raise ImportError("pyvts is required. Install with: pip install pyvts")
        
        self.plugin_name = plugin_name
        self.plugin_developer = plugin_developer
        self.token_path = Path(token_path)
        self.gain = gain
        self.smoothing = smoothing
        
        # VTube Studio connection
        self.vts: Optional[pyvts.vts] = None
        self.connected = False
        self.authenticated = False
        
        # State tracking
        self.current_mouth_value = 0.0  # Smoothed mouth open value
        self.current_emotion = 0.0      # Current mouth form (emotion)
        
        # Task management
        self.update_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        print(f"🎭 AvatarController initialized")
        print(f"   Gain: {self.gain}")
        print(f"   Smoothing: {self.smoothing}")
    
    async def connect(self, port: int = 8001) -> bool:
        """
        Connect to VTube Studio WebSocket API.
        
        Args:
            port: VTube Studio API port (default 8001)
            
        Returns:
            True if connection and authentication successful
        """
        try:
            print(f"🔌 Connecting to VTube Studio on port {port}...")
            
            # Initialize pyvts
            self.vts = pyvts.vts(
                plugin_info={
                    "plugin_name": self.plugin_name,
                    "developer": self.plugin_developer,
                    "authentication_token_path": str(self.token_path),
                }
            )
            
            # Connect to VTube Studio
            await self.vts.connect()
            self.connected = True
            print("✓ Connected to VTube Studio")
            
            # Authenticate
            await self._authenticate()
            
            if self.authenticated:
                print("✓ Avatar Controller ready!")
                return True
            else:
                print("✗ Authentication failed")
                return False
                
        except Exception as e:
            print(f"✗ Failed to connect to VTube Studio: {e}")
            print("   Make sure VTube Studio is running with API enabled")
            print("   (Settings → Allow plugins → Start API)")
            self.connected = False
            return False
    
    async def _authenticate(self):
        """Authenticate with VTube Studio."""
        try:
            print("🔑 Authenticating with VTube Studio...")
            
            # Check if token already exists and works
            if self.token_path.exists():
                try:
                    response = await self.vts.request_authenticate()
                    if response and isinstance(response, dict) and response.get('data', {}).get('authenticated'):
                        self.authenticated = True
                        print("✓ Authenticated with saved token")
                        return
                    else:
                        # Token invalid, delete it
                        self.token_path.unlink()
                        print("⚠️ Old token invalid, requesting new one...")
                except Exception as e:
                    print(f"⚠️ Token check failed: {e}")
                    try:
                        self.token_path.unlink()
                    except:
                        pass
            
            # Request new token - THIS SHOWS THE POPUP
            print("\n🔑 REQUESTING NEW TOKEN...")
            print("   👀 LOOK AT VTUBE STUDIO - CLICK 'ALLOW' IN POPUP")
            print("   ⏳ Waiting for you to click...\n")
            
            # This shows the popup and waits. The token is saved automatically to the file.
            # The return value doesn't matter - pyvts saves it to authentication_token_path
            await self.vts.request_authenticate_token()
            
            print("✓ Token request completed (saved to file)")
            
            # Now authenticate with the saved token
            await asyncio.sleep(0.5)
            response = await self.vts.request_authenticate()
            
            # Handle different response types
            if response is True:
                self.authenticated = True
                print("✓ Authenticated successfully!")
            elif isinstance(response, dict) and response.get('data', {}).get('authenticated'):
                self.authenticated = True
                print("✓ Authenticated successfully!")
            else:
                self.authenticated = False
                print(f"✗ Authentication failed: {response}")
                
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            self.authenticated = False
    
    # Token management is now handled by pyvts via authentication_token_path
    # These methods are kept for backward compatibility but not used
    
    async def disconnect(self):
        """Disconnect from VTube Studio."""
        if self.vts and self.connected:
            try:
                await self.vts.close()
                print("🔌 Disconnected from VTube Studio")
            except Exception as e:
                print(f"⚠️ Error during disconnect: {e}")
        
        self.connected = False
        self.authenticated = False
    
    def calculate_rms(self, audio_data: bytes) -> float:
        """
        Calculate Root Mean Square (RMS) of audio data.
        
        RMS measures the overall loudness/amplitude of the audio signal.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            RMS value normalized to 0.0-1.0 range
        """
        try:
            # Convert bytes to numpy array
            # Assuming 16-bit PCM audio (most common format)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            
            # Normalize to 0-1 range (16-bit audio max is 32768)
            normalized_rms = rms / 32768.0
            
            # Apply gain
            amplified = normalized_rms * self.gain
            
            # Clamp to 0-1
            return min(1.0, max(0.0, amplified))
            
        except Exception as e:
            print(f"⚠️ RMS calculation error: {e}")
            return 0.0
    
    def apply_smoothing(self, new_value: float) -> float:
        """
        Apply exponential moving average (EMA) smoothing.
        
        This prevents jittery mouth movements by smoothly transitioning
        between values instead of instant jumps.
        
        Args:
            new_value: New RMS value
            
        Returns:
            Smoothed value
        """
        # EMA formula: smoothed = alpha * current + (1 - alpha) * new
        self.current_mouth_value = (
            self.smoothing * self.current_mouth_value + 
            (1 - self.smoothing) * new_value
        )
        
        # Apply silence threshold
        if self.current_mouth_value < self.SILENCE_THRESHOLD:
            self.current_mouth_value = 0.0
        
        return self.current_mouth_value
    
    async def update_mouth_from_audio(self, audio_data: bytes):
        """
        Process audio chunk and update mouth parameter in VTube Studio.
        
        This is the main method to call from your TTS streaming loop.
        
        Args:
            audio_data: Raw audio bytes from TTS stream
        """
        if not self.authenticated:
            return
        
        try:
            # Calculate RMS amplitude
            rms = self.calculate_rms(audio_data)
            
            # Apply temporal smoothing
            smoothed_value = self.apply_smoothing(rms)
            
            # Update VTube Studio parameter (non-blocking)
            await self._set_parameter(self.PARAM_MOUTH_OPEN, smoothed_value)
            
        except Exception as e:
            print(f"⚠️ Error updating mouth: {e}")
    
    async def set_emotion(self, emotion: str = "neutral"):
        """
        Set facial expression based on text sentiment.
        
        Args:
            emotion: One of "happy", "sad", "angry", "surprised", "neutral"
        """
        if not self.authenticated:
            return
        
        # Map emotions to MouthForm values
        emotion_map = {
            "happy": 1.0,      # Smile
            "excited": 1.0,    # Smile
            "neutral": 0.0,    # Neutral
            "sad": -0.5,       # Slight frown
            "angry": -1.0,     # Frown
            "surprised": 0.5,  # Slightly open
        }
        
        value = emotion_map.get(emotion.lower(), 0.0)
        self.current_emotion = value
        
        try:
            await self._set_parameter(self.PARAM_MOUTH_FORM, value)
            print(f"😊 Emotion set to: {emotion} (value: {value})")
        except Exception as e:
            print(f"⚠️ Error setting emotion: {e}")
    
    async def _set_parameter(self, parameter_name: str, value: float):
        """
        Set a parameter in VTube Studio.
        
        Args:
            parameter_name: Name of the Live2D parameter
            value: Value to set (-1.0 to 1.0 for most parameters)
        """
        if not self.vts or not self.authenticated:
            return
        
        try:
            await self.vts.request(
                self.vts.vts_request.requestSetParameterValue(
                    parameter=parameter_name,
                    value=value
                )
            )
        except Exception as e:
            # Silently fail for parameter updates to avoid spam
            # (parameters update many times per second)
            pass
    
    async def reset_mouth(self):
        """Reset mouth to closed position."""
        self.current_mouth_value = 0.0
        if self.authenticated:
            await self._set_parameter(self.PARAM_MOUTH_OPEN, 0.0)
    
    async def process_audio_stream(self, audio_data: bytes, chunk_size: int = 4096):
        """
        Process an entire audio stream in chunks.
        
        This method splits audio into chunks and processes each one.
        Call this when you have the full audio data.
        
        Args:
            audio_data: Complete audio data
            chunk_size: Size of chunks to process
        """
        if not self.authenticated:
            return
        
        # Process audio in chunks
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            await self.update_mouth_from_audio(chunk)
            # Small delay to match audio playback timing
            await asyncio.sleep(chunk_size / (self.SAMPLE_RATE * 2))  # 2 bytes per sample
    
    async def get_available_models(self) -> list:
        """Get list of available Live2D models in VTube Studio."""
        if not self.authenticated:
            return []
        
        try:
            response = await self.vts.request(
                self.vts.vts_request.requestAvailableModels()
            )
            models = response['data'].get('availableModels', [])
            return [model['modelName'] for model in models]
        except Exception as e:
            print(f"⚠️ Error getting models: {e}")
            return []
    
    async def get_current_model(self) -> Optional[Dict]:
        """Get currently loaded Live2D model info."""
        if not self.authenticated:
            return None
        
        try:
            response = await self.vts.request(
                self.vts.vts_request.requestCurrentModelInfo()
            )
            return response['data']
        except Exception as e:
            print(f"⚠️ Error getting current model: {e}")
            return None
    
    def __repr__(self) -> str:
        status = "authenticated" if self.authenticated else "not connected"
        return f"<AvatarController({status}, gain={self.gain}, smoothing={self.smoothing})>"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_usage():
    """Example of how to use AvatarController."""
    
    # Initialize controller
    controller = AvatarController(
        plugin_name="Test TTS Controller",
        gain=2.5,
        smoothing=0.7
    )
    
    # Connect to VTube Studio
    if await controller.connect():
        print("✓ Connected!")
        
        # Get current model info
        model = await controller.get_current_model()
        if model:
            print(f"Current model: {model.get('modelName', 'Unknown')}")
        
        # Set emotion
        await controller.set_emotion("happy")
        
        # Simulate processing audio chunks
        # In real usage, you'd get these from your TTS stream
        fake_audio = np.random.randint(-1000, 1000, 4096, dtype=np.int16).tobytes()
        
        for i in range(10):
            await controller.update_mouth_from_audio(fake_audio)
            await asyncio.sleep(0.1)
        
        # Reset mouth
        await controller.reset_mouth()
        
        # Disconnect
        await controller.disconnect()
    else:
        print("✗ Failed to connect to VTube Studio")


if __name__ == "__main__":
    # Run example
    print("🎭 AvatarController Example")
    print("Make sure VTube Studio is running with API enabled!\n")
    asyncio.run(example_usage())

