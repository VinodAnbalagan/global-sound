import pytest
from src.audio_processor import extract_audio, reduce_noise
import os

def test_extract_audio(tmp_path):
    input_video = "tests/sample_video.mp4"  # Replace with real path 
    audio_path = tmp_path / "output.wav"
    extract_audio(str(input_video), str(audio_path))
    assert audio_path.exists(), "Audio extraction failed"

def test_reduce_noise():
    # Test will need real audio samples
    pass