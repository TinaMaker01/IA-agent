import gradio as gr
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import subprocess
import tempfile
import os
import json
import logging
import portalocker
from typing import Tuple, List, Dict, Any, Optional

from i18n import (
    EXAMPLES,
    SUPPORTED_UI_LANGS,
    SYSTEM_PROMPTS,
    STRINGS,
    t,
)
from language_utils import validate_message_language

# 1. Configuration and Logging Setup
class Config:
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    USAGE_FILE: str = "total_usage.json"
    BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL: str = "qwen-max"
    EMBEDDING_MODEL: str = "text-embedding-v3"
    PERSIST_DIRECTORY: str = "./chromadb"
    MAX_FREE_QUOTA: int = 10
    EXECUTION_TIMEOUT: int = 5
    FORBIDDEN_MODULES: List[str] = ["os", "subprocess", "sys", "shutil", "socket", "requests"]
    VERSION: str = "1.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CodingAgent")

if not Config.DASHSCOPE_API_KEY:
    logger.warning("DASHSCOPE_API_KEY not found in environment. Free tier will require it for the backend.")

CUSTOM_CSS = """
:root {
    --primary-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    --glass-bg: rgba(255, 255, 255, 0.7);
    --glass-border: rgba(255, 255, 255, 0.2);
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}

.gradio-container { 
    max-width: 1200px !important; 
    margin: auto; 
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background: #f8fafc;
}

#main-header { 
    background: var(--primary-gradient); 
    padding: 2rem; 
    border-radius: 20px; 
    color: white; 
    margin-bottom: 2rem;
    box-shadow: var(--shadow-lg);
    border: 1px solid var(--glass-border);
}

#main-header h1 { 
    margin: 0; 
    color: white !important; 
    font-size: 2.5rem; 
    font-weight: 800;
    letter-spacing: -0.025em;
}

#main-header p { 
    margin: 0.75rem 0 0 0; 
    opacity: 0.9; 
    font-size: 1.1rem;
    line-height: 1.5;
}

#chat-panel { 
    border: 1px solid #e2e8f0; 
    border-radius: 20px; 
    background: white;
    padding: 1.5rem;
    box-shadow: var(--shadow-md);
}

#input-group { 
    background: #f1f5f9; 
    border: 2px solid transparent; 
    border-radius: 16px; 
    padding: 0.5rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-top: 1rem;
}

#input-group:focus-within { 
    border-color: #6366f1; 
    background: white;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

#send-btn { 
    border-radius: 12px !important; 
    font-weight: 700; 
    padding: 0.5rem 1.5rem;
    transition: all 0.2s;
    background: var(--primary-gradient) !important;
    border: none !important;
    color: white !important;
}

#send-btn:hover { 
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

#send-btn:active { 
    transform: translateY(0); 
}

#footer { 
    text-align: center; 
    padding: 3rem 0; 
    color: #94a3b8; 
    font-size: 0.875rem;
    border-top: 1px solid #e2e8f0;
    margin-top: 3rem;
}

.secondary-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow-sm);
}

#security-notice {
    background: #fff7ed;
    border: 1px solid #ffedd5;
    border-radius: 12px;
    padding: 1rem;
    color: #9a3412;
    font-size: 0.9rem;
}

/* Chatbot Customization */
.chatbot .message.user {
    background: #f1f5f9 !important;
    border-radius: 18px 18px 4px 18px !important;
}

.chatbot .message.bot {
    background: white !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 18px 18px 18px 4px !important;
}

.dark .gradio-container {
    background: #0f172a;
}

.dark #chat-panel, .dark .secondary-card {
    background: #1e293b;
    border-color: #334155;
}

.dark #input-group {
    background: #334155;
}

.dark #input-group:focus-within {
    background: #1e293b;
}
"""

# 2. Utility Functions
def get_client_ip(request: gr.Request) -> str:
    return request.client.host if request and request.client else "127.0.0.1"


