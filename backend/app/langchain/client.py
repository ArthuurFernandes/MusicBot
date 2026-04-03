from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from flask import current_app


def get_llm() -> BaseChatModel:
    """
    Retorna o modelo configurado.
    Para trocar de provider basta mudar aqui — o resto do código não muda.

    Exemplos futuros:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o", api_key=...)

        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-opus-4-5", api_key=...)
    """
    return ChatOllama(
        base_url   = current_app.config["OLLAMA_BASE_URL"],
        model      = current_app.config["OLLAMA_MODEL"],
        timeout    = 120,
        keep_alive = current_app.config["OLLAMA_KEEP_ALIVE"],
    )


def build_messages(historico: list[dict], system_prompt: str = None) -> list:
    """Converte o histórico do banco para o formato LangChain."""
    messages = []

    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    role_map = {
        "user":      HumanMessage,
        "assistant": AIMessage,
    }

    for msg in historico:
        cls = role_map.get(msg["role"])
        if cls:
            messages.append(cls(content=msg["content"]))

    return messages

