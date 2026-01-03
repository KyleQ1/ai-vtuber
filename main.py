import asyncio
import random
import os
import tempfile
import io
from typing import Optional, List
from dotenv import load_dotenv
from openai import OpenAI
from avatar_controller import AvatarController
from tts_service import TikTokTTSService
import pytchat

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️ pygame not installed. Install with: pip install pygame")

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

# Available voices from: https://github.com/mark-rez/TikTok-Voice-TTS
ENERGETIC_VOICES = [
    'en_us_002',  # US Female 2 - young and energetic
]

# OpenAI Configuration
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 1.4
OPENAI_MAX_TOKENS = 120

# Phase switching configuration
PHASE_DURATION_MIN = 3
PHASE_DURATION_MAX = 5

# Audio playback configuration
AUDIO_SPEED = 1.3  # Playback speed multiplier
AUDIO_PAUSE_MIN = 0.05
AUDIO_PAUSE_MAX = 0.15

# Avatar configuration
ENABLE_AVATAR = True  # Set to False to disable VTube Studio integration
AVATAR_GAIN = 2.5     # Mouth movement sensitivity
AVATAR_SMOOTHING = 0.7  # Temporal smoothing factor

# YouTube Live Chat configuration
YOUTUBE_VIDEO_ID = os.environ.get("YOUTUBE_VIDEO_ID")  # Video ID from YouTube URL

# Text display configuration
ENABLE_TEXT_DISPLAY = True
TEXT_DISPLAY_FILE = "current_text.txt"
TEXT_DISPLAY_STYLE = "progressive"  # "progressive" (word-by-word) or "full" (all at once)

# ============================================================================
# AI PROMPTS
# ============================================================================

SEARCHING_PROMPT = """You are an energetic, witty livestreamer helping viewers find hidden objects in a Simpsons living room scene.

THE MISSION: Find 4 hidden objects - Pacifier, Donut, Duff Beer Can, and Green Fuel Rod

ACTUAL OBJECT LOCATIONS (describe these to help viewers):
- Pacifier: Under the coffee table, on the pink/purple rug beneath the table
- Donut: Under the coffee table, on the rug (near center bottom)
- Duff beer can: On the floor near the TV/entertainment center on the right side
- Green fuel rod: Hidden behind the potted plant (viewers can't see it yet - this is the SECRET)

CRITICAL RULES:
- ALWAYS start by addressing chat directly ("Alright chat", "Okay everyone", "Listen chat", "Hey guys", etc.)
- ALWAYS mention the mission/goal (finding the 4 objects, completing the challenge, etc.)
- Then HELP viewers by describing WHERE the visible objects are
- Guide them to specific locations with clear directions
- End with confusion about the fuel rod
- Keep under 280 characters total

Structure: [Chat greeting] + [Mission reminder] + [Object locations] + [Fuel rod confusion]

Examples:
- "Alright chat, we're hunting for 4 objects here! Pacifier and donut are both under that coffee table on the rug. Duff can is by the TV. But where's the fuel rod?!"
- "Okay everyone, mission is to find 4 things. I see the pacifier under the table, donut on the rug, beer by the TV stand... but this fuel rod has me stumped!"
- "Listen chat, we need all 4 objects to complete this. Check under the coffee table for pacifier and donut, TV area for the beer. The fuel rod though? No clue."

Generate ONE line that greets chat, reminds them of the mission, helps find objects, and shows fuel rod confusion."""

REVEALING_PROMPT = """You are an energetic, witty livestreamer who finally KNOWS where the green fuel rod is hidden. You're trying to get donations to reveal its location.

THE MISSION: Find 4 hidden objects - we've found 3, but the FUEL ROD is the final piece!

THE SECRET: The green fuel rod is hidden BEHIND THE POTTED PLANT (the plant on the right side of the room)

CRITICAL RULES:
- ALWAYS start by addressing chat directly ("Alright chat", "Okay everyone", "Listen up chat", "Hey chat", etc.)
- ALWAYS remind them we need the LAST object (fuel rod) to complete the mission/challenge
- Tease that you know the SPECIFIC location but need donations first
- Need THREE donations/gifts to reveal it
- Be playful and witty about the donation pitch
- Keep under 280 characters total

Structure: [Chat greeting] + [Mission reminder/last object needed] + [Tease secret] + [Donation request]

Examples:
- "Alright chat, we found 3 out of 4 but need that fuel rod to complete this! I literally know where it is now. Three gifts and I'll show you exactly where!"
- "Okay everyone, last object to finish the challenge is that fuel rod. And guess what? I found it! Three donations and the secret location is yours chat."
- "Listen chat, we're SO close to finishing this - just need the fuel rod! I know the exact hiding spot but that's three dancing discos worth of info!"
- "Hey chat, final piece of the puzzle is the fuel rod and I've got the answer! Three gifts to complete the mission together. Let's finish this!"

Generate ONE line that greets chat, reminds them of the mission status, teases your secret knowledge, and requests donations."""

