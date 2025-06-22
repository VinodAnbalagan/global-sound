import gradio as gr
import os
import tempfile

# Importing all custom modules from src/
from src.audio_processor import AudioProcessor
from src.transcriber import Transcriber
from src.translator import Translator
from src.subtitle_generator import SubtitleGenerator

# --- 1. INITIALIZE ALL MODELS ONCE ON STARTUP ---

# This improves performance by avoiding reloading on every request
print("Initializing all models, please wait...")

audio_processor = AudioProcessor()  # For extracting + denoising audio
transcriber = Transcriber(model_size="base")  # OpenAI Whisper
translator = Translator()  # mBART-50
subtitle_generator = SubtitleGenerator()  # .srt writer

print("\nAll models initialized. The application is ready.")

# --- NEW: USAGE COUNTER ---
COUNTER_FILE = "usage_count.txt"

def get_usage_count():
    """Reads the current usage count from the counter file."""
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except (ValueError, IndexError):
            return 0

def increment_usage_count():
    """Increments the usage count and saves it to the file."""
    count = get_usage_count() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

# --- 2. DEFINE THE MAIN FUNCTION (video -> subtitles) ---

def generate_subtitles_for_video(video_path, apply_noise_reduction, target_languages, preserve_technical_terms, progress=gr.Progress()):
    """
    The full pipeline: extract audio → transcribe → translate → create subtitles.
    """
    if not video_path:
        raise gr.Error("You must upload a video file.")
    if not target_languages:
        raise gr.Error("Please select at least one target language.")

    output_files = []
    temp_files_to_clean = []

    try:
        # --- Stage 1: Audio Processing ---
        progress(0.1, desc="Step 1/4: Extracting and cleaning audio...")
        processed_audio_path = audio_processor.extract_and_process_audio(video_path, apply_noise_reduction)
        temp_files_to_clean.append(processed_audio_path)

        # --- Stage 2: Transcription ---
        progress(0.3, desc="Step 2/4: Transcribing audio...")
        original_segments, src_lang = transcriber.transcribe_audio(processed_audio_path)

        # --- Generate Original Language Subtitle ---
        progress(0.6, desc="Step 3/4: Generating original language subtitles...")
        original_srt_path = subtitle_generator.create_srt_file(f"subtitles_{src_lang}", original_segments)
        output_files.append(original_srt_path)

        # --- Stage 3: Translation + Subtitle Generation ---
        for i, lang in enumerate(target_languages):
            if lang == src_lang:
                continue  # Skip if same as source
            progress(0.7 + (i * 0.3 / len(target_languages)), desc=f"Step 4/4: Translating to {lang}...")

            translated_segments = translator.translate_segments(
                segments=original_segments,
                src_lang=src_lang,
                target_lang=lang,
                preserve_technical=preserve_technical_terms
            )

            translated_srt_path = subtitle_generator.create_srt_file(f"subtitles_{lang}", translated_segments)
            output_files.append(translated_srt_path)

        # Final Progress
        progress(1.0, desc="All subtitles generated!")

        summary = (
            f"Processing Complete!\n\n"
            f"Source Language Detected: {src_lang.upper()}\n"
            f"Subtitles Generated: {len(output_files)}\n"
            f"Files Created: {', '.join([os.path.basename(f) for f in output_files])}"
        )

        preview_text = "Transcription Preview:\n" + "\n".join([seg['text'] for seg in original_segments[:5]])

        # Increment usage counter and create styled HTML to display it
        usage_count = increment_usage_count()
        usage_html = f"<div style='text-align: right; color: #555; font-size: 0.9em;'>📈 Processed Videos: {usage_count}</div>"

        return output_files, summary, preview_text, usage_html

    except Exception as e:
        raise gr.Error(f"An error occurred: {e}")

    finally:
        # Clean temporary audio files
        for temp_file in temp_files_to_clean:
            if os.path.exists(temp_file):
                os.remove(temp_file)

# --- 3. BUILD THE UI ---

with gr.Blocks(theme=gr.themes.Soft(), title="Global Sound 🌍", css="style.css") as demo:
    gr.Markdown("# Global Sound — AI-Powered Video Translator")
    gr.Markdown("Upload a video, and generate subtitles in multiple languages with technical term preservation!")

    with gr.Row():
        with gr.Column(scale=1):
            video_input = gr.Video(label="Upload Your Video", sources=['upload'])

            gr.Markdown("### Advanced Options")
            with gr.Accordion("Settings", open=False):
                noise_reduction = gr.Checkbox(label="Apply Noise Reduction", value=True)
                preserve_technical = gr.Checkbox(label="Preserve Technical Terms", value=True)

            languages = gr.CheckboxGroup(
                choices=[
                    ("Spanish", "es"), ("French", "fr"), ("German", "de"), ("Japanese", "ja"), ("Vietnamese", "sw"), 
                    ("Chinese", "zh"), ("Hindi", "hi"), ("Portuguese", "pt"), ("Korean", "ko"), ("Tamil", "ta"), ("Ukrainian", "uk")
                ],
                label="Translate To:",
                value=["es", "fr", "ta", "uk"] # default selected languages
            )

            process_btn = gr.Button(" Generate Subtitles", variant="primary")

        with gr.Column(scale=2):
            output_files = gr.File(label=" Download Subtitles", file_count="multiple", interactive=False)
            summary_output = gr.Textbox(label=" Summary", lines=5, interactive=False)
            preview_output = gr.Textbox(label=" Transcription Preview", lines=8, interactive=False)
            
            # Display for the usage counter, initialized with the current count
            usage_counter = gr.HTML(
                f"<div style='text-align: right; color: #555; font-size: 0.9em;'>📈 Processed Videos: {get_usage_count()}</div>"
            )

    # Wire the button to the function
    process_btn.click(
        fn=generate_subtitles_for_video,
        inputs=[video_input, noise_reduction, languages, preserve_technical],
        outputs=[output_files, summary_output, preview_output, usage_counter]
    )

    gr.Markdown("---")
    gr.Markdown("Made using OpenAI Whisper, mBART, Gradio, and Python")

# --- 4. LAUNCH ---

if __name__ == "__main__":
    demo.launch(debug=True)