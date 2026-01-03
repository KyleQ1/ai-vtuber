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
```

## TTS Configuration - Easy Switching!

Open `main.py` and change these lines (around line 27):

```python
# Use TikTok TTS (free, no setup needed):
TTS_PROVIDER = "tiktok"
VOICE_OPTIONS = {"tiktok": ['en_us_001']}

# OR use ElevenLabs (better quality, needs API key):
# TTS_PROVIDER = "elevenlabs"
# VOICE_OPTIONS = {"elevenlabs": ['rachel']}
```

### To use ElevenLabs:
1. `pip install elevenlabs`
2. Get API key from https://elevenlabs.io
3. Add `ELEVENLABS_API_KEY=your_key` to `.env`
4. Change config in `main.py` to use `"elevenlabs"`

## Configuration

Edit settings in `main.py`:
```python
# TTS - Change provider here
TTS_PROVIDER = "tiktok"  # or "elevenlabs"

# Avatar
ENABLE_AVATAR = True
AVATAR_GAIN = 2.5
AVATAR_SMOOTHING = 0.7

# Text Display
ENABLE_TEXT_DISPLAY = True
TEXT_DISPLAY_STYLE = "progressive"
```

## OBS Text Display Setup

1. Add Source → Text (GDI+)
2. Check "Read from file"
3. Select `current_text.txt`
4. Style and position it

## Usage

```bash
python main.py
```

## Troubleshooting

**Avatar doesn't move**: Increase `AVATAR_GAIN` to 3.0-4.0

**Movement is jittery**: Increase `AVATAR_SMOOTHING` to 0.8-0.9

**TikTok TTS fails**: Proxy services may be down, try again later

**ElevenLabs fails**: Check API key in `.env` and account credits