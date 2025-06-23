# app.py (Final Version with Correct Tuple Return)

import gradio as gr
import os
import tempfile
import time
import shutil

# Importing custom modules
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
        except (ValueError, TypeError):
            return 0

def increment_usage_count():
    count = get_usage_count() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count


# --- MAIN PROCESSING FUNCTION (SIMPLIFIED FOR UPLOAD) ---
def generate_subtitles_for_video(video_upload_path, apply_noise_reduction, target_language, preserve_technical_terms, quick_process, progress=gr.Progress()):
    """
    The full pipeline, now simplified to only handle a direct video file upload.
    """
    if not video_upload_path:
        raise gr.Error("You must upload a video file.")

    video_path = video_upload_path
    temp_files_to_clean = []

    try:
        duration_limit = 60 if quick_process else None
        if quick_process:
            print("Quick Process Mode enabled: processing first 60 seconds only.")

        progress(0.1, desc="Step 1/3: Extracting and cleaning audio...")
        processed_audio_path = audio_processor.extract_and_process_audio(video_path, apply_noise_reduction, duration_limit)
        temp_files_to_clean.append(processed_audio_path)

        progress(0.3, desc="Step 2/3: Transcribing audio...")
        original_segments, src_lang = transcriber.transcribe_audio(processed_audio_path)

        original_srt_path = subtitle_generator.create_srt_file(f"subtitles_{src_lang}", original_segments)
        output_files = [original_srt_path]
        final_video_subtitle_path = original_srt_path
        
        if target_language and target_language != src_lang:
            progress(0.7, desc=f"Step 3/3: Translating to {target_language}...")
            translated_segments = translator.translate_segments(original_segments, src_lang, target_language, preserve_technical_terms)
            translated_srt_path = subtitle_generator.create_srt_file(f"subtitles_{target_language}", translated_segments)
            output_files.append(translated_srt_path)
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

        # --- THIS IS THE FINAL FIX ---
        # We return a TUPLE of (video_path, subtitle_path) for the gr.Video component.
        video_player_update = (video_path, final_video_subtitle_path)
        
        return video_player_update, output_files, summary, preview_text, usage_html

    except Exception as e:
        print(f"An error occurred in the main pipeline: {e}")
        raise gr.Error(str(e))
    finally:
        for path in temp_files_to_clean:
            if os.path.isfile(path):
                try: os.remove(path)
                except OSError as e_os: print(f"Error removing file {path}: {e_os}")


# --- GRADIO UI (UNCHANGED) ---
with gr.Blocks(theme=gr.themes.Soft(), title="Global Sound 🌍", css="style.css") as demo:
    gr.Markdown("# Global Sound — AI-Powered Video Translator")
    gr.Markdown(
        "**This app now works with direct video uploads to ensure reliability on the free platform.**\n\n"
        "**How to Use:**\n"
        "1. First, download a YouTube video to your computer. You can use a free online service for this.\n"
        "2. Upload the downloaded video file (`.mp4`, `.mov`, etc.) below.\n"
        "3. Select your options and click 'Generate Subtitles'."
    )
    
    gr.Markdown(
        "<div style='text-align:center; padding: 10px; border-radius: 5px; background-color: #fef4e6; color: #b45309;'>"
        "⚠️ **Note:** This app runs on a free CPU. Processing is fastest with the **'Quick Process'** option. "
        "Full videos may take several minutes."
        "</div>"
    )

    with gr.Row(equal_height=True):
        with gr.Column(scale=2):
            gr.Markdown("### 1. Upload Your Video File")
            video_upload_input = gr.Video(label="Upload Video", sources=['upload'])

            gr.Markdown("### 2. Select Processing Options")
            with gr.Accordion("Settings", open=True):
                quick_process_checkbox = gr.Checkbox(label="Quick Process (First 60s Only)", value=True, info="Ideal for testing or a fast preview.")
                noise_reduction = gr.Checkbox(label="Apply Noise Reduction", value=True, info="Recommended for videos with background noise.")
                preserve_technical = gr.Checkbox(label="Preserve Technical Terms", value=True, info="Protects words like 'GAN' or 'PyTorch' from translation.")
            
            language_dropdown = gr.Dropdown(
                label="Translate To (Optional)",
                info="Select a language to translate the subtitles into.",
                choices=[
                    ("Spanish", "es"), ("French", "fr"), ("German", "de"), ("Japanese", "ja"), ("Vietnamese", "vi"), 
                    ("Chinese", "zh"), ("Hindi", "hi"), ("Portuguese", "pt"), ("Korean", "ko"), ("Tamil", "ta"), 
                    ("Ukrainian", "uk"), ("Russian", "ru"), ("Arabic", "ar")
                ],
                value="es" 
            )
            
            with gr.Row():
                process_btn = gr.Button("Generate Subtitles", variant="primary", scale=3)
                stop_btn = gr.Button("Stop", variant="stop", scale=1)

        with gr.Column(scale=3):
            gr.Markdown("### 3. View Results")
            video_output = gr.Video(label="Translated Video Player", interactive=False)
            output_files = gr.File(label="Download Subtitle Files (.srt)", file_count="multiple", interactive=False)
            summary_output = gr.Textbox(label="Processing Summary", lines=4, interactive=False)
            preview_output = gr.Textbox(label="Transcription Preview", lines=4, interactive=False)
            usage_counter = gr.HTML(f"<div style='text-align: right; color: #555; font-size: 0.9em;'>📈 Processed Videos: {get_usage_count()}</div>")

    process_event = process_btn.click(
        fn=generate_subtitles_for_video,
        inputs=[video_upload_input, noise_reduction, language_dropdown, preserve_technical, quick_process_checkbox],
        outputs=[video_output, output_files, summary_output, preview_output, usage_counter]
    )

    stop_btn.click(fn=None, inputs=None, outputs=None, cancels=[process_event])

    gr.Markdown("---")
    gr.Markdown("Made by Outlier contributors using OpenAI Whisper, mBART, and Gradio.")

if __name__ == "__main__":
    demo.launch(debug=True)
