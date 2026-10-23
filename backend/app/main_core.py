import mimetypes
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.api.system_router import router as system_router
from app.services.update_service import update_service

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")


def resolve_client_dir() -> Path:
    """Xác định thư mục chứa bản build Angular (hỗ trợ cả client/browser và client/)."""
    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([
            exe_dir / "client" / "browser",
            exe_dir / "client",
        ])
        if hasattr(sys, "_MEIPASS"):
            meipass_dir = Path(sys._MEIPASS).resolve()
            candidates.extend([
                meipass_dir / "client" / "browser",
                meipass_dir / "client",
            ])

    backend_dir = Path(__file__).resolve().parent.parent
    candidates.extend([
        backend_dir / "client" / "browser",
        backend_dir / "client",
        Path.cwd() / "client" / "browser",
        Path.cwd() / "client",
    ])

    for cand in candidates:
        if (cand / "index.html").is_file():
            return cand

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "client" / "browser"
    return backend_dir / "client" / "browser"


CLIENT_DIR = resolve_client_dir()

app = FastAPI(
    title="AutoCameraAI Admin API",
    version=update_service.current_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router, prefix="/api")


@app.get("/")
async def serve_root():
    global CLIENT_DIR
    index_path = CLIENT_DIR / "index.html"
    if not index_path.exists():
        CLIENT_DIR = resolve_client_dir()
        index_path = CLIENT_DIR / "index.html"

    if index_path.exists():
        return FileResponse(index_path, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    base_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    loading_file = base_dir / "loading.html"
    if loading_file.exists():
        return FileResponse(loading_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    return JSONResponse({"error": "Frontend not found", "path_checked": str(CLIENT_DIR)}, status_code=404)


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    global CLIENT_DIR
    if full_path.startswith("api/") or full_path in ["docs", "redoc", "openapi.json"]:
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    file_path = CLIENT_DIR / full_path
    if not file_path.exists():
        alt_client = resolve_client_dir()
        if (alt_client / full_path).exists():
            CLIENT_DIR = alt_client
            file_path = CLIENT_DIR / full_path

    if file_path.exists() and file_path.is_file():
        headers = {"Cache-Control": "no-cache"} if full_path.endswith((".html", ".js", ".css")) else None
        return FileResponse(file_path, headers=headers)

    static_extensions = (".js", ".css", ".map", ".png", ".jpg", ".jpeg", ".svg", ".woff", ".woff2", ".ttf", ".ico", ".webp")
    if full_path.lower().endswith(static_extensions):
        return JSONResponse({"detail": "Asset Not Found"}, status_code=404)

    index_path = CLIENT_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    return JSONResponse({"error": "Index not found", "path_checked": str(CLIENT_DIR)}, status_code=404)