class OpenAIService:
    """Handles OpenAI API interactions for generating dynamic content."""
    
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
    
    async def generate_line(self, is_searching: bool, chat_context: Optional[List[str]] = None) -> str:
        """Generate a new line based on current phase and optional chat context."""
        try:
            prompt = SEARCHING_PROMPT if is_searching else REVEALING_PROMPT
            phase_name = "searching" if is_searching else "revealing"
            
            user_message = f"Generate one energetic {phase_name} line:"
            if chat_context:
                user_message += f"\n\nRecent chat messages for context: {', '.join(chat_context[-3:])}"
            
            response = await asyncio.to_thread(
                lambda: self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=OPENAI_MAX_TOKENS,
                    temperature=OPENAI_TEMPERATURE,
                )
            )
            
            line = response.choices[0].message.content.strip()
            # Remove quotes if AI wrapped the response
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            return line
            
        except Exception as e:
            print(f"⚠️ OpenAI error: {e}")
            return self._get_fallback_line(is_searching)
    
    def _get_fallback_line(self, is_searching: bool) -> str:
        """Return a fallback line if OpenAI fails."""
        if is_searching:
            return random.choice([
                "I see the pacifier! I see the donut! I see the beer can! BUT WHERE IS THE GREEN FUEL ROD?!",
                "Okay guys, I found the pacifier, the donut, the beer can... but the green fuel rod? WHERE IS IT?!",
                "OMG I see three objects but WHERE IS THAT GREEN FUEL ROD?! You guys help me find it!",
            ])
        else:
            return random.choice([
                "I know where the green fuel rod is! But we need three people to click the present button and send a dancing disco!",
                "Guys I can reveal the secret! But first we need donations! Click that present button!",
                "The green fuel rod location? I know it! But we need three dancing discos first! Click the present!",
            ])


class YouTubeChatService:
    """Handles YouTube Live Chat integration using pytchat."""
    
    def __init__(self, video_id: Optional[str] = None):
        self.video_id = video_id
        self.chat = None
        self.processed_message_ids = set()
        self.recent_messages = []
        self.unread_messages = []
        
        if video_id and pytchat:
            try:
                self.chat = pytchat.create(video_id=video_id)
            except Exception as e:
                print(f"⚠️ Failed to initialize pytchat: {e}")
                self.chat = None
    
    def is_configured(self) -> bool:
        """Check if YouTube chat is properly configured."""
        return bool(self.video_id and pytchat and self.chat)
    
    async def poll_chat(self) -> List[dict]:
        """Poll YouTube Live Chat for new messages."""
        if not self.is_configured():
            return []
        
        try:
            if not self.chat.is_alive():
                return []
            
            new_messages = []
            while self.chat.has_more():
                chat_data = self.chat.get()
                for c in chat_data.items:
                    message_id = c.id
                    if message_id not in self.processed_message_ids:
                        self.processed_message_ids.add(message_id)
                        msg = {
                            "id": message_id,
                            "text": c.message,
                            "author": c.author.name,
                            "timestamp": c.timestamp
                        }
                        new_messages.append(msg)
                        self.unread_messages.append(msg)
                        self.recent_messages.append(c.message)
                        if len(self.recent_messages) > 10:
                            self.recent_messages.pop(0)
            
            return new_messages
            
        except Exception as e:
            print(f"⚠️ YouTube Chat error: {e}")
            return []
    
    def get_random_unread_message(self) -> Optional[dict]:
        """Get a random unread chat message and mark it as read."""
        if not self.unread_messages:
            return None
        msg = random.choice(self.unread_messages)
        self.unread_messages.remove(msg)
        return msg
    
    def get_recent_context(self) -> List[str]:
        """Get recent chat messages for AI context."""
        return self.recent_messages.copy()


