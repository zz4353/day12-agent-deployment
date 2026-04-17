#  Delivery Checklist — Day 12 Lab Submission

> **Student Name:** Vũ Minh Khải
> **Student ID:** 2A202600343
> **Date:** 17/04/2026

---

##  Submission Requirements

Submit a **GitHub repository** containing:

### 1. Mission Answers (40 points)

Create a file `MISSION_ANSWERS.md` with your answers to all exercises:

# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
```
1. API key hardcode: OPENAI_API_KEY đặt luôn ở trong code, dễ bị lộ key và sau này cần thay đổi key khác phải vào sửa code.
2. Port cố định: Cố định port=8000 ở trong code. Sau này muốn thay đổi rất khó khăn, phải vào sửa code.
3. Debug mode: print nội dung debug ra terminal thay vì log ra file.
4. Không có health check: Nếu agent crash, platform không biết để restart
5. Không có config management: Để hết các biến này ở trong file code: DEBUG = True, MAX_TOKENS = 500
```

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode | Env vars | Push code lên github ko lộ key, đổi config ko cần sửa code |
| Health check | Không có | Có | Cloud cần kiểm tra xem app còn sống ko để nếu app chết -> tự restart |
| Logging | print() | JSON | Dễ tìm log khi có lỗi |
| Shutdown | Đột ngột | Graceful | user đang gọi api mà ngắt giữa chừng -> mất data, lỗi |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
```
1. Base image là gì?
- python:3.11 bản full
2. Working directory là gì?
- WORKDIR /app: Là thư mục mặc định, các lệnh sau đó như COPY, RUN, CMD sẽ chạy tại đây
3. Tại sao COPY requirements.txt trước?
- Mỗi dòng trong Dockerfile = 1 layer. Docker lưu cache từng layer từ lần build trước. Build lại, nếu layer ko đổi -> dùng cache nhanh. Nếu đổi -> build lại layer đó và những layer sau.
nếu copy requirements.txt sau code, vì code thường xuyên thay đổi -> mỗi khi build phải copy lại requirements.txt và chạy lại pip install...
4. CMD vs ENTRYPOINT khác nhau thế nào?
- CMD: lệnh mặc định hoặc tham số mặc định. Dễ bị ghi đè. 
- ENTRYPOINT: lệnh chính sẽ chạy khi container start. Khó bị ghi đè.

```

### Exercise 2.3: Image size comparison
- Develop: [1.66] GB = [1660] MB
- Production: [236] MB
- Difference: [85.8]%

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://agent-api-production-45e1.up.railway.app
- Screenshot: day12-agent-deployment\screenshots\ex3.png

## Part 4: API Security

### Exercise 4.1-4.3: Test results
#### 4.1. Test results
Ghi chú: Sử dụng `uvicorn app:app --host 0.0.0.0 --port 8000 --reload` để chạy thay vì `python app.py`

`python app.py` chạy ra lỗi:
``` bash
API Key: demo-key-change-in-production
Test: curl -H 'X-API-Key: demo-key-change-in-production' http://localhost:8000/ask?question=hello
←[33mWARNING←[0m:  You must pass the application as an import string to enable 'reload' or 'workers'.
```

Results:

```bash

#  Không có key
$ curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

#  Có key
$ curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
{"detail":"Invalid API key."}

# Thêm, tìm key trong app.py chạy thì ra kq sau:
$ curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: demo-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
{"detail":[{"type":"missing","loc":["query","question"],"msg":"Field required","
input":null}]}
```

