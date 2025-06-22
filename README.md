# 🌍 Global Sound — AI-Powered Video Translator & Subtitle Generator

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Live%20Demo-yellow)](https://huggingface.co/spaces/vinod-anbalagan/global-sound)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Ever wanted to watch a technical lecture from another country or share an educational video with friends who speak a different language? **Global Sound** breaks down these barriers.

This tool lets you take any video—either by uploading a file or simply pasting a YouTube URL—and automatically generates accurate, multilingual subtitles. It's designed for students, educators, and anyone who believes knowledge should be accessible to all.

### 🎯 **[Try the Live Demo on Hugging Face Spaces](https://huggingface.co/spaces/vinod-anbalagan/global-sound)**

---

![App Screenshot](https://raw.githubusercontent.com/VinodAnbalagan/global-sound/main/assets/app_screenshot.png)
*(**Note:** Make sure you create an `assets` folder and add a screenshot named `app_screenshot.png` to your repository)*

---

## ✨ Key Features

-   **YouTube & Local File Support**: Simply paste a YouTube link or upload your own video file to get started.
-   **In-App Video Player**: Watch the translated video with synchronized subtitles directly in the app—no need to go back to YouTube.
-   **Noise-Resilient Transcription**: Uses **OpenAI Whisper** combined with `noisereduce` to generate clear text even from videos with background noise.
-   **Intelligent Translation**: Powered by **mBART-50**, it supports dozens of languages and preserves the original meaning.
-   **Technical Term Preservation**: A custom-built feature ensures that acronyms and technical terms (like "GAN", "LSTM", or "PyTorch") are not translated, maintaining context.
-   **Standard Subtitle Files**: Downloads `.srt` files for all generated languages, compatible with any video player or platform.

## 🏛️ System Architecture

The application uses a modular, multi-stage pipeline to process videos. The data flows from the user interface through audio processing, transcription, translation, and finally to subtitle generation.

![Architecture Diagram](https://raw.githubusercontent.com/VinodAnbalagan/global-sound/main/assets/architecture_diagram.png)
*(**Note:** You will need to create and upload this diagram to the `assets` folder)*

## 🛠️ Tech Stack

| Layer                 | Technology / Library                                 |
| --------------------- | ---------------------------------------------------- |
| **Web UI & Hosting**      | `Gradio`, Hugging Face Spaces                        |
| **Video Downloading**   | `pytube`                                             |
| **Audio Processing**    | `MoviePy`, `Librosa`, `noisereduce`                  |
| **AI Transcription**    | `openai-whisper` (State-of-the-art ASR)              |
| **AI Translation**      | `facebook/mbart-large-50-many-to-many-mmt`           |
| **Subtitle Generation** | `pysrt`                                              |

## ⚙️ How to Run Locally

To run this application on your own machine, follow these steps.

**1. Clone the repository:**
```bash
git clone https://github.com/VinodAnbalagan/global-sound.git
cd global-sound
```

**2. Create and activate a virtual environment:**
```bash
# Create a virtual environment
python -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate
# On Windows: venv\Scripts\activate
```

**3. Install dependencies:**
*(Note: You may need to install `ffmpeg` on your system if you don't have it.)*
```bash
pip install -r requirements.txt
```

**4. Run the application:**
```bash
python app.py
```
The app will be available at `http://127.0.0.1:7860` in your web browser.

