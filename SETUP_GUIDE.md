# Complete Setup Guide: VTube Studio + OBS + YouTube

## Step 1: Install and Setup VTube Studio

1. **Download VTube Studio** (if not already installed)
   - Get it from: https://store.steampowered.com/app/1922960/VTube_Studio/
   - Or from: https://denchisoft.com/

2. **Open VTube Studio**

3. **Enable API Access**:
   - Go to **Settings** (gear icon)
   - Find **"Plugin Security"** or **"API"** section
   - Enable **"Allow plugins to connect"**
   - Click **"Start API"** or **"Enable API"**
   - Note the port (usually `8001`)

4. **Load Your Avatar Model**:
   - Click **"Load Model"** or drag a `.vtube.json` file
   - Make sure the avatar is visible in the VTube Studio window

## Step 2: Connect Your Script to VTube Studio

1. **Make sure your script is configured** (in `main.py`):
   ```python
   ENABLE_AVATAR = True  # Should be True
   ```

2. **Run your script**:
   ```bash
   python main.py
   ```

3. **First-time connection**:
   - VTube Studio will show a popup asking to allow the plugin
   - Click **"Allow"** or **"Accept"**
   - A token file (`vts_token.json`) will be saved - you won't need to approve again

4. **Verify connection**:
   - You should see: `✓ VTube Studio integration: ENABLED`
   - The avatar should start moving its mouth when TTS plays

## Step 3: Add VTube Studio to OBS

Since you're streaming vertically, here's how to add the avatar:

### Option A: Window Capture (Recommended)

1. **In OBS**:
   - Right-click in **Sources** panel → **Add** → **Window Capture**
   - Name it: "VTube Studio Avatar"

2. **Configure Window Capture**:
   - **Window**: Select "VTube Studio" from dropdown
   - **Window Match Priority**: "Match title, also find window of same type"
   - ✅ Check **"Capture Cursor"** (optional)
   - ✅ Check **"Compatibility Mode"** (if you see black screen)

3. **Position and Resize**:
   - Click and drag the source to position it
   - Drag corners to resize to fit your vertical frame
   - Right-click → **Transform** → **Fit to Screen** (if needed)

### Option B: Game Capture (Alternative)

1. **In OBS**:
   - Right-click in **Sources** → **Add** → **Game Capture**
   - Name it: "VTube Studio"

2. **Configure**:
   - **Mode**: "Capture specific window"
   - **Window**: Select "VTube Studio"
   - **Allow Transparency**: ✅ (if supported)

### Option C: Display Capture (Last Resort)

If Window/Game capture doesn't work:
1. **Add** → **Display Capture**
2. Select the monitor where VTube Studio is running
3. Crop to just the VTube Studio window area

## Step 4: Add Text Display to OBS

1. **In OBS**:
   - Right-click in **Sources** → **Add** → **Text (GDI+)** or **Text (FreeType 2)**
   - Name it: "Current Speech"

2. **Configure Text Source**:
   - ✅ Check **"Read from file"**
   - Click **Browse** and select `current_text.txt` from your project folder
   - **Font**: Choose a readable font (e.g., Arial, Roboto)
   - **Size**: Adjust for your vertical layout (maybe 24-32px)
   - **Color**: Choose a visible color (white with black outline works well)
   - **Outline**: Add outline for readability

3. **Position**:
   - Place it where you want text to appear (maybe bottom of frame for vertical)
   - Make sure it doesn't overlap the avatar

## Step 5: Arrange Your Scene (Vertical Layout)

For a vertical YouTube stream, typical layout:

```
┌─────────────────┐
│                 │
│   VTube Studio  │
│     Avatar      │
│   (centered)    │
│                 │
│                 │
│  Current Text   │
│   (bottom)      │
└─────────────────┘
```

**Tips**:
- Center the avatar vertically
- Keep text at bottom with padding
- Consider adding a background or border
- Test with **Preview** before going live

## Step 6: Test Everything

1. **Start your script**: `python main.py`
2. **Check OBS Preview**:
   - Avatar should be visible
   - Avatar mouth should move when TTS plays
   - Text should appear word-by-word
3. **Test Stream**:
   - Use **Start Recording** first to test
   - Then **Start Streaming** to YouTube

## Troubleshooting

### Avatar Not Visible in OBS
- Try **Compatibility Mode** in Window Capture
- Try Game Capture instead
- Make sure VTube Studio window is not minimized
- Restart both VTube Studio and OBS

### Avatar Not Moving
- Check console output: Should see `✓ VTube Studio integration: ENABLED`
- Increase `AVATAR_GAIN` to 3.0 or 4.0 in `main.py`
- Make sure VTube Studio API is enabled and started
- Check that a model is loaded in VTube Studio

### Text Not Appearing
- Check that `ENABLE_TEXT_DISPLAY = True` in `main.py`
- Verify `current_text.txt` file exists in project folder
- Make sure OBS text source is pointing to the correct file path
- Check file permissions

### Connection Issues
- Make sure VTube Studio is running BEFORE starting your script
- Check that API is enabled in VTube Studio settings
- Delete `vts_token.json` and reconnect if needed
- Check firewall isn't blocking port 8001

## Quick Checklist

- [ ] VTube Studio installed and running
- [ ] API enabled in VTube Studio settings
- [ ] Avatar model loaded in VTube Studio
- [ ] Script connects successfully (see "ENABLED" message)
- [ ] VTube Studio window visible in OBS (Window/Game Capture)
- [ ] Text source added and reading from `current_text.txt`
- [ ] Avatar mouth moves when TTS plays
- [ ] Text appears word-by-word
- [ ] Everything positioned correctly for vertical layout

You're ready to stream! 🎉