def check_free_quota(ip: str, ui_lang: str) -> Tuple[bool, str]:
    """Check and decrement the free quota for an IP address with file locking."""
    try:
        with open(Config.USAGE_FILE, "r+", encoding="utf-8") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
            
            used = data.get(ip, 0)
            if used >= Config.MAX_FREE_QUOTA:
                return False, t(ui_lang, "quota_exhausted")

            data[ip] = used + 1
            f.seek(0)
            json.dump(data, f)
            f.truncate()
            
            remaining = Config.MAX_FREE_QUOTA - used - 1
            return True, t(ui_lang, "quota_free", remaining=str(remaining))
    except FileNotFoundError:
        with open(Config.USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump({ip: 1}, f)
        return True, t(ui_lang, "quota_free", remaining=str(Config.MAX_FREE_QUOTA - 1))
    except Exception as e:
        logger.error(f"Quota check error: {e}")
        return False, f"Internal Error: {str(e)}"


# Global Cache for performance
_CLIENT_CACHE: Dict[str, Any] = {}

def get_cached_client(api_key: str, client_type: str, **kwargs) -> Any:
    # Include all relevant kwargs in the cache key to handle different models/URLs
    kwargs_str = json.dumps(kwargs, sort_keys=True)
    cache_key = f"{client_type}_{api_key}_{kwargs_str}"
    if cache_key not in _CLIENT_CACHE:
        if client_type == "llm":
            _CLIENT_CACHE[cache_key] = ChatOpenAI(
                api_key=api_key,
                **kwargs
            )
        elif client_type == "embeddings":
            _CLIENT_CACHE[cache_key] = OpenAIEmbeddings(
                api_key=api_key,
                **kwargs
            )
    return _CLIENT_CACHE[cache_key]

@tool
def execute_python_code(code: str) -> str:
    """Safely run Python code and return stdout or an error message."""
    for module in Config.FORBIDDEN_MODULES:
        if f"import {module}" in code or f"from {module}" in code:
            return f"[ERROR] Security violation: Import of '{module}' is forbidden."

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            timeout=Config.EXECUTION_TIMEOUT,
            text=True,
            check=False,
        )
        output = result.stdout
        if result.stderr:
            return f"[ERROR] {result.stderr.strip()}"
        return output.strip() if output.strip() else "OK (no output)"
    except subprocess.TimeoutExpired:
        return f"[ERROR] Execution timed out ({Config.EXECUTION_TIMEOUT}s limit)"
    except Exception as e:
        return f"[ERROR] Unexpected execution error: {str(e)}"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def get_vectorstore(api_key: str, base_url: str, embed_model: str):
    embeddings = get_cached_client(
        api_key=api_key,
        client_type="embeddings",
        model=embed_model,
        base_url=base_url,
    )
    return Chroma(
        persist_directory=Config.PERSIST_DIRECTORY,
        embedding_function=embeddings,
    )


def create_search_knowledge_tool(api_key: str, base_url: str, embed_model: str):
    """Creates a configured search_knowledge tool."""
    
    @tool
    def search_knowledge(query: str) -> str:
        """Search the local knowledge base for material relevant to the question."""
        if isinstance(query, dict):
            query = query.get("query") or query.get("input") or str(query)
        if not isinstance(query, str) or not query.strip():
            return "Empty query — nothing to search."
        
        try:
            vs = get_vectorstore(api_key, base_url, embed_model)
            docs = vs.similarity_search(query, k=2)
            if not docs:
                return "No relevant information found."
            results = "\n\n---\n\n".join(doc.page_content for doc in docs)
            return f"Knowledge base results:\n\n{results}"
        except Exception as e:
            logger.error(f"Search knowledge error: {e}")
            return f"[ERROR] Failed to search knowledge base: {str(e)}"
    
    return search_knowledge


def build_agent_executor(
    api_key: str, 
    ui_lang: str, 
    base_url: str, 
    model_name: str, 
    embed_model: str
) -> AgentExecutor:
    """Build the LangChain AgentExecutor with the modern tools agent pattern."""
    lang = ui_lang if ui_lang in SUPPORTED_UI_LANGS else "en"
    llm = get_cached_client(
        api_key=api_key,
        client_type="llm",
        model=model_name,
        base_url=base_url,
        temperature=0,
        streaming=True,
    )
    
    search_tool = create_search_knowledge_tool(api_key, base_url, embed_model)
    tools = [execute_python_code, search_tool]
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPTS[lang]),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


