/**
 * ThreadLearn Mock Backend
 * Express proxy → AI2 FastAPI server (localhost:8001)
 *
 * Routes:
 *   GET  /health              — check mock backend + AI2 health
 *   POST /api/analyze         — proxy to AI2 POST /api/v1/ai/analyze
 *   GET  /api/history/:userId — proxy to AI2 GET /api/v1/ai/history/:userId
 *
 * AI2 requires JWT. This mock server uses a hardcoded mock token
 * so the demo works without a real auth system.
 *
 * Start: node server.js
 * Default port: 3001
 */

const express = require("express");
const cors = require("cors");
const fetch = require("node-fetch");
const jwt = require("jsonwebtoken");
require("dotenv").config({ path: require("path").join(__dirname, "../../ai2/server/.env") });

const app = express();
const PORT = process.env.PORT || 3001;
const AI2_BASE = process.env.AI2_URL || "http://localhost:8001";
const JWT_SECRET = process.env.JWT_SECRET || "your_super_secret_access_key_change_me";

function makeDemoToken() {
  return jwt.sign(
    { sub: "demo-user", exp: Math.floor(Date.now() / 1000) + 86400 },
    JWT_SECRET,
    { algorithm: "HS256" }
  );
}

// Re-generate token per request so it never expires mid-session
function getDemoToken() {
  return makeDemoToken();
}

app.use(cors());
app.use(express.json({ limit: "512kb" }));

// ── Helpers ──────────────────────────────────────────────────────────────────

async function proxyToAI2(path, options = {}) {
  const url = `${AI2_BASE}${path}`;
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getDemoToken()}`,
    ...(options.headers || {}),
  };
  const response = await fetch(url, { ...options, headers, signal: AbortSignal.timeout(200000) });
  const data = await response.json();
  return { status: response.status, data };
}

// ── Routes ───────────────────────────────────────────────────────────────────

/**
 * GET /health
 * Returns status of mock backend + upstream AI2 server.
 */
app.get("/health", async (req, res) => {
  let ai2Status = "unreachable";
  let retrieverDocs = 0;

  try {
    const { status, data } = await proxyToAI2("/health");
    if (status === 200) {
      ai2Status = data.status || "ok";
      retrieverDocs = data.retriever_docs || 0;
    }
  } catch {
    ai2Status = "unreachable";
  }

  res.json({
    mock_backend: "ok",
    ai2_server: ai2Status,
    retriever_docs: retrieverDocs,
    ai2_url: AI2_BASE,
  });
});

/**
 * POST /api/analyze
 * Body: { code: string, language?: string }
 * Proxies to AI2 POST /api/v1/ai/analyze
 * Injects mock user_id "demo-user" so AI2 logs correctly.
 */
app.post("/api/analyze", async (req, res) => {
  const { code, language = "javascript" } = req.body;

  if (!code || typeof code !== "string" || code.trim().length === 0) {
    return res.status(400).json({ error: "code is required and must be a non-empty string" });
  }

  try {
    const { status, data } = await proxyToAI2("/api/v1/ai/analyze", {
      method: "POST",
      body: JSON.stringify({
        code,
        language,
        user_id: "demo-user",
      }),
    });

    return res.status(status).json(data);
  } catch (err) {
    console.error("[/api/analyze] AI2 unreachable:", err.message);
    return res.status(502).json({
      error: "ai2_unavailable",
      message: "AI2 server không trả lời. Đảm bảo AI2 đang chạy tại " + AI2_BASE,
    });
  }
});

/**
 * POST /api/analyze/stream
 * SSE proxy — streams pipeline steps from AI2 to FE
 */
app.post("/api/analyze/stream", async (req, res) => {
  const { code, language = "javascript" } = req.body;

  if (!code || typeof code !== "string" || code.trim().length === 0) {
    return res.status(400).json({ error: "code is required" });
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  res.flushHeaders();

  try {
    const ai2Res = await fetch(`${AI2_BASE}/api/v1/ai/analyze/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getDemoToken()}`,
      },
      body: JSON.stringify({ code, language, user_id: "demo-user" }),
      signal: AbortSignal.timeout(200000),
    });

    if (!ai2Res.ok) {
      const err = await ai2Res.text();
      res.write(`event: error\ndata: ${JSON.stringify({ message: err })}\n\n`);
      return res.end();
    }

    await new Promise((resolve, reject) => {
      ai2Res.body.on("data", (chunk) => res.write(chunk));
      ai2Res.body.on("end", resolve);
      ai2Res.body.on("error", reject);
    });
  } catch (err) {
    console.error("[/api/analyze/stream] error:", err.message);
    res.write(`event: error\ndata: ${JSON.stringify({ message: err.message })}\n\n`);
  }

  res.end();
});

/**
 * GET /api/history/:userId
 * Query: ?page=1&limit=20
 * Proxies to AI2 GET /api/v1/ai/history/:userId
 */
app.get("/api/history/:userId", async (req, res) => {
  const { userId } = req.params;
  const { page = 1, limit = 20 } = req.query;

  try {
    const { status, data } = await proxyToAI2(
      `/api/v1/ai/history/${userId}?page=${page}&limit=${limit}`
    );
    return res.status(status).json(data);
  } catch (err) {
    console.error("[/api/history] AI2 unreachable:", err.message);
    return res.status(502).json({
      error: "ai2_unavailable",
      message: "AI2 server không trả lời.",
    });
  }
});

// ── HF Space keep-alive ───────────────────────────────────────────────────────
// Ping every 10 min so the Space doesn't sleep between analyses.
// Cold start costs ~20-25s; this keeps it warm for free.
const HF_SPACE_HEALTH = "https://anha12-threadlearn-ai2-api.hf.space/health";
const KEEPALIVE_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes

function pingHFSpace() {
  fetch(HF_SPACE_HEALTH, { signal: AbortSignal.timeout(10000) })
    .then(r => console.log(`[keep-alive] HF Space ping → ${r.status}`))
    .catch(e => console.warn(`[keep-alive] HF Space unreachable: ${e.message}`));
}

// ── Start ─────────────────────────────────────────────────────────────────────

app.listen(PORT, () => {
  console.log(`\n ThreadLearn Mock Backend`);
  console.log(` ─────────────────────────────────────`);
  console.log(` Backend : http://localhost:${PORT}`);
  console.log(` AI2 URL : ${AI2_BASE}`);
  console.log(` Health  : http://localhost:${PORT}/health`);
  console.log(` Analyze : POST http://localhost:${PORT}/api/analyze`);
  console.log(` History : GET  http://localhost:${PORT}/api/history/demo-user\n`);

  // Ping immediately on start, then every 10 min
  pingHFSpace();
  setInterval(pingHFSpace, KEEPALIVE_INTERVAL_MS);
});
