# 📝 MediSafe AI - Simple Step-by-Step Guide

## 🎯 Goal
Get MediSafe AI running on your computer in ~20 minutes

---

## ✅ Pre-Flight Checklist

Before you start, download and install (if not already installed):

- [ ] Node.js 18+ from https://nodejs.org/
- [ ] Python 3.11+ from https://www.python.org/downloads/
- [ ] MongoDB 7.0+ from https://www.mongodb.com/try/download/community
- [ ] Yarn: Run `npm install -g yarn` after Node.js is installed
- [ ] VS Code (optional) from https://code.visualstudio.com/

---

## 🚀 Quick Start (6 Steps)


### Step 2️⃣: Open Three Terminals (30 seconds)

Open VS Code → Open the extracted folder → Open 3 terminals:
- Terminal → New Terminal (repeat 3 times)
- Or use keyboard shortcut: `Ctrl + Shift + `` (backtick)

Label them mentally as:
- Terminal 1: MongoDB
- Terminal 2: Backend  
- Terminal 3: Frontend

---

### Step 3️⃣: Start MongoDB (1 minute)

**Terminal 1 - Run ONE of these:**

```bash
# Windows (as Administrator)
net start MongoDB

# Mac
brew services start mongodb-community@7.0

# Linux
sudo systemctl start mongod

# Or manual start (all platforms):
# Windows: mongod --dbpath C:\data\db
# Mac/Linux: mongod --dbpath /data/db
```

✅ Look for: "Waiting for connections on port 27017"

---

### Step 4️⃣: Start Backend (5-10 minutes first time)

**Terminal 2:**

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# Install dependencies (FIRST TIME ONLY - takes 5-10 min)
pip install -r requirements.txt

# Start server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

✅ Wait for: "Application startup complete"

**First run takes 2-3 minutes extra** for dataset download!

---

### Step 5️⃣: Start Frontend (3-5 minutes first time)

**Terminal 3:**

```bash
# Navigate to frontend
cd frontend

# Install dependencies (FIRST TIME ONLY - takes 3-5 min)
yarn install

# Start React app
yarn start
```

✅ Browser should auto-open to http://localhost:3000

---

### Step 6️⃣: Test It! (30 seconds)

1. Browser opens to http://localhost:3000
2. You see "MediSafe AI" interface
3. Type in the query box: "What are the interactions between aspirin and warfarin?"
4. Click "Analyze Query"
5. Wait 15-30 seconds
6. See results with risk score and citations!

🎉 **You're done!**

---

## ⚡ Super Quick Reference

### Starting Everything (After First Setup)

You only need to run these 3 commands in 3 different terminals:

```bash
# Terminal 1: MongoDB
mongod --dbpath /data/db  # or net start MongoDB on Windows

# Terminal 2: Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3: Frontend  
cd frontend
yarn start
```

Then open: http://localhost:3000

---

## 🛑 Stopping Everything

Press `Ctrl + C` in each terminal (1, 2, 3)

To stop MongoDB service:
- Windows: `net stop MongoDB`
- Mac: `brew services stop mongodb-community@7.0`
- Linux: `sudo systemctl stop mongod`

---

## 🔥 Most Common Issues & Quick Fixes

### ❌ "Module not found" (Backend)
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ "Port 3000 already in use" (Frontend)
```bash
# Kill the port
npx kill-port 3000
# Or on Windows: netstat -ano | findstr :3000, then taskkill /PID <PID> /F
```

### ❌ "Cannot connect to MongoDB"
```bash
# Make sure it's running
mongosh  # Should connect
# If not, start MongoDB (see Step 3)
```

### ❌ Blank page in browser
```bash
# Check backend is running
curl http://localhost:8001/api/
# Should show: {"message":"Drug Interaction RAG System API","status":"active"}

# If not showing, restart backend
```

### ❌ "Permission denied" (Mac/Linux)
```bash
sudo chown -R $USER:$USER /data/db
sudo chown -R $USER:$USER ~/Projects/MediSafe
```

---

## 📊 How to Know Everything is Working

### ✅ Checklist:

**MongoDB:**
- Terminal 1 shows: "Waiting for connections"
- Or run: `mongosh` → connects successfully

**Backend:**
- Terminal 2 shows: "Uvicorn running on http://0.0.0.0:8001"
- Open: http://localhost:8001/api/ → see JSON response

**Frontend:**
- Terminal 3 shows: "webpack compiled successfully"
- Open: http://localhost:3000 → see MediSafe AI interface
- No errors in browser console (press F12)

---

## 🎨 Features to Try

### 1. Dark Mode
- Click sun/moon toggle in header
- Theme switches instantly

### 2. Export Report
- Submit a query
- Go to "Result" tab
- Click "Export Report" button
- Text file downloads

### 3. Compare Queries
- Submit 2-3 different queries
- Go to "History" tab
- Click "+" on each query
- Go to "Compare" tab
- See side-by-side comparison

### 4. View Stats
- Check "Total Queries Processed"
- See "Risk Distribution" breakdown

---

## 📝 Example Queries to Try

```
1. What are the interactions between aspirin and warfarin?

2. Can I take antibiotics with antacids?

3. Is it safe to mix blood pressure medication with NSAIDs?

4. What are the side effects of combining statins with grapefruit juice?

5. Can ibuprofen and acetaminophen be taken together?
```

---

## ⏱️ Time Expectations

**First Time Setup:**
- Installing prerequisites: 15-20 minutes
- Project setup: 10-15 minutes
- **Total: ~30-35 minutes**

**Starting After Setup:**
- Starting all services: 1-2 minutes
- First query: 15-30 seconds
- Subsequent queries: 10-20 seconds

**Subsequent Runs:**
- Just start the 3 terminals: 2 minutes
- No reinstalling needed!

---

## 💾 Project Disk Space

- Backend (with dependencies): ~2 GB
- Frontend (with node_modules): ~500 MB
- MongoDB data: ~100 MB (grows with queries)
- **Total: ~2.5-3 GB**

---

## 🔧 When to Reinstall Dependencies

You only need to reinstall if:

❌ You deleted node_modules or venv folders  
❌ You updated package.json or requirements.txt  
❌ You get "module not found" errors  

Otherwise, just start the servers! ✅

---

## 🎯 Success Metrics

You know it's working when:

✅ MongoDB: No errors, shows "waiting for connections"  
✅ Backend: Shows startup complete, responds to http://localhost:8001/api/  
✅ Frontend: Opens in browser, shows UI, no console errors  
✅ Query: Enter query → Get result with risk score in 15-30 seconds  

---

## 📞 Need More Detail?

This is the **ultra-simplified guide**. For detailed troubleshooting:

👉 See **DETAILED_LOCAL_SETUP.md** (comprehensive 500+ line guide)  
👉 See **LOCAL_SETUP_INSTRUCTIONS.md** (detailed technical guide)  
👉 See **README.md** (project overview and features)

---

## 🎉 That's It!

If all three terminals are running and you can see the app at http://localhost:3000:

**🏆 Congratulations! You did it! 🏆**

Now try some queries and explore the features!

---

## 🚨 Emergency Quick Fix

If nothing works and you want to start fresh:

```bash
# 1. Stop everything (Ctrl+C in all terminals)

# 2. Delete generated files
cd backend
rm -rf venv __pycache__ data

cd ../frontend
rm -rf node_modules .cache

# 3. Follow steps 4 and 5 again (reinstall everything)
```

---

**Happy Querying! 🏥✨**

Remember: This is for educational purposes. Always consult healthcare professionals for medical advice!
