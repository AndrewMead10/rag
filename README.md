# Service Template

A comprehensive full-stack service template with FastAPI, React, and authentication built-in.

## Features

- 🚀 **FastAPI Backend** with automatic OpenAPI documentation
- ⚛️ **React Frontend** with TypeScript and Tailwind CSS
- 🔐 **JWT Authentication** with role-based access control
- 🐳 **Docker** ready for easy deployment
- 📱 **Responsive UI** with modern design patterns
- 🔍 **Type Safety** with end-to-end TypeScript integration

## Quick Start

### Development

1. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start backend**:
   ```bash
   cd backend
   pip install uv
   uv sync
   uv run alembic upgrade head
   uv run uvicorn app.main:app --reload --port 5656
   ```

3. **Start frontend**:
   ```bash
   cd frontend
   npm install
   # Optional: generate OpenAPI types (requires backend running or openapi.json present)
   # npm run gen:types
   npm run dev

   The frontend dev server runs on `http://localhost:3000` and proxies
   any requests starting with `/api` to the backend on `http://localhost:5656`.
   This avoids route collisions with client-side routes like `/auth/*` so
   refreshing deep links works correctly.
   ```

### Production

```bash
cp .env.example .env
# Configure production values in .env
docker-compose up -d
```

In production, the backend serves the built frontend from `/` and exposes all
API endpoints under `/api`. For example, `GET /api/auth/me` and the SPA route
`/auth/login` coexist without conflicts.

## Architecture

- **Backend**: FastAPI with SQLAlchemy, following a "pages pattern"
- **Frontend**: React with TanStack Router and Query for data fetching
- **Database**: SQLite with Alembic migrations
- **Authentication**: JWT tokens with refresh mechanism
- **Styles**: Tailwind CSS v4 (zero-config)
 - **Types**: OpenAPI -> TypeScript types pipeline via openapi-typescript

## Documentation

See [CLAUDE.md](./CLAUDE.md) for comprehensive documentation including:

- Detailed setup instructions
- Architecture overview
- Development workflows
- Production deployment guide
- Customization examples

## Access Points

- **Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Requirements

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose (for containerized deployment)

## OpenAPI Type Generation

Frontend types can be generated from the backend OpenAPI schema using `openapi-typescript`:

```bash
# From template/frontend
npm run gen:types  # reads openapi.json and writes src/lib/openapi-types.ts
```

When building via Docker, the backend OpenAPI is exported during the build and types are generated automatically in the frontend build stage.

## Tailwind CSS v4

This template uses Tailwind v4 with zero-config. Styles are imported in `src/styles/globals.css` via `@import "tailwindcss";` and custom variables are defined in CSS.

## License

This template is provided as-is for use in your own projects.
