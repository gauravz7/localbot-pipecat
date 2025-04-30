import wave
import pytest
from audio_transcribe import AudioTranscriber

@pytest.mark.asyncio
async def test_transcribe_chirp():
    # Open and read the WAV file
    with wave.open("en-IN-Chirp-HD-D.wav", "rb") as wav_file:
        # Get the audio data
        audio_data = wav_file.readframes(wav_file.getnframes())
        
        # Create a simple context
        class SimpleContext:
            def get_messages_for_persistent_storage(self):
                return []
                
            def create_wav_header(self, sample_rate, channels, bits_per_sample, data_length):
                return b'RIFF' + b'\x00' * 36
        
        # Initialize transcriber and transcribe
        transcriber = AudioTranscriber()
        result = await transcriber.transcribe(audio_data, SimpleContext())
        
        # Print results
        if result:
            text, prompt_tokens, completion_tokens, total_tokens = result
            print(f"\nTranscription: {text}")
            print(f"Tokens used: {total_tokens}")
        else:
            print("\nTranscription failed") 