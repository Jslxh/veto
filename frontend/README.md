# VETO Frontend — Demo Dashboard

A single-page React app built with Vite, Tailwind CSS, and Framer Motion that acts as a visual demo dashboard for the VETO Bounded Upsell-Decision Agent.

## Core Features

1. **Architecture Overview**: Interactive visual flow representing the decision pipeline: Fetching Razorpay Cart Data $\rightarrow$ Evaluating Rules $\rightarrow$ Guardrail Gate Filtering $\rightarrow$ SQLite Audit Log Committing.
2. **Batch Summary Metrics Panel**: Loads from `/batch-results` to show total propone vs. decline counts, overall average order value (AOV) uplift %, overall decline rates, and a visual bar chart representation of the decline reasons (no rules triggered, discount conflict, below confidence threshold).
3. **"Run a Cart" Interactive Sandbox**: Dropdown/card picker containing the 50 seed carts with filters (All, Discounted, Prior Declines, High Value). Running a cart performs a live evaluation through the FastAPI backend and displays the result (PROPOSE in emerald green, DECLINE in amber/red) and animates the confidence score count-up.
4. **SQLite Audit Trail View**: Displays a vertical timeline of SQLite logged decisions. Clicking a record expands it to show the full JSON trace containing ToolCall, Decision, and Outcome parameters.

---

## Setup & Running Locally

### 1. Prerequisites
Ensure you have Node.js (v18+) and npm installed.

### 2. Installation
Navigate to the `frontend/` directory and install the dependencies:
```bash
cd frontend
npm install
```

### 3. Environment Configuration
Verify that the `frontend/.env` file contains the correct backend URL:
```text
VITE_BACKEND_URL=http://localhost:8000
```

### 4. Running the Development Server
Start the Vite development server:
```bash
npm run dev
```
Open `http://localhost:5173` in your browser.

### 5. Production Build
Verify that the production code builds successfully:
```bash
npm run build
```
The compiled assets will be written to `frontend/dist/`.
