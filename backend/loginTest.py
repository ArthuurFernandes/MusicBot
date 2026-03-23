"""
loginTest.py — Login com Spotify (PKCE) usando Flask
Instalar: pip install flask requests spotipy
Rodar:    python loginTest.py
"""

import os, hashlib, base64, secrets
import urllib.parse
import requests
from flask import Flask, redirect, request, session, url_for, render_template_string
from functions import get_playlists, get_recently_played, get_top_tracks, get_top_artists, get_saved_tracks

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "troca-por-uma-chave-fixa-qualquer-aqui")
app.config["SESSION_COOKIE_SAMESITE"] = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

# ── Configuração ───────────────────────────────────────────────────────────────
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "b5727e21ded847928278e6fe1782060f")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
POST_LOGIN_REDIRECT_URI = os.getenv("POST_LOGIN_REDIRECT_URI", "/profile")
SCOPES = " ".join([
    "user-read-private",
    "user-read-email",
    "user-library-read",
    "user-top-read",
    "user-read-recently-played",
    "playlist-read-private",
    "playlist-modify-public",
    "playlist-modify-private",
])

AUTH_URL  = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE  = "https://api.spotify.com/v1"


def wants_html():
    accept_header = request.headers.get("Accept", "")
    return "text/html" in accept_header


def unauthorized():
    if wants_html():
        return redirect(url_for("index"))
    return {"error": "not_authenticated"}, 401


def get_current_user():
    token = session.get("access_token")
    if not token:
        return None, None

    me = requests.get(f"{API_BASE}/me", headers={"Authorization": f"Bearer {token}"})
    if me.status_code == 401:
        session.clear()
        return None, 401
    if not me.ok:
        return None, me.status_code

    user = me.json()
    return {
        "name": user.get("display_name", "Usuário"),
        "display_name": user.get("display_name", "Usuário"),
        "email": user.get("email", ""),
        "followers": user.get("followers", {}).get("total", 0),
        "avatar": (user.get("images") or [{}])[0].get("url", ""),
        "plan": user.get("product", "free").upper(),
        "product": user.get("product", "free"),
        "images": user.get("images", []),
    }, None

# ── PKCE ───────────────────────────────────────────────────────────────────────
def make_verifier():
    return base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()

def make_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

