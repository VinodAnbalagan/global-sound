# src/audio_processor.py

import tempfile
import moviepy.editor as mp
import librosa
import noisereduce as nr  # Corrected import name
import soundfile as sf

class AudioProcessor:
    """ 
    Handles extracting audio from video and applying noise reduction.
    """
    def __init__(self, target_sr: int = 16000):
        self.target_sr = target_sr

    def extract_and_process_audio(self, video_path: str, apply_noise_reduction: bool) -> str:
        print("Step 1: Extracting audio from video...")
        try:
            video_clip = mp.VideoFileClip(video_path)
            
            # --- CORRECTION 1: The codec 'pcm_s161e' is a typo. It should be 'pcm_s16le' ---
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                video_clip.audio.write_audiofile(temp_audio_file.name, fps=self.target_sr, codec='pcm_s16le') # Corrected codec
                temp_audio_path = temp_audio_file.name

            audio, sr = librosa.load(temp_audio_path, sr=self.target_sr)

            if apply_noise_reduction:
                print("Step 1a: Applying noise reduction...")
                # --- CORRECTION 2: The argument is 'sr', not 'src'. ---
                audio = nr.reduce_noise(y=audio, sr=self.target_sr) # Corrected argument

            # --- CORRECTION 3: The method is tempfile.NamedTemporaryFile, not namedTemporaryFile. ---
            final_audio_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(final_audio_file.name, audio, self.target_sr)
            print(f"Audio Processing complete. Saved to: {final_audio_file.name}")
            return final_audio_file.name

        except Exception as e:
            print(f"Error processing audio: {e}")
            raise
