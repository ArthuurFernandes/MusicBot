from .client import get_llm, build_messages


class OllamaRepository:

    def gerar_resposta(self, historico: list[dict], system_prompt: str = None) -> str | None:
        """
        Recebe o histórico e retorna a resposta do modelo.
        Usa o LangChain internamente — provider configurado em get_llm().
        """
        try:
            llm      = get_llm()
            messages = build_messages(historico, system_prompt)
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Erro ao chamar LLM: %s", e)
            return None