async def chat_with_agent_stream(
    message: str,
    history: List[Dict[str, str]],
    user_api_key: str,
    ui_lang: str,
    base_url: str,
    model_name: str,
    embed_model: str,
    request: gr.Request,
):
    usage_mode = "free"
    quota_msg = ""

    # Determine which API Key to use
    if user_api_key and user_api_key.strip():
        api_key_to_use = user_api_key.strip()
        usage_mode = "paid"
        quota_msg = t(ui_lang, "quota_paid")
    else:
        client_ip = get_client_ip(request)
        ok, msg = check_free_quota(client_ip, ui_lang)
        if not ok:
            yield msg
            return
        api_key_to_use = Config.DASHSCOPE_API_KEY
        quota_msg = msg

    if not api_key_to_use:
         yield "Error: No API Key provided and backend key is missing."
         return

    # Use provided overrides or defaults
    final_base_url = base_url.strip() if base_url and base_url.strip() else Config.BASE_URL
    final_model_name = model_name.strip() if model_name and model_name.strip() else Config.MODEL
    final_embed_model = embed_model.strip() if embed_model and embed_model.strip() else Config.EMBEDDING_MODEL

    try:
        agent_executor = build_agent_executor(
            api_key_to_use, 
            ui_lang, 
            final_base_url, 
            final_model_name, 
            final_embed_model
        )
    except Exception as e:
        logger.error(f"Agent building error: {e}")
        yield t(ui_lang, "api_key_invalid", error=str(e))
        return

    chat_history = []
    for h in (history or []):
        if h["role"] == "user":
            chat_history.append(("user", h["content"]))
        else:
            chat_history.append(("assistant", h["content"]))

    try:
        full_response = ""
        async for chunk in agent_executor.astream({"input": message, "chat_history": chat_history}):
            if "actions" in chunk:
                for action in chunk["actions"]:
                    yield f"**Calling tool:** `{action.tool}`...\n"
            elif "steps" in chunk:
                for step in chunk["steps"]:
                    yield f"**Tool output:**\n```\n{step.observation}\n```\n"
            elif "output" in chunk:
                full_response += chunk["output"]
                yield full_response

        if usage_mode == "free":
            full_response = f"{full_response}\n\n---\n{quota_msg}"
            yield full_response
            
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        yield t(ui_lang, "agent_error", error=str(e))


def reject_message(ui_lang: str, reason: Optional[str]) -> str:
    if reason == "cjk":
        return t(ui_lang, "lang_reject_cjk")
    return t(ui_lang, "lang_reject_other", detected=reason or "unknown")


async def respond(
    message: str, 
    history: List[Dict[str, str]], 
    api_key: str, 
    ui_lang: str, 
    base_url: str,
    model_name: str,
    embed_model: str,
    request: gr.Request
):
    history = history or []
    if not message or not str(message).strip():
        yield "", history
        return

    ui_lang = ui_lang if ui_lang in SUPPORTED_UI_LANGS else "en"
    ok, reason = validate_message_language(message)
    if not ok:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reject_message(ui_lang, reason)})
        yield "", history
        return

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ""})
    yield "", history

    async for chunk in chat_with_agent_stream(
        message, 
        history[:-2], 
        api_key, 
        ui_lang, 
        base_url, 
        model_name, 
        embed_model, 
        request
    ):
        history[-1]["content"] = chunk
        yield "", history


def switch_ui_language(lang: str):
    lang = lang if lang in SUPPORTED_UI_LANGS else "en"
    return (
        gr.update(value=STRINGS[lang]["hero_title"]),
        gr.update(value=STRINGS[lang]["hero_body"]),
        gr.update(label=STRINGS[lang]["chat_label"]),
        gr.update(
            placeholder=STRINGS[lang]["input_placeholder"],
        ),
        gr.update(value=STRINGS[lang]["send_btn"]),
        gr.update(
            label=STRINGS[lang]["api_key_label"],
            placeholder=STRINGS[lang]["api_key_placeholder"],
            info=STRINGS[lang]["api_key_info"],
        ),
        gr.update(label=STRINGS[lang]["sidebar_title"]),
        gr.update(value=STRINGS[lang]["sidebar_body"]),
        gr.update(label=STRINGS[lang]["examples_label"], samples=EXAMPLES[lang]),
        gr.update(value=STRINGS[lang]["clear_btn"]),
        gr.update(label=STRINGS[lang]["adv_settings_title"]),
        gr.update(label=STRINGS[lang]["base_url_label"]),
        gr.update(label=STRINGS[lang]["model_name_label"]),
        gr.update(label=STRINGS[lang]["embed_model_label"]),
    )


