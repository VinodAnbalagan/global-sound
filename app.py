# app.py

import gradio as gr
import os
import tempfile
from pytube import YouTube # NEW IMPORT
import time # NEW IMPORT

# Importing all custom modules from src/
from src.audio_processor import AudioProcessor
from src.transcriber import Transcriber
from src.translator import Translator
from src.subtitle_generator import SubtitleGenerator

# --- 1. INITIALIZE ALL MODELS ONCE ON STARTUP ---

print("Initializing all models, please wait...")
audio_processor = AudioProcessor()
transcriber = Transcriber(model_size="base")
translator = Translator()
subtitle_generator = SubtitleGenerator()
print("\nAll models initialized. The application is ready.")

# --- USAGE COUNTER ---
COUNTER_FILE = "usage_count.txt"

def get_usage_count():
    if not os.path.exists(COUNTER_FILE): return 0
    with open(COUNTER_FILE, "r") as f:
        try: return int(f.read().strip())
        except: return 0

def increment_usage_count():
    count = get_usage_count() + 1
    with open(COUNTER_FILE, "w") as f: f.write(str(count))
    return count

# --- NEW: HELPER FUNCTION FOR YOUTUBE ---
def download_youtube_video(url):
    """
    Downloads a YouTube video from a URL and returns the local file path.
    """
    print(f"Downloading YouTube video from URL: {url}")
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            raise gr.Error("No suitable video stream found for this YouTube URL. It might be age-restricted or private.")
        
        temp_dir = tempfile.mkdtemp()
        video_path = stream.download(output_path=temp_dir)
        print(f"YouTube video downloaded to: {video_path}")
        return video_path
    except Exception as e:
        print(f"Error downloading YouTube video: {e}")
        raise gr.Error(f"Failed to download the YouTube video. Please check the URL and ensure the video is public. Error: {e}")

# --- 2. COMPLETELY REPLACED MAIN FUNCTION ---

def generate_subtitles_for_video(video_upload_path, youtube_url, apply_noise_reduction, target_languages, preserve_technical_terms, progress=gr.Progress()):
    """
    The full pipeline: handles either a file upload or a YouTube URL.
    """
    video_path = ""
    temp_files_to_clean = []

    # Determine the input source
    if youtube_url:
        progress(0.05, desc="Downloading YouTube video...")
        video_path = download_youtube_video(youtube_url)
        temp_files_to_clean.append(os.path.dirname(video_path))
    elif video_upload_path:
        video_path = video_upload_path
    else:
        raise gr.Error("You must upload a video file or provide a YouTube URL.")

    try:
        # Stages 1 and 2
        progress(0.1, desc="Step 1/4: Extracting and cleaning audio...")
        processed_audio_path = audio_processor.extract_and_process_audio(video_path, apply_noise_reduction)
        temp_files_to_clean.append(processed_audio_path)

        progress(0.3, desc="Step 2/4: Transcribing audio...")
        original_segments, src_lang = transcriber.transcribe_audio(processed_audio_path)

        # Generate Original Subtitle
        progress(0.6, desc="Step 3/4: Generating original language subtitles...")
        original_srt_path = subtitle_generator.create_srt_file(f"subtitles_{src_lang}", original_segments)
        output_files = [original_srt_path]
        final_video_subtitle_path = original_srt_path
        preview_lang = src_lang

        # Stage 3: Translation
        if target_languages:
            preview_lang = target_languages[0]
            for i, lang in enumerate(target_languages):
                if lang == src_lang: continue
                progress(0.7 + (i * 0.2 / len(target_languages)), desc=f"Step 4/4: Translating to {lang}...")
                translated_segments = translator.translate_segments(original_segments, src_lang, lang, preserve_technical_terms)
                translated_srt_path = subtitle_generator.create_srt_file(f"subtitles_{lang}", translated_segments)
                output_files.append(translated_srt_path)
                
                if lang == preview_lang:
                    final_video_subtitle_path = translated_srt_path

        progress(1.0, desc="All subtitles generated!")
        summary = (
            f"Processing Complete!\n\n"
            f"Source Language: {src_lang.upper()}\n"
            f"Video Preview Subtitles: {preview_lang.upper()}\n"
            f"Generated Files: {', '.join([os.path.basename(f) for f in output_files])}"
        )
        preview_text = "Transcription Preview:\n" + "\n".join([seg['text'] for seg in original_segments[:5]])
        usage_count = increment_usage_count()
        usage_html = f"<div style='text-align: right; color: #555; font-size: 0.9em;'>📈 Processed Videos: {usage_count}</div>"

        # Return all outputs, including the new video player output
        return gr.Video(value=video_path, subtitles=final_video_subtitle_path), output_files, summary, preview_text, usage_html

    except Exception as e:
        raise gr.Error(f"An error occurred: {e}")
    finally:
        for path in temp_files_to_clean:
            if os.path.isfile(path): os.remove(path)
            elif os.path.isdir(path):
                import shutil
                shutil.rmtree(path)

