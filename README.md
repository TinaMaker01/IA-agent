# Coding Agent

A professional, multilingual (English/French) programming assistant built with Gradio and LangChain. It features a Retrieval-Augmented Generation (RAG) system for local knowledge, a Python code execution tool with safety guardrails, and a quota-based free tier.

## Key Features

- **Expert Programming Assistance**: Optimized for Python development.
- **RAG (Knowledge Base)**: Searches local documents in `./knowledge` via `ChromaDB` to provide context-aware answers.
- **Python Execution**: Runs Python code snippets directly from the chat interface, equipped with security guardrails.
- **Multilingual Support**: Fully localized interface and system prompts in English and French.
- **Quota Management**: Lifetime limit of 10 free requests per IP, with an option to use a personal DashScope API key for unlimited access.
- **Polished UI/UX**: Modern interface featuring a clean layout, responsive command bar, and organized settings using `Gradio` with custom CSS.

## Architecture & Maintainability

- **Modern Agent Pattern**: Uses `LangChain`'s `create_openai_tools_agent` and `AgentExecutor` for robust tool interaction.
- **Centralized Configuration**: All system settings are managed via a `Config` class in `app.py`.
- **Robust Quota System**: Uses `portalocker` for thread-safe/process-safe, file-based quota tracking.
- **Structured Logging**: Implements standard Python `logging` for improved monitoring and debugging.
- **Type Safety**: Fully type-hinted codebase for better maintainability.

## Security Considerations

> **Warning**: The `execute_python_code` tool executes code on the host system. While it includes a "forbidden modules" list (blocking `os`, `subprocess`, `sys`, etc.), it is **not a full sandbox**. Do not deploy this in an untrusted public environment without additional virtualization (e.g., Docker containers with strict security profiles).

## Prerequisites

- Python 3.10+
- A [DashScope (Aliyun)](https://bailian.console.aliyun.com/) API Key.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd coding-agent
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables**:
    Export your API key:
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

## Project Structure

- `app.py`: Main Gradio application, UI definition, agent orchestration, and configuration.
- `knowledge_base.py`: Script to process text files and populate the vector store.
- `i18n.py`: Internationalization strings and system prompts for EN/FR.
- `language_utils.py`: Language detection and validation heuristics.
- `knowledge/`: Source text files for the RAG system.
- `requirements.txt`: Project dependencies with pinned versions.
