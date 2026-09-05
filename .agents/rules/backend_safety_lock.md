# Backend Safety Lock Rule

## STRICT DIRECTIVE: BACKEND CODE IS LOCKED
The backend process is complete and verified. 

### Protected (Read-Only / Do Not Modify):
- `src/**` (All Python models, rules, engine, services, schemas, and logic)
- `tests/**` (All test suites and test cases)
- `TestCase/**`, `TESTCASE2/**`, `TESTCASE3/**`, `data/**` (All test data and inputs)
- `app.py` (Backend endpoints, server configuration, route definitions)
- `requirements.txt`, `.env*`

### Modifiable Scope:
- ONLY UI and frontend assets inside `frontend/`:
  - `frontend/styles.css`
  - `frontend/app.jsx`
  - `frontend/index.html`

Under no circumstances should any backend files, algorithms, or API routes be modified or disrupted.
