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


# --- USAGE COUNTER (runs in the background) ---
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


# --- MAIN PROCESSING FUNCTION ---
def generate_subtitles_for_video(video_upload_path, apply_noise_reduction, target_language, preserve_technical_terms, quick_process, progress=gr.Progress()):
    if not video_upload_path:
        raise gr.Error("You must upload a video file to begin.")

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
        
        # This condition correctly handles when target_language is None
        if target_language and target_language != src_lang:
            progress(0.7, desc=f"Step 3/3: Translating to {target_language.upper()}...")
            translated_segments = translator.translate_segments(original_segments, src_lang, target_language, preserve_technical_terms)
            translated_srt_path = subtitle_generator.create_srt_file(f"subtitles_{target_language}", translated_segments)
            output_files.append(translated_srt_path)
            final_video_subtitle_path = translated_srt_path

        progress(1.0, desc="Processing complete!")
        summary = (
            f"Processing Complete!\n\n"
            f"Source Language Detected: {src_lang.upper()}\n"
            f"Translation Language: {target_language.upper() if target_language else 'N/A (Transcription only)'}"
        )
        preview_text = "Transcription Preview:\n" + "\n".join([seg['text'] for seg in original_segments[:5]])
        
        increment_usage_count() # Counter increments silently

        video_player_update = (video_path, final_video_subtitle_path)
        
        # Return the 4 values required by the UI outputs
        return video_player_update, output_files, summary, preview_text

    except Exception as e:
        print(f"An error occurred in the main pipeline: {e}")
        raise gr.Error(str(e))
    finally:
        for path in temp_files_to_clean:
            if os.path.isfile(path):
                try: os.remove(path)
                except OSError as e_os: print(f"Error removing file {path}: {e_os}")


# --- GRADIO UI ---
with gr.Blocks(theme=gr.themes.Soft(), title="Global Sound 🌍", css="style.css") as demo:
    gr.Markdown("# Global Sound — AI-Powered Video Translator")
    
    # --- REVISED INSTRUCTIONS ---
    gr.Markdown(
        "Translate your videos into different languages or generate a transcription in the original language. "
        "This tool creates downloadable subtitle files (`.srt`) that you can use anywhere."
    )
    gr.Markdown("### How to Use")
    gr.Markdown(
        "1. **Upload Video**: Drag and drop or click to upload your video file (`.mp4`, `.mov`, etc.).\n"
        "2. **Choose Options**: \n"
        "   - For **translation**, select a target language from the dropdown.\n"
        "   - For **transcription only**, leave the language set to `No Translation`.\n"
        "3. **Generate**: Click the **Generate Subtitles** button and wait for the process to complete."
    )

    gr.Markdown(
        "<div style='text-align:center; padding: 10px; border-radius: 5px; background-color: #fef4e6; color: #b45309;'>"
        "**Tip:** This app runs on a free CPU. For best results on long videos, enable **'Quick Process'** for a fast preview or process videos in 10-20 minute segments."
        "</div>"
    )

    # --- IMPROVED LANGUAGE DROPDOWN SETUP ---
    language_choices = [
        ("Arabic", "ar"), ("Chinese", "zh"), ("English", "en"), ("French", "fr"), 
        ("German", "de"), ("Hindi", "hi"), ("Japanese", "ja"), ("Korean", "ko"), 
        ("Portuguese", "pt"), ("Russian", "ru"), ("Spanish", "es"), ("Tamil", "ta"), 
        ("Ukrainian", "uk"), ("Vietnamese", "vi")
    ]
    translation_options = [("No Translation", None)] + sorted(language_choices)


    with gr.Row(equal_height=True):
        with gr.Column(scale=2):
            gr.Markdown("### 1. Input & Options")
            video_upload_input = gr.Video(label="Upload Video", sources=['upload'])

            with gr.Accordion("Settings", open=True):
                quick_process_checkbox = gr.Checkbox(label="Quick Process (First 60s Only)", value=True, info="Ideal for testing or a fast preview.")
                noise_reduction = gr.Checkbox(label="Apply Noise Reduction", value=True, info="Recommended for videos with background noise.")
                preserve_technical = gr.Checkbox(label="Preserve Technical Terms", value=True, info="Protects words like 'GAN' or 'PyTorch' from translation.")
            
            language_dropdown = gr.Dropdown(
                label="Translate To",
                info="Select a language for translation or choose 'No Translation'.",
                choices=translation_options,
                value=None  # Default to "No Translation"
            )
            
            with gr.Row():
                process_btn = gr.Button("Generate Subtitles", variant="primary", scale=3)
                stop_btn = gr.Button("Stop", variant="stop", scale=1)

        with gr.Column(scale=3):
            gr.Markdown("### 2. Results")
            video_output = gr.Video(label="Video with Subtitles", interactive=False)
            output_files = gr.File(label="Download Subtitle Files (.srt)", file_count="multiple", interactive=False)
            summary_output = gr.Textbox(label="Processing Summary", lines=4, interactive=False)
            preview_output = gr.Textbox(label="Transcription Preview", lines=4, interactive=False)

    process_event = process_btn.click(
        fn=generate_subtitles_for_video,
        inputs=[video_upload_input, noise_reduction, language_dropdown, preserve_technical, quick_process_checkbox],
        outputs=[video_output, output_files, summary_output, preview_output]
    )

    stop_btn.click(fn=None, inputs=None, outputs=None, cancels=[process_event])

    gr.Markdown("---")
    gr.Markdown("Made from contributors using Gemini, OpenAI Whisper, mBART, and Gradio.")

if __name__ == "__main__":
    demo.launch(debug=True)
