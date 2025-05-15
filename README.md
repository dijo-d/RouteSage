
<p align="center">
  <img src="assets/routesage.svg" alt="RouteSage Logo" width="200"/>
</p>

<h1 align="center">RouteSage</h1>
<p align="center">Auto-documentation for FastAPI using LLMs</p>

---

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/fastapi-async--web--framework-green)
![LLM-Powered](https://img.shields.io/badge/LLM-powered-orange)
![CLI Tool](https://img.shields.io/badge/type-CLI--Tool-lightgrey)

> ✨ Auto-documentation tool for your FastAPI projects using the power of LLMs.

---

## 📌 What is RouteSage?

**RouteSage** is a weekend vibe-coded developer tool that generates **human-readable documentation** from FastAPI route definitions using **Large Language Models (LLMs)**. Whether you're building internal tools or public APIs, RouteSage saves time by explaining endpoints in plain English—automatically.

---

## 🚀 Features

- 🧠 **LLM-Powered**: Uses cutting-edge LLMs for natural-language summaries.
- ⚡ **CLI First**: Lightweight and terminal-based.
- 📚 **Smart Parsing**: Extracts paths, methods, parameters, and descriptions from FastAPI routes.
- 📝 **Readable Output**: Converts route data into developer-friendly documentation.
- 🔒 **Private**: Supports local models or secure API integration.
- 🔧 **Future-Proof**: Easy to extend to web interfaces and CI pipelines.

---

## 🛠️ Installation

### 📦 Option 1: Install from PyPI (coming soon)

```bash
pip install routesage
```

### 🛠️ Option 2: Clone from GitHub (recommended for development)

```bash
git clone https://github.com/yourusername/routesage.git
cd routesage
pip install -e .
```

---

## ⚙️ Usage

### 🖥️ Basic CLI Usage

```bash
routesage ./app/main.py
```

### 📂 With Custom Output File

```bash
routesage ./app/main.py --output docs/routes.md
```

---

## 📄 Example Output

```markdown
### GET /users/{user_id}

Retrieves details of a specific user by their unique `user_id`. Requires authentication. Returns user profile data if found, otherwise returns 404.

### POST /items/

Creates a new item in the inventory. Accepts a JSON body with item attributes like `name`, `price`, and `description`.
```

---

## 🧠 How It Works

1. Parses FastAPI route definitions using AST (Abstract Syntax Tree).
2. Extracts HTTP method, path, parameters, and summary.
3. Sends this context to a language model (OpenAI API or local).
4. Outputs human-friendly documentation.

---

## 🔌 Model Options

| Mode         | Source              | Notes                          |
|--------------|---------------------|--------------------------------|
| `openai`     | OpenAI GPT API      | Requires API key               |
| `deepseek`   | DeepSeek API        | Good reasoning and structure   |
| `anthropic`  | Anthropic Claude API| Best at long-form clarity      |
| `gemini`     | Google Gemini API   | Fast and multilingual          |

---

## 📦 Roadmap

- [x] CLI v1 Release
- [ ] Web UI for interactive documentation
- [ ] GitHub Action integration
- [ ] SQLModel and Pydantic v2 support
- [ ] Export to Swagger, Markdown, and PDF

---

## 🧑‍💻 Contributing

Pull requests are welcome! Feel free to fork and contribute.

```bash
git clone https://github.com/yourusername/routesage.git
cd routesage
# make changes and contribute 🚀
```

---

## 📜 License

MIT © [Dijo](https://github.com/dijo-d/RouteSage/blob/main/LICENSE)

---

## 🌐 Connect

- 🐙 GitHub: [RouteSage Repo](https://github.com/dijo-d/routesage)

---

> *“Let your routes speak for themselves.” – RouteSage*
