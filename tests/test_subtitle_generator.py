from src.subtitle_generator import generate_srt
import os

def test_generate_srt(tmp_path):
    segments = [{"start": 0.0, "end": 2.0, "text": "Hello world"}]
    output_file = tmp_path / "test.srt"
    generate_srt(segments, str(output_file))
    assert output_file.exists(), "SRT file was not created"