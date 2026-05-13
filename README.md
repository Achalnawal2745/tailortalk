# 🚀 TailorTalk: AI-Powered Google Drive Agent

TailorTalk is a high-performance, multimodal AI assistant designed to transform how you interact with your Google Drive. Powered by **Llama 3.3 70B** and **Llama 4 Scout Vision**, it doesn't just find files—it understands them.

## ✨ Key Features

- **🔍 Recursive Deep Search**: Traverses complex folder structures to find files anywhere in your drive.
- **👁️ Multimodal Vision**: Uses **Llama 4 Scout** to describe images (PNG, JPG, JPEG) in detail.
- **📄 Document Intelligence**:
  - Reads and summarizes **PDFs** (Resumes, Reports).
  - Parses **Word Documents** (.docx).
  - Analyzes **Google Sheets** and **Google Docs**.
- **🧠 Advanced Reasoning**: Built with **LangChain** and **FastAPI** for reliable tool calling and fast response times via **Groq**.
- **💻 Modern UI**: Sleek, interactive **Streamlit** frontend with real-time chat history.

## 🛠️ Tech Stack

- **Backend**: FastAPI, LangChain, Groq API.
- **Frontend**: Streamlit.
- **Models**: Llama 3.3 70B (Reasoning), Llama 4 Scout (Vision).
- **Integrations**: Google Drive API v3.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- A [Groq API Key](https://console.groq.com/)
- A Google Cloud [Service Account](https://console.cloud.google.com/) with Drive API enabled.

### 2. Setup
1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configuration
1. Create a `.env` file (see `.env.example`):
   ```env
   GROQ_API_KEY=your_key_here
   DRIVE_FOLDER_ID=your_folder_id_here
   GOOGLE_APPLICATION_CREDENTIALS=data/service-account.json
   ```
2. Place your `service-account.json` inside the `data/` folder.
3. **Crucial**: Share your Google Drive folder with the `client_email` found in your service account JSON.

### 4. Running the App
**Start the Backend:**
```bash
python -m uvicorn backend.main:app --reload
```

**Start the Frontend:**
```bash
streamlit run frontend/app.py
```

## 🌐 Deployment

This project is Docker-ready. For platforms like Railway or Render:
1. Set the `SERVICE_ACCOUNT_JSON` environment variable with the full text of your JSON file.
2. The app will automatically build using the included `Dockerfile`.

---
*Developed as part of the TailorTalk Internship Assignment.*
