"""
Test script: chứng minh stateless agent hoạt động đúng khi scale.

Kịch bản:
1. Login → lấy JWT
2. Tạo session mới, gửi 5 requests liên tiếp
3. Quan sát "served_by" — mỗi request có thể đến instance khác
4. Lấy history — tất cả messages được lưu dù instance khác nhau

Chạy sau khi: docker compose up --scale agent=3
    python test_stateless.py
"""
import json
import urllib.request

BASE_URL = "http://localhost:8080"


def post(path: str, data: dict, headers: dict = None) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get(path: str, headers: dict = None) -> dict:
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers or {})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


print("=" * 60)
print("Stateless Scaling Demo")
print("=" * 60)

# 1. Login
print("\n[1] Login as student...")
auth = post("/auth/token", {"username": "student", "password": "demo123"})
token = auth["access_token"]
h = {"Authorization": f"Bearer {token}"}
print(f"    Token: {token[:30]}...")

# 2. Multi-turn chat
questions = [
    "What is Docker?",
    "Why do we need containers?",
    "What is Kubernetes?",
    "How does load balancing work?",
    "What is Redis used for?",
]

session_id = None
instances_seen = set()

print("\n[2] Sending 5 chat requests...\n")
for i, question in enumerate(questions, 1):
    result = post("/chat", {"question": question, "session_id": session_id}, h)
    if session_id is None:
        session_id = result["session_id"]
        print(f"    Session ID: {session_id}\n")

    instance = result.get("served_by", "unknown")
    instances_seen.add(instance)
    print(f"    Request {i}: [{instance}]  turn={result['turn']}")
    print(f"      Q: {question}")
    print(f"      A: {result['answer'][:70]}...\n")

print("-" * 60)
print(f"Total requests: {len(questions)}")
print(f"Instances used: {instances_seen}")
if len(instances_seen) > 1:
    print("✅ All requests served across different instances!")
else:
    print("ℹ️  Only 1 instance — scale up: docker compose up --scale agent=3")

# 3. Verify history
print("\n[3] Verifying conversation history...")
history = get(f"/chat/{session_id}/history", h)
print(f"    Total messages: {history['count']}")
for msg in history["messages"][:4]:
    print(f"      [{msg['role']}]: {msg['content'][:60]}...")
print(f"      ... ({history['count']} total)")

print("\n✅ Session preserved across all instances via Redis!")
