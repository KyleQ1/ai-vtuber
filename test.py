import requests
import base64
import pygame
import io

# High-energy voice options:
# en_us_002 (Jessie - very expressive/upbeat)
# en_us_006 (Adult Male - fast-paced)
# en_us_009 (C-3PO-ish but very fast)
# en_us_ghostface (Good for chaotic energy)

def speak_tiktok(text, voice="en_us_002"):
    # TikTok's internal TTS endpoint
    url = "https://api16-normal-c-useast1a.tiktokv.com/media/api/ad/v1/tts/"
    
    # Format the text and parameters
    # Note: TikTok has a character limit per request (usually ~300)
    params = {
        "status_code": 1,
        "str": text,
        "tiktok_label": voice,
        "speaker_map_type": 0,
        "aid": 1233
    }

    try:
        response = requests.post(url, params=params)
        data = response.json()
        
        # The audio is returned as a base64 encoded string
        v_str = data["data"]["v_str"]
        audio_data = base64.b64decode(v_str)

        # Play the audio using pygame
        pygame.mixer.init()
        audio_stream = io.BytesIO(audio_data)
        pygame.mixer.music.load(audio_stream)
        pygame.mixer.music.play()

        # Wait for the audio to finish so it doesn't overlap weirdly
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
    except Exception as e:
        print(f"Error: {e}")

# Example of your nonstop loop
def livestream_loop():
    # You would replace this list with generated text from your AI
    thoughts = [
        "OH MY GOD WHERE IS THE FOURTH OBJECT?!",
        "I HAVE BEEN STARING AT THIS BUSH FOR THREE HOURS!!!",
        "IS IT UNDER THE ROCK? NO! THAT IS IMPOSSIBLE!!",
        "EVERYONE IN CHAT IS LYING TO ME I KNOW IT IS THERE!"
    ]
    
    for line in thoughts:
        print(f"AI is saying: {line}")
        speak_tiktok(line, voice="en_us_002")

if __name__ == "__main__":
    livestream_loop()