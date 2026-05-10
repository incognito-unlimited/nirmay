# Nirmay: Rural Health Report Simplifier 🌿

**Live Demo**: [https://nirmay.streamlit.app/](https://nirmay.streamlit.app/)

## Detailed Project Description
**Nirmay** is a compassionate, AI-powered Medical Interpreter specifically designed to bridge the healthcare literacy gap for rural and low-literacy populations. Medical reports (especially blood tests, diagnostic findings, and prescriptions) are frequently laden with dense, alarming jargon that can induce anxiety and confusion for patients without a medical background. 

Nirmay solves this by running state-of-the-art Optical Character Recognition (OCR) to extract unstructured text from uploaded health report PDFs (handling both digital and scanned documents) and translating it into plain, reassuring, and jargon-free language. 

The core application provides:
1. **Simplified Summary:** A short, gentle overview of what the document represents.
2. **Key Metrics Decoding:** Careful identification and plain-language explanation of any flagged metrics without providing direct medical diagnoses.
3. **Actionable Next Steps:** Three tailored, specific questions the patient should ask their human doctor at the next visit.
4. **Conversational Follow-ups:** A chat interface where patients can ask targeted questions based directly on the provided context of their report.

## Features
* **Hybrid AI Engine**: Secure, privacy-first local processing via Ollama (`llama3.1:8b`) with automatic fallback to Groq's high-speed cloud endpoint (`llama-3.1-8b-instant`).
* **Hybrid OCR Fallback**: Automatically tries to extract digital text using `PyPDF2`, and gracefully falls back to `pytesseract` OCR + `pdf2image` for scanned image PDFs.
* **Streamlit UI**: Simple, intuitive dialogue UI equipped with chat capabilities for follow-up questions.