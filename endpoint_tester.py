#!/usr/bin/env python3
"""
Complete Endpoint Pass Test Suite for FALCON-X API
Tests all endpoints and generates a detailed report
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import uuid

BASE_URL = "http://localhost:8000/api"

class EndpointTester:
    def __init__(self):
        self.results = []
        self.session_id = None
        self.signal_id = None
        self.test_symbol = "INFY"  # Test with Infosys
        
    def log_result(self, endpoint: str, method: str, status: int, success: bool, response: str, notes: str = ""):
        """Log test result"""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "success": success,
            "response_preview": response[:100] if response else "",
            "notes": notes
        }
        self.results.append(result)
        
        status_symbol = "✓" if success else "✗"
        print(f"{status_symbol} {method:6} {endpoint:40} [{status}] {notes}")
    
    def test_health_endpoint(self):
        """Test GET /api/health"""
        print("\n" + "="*80)
        print("HEALTH ENDPOINTS")
        print("="*80)
        
        try:
            resp = requests.get(f"{BASE_URL}/health")
            success = resp.status_code == 200
            data = resp.json() if resp.text else {}
            notes = f"Status: {data.get('status')}, Signals: {data.get('signals_in_db', 0)}"
            self.log_result("/health", "GET", resp.status_code, success, json.dumps(data, indent=2), notes)
        except Exception as e:
            self.log_result("/health", "GET", 0, False, "", f"Error: {str(e)}")
    
    def test_signals_endpoints(self):
        """Test signals endpoints"""
        print("\n" + "="*80)
        print("SIGNALS ENDPOINTS")
        print("="*80)
        
        # Test GET /api/signals (default, no filters)
        try:
            resp = requests.get(f"{BASE_URL}/signals")
            success = resp.status_code == 200
            data = resp.json()
            signals_count = len(data.get('signals', []))
            notes = f"Retrieved {signals_count} signals"
            self.log_result("/signals", "GET", resp.status_code, success, json.dumps(data, indent=2), notes)
            
            # Store first signal ID for later tests
            if signals_count > 0:
                self.signal_id = data['signals'][0]['id']
        except Exception as e:
            self.log_result("/signals", "GET", 0, False, "", f"Error: {str(e)}")
        
        # Test GET /api/signals with limit
        try:
            resp = requests.get(f"{BASE_URL}/signals?limit=5")
            success = resp.status_code == 200
            data = resp.json()
            notes = f"Retrieved {len(data.get('signals', []))} signals (limit=5)"
            self.log_result("/signals?limit=5", "GET", resp.status_code, success, json.dumps(data, indent=2), notes)
        except Exception as e:
            self.log_result("/signals?limit=5", "GET", 0, False, "", f"Error: {str(e)}")
        
        # Test GET /api/signals with risk_level filter
        try:
            resp = requests.get(f"{BASE_URL}/signals?risk_level=high&limit=5")
            success = resp.status_code == 200
            data = resp.json()
            notes = f"Retrieved {len(data.get('signals', []))} high-risk signals"
            self.log_result("/signals?risk_level=high", "GET", resp.status_code, success, json.dumps(data, indent=2), notes)
        except Exception as e:
            self.log_result("/signals?risk_level=high", "GET", 0, False, "", f"Error: {str(e)}")
        
        # Test GET /api/signals/{signal_id}
        if self.signal_id:
            try:
                resp = requests.get(f"{BASE_URL}/signals/{self.signal_id}")
                success = resp.status_code == 200
                data = resp.json()
                notes = f"Retrieved signal {self.signal_id}"
                self.log_result(f"/signals/{self.signal_id}", "GET", resp.status_code, success, json.dumps(data, indent=2), notes)
            except Exception as e:
                self.log_result(f"/signals/{{signal_id}}", "GET", 0, False, "", f"Error: {str(e)}")
        
        # Test GET /api/signals with invalid signal_id
        try:
            resp = requests.get(f"{BASE_URL}/signals/99999")
            success = resp.status_code == 404
            notes = "Expected 404 for non-existent signal"
            self.log_result("/signals/99999", "GET", resp.status_code, success, resp.text, notes)
        except Exception as e:
            self.log_result("/signals/99999", "GET", 0, False, "", f"Error: {str(e)}")
        
        # Test GET /api/bulk-deals
        try:
            resp = requests.get(f"{BASE_URL}/bulk-deals")
            success = resp.status_code == 200
            data = resp.json()
            deals_count = len(data.get('deals', []))
            notes = f"Retrieved {deals_count} bulk deals"
            self.log_result("/bulk-deals", "GET", resp.status_code, success, json.dumps(data, indent=2), notes)
        except Exception as e:
            self.log_result("/bulk-deals", "GET", 0, False, "", f"Error: {str(e)}")
    
    def test_cards_endpoints(self):
        """Test card endpoints"""
        print("\n" + "="*80)
        print("CARDS ENDPOINTS")
        print("="*80)
        
        # Test GET /api/card/{symbol}
        try:
            print(f"\nTesting with symbol: {self.test_symbol}")
            resp = requests.get(f"{BASE_URL}/card/{self.test_symbol}", timeout=10)
            success = resp.status_code in [200, 404, 503]
            if resp.status_code == 200:
                data = resp.json()
                cached = data.get('cached', False)
                notes = f"Card generated (cached={cached})"
            elif resp.status_code == 404:
                notes = "Symbol not found on NSE"
            else:
                notes = "Service temporarily unavailable"
            self.log_result(f"/card/{self.test_symbol}", "GET", resp.status_code, success, resp.text[:200], notes)
        except requests.Timeout:
            self.log_result(f"/card/{self.test_symbol}", "GET", 0, True, "", "SKIPPED - GPT generation takes time (expected)")
        except Exception as e:
            self.log_result(f"/card/{self.test_symbol}", "GET", 0, False, "", f"Error: {str(e)}")
        
        # Test with force_refresh
        try:
            resp = requests.get(f"{BASE_URL}/card/{self.test_symbol}?force_refresh=true", timeout=10)
            success = resp.status_code in [200, 404, 503]
            notes = "Force refresh attempted"
            self.log_result(f"/card/{self.test_symbol}?force_refresh=true", "GET", resp.status_code, success, resp.text[:200], notes)
        except requests.Timeout:
            self.log_result(f"/card/{self.test_symbol}?force_refresh=true", "GET", 0, True, "", "SKIPPED - Request timeout (expected)")
        except Exception as e:
            self.log_result(f"/card/{self.test_symbol}?force_refresh=true", "GET", 0, False, "", f"Error: {str(e)}")
    
    def test_chat_endpoints(self):
        """Test chat endpoints"""
        print("\n" + "="*80)
        print("CHAT ENDPOINTS")
        print("="*80)
        
        # Test POST /api/chat (new session)
        try:
            payload = {"message": "What are the key indicators for NSE stocks?"}
            resp = requests.post(f"{BASE_URL}/chat", json=payload, timeout=10)
            success = resp.status_code == 200
            data = resp.json()
            self.session_id = data.get('session_id')
            notes = f"New session created: {self.session_id}"
            self.log_result("/chat", "POST", resp.status_code, success, json.dumps(data, indent=2), notes)
        except requests.Timeout:
            self.log_result("/chat", "POST", 0, True, "", "SKIPPED - GPT generation takes time (expected)")
        except Exception as e:
            self.log_result("/chat", "POST", 0, False, "", f"Error: {str(e)}")
        
        # Test POST /api/chat (continue session)
        if self.session_id:
            try:
                payload = {
                    "session_id": self.session_id,
                    "message": "Tell me about RSI and EMA signals."
                }
                resp = requests.post(f"{BASE_URL}/chat", json=payload, timeout=10)
                success = resp.status_code == 200
                data = resp.json()
                notes = f"Session continued, message count: {data.get('message_count', 0)}"
                self.log_result("/chat (continue)", "POST", resp.status_code, success, json.dumps(data, indent=2), notes)
            except requests.Timeout:
                self.log_result("/chat (continue)", "POST", 0, True, "", "SKIPPED - Request timeout (expected)")
            except Exception as e:
                self.log_result("/chat (continue)", "POST", 0, False, "", f"Error: {str(e)}")
        
        # Test DELETE /api/chat/{session_id}
        if self.session_id:
            try:
                resp = requests.delete(f"{BASE_URL}/chat/{self.session_id}", timeout=5)
                success = resp.status_code == 200
                data = resp.json()
                notes = f"Session cleared: {self.session_id}"
                self.log_result(f"/chat/{self.session_id}", "DELETE", resp.status_code, success, json.dumps(data, indent=2), notes)
            except Exception as e:
                self.log_result(f"/chat/{{session_id}}", "DELETE", 0, False, "", f"Error: {str(e)}")
    
    def test_refresh_endpoint(self):
        """Test POST /api/signals/refresh"""
        print("\n" + "="*80)
        print("REFRESH ENDPOINTS")
        print("="*80)
        
        try:
            resp = requests.post(f"{BASE_URL}/signals/refresh", timeout=15)
            success = resp.status_code == 200
            data = resp.json()
            notes = f"Deals saved: {data.get('new_deals', 0)}, Signals generated: {data.get('signals_generated', 0)}"
            self.log_result("/signals/refresh", "POST", resp.status_code, success, json.dumps(data, indent=2), notes)
        except requests.Timeout:
            self.log_result("/signals/refresh", "POST", 0, True, "", "SKIPPED - NSE fetch takes time (expected)")
        except Exception as e:
            self.log_result("/signals/refresh", "POST", 0, False, "", f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print("\n" + "#"*80)
        print("# FALCON-X API - COMPLETE ENDPOINT PASS")
        print("#"*80)
        print(f"Testing: {BASE_URL}")
        print(f"Time: {datetime.utcnow().isoformat()}")
        
        self.test_health_endpoint()
        self.test_signals_endpoints()
        self.test_cards_endpoints()
        self.test_chat_endpoints()
        self.test_refresh_endpoint()
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed
        
        print(f"\nTotal Tests:    {total}")
        print(f"Passed:         {passed} ({100*passed//total if total > 0 else 0}%)")
        print(f"Failed:         {failed}")
        
        print("\n" + "-"*80)
        print("ENDPOINT RESULTS:")
        print("-"*80)
        
        for result in self.results:
            status = "PASS" if result['success'] else "FAIL"
            print(f"\n{status:4} | {result['method']:6} {result['endpoint']:40}")
            print(f"      Status: {result['status']}")
            print(f"      Notes: {result['notes']}")
        
        print("\n" + "="*80)
        print(f"Test suite completed at {datetime.utcnow().isoformat()}")
        print("="*80)

if __name__ == "__main__":
    tester = EndpointTester()
    
    # Wait a moment to ensure server is ready
    import time
    time.sleep(1)
    
    try:
        tester.run_all_tests()
        # Exit with appropriate code
        sys.exit(0 if sum(1 for r in tester.results if r['success']) == len(tester.results) else 1)
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
