import requests
import json

def check_query(text):
    print(f"\nQuery: {text}")
    try:
        resp = requests.post("http://localhost:8000/search", json={"text": text, "limit": 5})
        data = resp.json()
        results = data.get("results", [])
        print(f"Found {len(results)} results")
        for r in results:
            print(f"- {r.get('filename')} (score: {r.get('score', 0)})")
            print(f"  Chunk preview: {r.get('chunk', '')[:100]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_query("master en abogacia")
    check_query("Universidad Alfonso X el Sabio")
