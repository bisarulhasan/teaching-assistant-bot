# Deploying the Teaching Assistant Bot

Architecture: **frontend on Vercel** (public) → **Cloudflare Tunnel** → **self-hosted
backend** (FastAPI + Weaviate + Ollama) on a Mac.

```
Student ─▶ Vercel (Next.js "Pip") ─https─▶ Cloudflare edge ─tunnel─▶ Mac:8000 (FastAPI)
                                                                       ├─ Weaviate :8080
                                                                       └─ Ollama   :11434 (qwen2.5:7b)
```

> ⚠️ **Pilot, not production.** The backend runs on a 16 GB laptop. It must stay
> on/awake/connected, and `qwen2.5:7b` answers **one question at a time** —
> simultaneous students queue. For a class-scale rollout, either move the backend
> to an always-on box with more RAM, or switch generation to a hosted model
> (OpenRouter) so the laptop isn't the bottleneck. See "Scaling" below.

---

## 1. Backend (on the Mac)

```bash
cd teaching-assistant-bot
docker compose up -d                                   # Weaviate
ollama serve                                           # if not already running
.venv/bin/python -m src.pipeline ingest --fresh        # only when textbooks change
FRONTEND_ORIGIN="https://<your-app>.vercel.app" \
  .venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

`FRONTEND_ORIGIN` locks CORS to your Vercel domain (comma-separate multiple).

## 2. Cloudflare Tunnel

### Quick / throwaway (no account, URL changes each run — demos only)
```bash
cloudflared tunnel --url http://localhost:8000
# prints https://<random>.trycloudflare.com
```

### Durable / named (stable URL — for real use; needs a free Cloudflare account + a domain)
```bash
cloudflared tunnel login
cloudflared tunnel create ta-bot
cloudflared tunnel route dns ta-bot ta-bot.yourschool.dev
# ~/.cloudflared/config.yml:
#   tunnel: ta-bot
#   credentials-file: /Users/<you>/.cloudflared/<UUID>.json
#   ingress:
#     - hostname: ta-bot.yourschool.dev
#       service: http://localhost:8000
#     - service: http_status:404
cloudflared tunnel run ta-bot
# (optional) install as a login service so it survives reboots:
sudo cloudflared service install
```

## 3. Frontend on Vercel

1. Push this repo to GitHub.
2. Vercel → New Project → import the repo.
3. **Root Directory: `frontend`** (important — the Next app lives there).
4. Environment variable:
   `NEXT_PUBLIC_API_BASE_URL = https://ta-bot.yourschool.dev` (your tunnel URL).
5. Deploy. Then set the backend's `FRONTEND_ORIGIN` to the resulting
   `https://<app>.vercel.app` and restart it (step 1).

`NEXT_PUBLIC_*` vars are baked at build time — change the URL ⇒ redeploy.

## 4. Adding more textbooks

Drop PDFs into `data/raw/` named `"<year> <Subject> <Course> textbook.pdf"`
(e.g. `12 Science Biology textbook.pdf` — the loader parses year/subject/course
from the filename), then re-run `ingest --fresh`. The `/catalog` endpoint and the
picker pick up the new options automatically.

## Scaling — when the laptop isn't enough

Switch generation to a hosted open model (your "OpenRouter later" plan):
- add an OpenRouter branch to `src/generation/llm_client.py` and set `LLM_MODEL`;
- this removes the single-stream + always-on-laptop constraints. Weaviate +
  embeddings can also move to a server. Reranking already uses the Cohere API.
