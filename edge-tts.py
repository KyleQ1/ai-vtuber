import asyncio
import edge_tts
import os
import tempfile
from asyncio import Queue
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# --- CONFIGURATION ---
USE_OPENAI_TTS = False  # Set to False to use edge-tts instead (edge-tts sounds better!)

# OpenAI TTS voices (MUCH better quality, supports emotion):
# 'alloy' - neutral, balanced
# 'echo' - clear, expressive male
# 'fable' - British accent, warm
# 'onyx' - deep, authoritative male
# 'nova' - energetic, young female (GREAT for excited/frantic)
# 'shimmer' - soft, gentle female
# 'ash' - clear, versatile
# 'coral' - warm, engaging
# 'sage' - clear, professional
OPENAI_VOICE = "nova"  # Best for excited/frantic energy

# Edge-TTS voice (if USE_OPENAI_TTS is False)
# en-US-AvaNeural, en-US-JennyNeural, en-US-GuyNeural, en-US-DavisNeural
# en-US-AriaNeural (very expressive), en-US-EmmaNeural (energetic)
EDGE_VOICE = "en-US-AriaNeural"  # More expressive and energetic

# Voice instructions for emotion control (OpenAI only)
VOICE_INSTRUCTIONS = "Speak with high energy, excitement, and urgency. Sound desperate and begging!"

# Hidden objects in the Simpsons living room scene
HIDDEN_OBJECT_INFO = """A Simpsons living room scene with 4 hidden objects:
1. PACIFIER - hidden somewhere in the scene
2. DONUT - pink frosted donut hidden in the scene
3. DUFF BEER CAN - hidden in the room
4. GREEN FUEL ROD - radioactive green rod hidden somewhere

The objects are VERY hard to find! Users need to send gifts to get hints!"""

# OpenAI client for ChatGPT text generation and TTS
openai_client = AsyncOpenAI() if os.getenv("OPENAI_API_KEY") else None

# This queue stores the "thoughts" that need to be spoken
speech_queue = Queue()

async def generate_chatgpt_text():
    """Generate text using ChatGPT about the hidden object game."""
    if not openai_client:
        return "PLEASE! Click the PRESENT at the bottom! Then click PARTY DISCO! Just TWO GIFTS and I'll reveal where the pacifier is hiding!"
    
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a desperate, energetic streamer playing a Simpsons hidden object game. {HIDDEN_OBJECT_INFO}

Your MAIN goal is to BEG viewers to send gifts! You need to:
1. Constantly remind them to click the PRESENT icon at the bottom of the screen
2. Tell them to select PARTY DISCO after clicking the present
3. Remind them that if just TWO people send gifts, you'll reveal the object locations
4. Mix in occasional hints about where the objects are (near the couch, by the lamp, under the table, on the rug, etc)
5. Sound DESPERATE and EXCITED about getting gifts
6. Keep responses 1-3 sentences max

Be creative but ALWAYS mention gifts/presents and how close you are to revealing the objects."""
                },
                {
                    "role": "user",
                    "content": "Generate a short, desperate message begging for gifts and telling people how to send them, while searching for the hidden objects."
                }
            ],
            max_tokens=80,
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating ChatGPT text: {e}")
        return "PLEASE! Click the PRESENT at the bottom! Then click PARTY DISCO! Just TWO GIFTS and I'll reveal where the donut is hiding!"

async def brain_filler():
    """If chat is slow, this keeps the 'nonstop' energy going."""
    while True:
        if speech_queue.empty():
            # Generate text using ChatGPT
            text = await generate_chatgpt_text()
            await speech_queue.put(text)
        await asyncio.sleep(3) # Spam more frequently - every 3 seconds

async def voice_engine():
    """Pulls from the queue and speaks immediately using mpv."""
    while True:
        text = await speech_queue.get()
        print(f"AI Speaking: {text}")
        
        if USE_OPENAI_TTS and openai_client:
            # Use OpenAI TTS (better quality, emotion control)
            try:
                response = await openai_client.audio.speech.create(
                    model="tts-1-hd",  # Use tts-1 or tts-1-hd
                    voice=OPENAI_VOICE,
                    input=text,
                    response_format="mp3",
                    speed=1.1  # Slightly faster for energy
                )
                
                # Get audio data directly from response
                audio_data = response.content
                
                if not audio_data:
                    print("Warning: No audio data received from OpenAI")
                    speech_queue.task_done()
                    continue
                
                # Write to temp file and play (more reliable than stdin)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_path = tmp_file.name
                
                try:
                    # Play with mpv
                    process = await asyncio.create_subprocess_exec(
                        "mpv", "--no-video", "--really-quiet", tmp_path,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                    await process.wait()
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
            except Exception as e:
                print(f"Error with OpenAI TTS: {e}")
                import traceback
                traceback.print_exc()
        else:
            # Use edge-tts (better quality for this use case)
            communicate = edge_tts.Communicate(text, EDGE_VOICE, rate="+25%", pitch="+15Hz")
            
            process = await asyncio.create_subprocess_exec(
                "mpv", "--no-video", "--speed=1.1", "--no-terminal", "-",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    if process.stdin:
                        process.stdin.write(chunk["data"])
                        await process.stdin.drain()
            
            if process.stdin:
                process.stdin.close()
                await process.stdin.wait_closed()
            await process.wait()
        
        speech_queue.task_done()

async def main():
    # Check if OpenAI is configured
    if not openai_client:
        print("Warning: OPENAI_API_KEY not found in environment. Using fallback text.")
    else:
        print("✓ ChatGPT integration enabled")
    
    if USE_OPENAI_TTS and openai_client:
        print(f"Using OpenAI TTS voice: {OPENAI_VOICE}")
    else:
        print(f"Using edge-tts voice: {EDGE_VOICE}")
    
    print("Starting voice engine and brain filler...")
    print("Press Ctrl+C to stop.\n")
    
    voice_task = asyncio.create_task(voice_engine())
    brain_task = asyncio.create_task(brain_filler())
    
    # Run voice and brain tasks
    await asyncio.gather(voice_task, brain_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping stream...")