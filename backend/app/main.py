from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.routes import health, upload, jobs, videos, captions, render, projects

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Shortify AI Long-Video to Short-Video Converter API",
    lifespan=lifespan
)

# CORS setup for local development & preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(videos.router, prefix="/api", tags=["Videos"])
app.include_router(captions.router, prefix="/api", tags=["Captions"])
app.include_router(render.router, prefix="/api", tags=["Render"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])

@app.get("/")
def root():
    return {
        "message": "Welcome to Shortify API",
        "health": "/api/health",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
