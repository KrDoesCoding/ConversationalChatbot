from io import BytesIO
from groq import Groq
import wave

# Initialize API
API_KEY = "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"
client = Groq(api_key=API_KEY)

# Audio settings
CHANNELS = 1
RATE = 16000

def transcribe_audio(raw_audio):
    """Transcribes raw audio using Whisper API."""
    # Save the audio to a BytesIO object as a WAV file
    audio_data = BytesIO()
    with wave.open(audio_data, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(RATE)
        wf.writeframes(raw_audio)
    audio_data.seek(0)

    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_data.getvalue()),
            model="whisper-large-v3",
            response_format="verbose_json",
        )
        return transcription.text.strip()

    except Exception as e:
        print(f"Error in STT: {e}")
        return None
