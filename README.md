# 🌍 Global Sound — AI-Powered Video Translator & Subtitle Generator

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/vinod-anbalagan/global-sound)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Global Sound** is a multilingual subtitle generator that transcribes spoken content from videos, translates it intelligently across languages, and generates subtitle (`.srt`) files — all through a simple web UI.

Designed for educators, researchers, creators, and accessibility champions.

### 🎯 Try It Live → [Global Sound on Hugging Face Spaces](https://huggingface.co/spaces/vinod-anbalagan/global-sound)

---

![Architecture Diagram](assets/architecture_diagram.png)
_(Hint: Make sure to add the architecture diagram image to `assets/architecture_diagram.png` in your repo)_

---

## ✨ Key Features

- 🎤 **Noise-Resilient Transcription** using OpenAI Whisper and `noisereduce`.
- 🌐 **Multilingual Translation** with mBART-50: Supports Spanish, French, German, Japanese, Hindi, Chinese, Tamil, Korean, Portuguese — and more!
- 🤖 **Technical Term Preservation**: Acronyms like "GAN", "LSTM", or "PyTorch" won't get translated incorrectly.
- 🎞️ **Subtitle Generator**: Outputs accurate `.srt` files for both the original and translated texts.
- 🌐 **Simple Web UI**: Built with Gradio, deployable to Hugging Face Spaces with one click.

---

## 🛠 Tech Stack

| Layer            | Tech                                          |
| ---------------- | --------------------------------------------- |
| Transcription    | `openai-whisper`                              |
| Translation      | `facebook/mbart-large-50-many-to-many-mmt`    |
| Audio Processing | `moviepy`, `librosa`, `noisereduce`, `ffmpeg` |
| UI               | `Gradio`                                      |
| Hosting          | `Hugging Face Spaces`                         |

---

## ⚙️ Local Setup

```bash
# Clone the repo
git clone https://github.com/VinodAnbalagan/global-sound.git
cd global-sound

# Create & activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app locally
python app.py
```
