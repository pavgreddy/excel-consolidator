# Excel Consolidator 📊

An AI-powered tool that uploads multiple Excel/CSV files with inconsistent column names, cleans and consolidates them into one unified file, and generates a full PDF audit report of every transformation.

## Live Demo
🔗 [Try it here](https://pavan-excel-consolidator.streamlit.app)

## How it works
1. Upload multiple Excel or CSV files
2. Claude AI intelligently maps matching columns across files (e.g. "Item Code" = "SKU" = "Material ID")
3. Pandas cleans the data — removes duplicates, fills missing values, standardizes dates
4. DuckDB runs SQL analysis on the consolidated data
5. Download the clean consolidated Excel file + a PDF audit report

## Tech Stack
- **Backend:** Python, FastAPI, Docker
- **Frontend:** Streamlit
- **Data Processing:** Pandas, DuckDB (SQL)
- **AI:** Anthropic Claude API
- **Report Generation:** ReportLab
- **Deployment:** Render (backend), Streamlit Cloud (frontend)

## Run Locally

1. Clone the repo:
```bash
git clone https://github.com/pavgreddy/excel-consolidator.git
cd excel-consolidator
```

2. Create `.env` in the `backend` folder:

ANTHROPIC_API_KEY=your_key

3. Run the backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

4. Run the frontend:
```bash
cd frontend
pip install streamlit requests
streamlit run app.py
```

### Run with Docker
```bash
cd backend
docker build -t excel-consolidator .
docker run -p 8000:8000 --env-file .env excel-consolidator
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/upload-files` | Upload multiple Excel/CSV files |
| GET | `/map-columns` | AI column mapping via Claude |
| POST | `/clean-and-consolidate` | Clean and merge all files |
| GET | `/download-excel` | Download consolidated Excel |
| GET | `/download-report` | Download PDF audit report |
| GET | `/reset` | Reset session |