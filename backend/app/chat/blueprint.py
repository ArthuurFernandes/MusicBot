from flask import Blueprint, request
from .service import ChatService
from app.core.auth_guard import require_auth
from app.core.http import success, error, not_found
from app.spotify.repository import SpotifyRepository
from app.spotify.service import SpotifyService

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def _svc() -> ChatService:
    return ChatService()


def _get_spotify_id(token: str) -> str:
    """Busca o spotify_id do usuário autenticado."""
    return SpotifyService(SpotifyRepository(token)).get_profile()["id"]


# ── Criar novo chat ───────────────────────────────────────────────────────────

@chat_bp.post("/")
@require_auth
def criar_chat(token: str):
    body   = request.get_json(silent=True) or {}
    titulo = body.get("titulo", "Nova conversa")

    spotify_id = _get_spotify_id(token)
    resultado  = _svc().iniciar_chat(spotify_id, titulo)
    return success(resultado, 201)


# ── Listar chats do usuário ───────────────────────────────────────────────────

@chat_bp.get("/")
@require_auth
def listar_chats(token: str):
    spotify_id = _get_spotify_id(token)
    return success({"chats": _svc().listar_chats(spotify_id)})


# ── Enviar mensagem ───────────────────────────────────────────────────────────

@chat_bp.post("/<int:chat_id>/message")
@require_auth
def enviar_mensagem(token: str, chat_id: int):
    body     = request.get_json(silent=True) or {}
    mensagem = body.get("mensagem", "").strip()

    if not mensagem:
        return error("Campo 'mensagem' obrigatório", 400, "missing_message")

    spotify_id = _get_spotify_id(token)
    resultado  = _svc().enviar_mensagem(spotify_id, chat_id, mensagem)

    if resultado is None:
        return not_found("Chat não encontrado")

    return success(resultado)