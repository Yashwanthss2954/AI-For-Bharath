# AI-Based Unified Business Identifier (UBID) Platform

> **AI-powered business identity resolution and activity intelligence system for Karnataka Government**

## 🎯 Overview

This platform solves Karnataka's fragmented business data problem across 40+ department systems by creating a single Unified Business Identifier (UBID) for each business using AI-powered entity resolution and confidence-based decision making.

## ✨ Key Features

- **🔗 Entity Resolution**: Links duplicate records using ML-based fuzzy matching
- **🎯 Confidence Scoring**: Auto-links high confidence (>0.9), routes medium (0.6-0.9) for review
- **👤 Human-in-the-Loop**: Review queue for ambiguous cases with explainable evidence
- **📊 Activity Intelligence**: Classifies businesses as Active/Dormant/Closed from event streams
- **🔍 Advanced Search**: Query by PAN, GSTIN, name, pincode, or source record ID
- **📈 Policy Analytics**: Dashboard for business intelligence and compliance monitoring

## 🚀 Quick Start

See **[QUICKSTART.md](QUICKSTART.md)** for detailed setup instructions.

### TL;DR
```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
uvicorn src.api.app:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Visit: http://localhost:5173

## 📁 Project Structure

```
├── backend/
│   ├── data/                  # Sample CSV data
│   ├── output/                # Generated UBID registry & outputs
│   ├── src/
│   │   ├── api/              # FastAPI endpoints
│   │   ├── ubid/             # Core entity resolution logic
│   │   ├── main.py           # Pipeline runner
│   │   └── evaluate.py       # Evaluation metrics
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── App.jsx           # Dashboard UI
│   └── package.json
├── render.yaml               # Render deployment config
└── QUICKSTART.md            # Setup instructions
```

## 🛠️ Technology Stack

**Backend:**
- Python 3.11+
- FastAPI - REST API
- Pandas - Data processing
- RapidFuzz - Fuzzy string matching
- NetworkX - Graph-based clustering

**Frontend:**
- React 18
- Vite - Build tool
- Modern CSS with glass morphism design

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Local setup and running
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Render deployment steps
- **[README_DEPLOYMENT.md](README_DEPLOYMENT.md)** - Detailed deployment guide

## 🎨 Dashboard Actions

### 1. Review Queue
- View medium-confidence record pairs
- See matching evidence and scores
- **Merge** to link records or **Reject** to keep separate

### 2. UBID Search
- Search businesses by multiple criteria
- View unified business profiles
- See all source records linked to each UBID

### 3. Activity Monitoring
- Track Active/Dormant/Closed businesses
- View activity status breakdown
- Monitor business health metrics

## 🌐 Deployment

Deploy to **Render** (or Railway, Vercel, etc.):

1. Push to GitHub
2. Connect repository to Render
3. Use Blueprint deployment with `render.yaml`
4. Configure frontend environment variable

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for step-by-step guide.

## 🔌 API Endpoints

Visit http://localhost:8000/docs when backend is running for interactive API documentation.

Key endpoints:
- `GET /health` - Health check
- `GET /review/queue` - Get review queue
- `POST /review/decision` - Submit merge/reject decision
- `GET /ubids/search` - Search UBIDs
- `GET /activity/status` - Get activity classifications

## 📊 Sample Data

The system includes sample data:
- **Master Records**: 50+ business records across departments
- **Events**: Inspections, renewals, compliance filings
- **Output**: Auto-generated UBIDs, review queue, activity status

## 🤝 Contributing

This is a hackathon project for **Karnataka Commerce & Industries** Theme 1: UBID and Active Business Intelligence.

## 📄 License

Built for AI For Bharath Hackathon 2026

## 👥 Team

- Government of Karnataka
- Commerce & Industries Department
- UBID Intelligence Platform Team

## 🆘 Support

For issues or questions:
1. Check [QUICKSTART.md](QUICKSTART.md) troubleshooting section
2. Review API docs at `/docs` endpoint
3. Check browser console for frontend errors
4. Verify both backend and frontend are running

---

**Built with ❤️ for Karnataka's Digital Governance**
