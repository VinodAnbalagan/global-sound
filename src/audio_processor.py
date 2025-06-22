# src/audio_processor.py

import tempfile
import moviepy.editor as mp
import librosa
import noisereduce as nr
import soundfile as sf
import numpy as np # Make sure numpy is imported

class AudioProcessor:
    def __init__(self, target_sr: int = 16000):
        self.target_sr = target_sr

    # --- UPDATED FUNCTION ---
    def extract_and_process_audio(self, video_path: str, apply_noise_reduction: bool, duration_limit_secs: int = None) -> str:
        """
        Extracts audio, optionally truncates it, and applies noise reduction.
        """
        print("Step 1: Extracting audio from video...")
        try:
            video_clip = mp.VideoFileClip(video_path)
            
            # --- NEW: Truncate the clip if a duration is specified ---
            if duration_limit_secs and video_clip.duration > duration_limit_secs:
                print(f"Limiting video duration to {duration_limit_secs} seconds for quick process mode.")
                video_clip = video_clip.subclip(0, duration_limit_secs)
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                video_clip.audio.write_audiofile(temp_audio_file.name, fps=self.target_sr, codec='pcm_s16le')
                temp_audio_path = temp_audio_file.name

            audio, sr = librosa.load(temp_audio_path, sr=self.target_sr)

            if apply_noise_reduction:
                print("Step 1a: Applying noise reduction...")
                audio = nr.reduce_noise(y=audio, sr=self.target_sr)

            final_audio_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(final_audio_file.name, audio, self.target_sr)
            print(f"Audio Processing complete. Saved to: {final_audio_file.name}")
            return final_audio_file.name

        except Exception as e:
            print(f"Error processing audio: {e}")
            raise
