# ThreadLearn — Demo (standalone, no backend required)

Interactive UI demo of ThreadLearn — the same React interface as the live AI2
system, but replaying **pre-computed analysis results** for 12 built-in
JavaScript concurrency bug samples instead of calling a real backend. Built
so it can be deployed as a static site and linked from a CV/portfolio
without needing a GPU server running 24/7.

Every result shown (issues, severity, fix code, RAG knowledge-base
references, pipeline steps) matches the real AI2 output schema exactly — see
[`src/mockAnalysisResults.js`](src/mockAnalysisResults.js). This is not a
different, simplified UI — it is the production frontend with the network
call swapped for a scripted replay.

For the live version (calls a real FastAPI + LLM backend), see
[`../frontend-react`](../frontend-react).

---

## Run locally

```bash
cd mock-website/demo
npm install
npm run dev
# → http://localhost:5173
```

## Build for production

```bash
npm run build
npm run preview   # sanity-check the built dist/ locally
```

---

## Deploy (Vercel — recommended, free, ~2 minutes)

**Option A — via GitHub (recommended for CV link permanence):**

1. Push this repo (or just the `mock-website/demo` folder as its own repo) to GitHub.
2. Go to [vercel.com/new](https://vercel.com/new), import the repo.
3. Vercel auto-detects Vite. Set:
   - **Root Directory**: `mock-website/demo` (if deploying from the monorepo)
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `dist` (default)
4. Click **Deploy**. You get a permanent URL like `threadlearn-demo.vercel.app`.
5. (Optional) Add a custom domain or shorten via Vercel's project settings.

**Option B — via Vercel CLI (fastest, no GitHub needed):**

```bash
npm install -g vercel
cd mock-website/demo
vercel --prod
```

Follow the prompts (link/create project, confirm defaults). Done in under a minute.

---

## Deploy (Netlify — alternative, also free)

```bash
npm install -g netlify-cli
cd mock-website/demo
npm run build
netlify deploy --prod --dir=dist
```

Or drag-and-drop the `dist/` folder at [app.netlify.com/drop](https://app.netlify.com/drop).

---

## Deploy (GitHub Pages — if you want it under github.io)

```bash
npm install -D gh-pages
```

Add to `package.json` scripts: `"deploy": "gh-pages -d dist"`. Then:

```bash
npm run build
npm run deploy
```

Note: GitHub Pages serves from a subpath (`username.github.io/repo`) — add
`base: '/repo-name/'` to `vite.config.js` if you go this route, otherwise
assets 404.

---

## What to put in your CV

```
Demo: https://<your-deployed-url>.vercel.app
```

The demo works standalone (no signup, no backend, loads instantly) — good
for a reviewer to click straight from your CV/portfolio without setup.
