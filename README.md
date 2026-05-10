# Nirmay: Rural Health Report Simplifier 🌿

An AI-powered Medical Interpreter designed to help rural and low-literacy populations understand their medical reports.

## Features
* **Hybrid AI Engine**: Secure, privacy-first local processing via Ollama (`llama3.1:8b`) with automatic fallback to Groq's high-speed cloud endpoint.
* **Hybrid OCR Fallback**: Automatically tries to extract digital text using `PyPDF2`, and gracefully falls back to `pytesseract` OCR + `pdf2image` for scanned image PDFs.
* **Streamlit UI**: Simple, intuitive dialogue UI equipped with chat capabilities for follow-up questions.

## Deployment Next Steps

### 1. Streamlit Community Cloud (Recommended Cloud Setup)
1. Push this project to a GitHub repository.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io).
3. Click **"New App"** and select your GitHub repository, setting the entry point to `app.py`.
4. In the app's "Advanced Settings", add your `GROQ_API_KEY` to the **Secrets** section.
5. **Critical**: You must create a `packages.txt` file in your repository containing the Linux packages needed for OCR:
   ```text
   poppler-utils
   tesseract-ocr
   ```
   *Note*: In the cloud sandbox, the Ollama process isn't running on `localhost`. Setting up the API keys ensures your Groq Cloud fallback kicks in automatically!