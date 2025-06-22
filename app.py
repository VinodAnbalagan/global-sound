# app.py
import gradio as gr
import os
import tempfile
import yt_dlp 
import time
import shutil
import re # for parsing progress

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
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except ValueError:
            return 0

def increment_usage_count():
    count = get_usage_count() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count


# --- HELPER FUNCTION FOR YOUTUBE (REPLACED WITH YT-DLP) ---
def download_youtube_video(url, progress_callback):
    """Downloads a YouTube video using yt-dlp to a temporary directory and returns the path."""
    temp_dir = tempfile.mkdtemp()
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_callback],
        'nocheckcertificate': True, # To avoid SSL issues in some environments
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        # After download, the 'requested_downloads' key contains file info
        downloaded_file_path = ydl.prepare_filename(info_dict)

    print(f"Download complete. Video saved to: {downloaded_file_path}")
    return downloaded_file_path, temp_dir


# --- 2. MAIN PROCESSING FUNCTION ---
def generate_subtitles_for_video(youtube_url, apply_noise_reduction, target_language, preserve_technical_terms, quick_process, progress=gr.Progress()):
    """
    The full pipeline, now using yt-dlp for robust YouTube downloading.
    """
    if not youtube_url:
        raise gr.Error("You must provide a YouTube URL.")

    temp_files_to_clean = []

    try:
        # Stage 0: Download YouTube Video
        def progress_hook(d):
            if d['status'] == 'downloading':
                # Extract percentage from a string like ' 50.6%'
                percent_str = d.get('_percent_str', '0.0%').strip().replace('%', '')
                try:
                    percent = float(percent_str)
                    # We only care about the download part of the progress bar
                    progress(percent / 100, desc=f"Downloading YouTube video... {int(percent)}%")
                except ValueError:
                    pass # Ignore if conversion fails
            elif d['status'] == 'finished':
                progress(1.0, desc="Download complete. Preparing audio...")

        video_path, temp_dir = download_youtube_video(youtube_url, progress_hook)
        temp_files_to_clean.append(temp_dir) # Clean up the entire directory later

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
        
        # Stage 3: Translation
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
        print(f"An error occurred: {e}")
        raise gr.Error(f"An error occurred during processing. Please check the URL and try again. Details: {e}")
    finally:
        # Final cleanup
        for path in temp_files_to_clean:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError as e_os:
                    print(f"Error removing file {path}: {e_os}")
            elif os.path.isdir(path):
                try:
                    shutil.rmtree(path)
                except OSError as e_os:
                    print(f"Error removing directory {path}: {e_os}")


# --- 3. BUILD THE GRADIO UI (No changes needed here) ---
with gr.Blocks(theme=gr.themes.Soft(), title="Global Sound 🌍", css="style.css") as demo:
    gr.Markdown("# Global Sound — AI-Powered Video Translator")
    gr.Markdown("Translate any YouTube video into multiple languages. **The translated video will play directly in the results panel.**")
    
    gr.Markdown(
        "<div style='text-align:center; padding: 10px; border-radius: 5px; background-color: #fef4e6; color: #b45309;'>"
        "⚠️ **Note:** This app runs on a free CPU. Processing is fastest with the **'Quick Process'** option. "
        "Full videos may take several minutes."
        "</div>"
    )

    with gr.Row(equal_height=True):
        # --- LEFT COLUMN for INPUTS ---
        with gr.Column(scale=2):
            gr.Markdown("### 1. Enter YouTube URL")
            youtube_url_input = gr.Textbox(
                label="YouTube Video URL", 
                placeholder="e.g., https://www.youtube.com/watch?v=...",
                info="Paste the link to the YouTube video you want to translate."
            )

            gr.Markdown("### 2. Select Options")
            with gr.Accordion("Settings", open=True):
                quick_process_checkbox = gr.Checkbox(label="Quick Process (First 60s Only)", value=True, info="Ideal for testing or a fast preview.")
                noise_reduction = gr.Checkbox(label="Apply Noise Reduction", value=True, info="Recommended for videos with background noise.")
                preserve_technical = gr.Checkbox(label="Preserve Technical Terms", value=True, info="Protects words like 'GAN' or 'PyTorch' from translation.")
            
            language_dropdown = gr.Dropdown(
                label="Translate To (Optional)",
                info="Select a language to translate the subtitles into.",
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

        # --- RIGHT COLUMN for OUTPUTS ---
        with gr.Column(scale=3):
            gr.Markdown("### 3. View Results")
            video_output = gr.Video(label="Translated Video Player", interactive=False)
            output_files = gr.File(label="Download Subtitle Files (.srt)", file_count="multiple", interactive=False)
            summary_output = gr.Textbox(label="Processing Summary", lines=4, interactive=False)
            preview_output = gr.Textbox(label="Transcription Preview", lines=4, interactive=False)
            usage_counter = gr.HTML(f"<div style='text-align: right; color: #555; font-size: 0.9em;'>📈 Processed Videos: {get_usage_count()}</div>")

    # --- BUTTON CLICK EVENTS ---
    process_event = process_btn.click(
        fn=generate_subtitles_for_video,
        inputs=[youtube_url_input, noise_reduction, language_dropdown, preserve_technical, quick_process_checkbox],
        outputs=[video_output, output_files, summary_output, preview_output, usage_counter]
    )

    stop_btn.click(fn=None, inputs=None, outputs=None, cancels=[process_event])

    gr.Markdown("---")
    gr.Markdown("Made by Outlier contributors using OpenAI Whisper, mBART, and Gradio.")

# --- 4. LAUNCH THE APP ---
if __name__ == "__main__":
    demo.launch(debug=True)