# --- 3. COMPLETELY REPLACED UI SECTION ---

with gr.Blocks(theme=gr.themes.Soft(), title="Global Sound 🌍", css="style.css") as demo:
    gr.Markdown("# Global Sound — AI-Powered Video Translator")
    gr.Markdown("Translate any video by uploading a file or pasting a YouTube URL. **The translated video will play directly in the results panel.**")

    with gr.Row():
        # --- LEFT COLUMN for INPUTS ---
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("Upload Video File"):
                    video_upload_input = gr.Video(label="Upload Your Video", sources=['upload'])
                with gr.TabItem("From YouTube URL"):
                    youtube_url_input = gr.Textbox(label="Enter YouTube Video URL", placeholder="e.g., https://www.youtube.com/watch?v=...")
                    gr.Markdown("<p style='font-size:0.9em;color:#555;'>Your video will be downloaded and displayed with subtitles in the results panel.</p>")

            gr.Markdown("### Processing Options")
            with gr.Accordion("Settings", open=True):
                noise_reduction = gr.Checkbox(label="Apply Noise Reduction", value=True, info="Recommended for noisy audio.")
                preserve_technical = gr.Checkbox(label="Preserve Technical Terms", value=True, info="Protects words like 'GAN' or 'PyTorch'.")

            languages = gr.CheckboxGroup(
                choices=[
                    ("Spanish", "es"), ("French", "fr"), ("German", "de"), ("Japanese", "ja"), ("Vietnamese", "vi"), 
                    ("Chinese", "zh"), ("Hindi", "hi"), ("Portuguese", "pt"), ("Korean", "ko"), ("Tamil", "ta"), ("Ukrainian", "uk")
                ],
                label="Translate To:",
                value=["es", "fr", "ta", "uk"]
            )
            process_btn = gr.Button("Generate Subtitles", variant="primary")

        # --- RIGHT COLUMN for OUTPUTS ---
        with gr.Column(scale=3):
            gr.Markdown("### Results")
            video_output = gr.Video(label="Translated Video Player") # NEW output component
            # NEW, CORRECTED CODE
            output_files = gr.File(label="Download All Subtitle Files (.srt)", max_files=20, interactive=False)
            summary_output = gr.Textbox(label="Processing Summary", lines=4, interactive=False)
            preview_output = gr.Textbox(label="Transcription Preview", lines=4, interactive=False)
            usage_counter = gr.HTML(f"<div style='text-align: right; color: #555; font-size: 0.9em;'>📈 Processed Videos: {get_usage_count()}</div>")

    # --- UPDATED .click() method with NEW inputs and outputs ---
    process_btn.click(
        fn=generate_subtitles_for_video,
        inputs=[video_upload_input, youtube_url_input, noise_reduction, languages, preserve_technical],
        outputs=[video_output, output_files, summary_output, preview_output, usage_counter]
    )

    gr.Markdown("---")
    gr.Markdown("Made using OpenAI Whisper, mBART, Gradio, and Python")

# --- 4. LAUNCH ---
if __name__ == "__main__":
    demo.launch(debug=True)
