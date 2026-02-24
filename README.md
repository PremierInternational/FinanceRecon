# FinanceRecon

A financial reconciliation tool for comparing two Excel files and identifying matches, variances, and missing records.

Two versions of the app exist side by side:

| Version | Stack | Location |
|---|---|---|
| **Streamlit** (original) | Python + Streamlit | repo root |
| **React** (rework) | FastAPI + React/Vite | `react_app/` |

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv

# Windows (bash/Git Bash)
source venv/Scripts/activate

# Windows (Command Prompt)
venv\Scripts\activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
pip install -r react_app/backend/requirements.txt
```

### 3. Install frontend dependencies

```bash
cd react_app/frontend
npm install
cd ../..
```

---

## Running the Streamlit version

```bash
streamlit run GL_Recon.py
```

Opens at **http://localhost:8501**

---

## Running the React version

The React version requires two processes running simultaneously.

**Terminal 1 — FastAPI backend (port 8000):**

```bash
cd react_app/backend
uvicorn main:app --reload
```

**Terminal 2 — React frontend (port 5173):**

```bash
cd react_app/frontend
npm run dev
```

Opens at **http://localhost:5173**

---

## Running both versions side by side

Open three terminals and run all three commands above at the same time:

| Terminal | Command | URL |
|---|---|---|
| 1 | `streamlit run GL_Recon.py` | http://localhost:8501 |
| 2 | `cd react_app/backend && uvicorn main:app --reload` | http://localhost:8000 |
| 3 | `cd react_app/frontend && npm run dev` | http://localhost:5173 |

---

## How it works

1. **Upload** two Excel files (.xlsx or .xls)
2. **Configure** match key columns (the columns used to join the two files)
3. **Select** the numeric column to compare
4. **Set tolerance** (optional) — ignore differences below a dollar or percentage threshold
5. **Run** — view matched/unmatched stats, filter the results table, and download the output as Excel

Configuration settings can be saved as named **profiles** and reloaded on future runs.

---

## Mock data

Sample files for testing are in `mock_data/`:

- `General_Ledger.xlsx` — 16 rows across 7 departments
- `Subledger.xlsx` — 16 rows with intentional variances and missing/extra records

Suggested settings:
- **Match keys:** `Account_Code` + `Department`
- **Compare column:** `Amount`
- **Tolerance:** `$20` dollar threshold
