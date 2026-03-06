# 🚀 CodeRefine AI – AI Code Review & Security Analyzer

CodeRefine AI is a full-stack, AI-powered developer tool that performs automated code analysis, security scanning, and intelligent code rewriting. By leveraging large language models, this platform helps developers improve code quality, automatically review code, detect vulnerabilities, and instantly refactor complex syntax.

---

## ✨ Key Features

- **🔍 AI Code Review**: Analyze source code to detect bugs, security issues, and performance problems.
- **🛠️ AI Code Rewrite**: Automatically refactor and optimize code using state-of-the-art AI.
- **📁 GitHub Repository Analyzer**: Analyze entire GitHub repositories and detect risky files and vulnerabilities.
- **🛡️ Security Analysis**: Identify insecure coding patterns, exposed credentials, and risky configurations.
- **💡 Code Explanation**: Explain complex code logic using AI to help developers rapidly understand new codebases.

---

## 💻 Tech Stack

### Frontend
- **HTML5**
- **Tailwind CSS**
- **JavaScript (Vanilla)**

### Backend
- **Python**
- **FastAPI**

### AI Capabilities
- **Groq API**
- **Llama 3.3 70B Model**

### Other Tools
- **GitPython**
- **Docker**
- **Render** (Deployment)

---

## 🏗️ Architecture Overview

The system follows a streamlined flow for rapid analysis:

**User Input** ➔ **FastAPI Backend** ➔ **AI Model (Groq)** ➔ **Code Analysis** ➔ **Results Displayed in UI**

---

## 📂 Project Structure

```text
.
├── backend/
│   ├── main.py
│   ├── ai_service.py
│   ├── github_analyzer.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── styles.css
├── Dockerfile
└── render.yaml
```

---

## ⚙️ Installation

To run this project locally, follow these steps:

**1. Clone the repository**
```bash
git clone https://github.com/kantrolv/code
```

**2. Navigate into the project**
```bash
cd code
```

**3. Install dependencies**
```bash
pip install -r backend/requirements.txt
```

**4. Add environment variables**
Create a `.env` file in the root or backend directory and add your Groq API key:
```env
GROQ_API_KEY=your_api_key
```

**5. Run the server**
```bash
uvicorn backend.main:app --reload
```

---

## 🚀 Deployment

The application is fully containerized and automatically deployed using **Docker** and **Render**.

**Deployment Steps:**
1. Code is pushed to GitHub.
2. Render reads the `render.yaml` configuration.
3. Docker builds the application container based on the `Dockerfile`.
4. The FastAPI server is automatically started and exposed securely.

---

## 🌐 Live Demo

Experience CodeRefine AI live:  
👉 **[Live Demo: https://coderefine-ai.onrender.com](https://coderefine-ai.onrender.com)**

---

## 🔮 Future Improvements

- [ ] **Automated PR Generation**: Generate automatic pull requests for fixing detected vulnerabilities.
- [ ] **Advanced Security Scoring**: Provide standard security benchmarking and grading for scanned repositories.
- [ ] **Dependency Scanning**: Identify and alert users on outdated or vulnerable repository dependencies.
- [ ] **Real-Time Collaboration**: Real-time collaborative workspace for development teams.

---

## 🤝 Contributing

Contributions are always welcome!  
If you have suggestions or want to add features, feel free to **open an issue** or **submit a pull request**. 

---

## 📄 License

This project is licensed under the **MIT License**.
