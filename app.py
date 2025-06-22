# app.py

import gradio as gr
import os
import tempfile
from pytube import YouTube
from pytube.cli import on_progress
import time
import shutil

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

# --- USAGE COUNTER (same as before) ---
COUNTER_FILE = "usage_count.txt"
# ... (all counter functions are the same)

# --- HELPER FUNCTION FOR YOUTUBE (same as before) ---
def download_youtube_video(url):
    # ... (this function is the same)
    
# --- 2. MAIN FUNCTION - UPDATED FOR SINGLE LANGUAGE DROPDOWN ---

def generate_subtitles_for_video(video_upload_path, youtube_url, apply_noise_reduction, target_language, preserve_technical_terms, quick_process, progress=gr.Progress()):
    """
    The full pipeline, now optimized for a single target language for speed.
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
        duration_limit = 60 if quick_process else None
        if quick_process:
            print("Quick Process Mode enabled: processing first 60 seconds only.")

        # Stage 1: Audio Processing
        progress(0.1, desc="Step 1/3: Extracting and cleaning audio...")
        processed_audio_path = audio_processor.extract_and_process_audio(video_path, apply_noise_reduction, duration_limit)
        temp_files_to_clean.append(processed_audio_path)

        # Stage 2: Transcription
        progress(0.3, desc="Step 2/3: Transcribing audio...")
        original_segments, src_lang = transcriber.transcribe_audio(processed_audio_path)

        # Generate Original Subtitle
        original_srt_path = subtitle_generator.create_srt_file(f"subtitles_{src_lang}", original_segments)
        output_files = [original_srt_path]
        final_video_subtitle_path = original_srt_path
        
        # Stage 3: Translation (now much simpler)
        if target_language and target_language != src_lang:
            progress(0.7, desc=f"Step 3/3: Translating to {target_language}...")
            translated_segments = translator.translate_segments(original_segments, src_lang, target_language, preserve_technical_terms)
            translated_srt_path = subtitle_generator.create_srt_file(f"subtitles_{target_language}", translated_segments)
            output_files.append(translated_srt_path)
            # Set the video player to use the new translated subtitle
            final_video_subtitle_path = translated_srt_path

        progress(1.0, desc="Processing complete!")
        summary = (
            f"Processing Complete!\n\n"
            f"Source Language Detected: {src_lang.upper()}\n"
            f"Translation Language: {target_language.upper() if target_language else 'N/A'}"
        )
        preview_text = "Transcription Preview:\n" + "\n".join([seg['text'] for seg in original_segments[:5]])
        usage_count = increment_usage_count()
        usage_html = f"<div style='text-align: right; color: #555; font-size: 0.9em;'>📈 Processed Videos: {usage_count}</div>"

        return gr.Video(value=video_path, subtitles=final_video_subtitle_path), output_files, summary, preview_text, usage_html

    except Exception as e:
        raise gr.Error(f"An error occurred: {e}")
    finally:
        for path in temp_files_to_clean:
            if os.path.isfile(path): os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

# --- 3. BUILD THE UI WITH A DROPDOWN FOR LANGUAGES ---

with gr.Blocks(theme=gr.themes.Soft(), title="Global Sound 🌍", css="style.css") as demo:
    gr.Markdown("# Global Sound — AI-Powered Video Translator")
    gr.Markdown("Translate any video by uploading a file or pasting a YouTube URL. **The translated video will play directly in the results panel.**")
    
    gr.Markdown(
        "<div style='text-align:center; padding: 10px; border-radius: 5px; background-color: #fef4e6; color: #b45309;'>"
        "⚠️ **Note:** This app runs on a free CPU. Processing is fastest with the **'Quick Process'** option. "
        "Full videos may take several minutes."
        "</div>"
    )

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
                quick_process_checkbox = gr.Checkbox(label="Quick Process (First 60s Only)", value=True, info="Ideal for testing or a fast preview of the quality.")
                noise_reduction = gr.Checkbox(label="Apply Noise Reduction", value=True, info="Recommended for noisy audio.")
                preserve_technical = gr.Checkbox(label="Preserve Technical Terms", value=True, info="Protects words like 'GAN' or 'PyTorch'.")

            # --- NEW: Language Dropdown ---
            language_dropdown = gr.Dropdown(
                label="Translate To (Optional)",
                choices=[
                    ("Spanish", "es"), ("French", "fr"), ("German", "de"), ("Japanese", "ja"), ("Vietnamese", "vi"), 
                    ("Chinese", "zh"), ("Hindi", "hi"), ("Portuguese", "pt"), ("Korean", "ko"), ("Tamil", "ta"), ("Ukrainian", "uk"),
                    ("Russian", "ru"), ("Arabic", "ar")
                ],
                value="es" # Default to Spanish
            )
            
            with gr.Row():
                process_btn = gr.Button("Generate Subtitles", variant="primary", scale=3)
                stop_btn = gr.Button("Stop", variant="stop", scale=1)

        # --- RIGHT COLUMN for OUTPUTS (same as before) ---
        with gr.Column(scale=3):
            # ... all output components are the same
            gr.Markdown("### Results")
            video_output = gr.Video(label="Translated Video Player")
            output_files = gr.File(label="Download Subtitle Files (.srt)", file_count="multiple", interactive=False)
            summary_output = gr.Textbox(label="Processing Summary", lines=4, interactive=False)
            preview_output = gr.Textbox(label="Transcription Preview", lines=4, interactive=False)
            usage_counter = gr.HTML(f"<div style='text-align: right; color: #555; font-size: 0.9em;'>📈 Processed Videos: {get_usage_count()}</div>")

    # --- UPDATED .click() method with the new dropdown input ---
    process_event = process_btn.click(
        fn=generate_subtitles_for_video,
        inputs=[video_upload_input, youtube_url_input, noise_reduction, language_dropdown, preserve_technical, quick_process_checkbox],
        outputs=[video_output, output_files, summary_output, preview_output, usage_counter]
    )

    stop_btn.click(fn=None, inputs=None, outputs=None, cancels=[process_event])

    gr.Markdown("---")
    gr.Markdown("Made using OpenAI Whisper, mBART, Gradio, and Python.")

# --- 4. LAUNCH ---
if __name__ == "__main__":
    demo.launch(debug=True)
