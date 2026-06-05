# Coding Agent

A professional, provider-agnostic, and multilingual (English/French) programming assistant built with Gradio and LangChain. It features a Retrieval-Augmented Generation (RAG) system for local knowledge, real-time async streaming, a Python code execution tool with safety guardrails, and a highly polished modern UI.

## Key Features

- **Expert Programming Assistance**: Optimized for Python development with real-time word-by-word streaming.
- **Provider Agnostic**: Works with **any OpenAI-compatible API** (DashScope, OpenAI, DeepSeek, Groq, etc.) via dynamic UI configuration.
- **Advanced RAG (Knowledge Base)**: Searches local documents in `./knowledge` via `ChromaDB`. Supports custom embedding models.
- **Secure Python Execution**: Runs Python code snippets directly from the chat interface with integrated security guardrails.
- **Modern UI/UX**: Redesigned in June 2026 with a premium "Glassmorphism" aesthetic, async feedback loops, and interactive tool logs.
- **Multilingual Support**: Fully localized interface and system prompts in English and French.
- **Quota Management**: Includes a built-in free tier (10 requests/IP) with easy override for personal API keys.

## Architecture & Performance

- **Async Streaming**: Uses `astream` for high-performance, low-latency user feedback.
- **Smart Caching**: Implements a global client cache to minimize connection overhead across different providers.
- **Modern Agent Pattern**: Powered by `LangChain`'s `create_openai_tools_agent` for intelligent tool selection and execution.
- **Centralized Configuration**: All system settings are managed via a `Config` class, with real-time UI overrides.

## Security Considerations

> **Warning**: The `execute_python_code` tool executes code on the host system. While it includes a "forbidden modules" list (blocking `os`, `subprocess`, `sys`, etc.), it is **not a full sandbox**. Do not deploy this in an untrusted public environment without additional virtualization (e.g., Docker containers).

## Prerequisites

- Python 3.10+
- An API Key from an OpenAI-compatible provider (e.g., [DashScope](https://bailian.console.aliyun.com/), [OpenAI](https://platform.openai.com/), [DeepSeek](https://platform.deepseek.com/)).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/TinaMaker01/IA-agent.git
    cd coding-agent
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables (Optional)**:
    You can set a default backend key:
    ```bash
    export DASHSCOPE_API_KEY="your-api-key-here"
    ```

## Usage

### 1. Build the Knowledge Base
Place your documentation text files (`.txt`) in the `knowledge/` directory, then run:
```bash
python knowledge_base.py
```
This will create a `chromadb/` directory containing the vectorized documents.

### 2. Run the Application
Start the Gradio web interface:
```bash
python app.py
```
The app will be available at `http://localhost:7860`.

### 3. Using Custom Providers
Open the **⚙️ Advanced API Settings** in the sidebar to configure:
- **API Base URL**: Set your provider's endpoint (e.g., `https://api.openai.com/v1`).
- **LLM Model Name**: Choose your preferred model (e.g., `gpt-4o`, `deepseek-chat`).
- **Embedding Model**: Set the model used for knowledge retrieval.

## Project Structure

- `app.py`: Main application logic featuring async streaming and modern UI.
- `knowledge_base.py`: RAG processing script for vector store population.
- `i18n.py`: Multi-language support (EN/FR) and localized prompts.
- `language_utils.py`: Input validation and language detection.
- `.gitignore`: Configured to keep the repository clean of sensitive and temporary files.
- `requirements.txt`: Updated dependencies for June 2026.
