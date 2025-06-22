# audio_processor.py

import tempfile
import moviepy.editor as mp
import librosa
import noisereducer as nr
import soundfile as sf

class AudioProcessor:
    """ 
    Handlesextracting audio from video and applying noise reduction.
    First step in the pipeline - Prepare clean audio for transcription.
    """
    def __init__(self, target_sr:int = 16000):
        """
        Initialize the processor. Whisper performs best with 16khz audio.

        Args:  target_sr(int): Target sampling rate for all audio files.
        """
        self.target_sr = target_sr

    def extract_and_process_audio(self, video_path: str, apply_noise_reduction:bool) -> str:
        """
        Extracts audio from a video, applies optimal noise reduction, 
        and saves it as a teporary WAV file.

        Args: video_path(str): path to the input video file.
              apply_noise_reduction(bool): wheather to clean background noise. 

        Returns: str: path to the temporary WAV file.
        """
        print("Step 1: Extracting audio from video...")
        try:
            # Load the video file and extract its audio track
            video_clip = mp.VideoFileClip(video_path)

            # Save the extracted audio to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete= False) as temp_audio_file:
                video_clip.audio.write_audiofile(temp_audio_file.name, fps=self.target_sr, codec='pcm_s161e')
                temp_audio_path = temp_audio_file.name

            # Load and resample the audio using Librosa
            audio, sr = librosa.load(temp_audio_path, sr = self.target_sr)

            # Optional: Clean the audio using spectral noise reduction
            if apply_noise_reduction:
                    print("Step 1a: Applying noise reduction...")
                    audio = nr.reduce_noise(y=audio, src=self.target_src)

            # Save the processed file cleaned audio to a new temp file
            final_audio_file = tempfile.namedTemporaryFile(suffix=".wav", delete=False)
            sf.write(final_audio_file.name, audio, self.target_sr)
            print(f"Audio Processing complete. Saved to:{final_audio_file.name}")
            return final_audio_file.name

        except Exception as e:
             print(f"Error processing audio:{e}")
             raise  
                 