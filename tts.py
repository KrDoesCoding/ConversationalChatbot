# tts.py - Optimized Edge TTS with reduced latency

import os
import asyncio
import edge_tts
import pygame
import threading
import tempfile
import time

# Global lock for pygame access
pygame_lock = threading.RLock()

# Initialize pygame mixer once at module level to reduce startup time
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1)
except Exception:
    pass

# Cache for voice instances
voice_cache = {}

def clean_text(text):
    """Cleans text before feeding into TTS."""
    return " ".join(text.split()).strip()

def text_to_speech(text):
    """
    Converts text to speech using Microsoft Edge TTS with optimizations for reduced latency.
    """
    # Create a flag to indicate TTS is actively playing
    tts_active = threading.Event()

    async def generate_speech(text):
        voices = [
            "en-US-AriaNeural",     # Female, very natural
            "en-US-GuyNeural",      # Male, natural
            "en-US-SteffanNeural",  # Male, conversational
        ]
        
        voice = voices[0]
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_file.close()
        
        # Generate speech with optimized settings
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(temp_file.name)
        
        return temp_file.name

    def play_speech():
        temp_file_path = None
        try:
            # Clean the text
            cleaned_text = clean_text(text)

            # Set up asyncio with optimized settings
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Generate speech to a temporary file
            temp_file_path = loop.run_until_complete(generate_speech(cleaned_text))
            loop.close()

            # Use the lock to prevent concurrent pygame access
            with pygame_lock:
                # Make sure pygame mixer is properly initialized
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=22050, size=-16, channels=1)
                
                # Load audio file
                try:
                    pygame.mixer.music.load(temp_file_path)
                except Exception as e:
                    print(f"Failed to load audio: {e}")
                    # Retry once with reinitialization if loading fails
                    pygame.mixer.quit()
                    time.sleep(0.1)
                    pygame.mixer.init(frequency=22050, size=-16, channels=1)
                    pygame.mixer.music.load(temp_file_path)
                
                # Set flag that TTS is active
                tts_active.set()
                
                # Play the audio
                pygame.mixer.music.play()

                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(30)  # Higher tick rate for more responsive ending
                
                # No need to quit the mixer every time, just stop the music
                pygame.mixer.music.stop()

            # Clear flag when TTS is done
            tts_active.clear()
            
            # Remove temporary file
            if temp_file_path:
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass  # If file removal fails, it's not critical

        except Exception as e:
            print(f"Error in TTS: {e}")
            import traceback
            traceback.print_exc()
            
            # Make sure to clear flag in case of error
            tts_active.clear()
            
            # Clean up in case of error
            with pygame_lock:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
            
            # Remove temporary file in case of error
            if temp_file_path:
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

    # Run speech generation and playback in a thread
    speech_thread = threading.Thread(target=play_speech)
    speech_thread.daemon = True
    speech_thread.start()
    
    return tts_active

# Preload the voice model to reduce first-time latency
def preload_tts_engine():
    """Preload TTS engine in background to reduce first-response latency"""
    def _preload():
        dummy_text = "Preloading text to speech engine."
        text_to_speech(dummy_text)
    
    # Start preloading in background
    preload_thread = threading.Thread(target=_preload)
    preload_thread.daemon = True
    preload_thread.start()

# Auto-preload the engine when module is imported
preload_tts_engine()

if __name__ == "__main__":
    while True:
        user_input = input("Enter text (or 'exit' to stop): ")
        if user_input.lower() == "exit":
            break
        text_to_speech(user_input)