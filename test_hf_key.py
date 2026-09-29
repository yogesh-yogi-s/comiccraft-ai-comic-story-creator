"""
Run this script to verify your HuggingFace API key and endpoint connectivity.
Usage: python test_hf_key.py
"""
import requests
import os
import socket
from dotenv import load_dotenv

load_dotenv()

hf_key = os.getenv("HF_API_KEY", "").strip().strip('"').strip("'")
print(f"HF Key present : {bool(hf_key)}")
print(f"HF Key length  : {len(hf_key)} chars (expected 37+)")
print(f"HF Key prefix  : {hf_key[:8]}..." if hf_key else "  -> No key found in .env!")
print()

# Step 1: DNS check
for host in ["api-inference.huggingface.co", "router.huggingface.co", "huggingface.co"]:
    try:
        ip = socket.gethostbyname(host)
        print(f"DNS OK   : {host} -> {ip}")
    except Exception as e:
        print(f"DNS FAIL : {host} -> {e}")

print()

# Step 2: Auth check
H = {"Authorization": f"Bearer {hf_key}"}
r = requests.get("https://huggingface.co/api/whoami", headers=H, timeout=10)
if r.status_code == 200:
    d = r.json()
    print(f"Auth OK  : logged in as '{d.get('name')}' | Pro: {d.get('isPro')}")
else:
    print(f"Auth FAIL: HTTP {r.status_code} -> {r.text[:200]}")
    print("  -> Go to https://huggingface.co/settings/tokens and create a new token")
    exit(1)

print()

# Step 3: Inference endpoint test
print("Testing inference endpoint...")
test_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
H2 = {**H, "Content-Type": "application/json"}
r2 = requests.post(test_url,
    json={"inputs": "a heroic robot, comic book panel", "parameters": {"num_inference_steps": 4}},
    headers=H2, timeout=30)
print(f"Inference: HTTP {r2.status_code} | bytes={len(r2.content)}")
if r2.status_code == 200 and len(r2.content) > 1000:
    print("  -> SUCCESS! HuggingFace inference is working.")
else:
    print(f"  -> Response: {r2.text[:300]}")