#### 4.2. Test results
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3NzY0MTgzMzQsImV4cCI6MTc3NjQyMTkzNH0.JCkXntrxQMy5iiZcQzNVUKSJFLknft2UsDGM13bS9SU"
$ curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
{"question":"Explain JWT","answer":"Đây là câu trả lời từ AI agent (mock). Trong
 production, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaini
ng":9,"budget_remaining_usd":2.1e-05}}
```

#### 4.3. Test results
```bash
$ for i in {1..20}; do
  curl http://localhost:8000/ask -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question": "Test '$i'"}'
  echo ""
done
{"question":"Test 1","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi củ
a bạn đã được nhận.","usage":{"requests_remaining":8,"budget_remaining_usd":4e-0
5}}
{"question":"Test 2","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi củ
a bạn đã được nhận.","usage":{"requests_remaining":7,"budget_remaining_usd":5.8e
-05}}
{"question":"Test 3","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thê
m câu hỏi đi nhé.","usage":{"requests_remaining":6,"budget_remaining_usd":7.4e-0
5}}
{"question":"Test 4","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi củ
a bạn đã được nhận.","usage":{"requests_remaining":5,"budget_remaining_usd":9.3e
-05}}
{"question":"Test 5","answer":"Đây là câu trả lời từ AI agent (mock). Trong prod
uction, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":4
,"budget_remaining_usd":0.000114}}
{"question":"Test 6","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thê
m câu hỏi đi nhé.","usage":{"requests_remaining":3,"budget_remaining_usd":0.0001
3}}
{"question":"Test 7","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thê
m câu hỏi đi nhé.","usage":{"requests_remaining":2,"budget_remaining_usd":0.0001
46}}
{"question":"Test 8","answer":"Đây là câu trả lời từ AI agent (mock). Trong prod
uction, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":1
,"budget_remaining_usd":0.000167}}
{"question":"Test 9","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thê
m câu hỏi đi nhé.","usage":{"requests_remaining":0,"budget_remaining_usd":0.0001
84}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":26}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":26}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":25}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":25}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":25}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":24}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":24}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":24}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":23}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":23}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_a
fter_seconds":23}}

```


### Exercise 4.4: Cost guard implementation
```
import redis
from datetime import datetime

r = redis.Redis()

def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False
    
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)  # 32 days
    return True
```

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
#### Exercise 5.1
```
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        # Check Redis
        r.ping()
        # Check database
        db.execute("SELECT 1")
        return {"status": "ready"}
    except:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready"}
        )
```

#### Exercise 5.2
Ghi chú: Phần này ko hoàn thành được do mock LLM chạy quá nhanh
```
import signal
import sys
import time
import logging

logger = logging.getLogger(__name__)

# Globals theo dõi state
_accepting_requests = True      # flag chặn request mới
_in_flight_requests = 0         # đếm request đang xử lý
SHUTDOWN_TIMEOUT = 30           # giây


def shutdown_handler(signum, frame):
    """Handle SIGTERM from container orchestrator"""
    global _accepting_requests

    logger.info(f"Received signal {signum} — starting graceful shutdown")

    # 1. Stop accepting new requests
    #    Middleware sẽ check flag này và trả 503 cho request mới
    _accepting_requests = False
    logger.info("1/4 Stopped accepting new requests")

    # 2. Finish current requests (chờ tối đa SHUTDOWN_TIMEOUT giây)
    elapsed = 0
    while _in_flight_requests > 0 and elapsed < SHUTDOWN_TIMEOUT:
        logger.info(f"   Waiting for {_in_flight_requests} in-flight requests...")
        time.sleep(1)
        elapsed += 1

    if _in_flight_requests > 0:
        logger.warning(f"2/4 Timeout — {_in_flight_requests} requests chưa xong, force shutdown")
    else:
        logger.info("2/4 All in-flight requests completed")

    # 3. Close connections (database, Redis, HTTP clients, ...)
    try:
        # Đóng Redis
        # r.close()
        # Đóng DB pool
        # db.dispose()
        logger.info("3/4 Closed all external connections")
    except Exception as e:
        logger.error(f"   Error closing connections: {e}")

    # 4. Exit
    logger.info("4/4 Shutdown complete.")
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown_handler)
```
##### Chạy test
Phần này ko hoàn thành được, request trả về quá nhanh do sử dụng mock llm. tôi đã setup 1 cmd chạy `python app.py &
PID=$!` và sử dụng git bash để gửi request.
```bash
python app.py &
PID=$!

# Gửi request
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Long task"}' &

# Ngay lập tức kill
kill -TERM $PID
```

#### Exercise 5.3
Phần này ko có gì, code đã được cài đặt sẵn.

#### Exercise 5.4
Ghi chú: để chạy lệnh `docker compose up --scale agent=3` như hướng dẫn, cần phải thêm .env.local và tạo thêm 1 dockerfile...

Chạy `docker compose up --scale agent=3`
```

