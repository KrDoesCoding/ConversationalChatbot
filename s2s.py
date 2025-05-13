import threading
import time
from vad import OptimizedVADRecorder
from stt_groq import transcribe_audio
from llm import process_transcript_with_llm
from tts import text_to_speech

class VoiceAssistant:
    """Voice assistant class that coordinates the S2S pipeline components."""
    
    def __init__(self):
        self.vad_recorder = OptimizedVADRecorder()
        self.should_stop = False
        self.is_speaking = False
        
    def speak_response(self, text):
        """Speak the AI response and handle the speaking state."""
        self.is_speaking = True
        self.vad_recorder.start_ai_speaking()
        text_to_speech(text)
        self.is_speaking = False
        self.vad_recorder.stop_ai_speaking()
    
    def run(self):
        """Run the voice assistant in continuous mode."""
        print("Voice Assistant is running. Say 'exit' to stop.")
        
        while not self.should_stop:
            # Record audio and detect speech
            raw_audio = self.vad_recorder.record_audio()
            if raw_audio is None or self.should_stop:
                continue
            
            # Transcribe audio to text
            transcription = transcribe_audio(raw_audio)
            if transcription:
                print(f"User: {transcription}")
                
                # Check for exit command
                if "exit" in transcription.lower():
                    print("Exiting the assistant...")
                    self.should_stop = True
                    break
                
                # Process transcription with LLM
                response = process_transcript_with_llm(transcription)
                print(f"AI: {response}")
                
                # Convert response to speech
                self.speak_response(response)
                
            time.sleep(0.1)  # Small delay to prevent CPU hogging

# Function for backwards compatibility with the original version
def voice_assistant():
    assistant = VoiceAssistant()
    assistant.run()

if __name__ == "__main__":
    try:
        voice_assistant()
    except KeyboardInterrupt:
        print("Exiting...")