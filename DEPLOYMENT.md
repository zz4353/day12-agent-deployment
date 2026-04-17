# Deployment Information

## Public URL
https://t1-production-6de4.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
$ curl https://t1-production-6de4.up.railway.app
{"app":"Production AI Agent","version":"1.0.0","environment":"production","insta
nce_id":"instance-801cb4","endpoints":{"login":"POST /auth/token","ask":"POST /a
sk (single-turn)","chat":"POST /chat (multi-turn with session)","history":"GET /
chat/{session_id}/history","my_usage":"GET /me/usage","health":"GET /health","re
ady":"GET /ready"}}
```

### API Test (with authentication)
```bash
$ curl -X POST https://t1-production-6de4.up.railway.app/chat \
  -H "X-API-Key: knGzF0w9Kb2LiNxHMselm1BOyVaCW5jSPXfRAYdt" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
{"session_id":"01771f58-06ba-48ab-968f-1a43554c7970","question":"Hello","answer"
:"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","turn":1
,"served_by":"instance-df29eb","storage":"in-memory","usage":{"requests_remainin
g":19,"cost_usd":1.8e-05}}
```

## Environment Variables Set
- PORT: 8080
- REDIS_URL: redis://default:WxIQeMUArOjPRDbBWfLJBjtmNgmPptFE@redis.railway.internal:6379
- AGENT_API_KEY: knGzF0w9Kb2LiNxHMselm1BOyVaCW5jSPXfRAYdt
- LOG_LEVEL: INFO

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)