(py311) K:\day12_ha-tang-cloud_va_deployment\05-scaling-reliability\production>docker compose down
time="2026-04-17T17:58:49+07:00" level=warning msg="K:\\day12_ha-tang-cloud_va_deployment\\05-scaling-reliability\\production\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
[+] Running 6/6
 ✔ Container production-nginx-1  Removed                                                                           0.0s
 ✔ Container production-agent-1  Removed                                                                           0.0s
 ✔ Container production-agent-2  Removed                                                                           0.0s
 ✔ Container production-agent-3  Removed                                                                           0.0s
 ✔ Container production-redis-1  Removed                                                                           0.0s
 ✔ Network production_agent_net  Removed                                                                           0.4s

(py311) K:\day12_ha-tang-cloud_va_deployment\05-scaling-reliability\production>docker image rm production-agent:latest
Untagged: production-agent:latest
Deleted: sha256:9ccccfebe35c62ca2214fed98a3fde61c544500acbf97ef5dec5eae5fd9ff9d9

(py311) K:\day12_ha-tang-cloud_va_deployment\05-scaling-reliability\production>docker compose up --scale agent=3 --build
time="2026-04-17T17:58:50+07:00" level=warning msg="K:\\day12_ha-tang-cloud_va_deployment\\05-scaling-reliability\\production\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
[+] Building 2.1s (14/14) FINISHED
 => [internal] load local bake definitions                                                                         0.0s
 => => reading from stdin 412B                                                                                     0.0s
 => [internal] load build definition from Dockerfile                                                               0.0s
 => => transferring dockerfile: 676B                                                                               0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim                                                1.4s
 => [auth] library/python:pull token for registry-1.docker.io                                                      0.0s
 => [internal] load .dockerignore                                                                                  0.0s
 => => transferring context: 2B                                                                                    0.0s
 => [1/6] FROM docker.io/library/python:3.11-slim@sha256:233de06753d30d120b1a3ce359d8d3be8bda78524cd8f520c99883bf  0.0s
 => => resolve docker.io/library/python:3.11-slim@sha256:233de06753d30d120b1a3ce359d8d3be8bda78524cd8f520c99883bf  0.0s
 => [internal] load build context                                                                                  0.0s
 => => transferring context: 356B                                                                                  0.0s
 => CACHED [2/6] WORKDIR /app                                                                                      0.0s
 => CACHED [3/6] COPY 05-scaling-reliability/production/requirements.txt ./requirements.txt                        0.0s
 => CACHED [4/6] RUN pip install --no-cache-dir -r requirements.txt redis==5.1.0                                   0.0s
 => CACHED [5/6] COPY 05-scaling-reliability/production/app.py ./app.py                                            0.0s
 => CACHED [6/6] COPY 05-scaling-reliability/production/utils ./utils                                              0.0s
 => exporting to image                                                                                             0.4s
 => => exporting layers                                                                                            0.0s
 => => exporting manifest sha256:53c13919fd928814c768b9e66c4bc6bf0fc208dc6fd6c325b6675a7820cddfe6                  0.0s
 => => exporting config sha256:366726d5e0188ffa1413bc908eb3aa6a0c414232c38c06b797c270753c6cb1e0                    0.0s
 => => exporting attestation manifest sha256:365eac5f7818aa8ee8a677d66f3168dbbec4e5b3247f22e0a72a6e94ac22a7e1      0.0s
 => => exporting manifest list sha256:6b05bac4014b8a74317ce00683691bccee31ca0c3ff53aab3cbf27dccaa30cc4             0.0s
 => => naming to docker.io/library/production-agent:latest                                                         0.0s
 => => unpacking to docker.io/library/production-agent:latest                                                      0.3s
 => resolving provenance for metadata file                                                                         0.0s
[+] Running 7/7
 ✔ agent                         Built                                                                             0.0s
 ✔ Network production_agent_net  Created                                                                           0.0s
 ✔ Container production-redis-1  Created                                                                           0.1s
 ✔ Container production-agent-3  Created                                                                           0.1s
 ✔ Container production-agent-1  Created                                                                           0.1s
 ✔ Container production-agent-2  Created                                                                           0.1s
 ✔ Container production-nginx-1  Created                                                                           0.1s
