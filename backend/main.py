"""
AeroVault — National Airport Flight Management System
Backend Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from database import init_db
from routers import flights, crew, maintenance, auth, notifications, admin
from seed_data import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    seed_database()
    yield
    # Shutdown (nothing needed)


app = FastAPI(
    title="AeroVault",
    description="National Airport Flight Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow frontend dev server and same-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router,          prefix="/api/auth",          tags=["Auth"])
app.include_router(flights.router,       prefix="/api/flights",        tags=["Flights"])
app.include_router(crew.router,          prefix="/api/crew",           tags=["Crew"])
app.include_router(maintenance.router,   prefix="/api/maintenance",    tags=["Maintenance"])
app.include_router(notifications.router, prefix="/api/notifications",  tags=["Notifications"])
app.include_router(admin.router,         prefix="/api/admin",          tags=["Admin"])

# Serve React frontend (built files)
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = os.path.join(frontend_dist, "index.html")
        return FileResponse(index)
