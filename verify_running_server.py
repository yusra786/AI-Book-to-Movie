import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

print("--- Querying Active Flask Server ---")
tests_failed = 0

def run_test(name, url, method="GET", json_body=None, check_str=None):
    global tests_failed
    print(f"Test {name}: {method} {url} ...", end=" ")
    try:
        if method == "GET":
            r = requests.get(BASE_URL + url)
        else:
            r = requests.post(BASE_URL + url, json=json_body)
            
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        if check_str:
            assert check_str in r.text or check_str in r.json().get("reply", ""), f"Response did not contain: {check_str}"
        print("PASS")
    except Exception as e:
        print("FAIL")
        print(f"  Details: {e}")
        tests_failed += 1

run_test("Home Page", "/", "GET", check_str="AI Adaptation Guide")
run_test("Chat Page", "/chat", "GET", check_str="Chat with AI")
run_test("Recommendations Page", "/recommendations", "GET", check_str="AI Recommendations")
run_test("Dashboard Page", "/dashboard", "GET", check_str="Dashboard")
run_test("Login Page", "/login", "GET", check_str="Login - AI Adaptation")
run_test("Recommendations API", "/api/recommendations", "GET", check_str=None)
run_test("POST Chat RAG (Dune)", "/chat", "POST", json_body={"message": "Tell me about Dune", "history": []}, check_str="Dune")

if tests_failed > 0:
    print(f"\nVerification FAILED with {tests_failed} failures.")
    sys.exit(1)
else:
    print("\nVerification PASSED successfully!")
    sys.exit(0)