with gr.Blocks(
    title="Coding Agent",
    theme=gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="slate",
        font=("Inter", "ui-sans-serif", "system-ui"),
        spacing_size="md",
        radius_size="lg",
    ),
    css=CUSTOM_CSS,
) as demo:
    with gr.Row(elem_id="main-header"):
        with gr.Column(scale=4):
            hero_title = gr.Markdown(STRINGS["en"]["hero_title"])
            hero_body = gr.Markdown(STRINGS["en"]["hero_body"])
        with gr.Column(scale=1, min_width=200):
            ui_lang = gr.Dropdown(
                choices=[("English", "en"), ("Français", "fr")],
                value="en",
                label="🌐 Language",
                container=True
            )

    with gr.Row(equal_height=False):
        with gr.Column(scale=3):
            with gr.Column(elem_id="chat-panel"):
                chatbot = gr.Chatbot(
                    label=STRINGS["en"]["chat_label"],
                    height=600,
                    show_copy_button=True,
                    bubble_full_width=False,
                    avatar_images=(
                        "https://api.dicebear.com/7.x/avataaars/svg?seed=user",
                        "https://api.dicebear.com/7.x/bottts/svg?seed=coding-agent",
                    ),
                    type="messages",
                    render_markdown=True,
                )
                with gr.Group(elem_id="input-group"):
                    with gr.Row():
                        msg = gr.Textbox(
                            placeholder=STRINGS["en"]["input_placeholder"],
                            lines=1,
                            max_lines=10,
                            scale=10,
                            show_label=False,
                            container=False,
                        )
                        send_btn = gr.Button(
                            STRINGS["en"]["send_btn"],
                            variant="primary",
                            scale=1,
                            elem_id="send-btn",
                        )
                with gr.Row():
                    clear_btn = gr.Button(
                        STRINGS["en"]["clear_btn"], 
                        variant="secondary", 
                        size="sm",
                        elem_id="clear-btn"
                    )

            def clear_chat():
                return "", []

            clear_btn.click(clear_chat, None, [msg, chatbot])

            with gr.Column(elem_classes=["secondary-card"]):
                examples = gr.Examples(
                    examples=EXAMPLES["en"],
                    inputs=msg,
                    label=STRINGS["en"]["examples_label"],
                    examples_per_page=4
                )

        with gr.Column(scale=1):
            with gr.Group(elem_classes=["secondary-card"]):
                gr.Markdown("### 🔑 Configuration")
                api_key_input = gr.Textbox(
                    label=STRINGS["en"]["api_key_label"],
                    show_label=True,
                    type="password",
                    placeholder=STRINGS["en"]["api_key_placeholder"],
                    info=STRINGS["en"]["api_key_info"],
                )
                
                with gr.Accordion(STRINGS["en"]["adv_settings_title"], open=False) as adv_settings:
                    base_url_input = gr.Textbox(
                        label=STRINGS["en"]["base_url_label"],
                        placeholder=Config.BASE_URL,
                        value=Config.BASE_URL
                    )
                    model_name_input = gr.Textbox(
                        label=STRINGS["en"]["model_name_label"],
                        placeholder=Config.MODEL,
                        value=Config.MODEL
                    )
                    embed_model_input = gr.Textbox(
                        label=STRINGS["en"]["embed_model_label"],
                        placeholder=Config.EMBEDDING_MODEL,
                        value=Config.EMBEDDING_MODEL
                    )
            
            sidebar_accordion = gr.Accordion(STRINGS["en"]["sidebar_title"], open=True)
            with sidebar_accordion:
                sidebar_body = gr.Markdown(STRINGS["en"]["sidebar_body"])
            
            with gr.Column(elem_id="security-notice"):
                gr.Markdown("### 🛡️ Security")
                gr.Markdown("Code execution is sandboxed against basic system calls. Use caution with untrusted scripts.")

    footer = gr.Markdown(
        f"Coding Agent v{Config.VERSION} • Optimized for Performance • [GitHub](https://github.com/)",
        elem_id="footer"
    )

    ui_lang.change(
        switch_ui_language,
        inputs=[ui_lang],
        outputs=[
            hero_title,
            hero_body,
            chatbot,
            msg,
            send_btn,
            api_key_input,
            sidebar_accordion,
            sidebar_body,
            examples,
            clear_btn,
            adv_settings,
            base_url_input,
            model_name_input,
            embed_model_input,
        ],
    )

    submit_inputs = [
        msg, 
        chatbot, 
        api_key_input, 
        ui_lang, 
        base_url_input, 
        model_name_input, 
        embed_model_input
    ]
    submit_outputs = [msg, chatbot]

    msg.submit(respond, submit_inputs, submit_outputs)
    send_btn.click(respond, submit_inputs, submit_outputs)


if __name__ == "__main__":
    if not os.path.exists(Config.USAGE_FILE):
        with open(Config.USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    demo.launch(server_port=7860, share=False)
