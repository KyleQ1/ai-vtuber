# AI Livestreamer with VTube Studio

An AI livestreamer that generates TTS content and animates a Live2D avatar using VTube Studio.

## Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Create `.env` file:
```
OPENAI_API_KEY=your_key_here
YOUTUBE_VIDEO_ID=your_video_id  # Optional: for chat integration (e.g., HCOWjMnvny8)
```

## VTube Studio Setup

1. Open VTube Studio
2. Go to Settings and enable "Allow plugins"
3. Click "Start API"
4. Run the script and click "Allow" when prompted (only needed once)

## Configuration

Edit settings in `main.py`:
```python
ENABLE_AVATAR = True      # Enable/disable VTube Studio
AVATAR_GAIN = 2.5         # Mouth movement sensitivity
AVATAR_SMOOTHING = 0.7    # Smoothing (higher = smoother)

ENABLE_TEXT_DISPLAY = True           # Enable/disable text overlay
TEXT_DISPLAY_FILE = "current_text.txt"  # Output file for OBS
TEXT_DISPLAY_STYLE = "progressive"   # "progressive" (word-by-word) or "full"
```

## OBS Text Display Setup

The system can display the current text being spoken, perfect for stream overlays:

1. **Enable in config** (already enabled by default):
```python
ENABLE_TEXT_DISPLAY = True
TEXT_DISPLAY_STYLE = "progressive"  # Shows text word-by-word as spoken
```

2. **Add to OBS**:
   - Add Source → Text (GDI+) or Text (FreeType 2)
   - Check "Read from file"
   - Select `current_text.txt` from the project directory
   - Style the text (font, color, size, etc.)
   - Position on your stream

3. **Display modes**:
   - `"progressive"` - Words appear one at a time as they're spoken (synchronized with audio)
   - `"full"` - Entire text appears at once, then clears when done

The text automatically clears between lines and stays synchronized with the audio playback!

## YouTube Live Chat Integration (Optional)

To enable chat reading, just add your video ID to `.env`:
```
YOUTUBE_VIDEO_ID=HCOWjMnvny8
```

The AI will read chat messages and use them as context. No API keys needed! Uses `pytchat` library.

## Usage

```bash
python main.py
```

The avatar will automatically sync lip movements with the TTS audio.

## How It Works

The system has three main components:

- `tts_service.py` - Handles TikTok TTS API calls
- `avatar_controller.py` - Controls VTube Studio WebSocket connection and lip-sync
- `main.py` - Orchestrates everything (AI generation, audio playback, avatar control)

The `AvatarController` analyzes audio amplitude using RMS calculation and controls the MouthOpen parameter in real-time. It uses exponential smoothing to prevent jittery movements.

Audio playback and avatar control run in parallel so there's no delay.

## Troubleshooting

**Avatar doesn't move**: Increase `AVATAR_GAIN` to 3.0-4.0

**Movement is jittery**: Increase `AVATAR_SMOOTHING` to 0.8-0.9

**Connection fails**: Make sure VTube Studio API is enabled and started