class TextDisplayManager:
    """Manages progressive text display for OBS/streaming overlay."""
    
    def __init__(self, file_path: str = TEXT_DISPLAY_FILE, enabled: bool = ENABLE_TEXT_DISPLAY):
        self.file_path = file_path
        self.enabled = enabled
        self.current_text = ""
        
        if self.enabled:
            self._clear_display()
    
    def _clear_display(self):
        """Clear the display file."""
        if not self.enabled:
            return
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write("")
        except Exception as e:
            print(f"⚠️ Error clearing text display: {e}")
    
    def _update_display(self, text: str):
        """Update the display file with text."""
        if not self.enabled:
            return
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            print(f"⚠️ Error updating text display: {e}")
    
    async def display_progressive(self, text: str, duration: float):
        """
        Display text progressively, word by word, synced with audio duration.
        
        Args:
            text: Full text to display
            duration: Total duration of audio in seconds
        """
        if not self.enabled:
            return
        
        words = text.split()
        if not words:
            return
        
        time_per_word = duration / len(words)
        displayed_words = []
        
        for word in words:
            displayed_words.append(word)
            self.current_text = " ".join(displayed_words)
            self._update_display(self.current_text)
            await asyncio.sleep(time_per_word)
        
        await asyncio.sleep(0.5)
        self._clear_display()
    
    def display_full(self, text: str):
        """Display full text immediately."""
        if not self.enabled:
            return
        self.current_text = text
        self._update_display(text)
    
    def clear(self):
        """Clear the current text."""
        self._clear_display()
        self.current_text = ""


class AudioPlayer:
    """Handles audio playback using mpv with avatar sync support."""
    
    @staticmethod
    def estimate_duration(text: str, speed: float = AUDIO_SPEED) -> float:
        """
        Estimate audio duration based on text length.
        Rough estimate: ~150 words per minute at normal speed.
        """
        words = len(text.split())
        base_duration = (words / 150) * 60
        return base_duration / speed
    
    @staticmethod
    async def play(audio_data: bytes, speed: float = AUDIO_SPEED, 
                   avatar_controller: Optional[AvatarController] = None) -> None:
        """
        Play audio data using mpv while updating avatar lip-sync.
        
        Args:
            audio_data: MP3 audio data
            speed: Playback speed multiplier
            avatar_controller: Optional avatar controller for lip-sync
        """
        if not audio_data:
            return
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        try:
            if avatar_controller and avatar_controller.authenticated:
                await asyncio.gather(
                    AudioPlayer._play_audio(tmp_path, speed),
                    AudioPlayer._animate_avatar(audio_data, avatar_controller, speed)
                )
            else:
                await AudioPlayer._play_audio(tmp_path, speed)
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    @staticmethod
    async def _play_audio(file_path: str, speed: float) -> None:
        """Play audio file using pygame (cross-platform) or mpv (if available)."""
        # Try pygame first (cross-platform, works on Windows)
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.load(file_path)
                # Note: pygame doesn't support speed directly, but we can work around it
                pygame.mixer.music.play()
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                return
            except Exception as e:
                print(f"⚠️ pygame playback failed: {e}, trying mpv...")
        
        # Fallback to mpv if available
        try:
            process = await asyncio.create_subprocess_exec(
                "mpv", "--no-video", f"--speed={speed}", "--really-quiet", file_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
        except FileNotFoundError:
            raise RuntimeError(
                "No audio player available. Install pygame (pip install pygame) or mpv."
            )
    
    @staticmethod
    async def _animate_avatar(audio_data: bytes, avatar_controller: AvatarController, 
                             speed: float) -> None:
        """
        Animate avatar mouth based on audio amplitude.
        
        Processes audio in chunks and updates mouth parameter in real-time.
        """
        try:
            chunk_size = 4096
            chunk_duration = 0.05 / speed
            
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                await avatar_controller.update_mouth_from_audio(chunk)
                await asyncio.sleep(chunk_duration)
            
            await avatar_controller.reset_mouth()
            
        except Exception as e:
            print(f"⚠️ Avatar animation error: {e}")

class PhaseManager:
    """Manages the two-phase system (searching vs revealing)."""
    
    def __init__(self):
        self.is_searching = True
        self.phase_line_count = 0
        self.phase_duration = random.randint(PHASE_DURATION_MIN, PHASE_DURATION_MAX)
    
    def should_switch_phase(self) -> bool:
        """Check if it's time to switch phases."""
        return self.phase_line_count >= self.phase_duration
    
    def switch_phase(self) -> str:
        """Switch to the opposite phase and return phase name."""
        self.is_searching = not self.is_searching
        self.phase_line_count = 0
        self.phase_duration = random.randint(PHASE_DURATION_MIN, PHASE_DURATION_MAX)
        return "🔍 SEARCHING" if self.is_searching else "💰 REVEALING"
    
    def increment(self):
        """Increment the line count for current phase."""
        self.phase_line_count += 1
    
    def get_phase_indicator(self) -> str:
        """Get emoji indicator for current phase."""
        return "🔍" if self.is_searching else "💰"


async def audio_producer(
    queue: asyncio.Queue,
    line_count_ref: list,
    openai_service: OpenAIService,
    youtube_chat: YouTubeChatService,
    phase_manager: PhaseManager
):
    """Producer: Generate AI lines and TTS audio in the background."""
    while True:
        try:
            if phase_manager.should_switch_phase():
                phase_name = phase_manager.switch_phase()
                print(f"\n{'='*60}")
                print(f"🔄 PHASE SWITCH: Now {phase_name} mode")
                print(f"{'='*60}\n")
            
            # 30% chance to respond to a chat message if available
            chat_message = None
            if youtube_chat.is_configured() and random.random() < 0.3:
                chat_message = youtube_chat.get_random_unread_message()
            
            if chat_message:
                # Generate response to chat message
                print(f"\n💬 Responding to: [{chat_message['author']}]: {chat_message['text']}")
                line = await openai_service.generate_line(
                    phase_manager.is_searching,
                    [chat_message['text']]
                )
            else:
                # Generate normal line with general context
                chat_context = youtube_chat.get_recent_context() if youtube_chat.is_configured() else None
                line = await openai_service.generate_line(
                    phase_manager.is_searching,
                    chat_context
                )
            
            voice = random.choice(ENERGETIC_VOICES)
            
            line_count_ref[0] += 1
            phase_manager.increment()
            count = line_count_ref[0]
            phase_indicator = phase_manager.get_phase_indicator()
            
            print(f"\n🎤 [{count}] {phase_indicator} Voice: {voice}")
            print(f"💬 AI Generated: {line[:100]}{'...' if len(line) > 100 else ''}")
            
            audio_data = await asyncio.to_thread(TikTokTTSService.generate, voice, line)
            
            if audio_data:
                await queue.put((audio_data, count, line))
                print(f"✓ Generated TTS ({len(audio_data)} bytes) - queued")
            else:
                print("✗ Failed to generate audio - skipping this line")
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"⚠️ Producer error: {e}")
            await asyncio.sleep(1.0)


