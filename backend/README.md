# GradPilot Backend

GradPilot is a FastAPI backend for graduation project discovery and planning. It supports:
- source-backed project generation from arXiv and GitHub
- optional Ollama-powered idea generation and project chat
- PostgreSQL persistence for users, saved projects, favorites, and chat sessions
- in-memory fallback for `/projects` when the database is disabled

## Project Structure

```text
backend/
  app/
    core/
      config.py
    controllers/
      advisor_controller.py
      chat_controller.py
      project_controller.py
      source_controller.py
      user_controller.py
    db/
      __init__.py
      database.py
      models.py
    models/
      project_model.py
    routes/
      advisor_routes.py
      chat_routes.py
      project_routes.py
      source_routes.py
      user_routes.py
    schemas/
      advisor_schema.py
      project_schema.py
      source_schema.py
      user_schema.py
    services/
      advisor_service.py
      arxiv_service.py
      chat_service.py
      github_service.py
      llm_service.py
      project_service.py
      source_service.py
      user_service.py
    main.py
  tests/
    conftest.py
    test_advisor_quality.py
    test_persistence_fallback.py
  .env.example
  requirements.txt
  README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

## PostgreSQL Setup

Create the database:

```bash
createdb gradpilot
```

Or with `psql`:

```sql
psql -U postgres
CREATE DATABASE gradpilot;
```

Update `.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/gradpilot
ENABLE_DATABASE=true
ARXIV_BASE_URL=https://export.arxiv.org/api/query
ARXIV_MAX_RESULTS=5
ARXIV_SORT_BY=relevance
ARXIV_SORT_ORDER=descending
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
ENABLE_LLM=true
ENABLE_ARXIV=true
ENABLE_GITHUB=true
```

If you want the backend to run without PostgreSQL persistence, set:

```env
ENABLE_DATABASE=false
```

## Optional Ollama Setup

```bash
ollama pull llama3.1:8b
ollama serve
```

## Run the Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Base URLs:
- API: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

## Endpoints

### General

- `GET /`
- `GET /health`

### Projects

- `GET /projects`
- `GET /projects/search?q=ai`
- `GET /projects/{project_id}`
- `POST /projects`
- `PUT /projects/{project_id}`
- `DELETE /projects/{project_id}`
- `POST /projects/save-generated`

### Advisor

- `POST /advisor/recommend`
- `POST /advisor/generate-projects`
- `POST /advisor/chat`
- `POST /advisor/blueprint`
- `POST /advisor/export-markdown`

### Sources

- `GET /sources/search?query=ai+flutter`

### Users

- `POST /users/register`
- `POST /users/login`
- `GET /users`
- `GET /users/{id}`
- `PUT /users/{id}`
- `DELETE /users/{id}`

### Favorites

- `POST /favorites`
- `GET /favorites?user_id=1`
- `DELETE /favorites/{favorite_id}`

### Chat Sessions

- `GET /chat/sessions?user_id=1`
- `GET /chat/sessions/{session_id}`
- `DELETE /chat/sessions/{session_id}`

## Example Requests

### Generate Projects

```json
{
  "prompt_text": "We want an AI healthcare mobile app using Flutter and FastAPI, intermediate difficulty, and we need to finish it in 5 months.",
  "max_results": 5
}
```

### Register User

```json
{
  "full_name": "Ahmed",
  "email": "student@test.com",
  "phone": "01000000000",
  "department": "Computer Science",
  "password": "123456",
  "avatar_style": "blue"
}
```

### Login User

```json
{
  "email": "student@test.com",
  "password": "123456"
}
```

### Favorite a Project

```json
{
  "user_id": 1,
  "project_id": 2
}
```

### Advisor Chat With Persistence

```json
{
  "project": {
    "id": 1,
    "title": "AI Healthcare Assistant",
    "category": "AI",
    "difficulty": "medium",
    "duration_months": 5,
    "tech_stack": ["Flutter", "FastAPI", "Python"],
    "description": "A mobile AI healthcare assistant project.",
    "problem": "Students need a practical healthcare AI graduation project.",
    "solution": "Build a mobile app with FastAPI backend and AI assistant.",
    "features": ["Symptom input", "AI advice", "Dashboard"],
    "evaluation_metrics": ["response relevance", "latency", "user satisfaction"],
    "paper_link": "https://arxiv.org/abs/1234.5678",
    "github_link": "https://github.com/example/repo",
    "feasibility_score": 85,
    "scope": "5-month MVP project.",
    "architecture_summary": "Flutter frontend + FastAPI backend + AI service.",
    "weekly_milestones": ["Week 1: planning", "Week 2: backend", "Week 3: Flutter"],
    "risks": ["Scope creep", "API integration"],
    "source_status": "real_sources",
    "source_titles": ["Example Paper", "example/repo"],
    "source_quality_score": 80,
    "paper_score": 75,
    "repository_score": 85
  },
  "messages": [
    {
      "role": "user",
      "content": "احنا تلاتة في التيم، نقسم المشروع إزاي؟"
    }
  ],
  "user_id": 1,
  "session_id": null
}
```

## Testing

Run the regression suite:

```bash
pytest -q
python -m compileall app tests
```

Database integration tests are skipped unless `TEST_DATABASE_URL` is set.
