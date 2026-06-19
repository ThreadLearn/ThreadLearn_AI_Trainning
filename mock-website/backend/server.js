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

const app = express();
const PORT = process.env.PORT || 3001;
const AI2_BASE = process.env.AI2_URL || "http://localhost:8001";

// Mock JWT for demo — AI2 auth middleware accepts this in mock/dev mode
// Real integration: forward the user's actual JWT from Authorization header
const MOCK_JWT = process.env.MOCK_JWT || "mock-demo-token";

app.use(cors());
app.use(express.json({ limit: "512kb" }));

// ── Helpers ──────────────────────────────────────────────────────────────────

async function proxyToAI2(path, options = {}) {
  const url = `${AI2_BASE}${path}`;
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${MOCK_JWT}`,
    ...(options.headers || {}),
  };
  const response = await fetch(url, { ...options, headers });
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

// ── Start ─────────────────────────────────────────────────────────────────────

app.listen(PORT, () => {
  console.log(`\n ThreadLearn Mock Backend`);
  console.log(` ─────────────────────────────────────`);
  console.log(` Backend : http://localhost:${PORT}`);
  console.log(` AI2 URL : ${AI2_BASE}`);
  console.log(` Health  : http://localhost:${PORT}/health`);
  console.log(` Analyze : POST http://localhost:${PORT}/api/analyze`);
  console.log(` History : GET  http://localhost:${PORT}/api/history/demo-user\n`);
});