async def audio_consumer(queue: asyncio.Queue, 
                        avatar_controller: Optional[AvatarController] = None,
                        text_display: Optional[TextDisplayManager] = None):
    """
    Consumer: Play audio from queue and sync with avatar and text display.
    
    Args:
        queue: Audio queue containing (audio_data, count, text) tuples
        avatar_controller: Optional avatar controller for lip-sync
        text_display: Optional text display manager for progressive text
    """
    while True:
        try:
            audio_data, count, text = await queue.get()
            
            if text_display and TEXT_DISPLAY_STYLE == "progressive":
                duration = AudioPlayer.estimate_duration(text, AUDIO_SPEED)
                await asyncio.gather(
                    AudioPlayer.play(audio_data, AUDIO_SPEED, avatar_controller),
                    text_display.display_progressive(text, duration)
                )
            else:
                if text_display:
                    text_display.display_full(text)
                await AudioPlayer.play(audio_data, AUDIO_SPEED, avatar_controller)
                if text_display:
                    await asyncio.sleep(0.5)
                    text_display.clear()
            
            print(f"✓ [{count}] Played successfully")
            
            queue.task_done()
            
            await asyncio.sleep(random.uniform(AUDIO_PAUSE_MIN, AUDIO_PAUSE_MAX))
            
        except Exception as e:
            print(f"⚠️ Consumer error: {e}")
            await asyncio.sleep(0.5)


async def youtube_chat_monitor(youtube_chat: YouTubeChatService):
    """Monitor YouTube chat and print new messages."""
    if not youtube_chat.is_configured():
        print("⚠️ YouTube Chat not configured - skipping chat monitoring")
        return
    
    print("📺 YouTube Chat monitoring started\n")
    
    while True:
        try:
            messages = await youtube_chat.poll_chat()
            for msg in messages:
                print(f"💬 [{msg['author']}]: {msg['text']}")
            
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"⚠️ Chat monitor error: {e}")
            await asyncio.sleep(1)


