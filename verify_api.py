import requests
import sys

BASE_URL = "http://localhost:8088"

def test_health():
    print("Testing Health...")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        resp.raise_for_status()
        print(f"Health OK: {resp.json()}")
    except Exception as e:
        print(f"Health FAILED: {e}")

def test_chat():
    print("\nTesting Chat...")
    try:
        resp = requests.post(f"{BASE_URL}/api/chat", json={"message": "Hola, test de verificacion"})
        resp.raise_for_status()
        print(f"Chat OK: {resp.json()}")
    except Exception as e:
        print(f"Chat FAILED: {e}")

def test_upload():
    print("\nTesting Upload...")
    try:
        files = {'file': ('test_rag.txt', open('test_rag.txt', 'rb'), 'text/plain')}
        resp = requests.post(f"{BASE_URL}/api/upload", files=files)
        resp.raise_for_status()
        data = resp.json()
        print(f"Upload OK: {data}")
        return data.get("id")
    except Exception as e:
        print(f"Upload FAILED: {e}")
        return None

def test_search():
    print("\nTesting Search...")
    try:
        resp = requests.post(f"{BASE_URL}/api/search", json={"text": "verificacion del sistema"})
        resp.raise_for_status()
        print(f"Search OK: {resp.json()}")
    except Exception as e:
        print(f"Search FAILED: {e}")

if __name__ == "__main__":
    test_health()
    test_chat()
    file_id = test_upload()
    if file_id:
        test_search()
