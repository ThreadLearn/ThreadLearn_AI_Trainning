# ThreadLearn Mock Website

Demo IDE analyzer — race condition detection UI.

## Cấu trúc

```
mock-website/
├── frontend/
│   └── index.html        ← Mở thẳng trong browser, không cần build
└── backend/
    ├── package.json
    └── server.js         ← Express proxy → AI2 :8001
```

## Chạy

### Frontend only (Mock mode)
Mở `frontend/index.html` thẳng trong browser. Chọn tab **Mock** → không cần backend.

### Frontend + Backend (Live AI2 mode)

**Bước 1:** Đảm bảo AI2 server đang chạy
```bash
cd ThreadLearn-AI-Trainning/server/server
uvicorn main:app --reload --port 8001
```

**Bước 2:** Cài và chạy Express backend
```bash
cd mock-website/backend
npm install
node server.js
# → http://localhost:3001
```

**Bước 3:** Mở `frontend/index.html` trong browser, chọn tab **Live AI2**

## Endpoints Backend

| Method | URL | Mô tả |
|--------|-----|-------|
| GET | `/health` | Check backend + AI2 status |
| POST | `/api/analyze` | Proxy → AI2 `/api/v1/ai/analyze` |
| GET | `/api/history/:userId` | Proxy → AI2 `/api/v1/ai/history/:userId` |

## Env vars (tuỳ chọn)

```bash
PORT=3001          # port backend (default 3001)
AI2_URL=http://localhost:8001  # địa chỉ AI2
MOCK_JWT=your-jwt  # JWT gửi lên AI2 (default: mock-demo-token)
```
