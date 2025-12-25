import requests
import sys
import re

BASE_URL = "http://127.0.0.1:5000"
s = requests.Session()

try:
    # 1. Login
    print("Getting login page...")
    r = s.get(f"{BASE_URL}/login")
    if r.status_code != 200:
        print(f"Failed to load login page: {r.status_code}")
        sys.exit(1)
        
    csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', r.text)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    print(f"CSRF Token: {csrf_token}")
    
    login_data = {
        'email': 'test_fix@example.com',
        'password': 'password123',
        'csrf_token': csrf_token,
        'submit': 'Login'
    }
    
    print("Logging in...")
    r = s.post(f"{BASE_URL}/login", data=login_data)
    print(f"Login Response: {r.status_code}")
    
    # 2. Create Post
    print("Creating Post...")
    
    # Get create post page for fresh CSRF if needed? Usually same session/token is fine or rotated.
    # But lets try direct post first.
    
    post_data = {
        'title': 'Crash Test',
        'content': 'Content for crash test',
        'excerpt': 'Excerpt',
        'category': 'technology',
        'is_published': 'y',
        'csrf_token': csrf_token,
        'submit': 'Submit Post'
    }
    
    r = s.post(f"{BASE_URL}/post/new", data=post_data)
    print(f"Create Post status: {r.status_code}")
    if r.status_code == 500:
        print("Got 500 Error")
    else:
        print("Success or other error")
        
except Exception as e:
    print(f"Exception: {e}")
