from src.transcriber import transcribe_audio

def test_transcribe_audio():
    dummy_audio_path = "tests/sample.wav"  # Replace with real path if needed
    result = transcribe_audio(dummy_audio_path)
    assert isinstance(result, list), "Transcription output should be a list"
    assert all("text" in segment for segment in result), "Each segment should have text"