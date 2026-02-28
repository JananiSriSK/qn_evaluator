# TROUBLESHOOTING: 404 Error on /domains/create

## Problem
The `/domains/create` endpoint returns 404 Not Found even though it's defined in main_v2.py.

## Root Cause
The server is running but hasn't picked up the new routes. This happens when:
1. The server wasn't restarted after code changes
2. The wrong main file is running (main.py instead of main_v2.py)
3. Python is caching the old module

## Solution

### Step 1: Stop the Current Server
Press `Ctrl+C` in the terminal where the server is running.

### Step 2: Verify No Server is Running
```bash
# Windows
netstat -ano | findstr :8002
# If you see a PID, kill it:
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8002 | xargs kill -9
```

### Step 3: Start the Correct Server
```bash
cd backend
python main_v2.py
```

OR use the batch file:
```bash
cd backend
start_v2.bat
```

### Step 4: Verify Server Started Correctly
You should see:
```
INFO:     Starting up Question Intelligence System...
INFO:     System startup completed successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002
```

### Step 5: Test the Endpoint
```bash
python test_endpoint.py
```

Expected output:
```
Testing health endpoint...
Status: 200
Response: {'status': 'ok', 'message': 'Question Intelligence System v2.0 is running'}

Testing create domain endpoint...
Status: 200
Response: {'message': 'Domain created successfully', ...}
```

## Quick Test Commands

```bash
# Test health
curl http://localhost:8002/

# Test create domain
curl -X POST http://localhost:8002/domains/create \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"test\",\"domain_name\":\"TEST\"}"

# Test list domains
curl http://localhost:8002/domains/test
```

## If Still Not Working

1. Check if you're in the correct directory:
   ```bash
   pwd  # Should show .../qn_evaluator_2/backend
   ```

2. Check if main_v2.py exists:
   ```bash
   ls main_v2.py
   ```

3. Check Python is using the correct file:
   ```bash
   python -c "import main_v2; print(main_v2.__file__)"
   ```

4. Clear Python cache:
   ```bash
   # Windows
   del /s *.pyc
   rmdir /s __pycache__

   # Linux/Mac
   find . -type d -name __pycache__ -exec rm -r {} +
   find . -type f -name '*.pyc' -delete
   ```

5. Restart with explicit path:
   ```bash
   python c:\Users\Jananisri\Desktop\study\mcanotes\SEM_4_Project\proj\qn_evaluator_2\backend\main_v2.py
   ```

## Frontend Fix

If the frontend is showing "failed to create domain", after fixing the backend:

1. Refresh the browser (Ctrl+F5)
2. Clear browser cache
3. Check browser console for actual error
4. Verify API base URL in `src/services/api-v2.js` is `http://localhost:8002`

## Verification Checklist

- [ ] Server stopped completely
- [ ] No process on port 8002
- [ ] Started with `python main_v2.py`
- [ ] Saw "System startup completed successfully"
- [ ] Health endpoint returns 200
- [ ] Create domain endpoint returns 200
- [ ] Frontend can connect

## Still Having Issues?

Run the full test suite:
```bash
cd backend
python test_api.py
```

This will test all 9 endpoints and show which ones are working.
