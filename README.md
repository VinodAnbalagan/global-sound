# 🌍 Global Sound — AI-Powered Video Translator & Subtitle Generator

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Live%20Demo-yellow)](https://huggingface.co/spaces/vinod-anbalagan/global-sound)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Ever wanted to watch a technical lecture from another country or share an educational video with friends who speak a different language? **Global Sound** breaks down these barriers.

This tool lets you take any video file from your computer and automatically generates accurate, multilingual subtitles. It's designed for students, educators, and anyone who believes knowledge should be accessible to all.

### 🎯 **[Try the Live Demo on Hugging Face Spaces](https://huggingface.co/spaces/vinod-anbalagan/global-sound)**

---

## ✨ Key Features

-   **Direct Video Upload**: A robust workflow where you upload a video file directly from your computer, ensuring reliability on the free cloud platform.
-   **In-App Video Player**: Watch the translated video with synchronized subtitles directly in the app.
-   **Noise-Resilient Transcription**: Uses **OpenAI Whisper** combined with `noisereduce` to generate clear text even from videos with background noise.
-   **Intelligent Translation**: Powered by **mBART-50**, it supports dozens of languages and preserves the original meaning.
-   **Technical Term Preservation**: A custom-built feature ensures that acronyms and technical terms (like "GAN", "LSTM", or "PyTorch") are not translated, maintaining context.
-   **Standard Subtitle Files**: Downloads `.srt` files for all generated languages, compatible with any video player or platform.


## 🏛️ System Architecture

The application uses a modular, multi-stage pipeline to process video files uploaded by the user. The data flows from the user's browser, is processed on the server, and the results are returned to the UI.

```bash
User's Computer  
(Client-Side)  
│  
├─ User Interface (Browser)  
│   ├─ User Downloads Video (external) → Locally saved .mp4  
│   └─ Gradio UI on Hugging Face → User uploads video  
│  
└─ Click 'Generate Subtitles' → Web Server/Orchestration  
    │  
    ├─ Gradio Event Handler (app.py)  
    │   └─ Temp Uploaded Video File  
    │  
    └─ Core Processing Pipeline:  
        │  
        ├─ 1. Audio Extraction & Cleaning:  
        │   ├─ Extract audio from video  
        │   ├─ Apply noise reduction (if enabled)  
        │   └─ Output: Clean .wav audio  
        │  
        ├─ 2. Transcription:  
        │   ├─ Whisper ASR model processes audio  
        │   ├─ Generate timestamped segments  
        │   └─ Output: Timestamped Segments (Original)  
        │  
        ├─ 3. Translation Decision:  
        │   └─ Is target language selected?  
        │       ├─ Yes → 4. Translation  
        │       │   ├─ mBART model translates segments  
        │       │   └─ Output: Timestamped Segments (Translated)  
        │       │  
        │       └─ No → Skip translation  
        │  
        └─ 5. Subtitle Generation:  
            ├─ Convert segments to .srt format  
            ├─ Create both original and translated .srt files  
            └─ Output: Generated .srt files
```

## 🛠️ Tech Stack

| Layer                 | Technology / Library                                 |
| --------------------- | ---------------------------------------------------- |
| **Web UI & Hosting**      | `Gradio`, Hugging Face Spaces                        |
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
_(Note: You may need to install `ffmpeg` on your system if you don't have it.)_

```bash
pip install -r requirements.txt
```

**4. Run the application:**

```bash
python app.py
```

The app will be available at `http://127.0.0.1:7860` in your web browser.




