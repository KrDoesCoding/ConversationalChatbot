import pyaudio
import numpy as np
import time
import threading
import queue
import torch

class OptimizedVADRecorder:
    def __init__(self, 
                 sample_rate=16000, 
                 channels=1, 
                 chunk_size=1024, 
                 silence_limit=20,
                 max_recording_duration=30):
        """
        Optimized Voice Activity Detection Recorder
        
        Args:
            sample_rate (int): Audio sampling rate
            channels (int): Number of audio channels
            chunk_size (int): Number of frames per buffer
            silence_limit (int): Silence threshold to end recording
            max_recording_duration (int): Maximum recording time in seconds
        """
        # Load Silero VAD model with optimized loading
        self.vad_model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,  # Reduce reload overhead
            trust_repo=True
        )
        
        # Unpack utility functions
        (self.get_speech_timestamps, 
         self.save_audio, 
         self.read_audio, 
         self.VADIterator, 
         self.collect_chunks) = utils

        # Audio configuration
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = channels
        self.RATE = sample_rate
        self.CHUNK = chunk_size
        
        # Detection parameters
        self.SILENCE_LIMIT = silence_limit
        self.MAX_RECORDING_DURATION = max_recording_duration
        
        # Flags and queues
        self.is_ai_speaking = False
        self.audio_queue = queue.Queue()
        
        # Precompute constants for performance
        self.NORMALIZATION_FACTOR = 1.0 / 32768.0
        
        # Optimize PyAudio initialization
        self.pyaudio = pyaudio.PyAudio()

    def start_ai_speaking(self):
        """Pause VAD during AI speech."""
        self.is_ai_speaking = True
        print("🤖 AI is speaking, pausing VAD...")

    def stop_ai_speaking(self):
        """Resume VAD after AI speech with minimal delay."""
        time.sleep(0.2)  # Slight delay to prevent speech bleed
        self.is_ai_speaking = False
        print("🎤 Resuming VAD...")

    def record_audio(self):
        """
        Optimized continuous audio recording with VAD
        
        Improvements:
        - Reduced memory allocations
        - Minimized redundant computations
        - Efficient tensor conversion
        - Configurable parameters
        """
        stream = self.pyaudio.open(
            format=self.FORMAT, 
            channels=self.CHANNELS, 
            rate=self.RATE,
            input=True, 
            frames_per_buffer=self.CHUNK
        )

        print("🎤 Listening for speech...")

        # Preallocate buffers for efficiency
        audio_buffer = []
        window_buffer = []
        speech_detected = False
        silence_counter = 0
        start_time = time.time()

        # Initial window collection
        for _ in range(30):
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            window_buffer.append(data)
            audio_buffer.append(data)

        while True:
            # AI speech interruption check (minimal overhead)
            if self.is_ai_speaking:
                time.sleep(0.1)
                continue

            # Read audio chunk
            try:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
            except Exception as e:
                print(f"Audio stream error: {e}")
                break

            audio_buffer.append(data)
            window_buffer.append(data)

            # Maintain fixed-size window
            if len(window_buffer) > 30:
                window_buffer.pop(0)

            # Efficient tensor conversion
            window_bytes = b''.join(window_buffer)
            window_np = np.frombuffer(window_bytes, dtype=np.int16).astype(np.float32) * self.NORMALIZATION_FACTOR
            window_tensor = torch.from_numpy(window_np)  # More direct conversion

            # Speech detection
            speech_timestamps = self.get_speech_timestamps(
                window_tensor, 
                self.vad_model, 
                sampling_rate=self.RATE
            )

            # Speech state management
            if speech_timestamps and not speech_detected:
                print("🔊 User speech detected! Recording...")
                speech_detected = True
                silence_counter = 0

            elif speech_detected:
                silence_counter = 0 if speech_timestamps else silence_counter + 1

                # End of speech detection
                if silence_counter >= self.SILENCE_LIMIT:
                    print("🔇 End of user speech detected")
                    break

            # Prevent infinite recording
            if time.time() - start_time > self.MAX_RECORDING_DURATION:
                print("⏰ Max recording time reached")
                break

        # Cleanup
        stream.stop_stream()
        stream.close()

        return b''.join(audio_buffer)

    def __del__(self):
        """Ensure PyAudio termination"""
        try:
            self.pyaudio.terminate()
        except:
            pass

def record_audio():
    """Compatibility wrapper for existing code"""
    recorder = OptimizedVADRecorder()
    return recorder.record_audio()

# Standalone execution for testing
if __name__ == "__main__":
    try:
        while True:
            audio_data = record_audio()
            print(f"Recorded audio length: {len(audio_data)} bytes")
    except KeyboardInterrupt:
        print("\nExiting...")