Attaching to agent-1, agent-2, agent-3, nginx-1, redis-1
redis-1  | 1:C 17 Apr 2026 10:58:53.305 * oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
redis-1  | 1:C 17 Apr 2026 10:58:53.305 * Redis version=7.4.8, bits=64, commit=00000000, modified=0, pid=1, just started
redis-1  | 1:C 17 Apr 2026 10:58:53.305 * Configuration loaded
redis-1  | 1:M 17 Apr 2026 10:58:53.305 * monotonic clock: POSIX clock_gettime
redis-1  | 1:M 17 Apr 2026 10:58:53.306 * Running mode=standalone, port=6379.
redis-1  | 1:M 17 Apr 2026 10:58:53.306 * Server initialized
redis-1  | 1:M 17 Apr 2026 10:58:53.307 * Ready to accept connections tcp
nginx-1  | /docker-entrypoint.sh: /docker-entrypoint.d/ is not empty, will attempt to perform configuration
nginx-1  | /docker-entrypoint.sh: Looking for shell scripts in /docker-entrypoint.d/
nginx-1  | /docker-entrypoint.sh: Launching /docker-entrypoint.d/10-listen-on-ipv6-by-default.sh
nginx-1  | 10-listen-on-ipv6-by-default.sh: info: Getting the checksum of /etc/nginx/conf.d/default.conf
nginx-1  | 10-listen-on-ipv6-by-default.sh: info: Enabled listen on IPv6 in /etc/nginx/conf.d/default.conf
nginx-1  | /docker-entrypoint.sh: Sourcing /docker-entrypoint.d/15-local-resolvers.envsh
nginx-1  | /docker-entrypoint.sh: Launching /docker-entrypoint.d/20-envsubst-on-templates.sh
nginx-1  | /docker-entrypoint.sh: Launching /docker-entrypoint.d/30-tune-worker-processes.sh
nginx-1  | /docker-entrypoint.sh: Configuration complete; ready for start up
agent-3  | ✅ Connected to Redis
agent-3  | INFO:     Started server process [1]
agent-3  | INFO:     Waiting for application startup.
agent-3  | INFO:app:Starting instance instance-87c7b9
agent-3  | INFO:app:Storage: Redis ✅
agent-3  | INFO:     Application startup complete.
agent-3  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
agent-2  | ✅ Connected to Redis
agent-2  | INFO:     Started server process [1]
agent-2  | INFO:     Waiting for application startup.
agent-2  | INFO:app:Starting instance instance-d869f8
agent-2  | INFO:app:Storage: Redis ✅
agent-2  | INFO:     Application startup complete.
agent-2  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
agent-1  | ✅ Connected to Redis
agent-1  | INFO:     Started server process [1]
agent-1  | INFO:     Waiting for application startup.
agent-1  | INFO:app:Starting instance instance-5b4007
agent-1  | INFO:app:Storage: Redis ✅
agent-1  | INFO:     Application startup complete.
agent-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
agent-3  | INFO:     127.0.0.1:46570 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:46584 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:46588 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:45340 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:45346 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:45360 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:37836 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:37850 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:37862 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:53588 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:53594 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:53606 - "GET /health HTTP/1.1" 200 OK
```

Test results:
```

Khai@DESKTOP-9SDH8UA MINGW64 ~
$ for i in {1..10}; do
  curl http://localhost:8080/chat -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Request '$i'"}'
  echo