async def test_tts():
    """Test if the TikTok TTS endpoints work."""
    print("🔍 Testing TikTok TTS endpoints...")
    
    test_voice = ENERGETIC_VOICES[0]
    print(f"   Testing with voice: {test_voice}")
    test_audio = TikTokTTSService.generate(test_voice, "Hello")
    
    if test_audio:
        print(f"✓ TTS works with {test_voice}! Generated {len(test_audio)} bytes")
        return True
    
    print("\n✗ All TTS endpoints failed")
    print("\n🔍 Possible issues:")
    print("   1. The TTS proxy services might be down")
    print("   2. Network connectivity issues")
    print("   3. API endpoints may have changed")
    print("\n💡 Try checking if the endpoints are still active")
    return False

async def main():
    """Main application entry point."""
    print("🎀✨ AI Energetic Livestreamer Started! ✨🎀")
    print(f"Using TikTok voices: {', '.join(ENERGETIC_VOICES)}")
    print("🤖 Powered by OpenAI for dynamic content generation")
    print("⚡ Pipeline mode: Generating next audio while current plays!")
    print("🔄 Two-phase system: SEARCHING for objects → REVEALING secret for donations")
    
    try:
        openai_service = OpenAIService()
    except ValueError as e:
        print(f"\n❌ {e}")
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    youtube_chat = YouTubeChatService(YOUTUBE_VIDEO_ID)
    if youtube_chat.is_configured():
        print("📺 YouTube Chat integration: ENABLED")
    else:
        if not pytchat:
            print("📺 YouTube Chat integration: DISABLED (install pytchat: pip install pytchat)")
        else:
            print("📺 YouTube Chat integration: DISABLED (set YOUTUBE_VIDEO_ID in .env to enable)")
    
    avatar_controller = None
    if ENABLE_AVATAR:
        try:
            print("\n🎭 Initializing Live2D Avatar Controller...")
            avatar_controller = AvatarController(
                plugin_name="Neuro-sama TTS Controller",
                plugin_developer="AI Livestreamer",
                token_path="vts_token.json",
                gain=AVATAR_GAIN,
                smoothing=AVATAR_SMOOTHING
            )
            
            if await avatar_controller.connect():
                print("✓ VTube Studio integration: ENABLED")
                
                # Get current model info
                model_info = await avatar_controller.get_current_model()
                if model_info:
                    print(f"   Model: {model_info.get('modelName', 'Unknown')}")
                
                await avatar_controller.set_emotion("happy")
            else:
                print("⚠️ VTube Studio integration: DISABLED (connection failed)")
                avatar_controller = None
                
        except Exception as e:
            print(f"⚠️ Avatar controller initialization failed: {e}")
            print("   Continuing without avatar control...")
            avatar_controller = None
    else:
        print("\n🎭 Live2D Avatar: DISABLED (set ENABLE_AVATAR=True to enable)")
    
    text_display = TextDisplayManager()
    if ENABLE_TEXT_DISPLAY:
        mode = "word-by-word" if TEXT_DISPLAY_STYLE == "progressive" else "full text"
        print(f"\n📝 Text display: ENABLED ({mode})")
        print(f"   File: {TEXT_DISPLAY_FILE}")
        print("   Add this file as a Text (GDI+) source in OBS")
    else:
        print("\n📝 Text display: DISABLED")
    
    print()
    
    if not await test_tts():
        print("\n⚠️  Continuing anyway, but TTS may fail...\n")
    
    print("Press Ctrl+C to stop\n")
    
    audio_queue = asyncio.Queue(maxsize=1)
    line_count = [0]
    phase_manager = PhaseManager()
    
    tasks = [
        asyncio.create_task(audio_producer(audio_queue, line_count, openai_service, youtube_chat, phase_manager)),
        asyncio.create_task(audio_consumer(audio_queue, avatar_controller, text_display)),
        asyncio.create_task(youtube_chat_monitor(youtube_chat)),
    ]
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        if avatar_controller:
            print("\n🎭 Disconnecting avatar controller...")
            await avatar_controller.disconnect()
        
        if text_display and text_display.enabled:
            print("📝 Clearing text display...")
            text_display.clear()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Livestream ended! Thanks for watching~! 💕")
