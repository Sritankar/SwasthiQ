import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.database import Base, SessionLocal, engine
from app.routers.dashboard import router as dashboard_router
from app.routers.inventory import router as inventory_router
from app.routers.patient_sales import router as patient_sales_router
from app.seed import seed_database

FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def resolve_allowed_origins() -> list[str]:
    configured_origins = os.getenv("ALLOWED_ORIGINS")
    if configured_origins:
        origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
        if origins:
            return origins

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(
    title="SwasthiQ Pharmacy Module API",
    description="REST APIs for dashboard and inventory features of a pharmacy EMR module.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=resolve_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(inventory_router)
app.include_router(patient_sales_router)


@app.get("/api/health")
def healthcheck():
    return {"success": True, "data": {"status": "ok"}}


if (FRONTEND_DIST_DIR / "index.html").exists():
    frontend_root = FRONTEND_DIST_DIR.resolve()

    @app.get("/", include_in_schema=False)
    def serve_frontend_root():
        return FileResponse(frontend_root / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        requested_file = (frontend_root / full_path).resolve()
        if frontend_root in requested_file.parents and requested_file.is_file():
            return FileResponse(requested_file)

        return FileResponse(frontend_root / "index.html")
