import whisper
import math

class Transcriber:
    """
    Wrapper for OpenAI's Whisper model to transcribe speech from audio.
    """
    def __init__(self, model_size:str = "base"):
        """
        Initialize Whisper model from transcription.
        Args: model_size(str): Choose from 'tiny', 'base', 'small', 'medium', 'large'
        """
        print(f"Loading Whsiper model: {model_size}...")
        self.model = whisper.load_model(model_size)
        print("Whisper model loaded.")

    def transcribe_audio(self, audio_path:str) -> (list, str):
        """
        Transcribes the given audio file using Whisper.

        Args: audio_path(str): Path to the cleaned audio file. 
        Returns: tuple: List of segment dictionaries with timestamps and detected language.
        """    
        print(f"Step 2: Transcribing audio file: {audio_path}...")
        try:
            result = self.model.transcribe(audio_path, word_timestamps= False)
            print(f" Transcription complete. Detected language: {result['language']}.")
            return result["segments"], result["language"]
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            raise