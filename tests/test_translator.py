from src.translator import translate_segments

def test_translate_segments():
    dummy_segments = [{"text": "Hello world", "start": 0.0, "end": 1.5}]
    translated = translate_segments(dummy_segments, "es")
    assert isinstance(translated, list), "Translation output should be a list"
    assert all("text" in segment for segment in translated), "Each segment should have text"