# ── Templates ──────────────────────────────────────────────────────────────────

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MusicBot — Login</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root { --green: #1DB954; --bg: #080808; --card: #101010; --border: #1e1e1e; --text: #f0ede8; --muted: #555; }
    body { background: var(--bg); font-family: 'DM Sans', sans-serif; min-height: 100vh; display: grid; grid-template-columns: 1fr 1fr; }
    .left { background: #0d0d0d; border-right: 1px solid var(--border); display: flex; flex-direction: column; justify-content: space-between; padding: 48px; position: relative; overflow: hidden; }
    .left::before { content: ''; position: absolute; width: 500px; height: 500px; border-radius: 50%; background: radial-gradient(circle, rgba(29,185,84,0.12) 0%, transparent 70%); bottom: -150px; left: -150px; pointer-events: none; }
    .brand { font-family: 'Bebas Neue', sans-serif; font-size: 22px; letter-spacing: 0.12em; color: var(--green); }
    .big-text { font-family: 'Bebas Neue', sans-serif; font-size: clamp(72px, 9vw, 120px); line-height: 0.92; letter-spacing: -0.01em; color: var(--text); position: relative; z-index: 1; }
    .big-text em { font-style: normal; color: var(--green); display: block; }
    .left-footer { font-size: 12px; color: var(--muted); letter-spacing: 0.04em; }
    .wave { display: flex; align-items: center; gap: 3px; margin-bottom: 32px; }
    .wave span { display: block; width: 3px; background: var(--green); border-radius: 2px; opacity: 0.6; animation: wave 1.4s ease-in-out infinite; }
    .wave span:nth-child(1)  { height:12px; animation-delay:0s }
    .wave span:nth-child(2)  { height:28px; animation-delay:.1s }
    .wave span:nth-child(3)  { height:18px; animation-delay:.2s }
    .wave span:nth-child(4)  { height:38px; animation-delay:.15s }
    .wave span:nth-child(5)  { height:22px; animation-delay:.05s }
    .wave span:nth-child(6)  { height:32px; animation-delay:.25s }
    .wave span:nth-child(7)  { height:14px; animation-delay:.3s }
    .wave span:nth-child(8)  { height:24px; animation-delay:.1s }
    .wave span:nth-child(9)  { height:36px; animation-delay:.2s }
    .wave span:nth-child(10) { height:16px; animation-delay:0s }
    @keyframes wave { 0%,100%{transform:scaleY(1)} 50%{transform:scaleY(0.4)} }
    .right { display: flex; align-items: center; justify-content: center; padding: 48px 40px; }
    .login-box { width: 100%; max-width: 360px; animation: fadein .5s ease both; }
    @keyframes fadein { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
    .login-box h2 { font-family:'Bebas Neue',sans-serif; font-size:36px; letter-spacing:.06em; color:var(--text); margin-bottom:8px; }
    .login-box p { font-size:14px; color:var(--muted); margin-bottom:40px; line-height:1.6; }
    .btn { display:flex; align-items:center; justify-content:center; gap:12px; width:100%; padding:16px; background:var(--green); color:#000; font-family:'DM Sans',sans-serif; font-size:14px; font-weight:500; letter-spacing:.04em; text-decoration:none; border-radius:8px; transition:background .2s, transform .15s, box-shadow .2s; }
    .btn:hover { background:#1ed760; transform:translateY(-2px); box-shadow:0 8px 32px rgba(29,185,84,.3); }
    .btn:active { transform:translateY(0); }
    .btn svg { width:20px; height:20px; flex-shrink:0; }
    .divider { display:flex; align-items:center; gap:12px; margin:28px 0; font-size:11px; letter-spacing:.08em; color:var(--muted); }
    .divider::before,.divider::after { content:''; flex:1; height:1px; background:var(--border); }
    .note { font-size:12px; color:var(--muted); text-align:center; line-height:1.7; }
    @media(max-width:640px){ body{grid-template-columns:1fr} .left{display:none} .right{padding:40px 24px} }
  </style>
</head>
<body>
  <div class="left">
    <div class="brand">MUSICBOT</div>
    <div>
      <div class="wave"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>
      <div class="big-text">SUA<br><em>MÚSICA</em><br>EM DADOS</div>
    </div>
    <div class="left-footer">Conectado ao Spotify Web API</div>
  </div>
  <div class="right">
    <div class="login-box">
      <h2>ENTRAR</h2>
      <p>Conecte sua conta do Spotify para visualizar suas estatísticas e gerenciar suas playlists.</p>
      <a href="/login" class="btn">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.371-.721.49-1.101.24-3.021-1.858-6.832-2.278-11.322-1.237-.433.101-.861-.17-.961-.601s.17-.861.601-.961c4.91-1.12 9.122-.63 12.512 1.43.38.241.49.721.271 1.13zm1.47-3.27c-.301.459-.921.6-1.381.301-3.461-2.122-8.732-2.738-12.822-1.5-.511.15-1.051-.15-1.201-.66-.15-.511.15-1.051.66-1.201 4.671-1.411 10.471-.72 14.44 1.71.46.301.6.921.301 1.35zm.129-3.401c-4.141-2.46-10.981-2.69-14.941-1.49-.631.19-1.291-.16-1.491-.79-.19-.631.16-1.291.79-1.491 4.551-1.381 12.121-1.111 16.891 1.721.571.339.759 1.07.419 1.641-.34.569-1.07.759-1.668.409z"/>
        </svg>
        Continuar com Spotify
      </a>
      <div class="divider">acesso seguro via OAuth 2.0 PKCE</div>
      <p class="note">Seus dados ficam apenas na sua sessão.<br>Nunca armazenamos sua senha.</p>
    </div>
  </div>
</body>
</html>
"""

PROFILE_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MusicBot — Perfil</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root { --green:#1DB954; --bg:#080808; --border:#1e1e1e; --text:#f0ede8; --muted:#555; --card:#111; }
    body { background:var(--bg); font-family:'DM Sans',sans-serif; color:var(--text); min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:40px 20px; }
    .profile-card { width:100%; max-width:440px; background:var(--card); border:1px solid var(--border); border-radius:16px; overflow:hidden; animation:fadein .5s ease both; }
    @keyframes fadein { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
    .banner { height:100px; background:linear-gradient(135deg,#0f3d20 0%,#1a1a1a 60%,#0d2b17 100%); position:relative; }
    .banner::after { content:''; position:absolute; inset:0; background:repeating-linear-gradient(45deg,transparent,transparent 20px,rgba(255,255,255,.015) 20px,rgba(255,255,255,.015) 40px); }
    .avatar-wrap { display:flex; justify-content:space-between; align-items:flex-end; padding:0 28px; margin-top:-40px; position:relative; z-index:1; }
    .avatar { width:80px; height:80px; border-radius:50%; border:3px solid var(--bg); object-fit:cover; background:#222; }
    .avatar-placeholder { width:80px; height:80px; border-radius:50%; border:3px solid var(--bg); background:#1a1a1a; display:flex; align-items:center; justify-content:center; font-family:'Bebas Neue',sans-serif; font-size:32px; color:var(--green); }
    .badge { display:flex; align-items:center; gap:6px; background:rgba(29,185,84,.12); border:1px solid rgba(29,185,84,.25); color:var(--green); font-size:11px; font-weight:500; letter-spacing:.06em; padding:6px 12px; border-radius:20px; margin-bottom:4px; }
    .badge::before { content:''; width:6px; height:6px; border-radius:50%; background:var(--green); box-shadow:0 0 6px var(--green); }
    .info { padding:16px 28px 28px; }
    .info h1 { font-family:'Bebas Neue',sans-serif; font-size:32px; letter-spacing:.04em; margin-bottom:4px; }
    .info .email { font-size:13px; color:var(--muted); margin-bottom:20px; }
    .stats { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:24px; }
    .stat { background:var(--bg); border:1px solid var(--border); border-radius:10px; padding:14px 16px; }
    .stat-value { font-family:'Bebas Neue',sans-serif; font-size:28px; color:var(--green); line-height:1; margin-bottom:4px; }
    .stat-label { font-size:11px; color:var(--muted); letter-spacing:.06em; text-transform:uppercase; }
    .actions { display:flex; gap:10px; }
    .btn-outline { flex:1; padding:12px; background:transparent; border:1px solid var(--border); color:var(--muted); font-family:'DM Sans',sans-serif; font-size:13px; border-radius:8px; cursor:pointer; text-align:center; text-decoration:none; transition:border-color .2s, color .2s; }
    .btn-outline:hover { border-color:#444; color:var(--text); }
    .brand { margin-top:32px; font-family:'Bebas Neue',sans-serif; font-size:13px; letter-spacing:.2em; color:#2a2a2a; }
  </style>
</head>
<body>
  <div class="profile-card">
    <div class="banner"></div>
    <div class="avatar-wrap">
      {% if avatar %}
        <img class="avatar" src="{{ avatar }}" alt="{{ name }}">
      {% else %}
        <div class="avatar-placeholder">{{ name[0] }}</div>
      {% endif %}
      <div class="badge">Conectado</div>
    </div>
    <div class="info">
      <h1>{{ name }}</h1>
      <p class="email">{{ email }}</p>
      <div class="stats">
        <div class="stat">
          <div class="stat-value">{{ followers }}</div>
          <div class="stat-label">Seguidores</div>
        </div>
        <div class="stat">
          <div class="stat-value">{{ plan }}</div>
          <div class="stat-label">Plano</div>
        </div>
      </div>
      <div class="actions">
        <a href="/" class="btn-outline">← Início</a>
        <a href="/logout" class="btn-outline">Sair</a>
      </div>
    </div>
  </div>
  <div class="brand">MUSICBOT</div>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"><title>Erro</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400&display=swap" rel="stylesheet">
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#080808;font-family:'DM Sans',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;color:#f0ede8;padding:20px}
    .card{text-align:center;max-width:360px;width:100%;background:#111;border:1px solid #1e1e1e;border-radius:16px;padding:48px 32px}
    .icon{font-size:40px;margin-bottom:16px}
    h2{font-family:'Bebas Neue',sans-serif;font-size:28px;letter-spacing:.06em;margin-bottom:12px}
    p{color:#555;font-size:13px;margin-bottom:28px;line-height:1.6;word-break:break-word}
    a{color:#1DB954;font-size:13px;text-decoration:none}
    a:hover{text-decoration:underline}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">⚠️</div>
    <h2>ERRO NA AUTENTICAÇÃO</h2>
    <p>{{ error }}</p>
    <a href="/">← Tentar novamente</a>
  </div>
</body>
</html>
"""

# ── Rotas de autenticação ──────────────────────────────────────────────────────

@app.route("/")
def index():
    if "access_token" in session:
        return redirect(url_for("profile"))
    return render_template_string(LOGIN_HTML)


@app.route("/login")
def login():
    verifier  = make_verifier()
    challenge = make_challenge(verifier)
    state     = secrets.token_urlsafe(16)

    session["verifier"] = verifier
    session["state"]    = state

    params = urllib.parse.urlencode({
        "client_id":             CLIENT_ID,
        "response_type":         "code",
        "redirect_uri":          REDIRECT_URI,
        "scope":                 SCOPES,
        "state":                 state,
        "code_challenge_method": "S256",
        "code_challenge":        challenge,
    })
    return redirect(f"{AUTH_URL}?{params}")


@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        return render_template_string(ERROR_HTML, error=error)

    if request.args.get("state") != session.get("state"):
        return render_template_string(ERROR_HTML, error="State inválido. Tente novamente.")

    code = request.args.get("code")
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "code_verifier": session.pop("verifier", ""),
    })

    if not resp.ok:
        return render_template_string(ERROR_HTML, error=resp.text)

    tokens = resp.json()
    session["access_token"]  = tokens["access_token"]
    session["refresh_token"] = tokens.get("refresh_token")
    return redirect(POST_LOGIN_REDIRECT_URI)


@app.route("/profile")
def profile():
    user, error_status = get_current_user()
    if user is None:
        if error_status is None or error_status == 401:
            return unauthorized()
        return {"error": "spotify_request_failed"}, error_status

    if wants_html():
        return render_template_string(
            PROFILE_HTML,
            name=user["name"],
            email=user["email"] or "—",
            followers=user["followers"],
            avatar=user["avatar"],
            plan=user["plan"],
        )

    return user


@app.route("/logout")
def logout():
    session.clear()
    if wants_html():
        return redirect(url_for("index"))
    return "", 204


# ── Rotas de dados do Spotify ──────────────────────────────────────────────────

@app.route("/playlists")
def playlists():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return {"playlists": get_playlists(token)}


@app.route("/recently-played")
def recently_played():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return {"tracks": get_recently_played(token)}


@app.route("/top-tracks")
def top_tracks():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return {"tracks": get_top_tracks(token)}


@app.route("/top-artists")
def top_artists():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return {"artists": get_top_artists(token)}


@app.route("/saved-tracks")
def saved_tracks():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return {"tracks": get_saved_tracks(token)}


# ── Inicia o servidor ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true",
    )
