# Noor — Teaching Assistant Frontend

Friendly student-facing UI for the RAG teaching-assistant bot. Students pick
their year / subject / course, then chat with **Noor**, who answers only from
their own textbooks and shows the exact chapter, section and page.

Built with Next.js (App Router) + Tailwind v4. Talks to the FastAPI backend in
[`../src/api`](../src/api).

## Local development

```bash
cp .env.local.example .env.local      # set NEXT_PUBLIC_API_BASE_URL
npm install
npm run dev                           # http://localhost:3000
```

The backend must be running too:

```bash
# from the repo root
docker compose up -d                  # Weaviate
.venv/bin/python -m uvicorn src.api.main:app --port 8000
```

## Environment

| Variable                   | Purpose                                    |
| -------------------------- | ------------------------------------------ |
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of the FastAPI backend `/ask` etc |

## Deploying to Vercel

- Set the project **Root Directory** to `frontend/`.
- Add `NEXT_PUBLIC_API_BASE_URL` env var pointing at your publicly reachable
  backend (see repo root README for exposing the self-hosted backend over HTTPS).
- Set `FRONTEND_ORIGIN` on the **backend** to this Vercel domain for CORS.

## Design notes

- Aesthetic: warm graph-paper notebook (on-theme for maths).
- Fonts: Fraunces (display), Nunito (body), Space Mono (citations).
- No math typesetting yet — LLM LaTeX renders as plain text. KaTeX is a planned
  enhancement.
