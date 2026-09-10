# AI Research Copilot — Frontend

The Next.js research workspace for conversation history, streamed answers, citations, document upload, memory, and report export.

## Local development

Install dependencies and start the development server:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The app calls the API at the configured `NEXT_PUBLIC_API_URL`.

## Environment

| Variable | Required | Description |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Yes in production | Public base URL of the FastAPI backend, for example `https://ai-research-copilot-api.onrender.com`. |

Never put provider API keys or Supabase service-role credentials in frontend variables.

## Quality checks

```bash
npm run lint
npm run build
```

## Deployment

Deploy this directory as the Vercel project root. Configure `NEXT_PUBLIC_API_URL` and ensure its origin is present in the backend's `ALLOWED_ORIGINS` variable. See the [root README](../README.md) and [operations guide](../vault/30-Operations.md) for the complete deployment setup.

Released under the [MIT License](../LICENSE).
