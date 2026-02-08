#!/usr/bin/env python3
"""Comprehensive API Test"""

import requests
import json

BASE = "http://localhost:8000"

def test(name, method, url, **kwargs):
    """Test helper"""
    try:
        print(f"\n🧪 {name}...")
        
        if method == "GET":
            r = requests.get(f"{BASE}{url}", **kwargs)
        else:
            r = requests.post(f"{BASE}{url}", **kwargs)
        
        if r.status_code == 200:
            print(f"✅ SUCCESS ({r.status_code})")
            data = r.json()
            print(f"📦 Data: {json.dumps(data, indent=2)[:200]}...")
            return True
        else:
            print(f"❌ FAILED ({r.status_code})")
            print(f"Error: {r.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


print("="*60)
print("🚀 CRYPTO AI AGENT - API TESTS")
print("="*60)

# Test health
test("Health Check", "GET", "/health")

# Test market
test("Top 10 Cryptos", "GET", "/api/v1/market/top?limit=10")
test("BTC Ticker", "GET", "/api/v1/market/ticker/BTC/USDT")
test("BTC History", "GET", "/api/v1/market/history/BTC/USDT?limit=30")

# Test analysis
test("BTC Indicators", "GET", "/api/v1/analysis/indicators/BTC/USDT")
test("BTC Signals", "GET", "/api/v1/analysis/signals/BTC/USDT")
test("BTC Trend", "GET", "/api/v1/analysis/trend/BTC/USDT")

# Test predictions
test("Price Prediction", "POST", "/api/v1/predictions/price", 
     json={"symbol": "BTC/USDT", "periods": 7})

# Test AI chat
test("AI Chat", "POST", "/api/v1/ai/chat",
     json={"message": "What is Bitcoin?", "stream": False})

print("\n" + "="*60)
print("✅ Tests completed!")
print("="*60)
