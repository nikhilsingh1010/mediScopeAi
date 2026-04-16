# 🩺 mediScopeAi  
### AI-Powered Medical Report Diagnosis & Patient–Doctor Intelligence Platform

mediScopeAi is a **GenAI-powered medical diagnosis platform** that allows patients to upload medical reports and receive AI-assisted diagnostic insights, while enabling doctors to securely review patient diagnosis history.  
The system uses **FastAPI, Streamlit, LangChain, Google Gemini embeddings, Pinecone, and MongoDB**.

---

## 🚀 Features

### 👤 Patient
- Secure signup & login
- Upload medical reports (PDF / TXT)
- AI-generated diagnosis from uploaded reports
- Ask follow-up medical questions
- View diagnosis sources and references

### 🩺 Doctor
- Secure doctor authentication
- View patient diagnosis history
- Access previous reports and AI-generated answers
- Review supporting document sources

---

## 🧠 Tech Stack

### Backend
- **FastAPI** – REST API
- **MongoDB Atlas** – User & diagnosis storage
- **LangChain** – RAG pipeline
- **Google Gemini Embeddings** – Text embeddings
- **Pinecone** – Vector database
- **Python AsyncIO** – Non-blocking processing

### Frontend
- **Streamlit** – Interactive UI

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory:

```env
MONGO_URI=your_mongodb_connection_string
DB_NAME=rbac-diagnosis

OPENAI_API_KEY=your_openai_api_key

PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=rbac-diagnosis-index

📦 Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/nikhilsingh1010/mediScopeAi.git
cd MedicalReportDiagnosis

2️⃣ Create Virtual Environment
python -m venv .venv

3️⃣ Activate Virtual Environment

Windows (PowerShell):

.\.venv\Scripts\Activate


Mac / Linux:

source .venv/bin/activate

4️⃣ Install Dependencies
pip install -r requirements.txt

▶️ Running the Project
Start Backend (FastAPI)
uvicorn server.main:app --reload


Backend runs at:

http://127.0.0.1:8000

Start Frontend (Streamlit)
streamlit run client/app.py

🔐 API Highlights

POST /auth/login – User authentication

POST /reports/upload – Upload medical reports

POST /diagnosis/analyze – AI diagnosis

GET /diagnosis/history – View diagnosis history

🧪 Sample Use Case

User logs in

Uploads a blood report PDF

AI extracts medical values

GenAI analyzes abnormalities

User receives diagnostic insights

History saved for future reference

🧠 Future Enhancements

✅ OCR for scanned reports

📈 Health trend analytics

🧑‍⚕️ Doctor dashboard

🌐 Cloud deployment

🔔 Health alerts & recommendations

🤝 Contributing

Contributions are welcome!

Fork the repo

Create a new branch

Commit changes

Open a Pull Request

👨‍💻 Author

Nikhil Singh Thakur

GitHub: https://github.com/nikhilsingh1010

Role: Software Engineer Intern / Full-Stack Developer

📜 License

This project is licensed under the MIT License.

⭐ If you like this project, don’t forget to star the repository!