done
{"session_id":"0ab431a0-e886-4b30-8841-a3bc5799902b","question":"Request 1","ans
wer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","tur
n":2,"served_by":"instance-87c7b9","storage":"redis"}
{"session_id":"4878b1a2-1f69-4d99-8ff0-cebcc49291d0","question":"Request 2","ans
wer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","tur
n":2,"served_by":"instance-d869f8","storage":"redis"}
{"session_id":"d83aac7a-22e3-483f-bff5-d1858557ab19","question":"Request 3","ans
wer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","turn"
:2,"served_by":"instance-5b4007","storage":"redis"}
{"session_id":"5bb035ef-c206-4335-990e-68d455908fe7","question":"Request 4","ans
wer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là respons
e từ OpenAI/Anthropic.","turn":2,"served_by":"instance-87c7b9","storage":"redis"
}
{"session_id":"8e57faf7-5889-4d2a-989c-dbe1515a9089","question":"Request 5","ans
wer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","turn"
:2,"served_by":"instance-d869f8","storage":"redis"}
{"session_id":"3e96740e-0201-43e5-9519-626d306ac3d2","question":"Request 6","ans
wer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","tur
n":2,"served_by":"instance-5b4007","storage":"redis"}
{"session_id":"e881e328-eb61-4179-91e3-4891a662caf3","question":"Request 7","ans
wer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","tur
n":2,"served_by":"instance-87c7b9","storage":"redis"}
{"session_id":"b09d07f8-7e2f-44ad-a2f7-726261c8e42a","question":"Request 8","ans
wer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là respons
e từ OpenAI/Anthropic.","turn":2,"served_by":"instance-d869f8","storage":"redis"
}
{"session_id":"ea6b6842-899a-4c2c-a0ed-f5ac53175280","question":"Request 9","ans
wer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là respons
e từ OpenAI/Anthropic.","turn":2,"served_by":"instance-5b4007","storage":"redis"
}
{"session_id":"ced0c7f4-f030-4103-9aea-e4cded29af2d","question":"Request 10","an
swer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","tu
rn":2,"served_by":"instance-87c7b9","storage":"redis"}
```

Logs
```
agent-2  | ✅ Connected to Redis
agent-2  | INFO:     Started server process [1]
agent-2  | INFO:     Waiting for application startup.
agent-2  | INFO:app:Starting instance instance-d869f8
agent-1  | ✅ Connected to Redis
agent-1  | INFO:     Started server process [1]
agent-1  | INFO:     Waiting for application startup.
agent-3  | ✅ Connected to Redis
agent-3  | INFO:     Started server process [1]
agent-3  | INFO:     Waiting for application startup.
agent-3  | INFO:app:Starting instance instance-87c7b9
agent-3  | INFO:app:Storage: Redis ✅
agent-3  | INFO:     Application startup complete.
agent-3  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
agent-2  | INFO:app:Storage: Redis ✅
agent-2  | INFO:     Application startup complete.
agent-3  | INFO:     127.0.0.1:46570 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:45340 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:37836 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:53588 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:47674 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:51442 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:41840 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:44774 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:55968 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:53532 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
agent-2  | INFO:     127.0.0.1:46584 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:45346 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:app:Starting instance instance-5b4007
agent-1  | INFO:app:Storage: Redis ✅
agent-1  | INFO:     Application startup complete.
agent-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
agent-1  | INFO:     127.0.0.1:46588 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:45360 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:37862 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:53606 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:47700 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:51458 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:54416 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:44786 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:55978 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:53536 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:37170 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:51318 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     172.19.0.6:33916 - "POST /chat HTTP/1.1" 200 OK
agent-1  | INFO:     172.19.0.6:33916 - "POST /chat HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:37850 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:53594 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:47690 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:51470 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:54432 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:37154 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:51294 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     172.19.0.6:44986 - "POST /chat HTTP/1.1" 200 OK
agent-3  | INFO:     172.19.0.6:44986 - "POST /chat HTTP/1.1" 200 OK
agent-3  | INFO:     172.19.0.6:44986 - "POST /chat HTTP/1.1" 200 OK
agent-3  | INFO:     172.19.0.6:44986 - "POST /chat HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:54872 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:48042 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:46920 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:45362 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:40574 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:47206 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:47634 - "GET /health HTTP/1.1" 200 OK
agent-3  | INFO:     127.0.0.1:34202 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:44802 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     172.19.0.6:33916 - "POST /chat HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:54886 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:48062 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:46926 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:45370 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:40588 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:47220 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:47638 - "GET /health HTTP/1.1" 200 OK
agent-1  | INFO:     127.0.0.1:34214 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:55984 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:53536 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:37176 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:51306 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     172.19.0.6:40308 - "POST /chat HTTP/1.1" 200 OK
agent-2  | INFO:     172.19.0.6:40308 - "POST /chat HTTP/1.1" 200 OK
agent-2  | INFO:     172.19.0.6:40308 - "POST /chat HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:54892 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:48048 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:46922 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:45364 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:40562 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:47212 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:47630 - "GET /health HTTP/1.1" 200 OK
agent-2  | INFO:     127.0.0.1:34200 - "GET /health HTTP/1.1" 200 OK
```

#### Exercise 5.5
Test results:
```

(py311) k:\day12_ha-tang-cloud_va_deployment\05-scaling-reliability\production>python test_stateless.py
============================================================
Stateless Scaling Demo
============================================================

Session ID: 80ddcff5-25ce-4493-868e-859386f23a82

Request 1: [instance-d869f8]
  Q: What is Docker?
  A: Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!...

Request 2: [instance-5b4007]
  Q: Why do we need containers?
  A: Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận....

Request 3: [instance-87c7b9]
  Q: What is Kubernetes?
  A: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ O...

Request 4: [instance-d869f8]
  Q: How does load balancing work?
  A: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ O...

Request 5: [instance-5b4007]
  Q: What is Redis used for?
  A: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ O...

------------------------------------------------------------
Total requests: 5
Instances used: {'instance-5b4007', 'instance-87c7b9', 'instance-d869f8'}
✅ All requests served despite different instances!

--- Conversation History ---
Total messages: 10
  [user]: What is Docker?...
  [assistant]: Container là cách đóng gói app để chạy ở mọi nơi. Build once...
  [user]: Why do we need containers?...
  [assistant]: Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã đư...
  [user]: What is Kubernetes?...
  [assistant]: Đây là câu trả lời từ AI agent (mock). Trong production, đây...
  [user]: How does load balancing work?...
  [assistant]: Đây là câu trả lời từ AI agent (mock). Trong production, đây...
  [user]: What is Redis used for?...
  [assistant]: Đây là câu trả lời từ AI agent (mock). Trong production, đây...

✅ Session history preserved across all instances via Redis!
```
---

### 2. Full Source Code - Lab 06 Complete (60 points)

Your final production-ready agent with all files:

```
your-repo/
├── app/
│   ├── main.py              # Main application
│   ├── config.py            # Configuration
│   ├── auth.py              # Authentication
│   ├── rate_limiter.py      # Rate limiting
│   └── cost_guard.py        # Cost protection
├── utils/
│   └── mock_llm.py          # Mock LLM (provided)
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Full stack
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
├── .dockerignore            # Docker ignore
├── railway.toml             # Railway config (or render.yaml)
└── README.md                # Setup instructions
```

**Requirements:**
-  All code runs without errors
-  Multi-stage Dockerfile (image < 500 MB)
-  API key authentication
-  Rate limiting (10 req/min)
-  Cost guard ($10/month)
-  Health + readiness checks
-  Graceful shutdown
-  Stateless design (Redis)
-  No hardcoded secrets

---

### 3. Service Domain Link

Create a file `DEPLOYMENT.md` with your deployed service information:

```markdown
# Deployment Information

## Public URL
https://your-agent.railway.app

## Platform
Railway / Render / Cloud Run

## Test Commands

### Health Check
```bash
curl https://your-agent.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
```

##  Pre-Submission Checklist

- [X] Repository is public (or instructor has access)
- [X] `MISSION_ANSWERS.md` completed with all exercises
- [X] `DEPLOYMENT.md` has working public URL
- [X] All source code in `app/` directory
- [X] `README.md` has clear setup instructions
- [X] No `.env` file committed (only `.env.example`)
- [X] No hardcoded secrets in code
- [X] Public URL is accessible and working
- [X] Screenshots included in `screenshots/` folder
- [X] Repository has clear commit history

---

##  Self-Test

Before submitting, verify your deployment:

```bash
# 1. Health check
curl https://your-app.railway.app/health

# 2. Authentication required
curl https://your-app.railway.app/ask
# Should return 401

# 3. With API key works
curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
  -X POST -d '{"user_id":"test","question":"Hello"}'
# Should return 200

# 4. Rate limiting
for i in {1..15}; do 
  curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
    -X POST -d '{"user_id":"test","question":"test"}'; 
done
# Should eventually return 429
```

---

##  Submission

**Submit your GitHub repository URL:**

```
https://github.com/your-username/day12-agent-deployment
```

**Deadline:** 17/4/2026

---

##  Quick Tips

1.  Test your public URL from a different device
2.  Make sure repository is public or instructor has access
3.  Include screenshots of working deployment
4.  Write clear commit messages
5.  Test all commands in DEPLOYMENT.md work
6.  No secrets in code or commit history

---

##  Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CODE_LAB.md](CODE_LAB.md)
- Ask in office hours
- Post in discussion forum

---

**Good luck! **
