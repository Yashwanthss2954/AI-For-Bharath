# Quick Start Guide - UBID Intelligence Platform

## Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- Git

## Running Locally

### Step 1: Clone the Repository
```bash
git clone https://github.com/Yashwanthss2954/AI-For-Bharath.git
cd "AI For Bharath"
```

### Step 2: Setup and Run Backend

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Run the UBID pipeline (generates sample data)
python -m src.main

# Start the API server
uvicorn src.api.app:app --reload
```

**Backend will run on:** http://localhost:8000

### Step 3: Setup and Run Frontend

Open a **new terminal** window:

```bash
# Navigate to frontend folder (from project root)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend will run on:** http://localhost:5173

### Step 4: Access the Application

Open your browser and go to: **http://localhost:5173**

You should see the **Unified Business Intelligence Command Center** dashboard.

## What You'll See

- **Review Queue**: Medium-confidence record pairs needing human review
- **UBID Search**: Search businesses by name, PAN, GSTIN, pincode
- **Activity Intelligence**: View Active/Dormant/Closed business counts
- **Metrics**: Total businesses unified, review queue status

## Making Changes

The pipeline generates sample data from:
- `backend/data/master_records.csv` - Sample business records
- `backend/data/events.csv` - Sample activity events

To regenerate data after modifying these files:
```bash
cd backend
python -m src.main
```

## API Documentation

Once backend is running, visit: http://localhost:8000/docs

This shows all available API endpoints with interactive testing.

## Troubleshooting

**Backend won't start:**
- Check Python version: `python3 --version` (should be 3.11+)
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

**Frontend shows API errors:**
- Make sure backend is running on port 8000
- Check browser console for specific errors
- Verify proxy settings in `frontend/vite.config.js`

**Port already in use:**
- Backend: Kill process on port 8000: `lsof -ti:8000 | xargs kill`
- Frontend: Kill process on port 5173: `lsof -ti:5173 | xargs kill`

## Stopping the Application

- Press `Ctrl+C` in both terminal windows
- Deactivate Python virtual environment: `deactivate`

## Next Steps

- Modify sample data in `backend/data/` folder
- Explore API endpoints at http://localhost:8000/docs
- Review pipeline code in `backend/src/ubid/pipeline.py`
- Check frontend code in `frontend/src/App.jsx`

For deployment instructions, see [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
