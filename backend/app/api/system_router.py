import threading
from fastapi import APIRouter, HTTPException
from app.services.update_service import update_service

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/version")
async def get_version():
    return {
        "version": update_service.current_version,
    }


@router.post("/update/check")
def check_update():
    info = update_service.check_for_updates()
    if info:
        return {
            "has_update": True,
            "version": info["version"],
            "download_url": info["download_url"],
        }
    return {
        "has_update": False,
        "version": update_service.current_version,
    }


@router.get("/update/progress")
async def get_update_progress():
    return {
        "is_downloading": update_service.is_downloading,
        "progress": update_service.download_progress,
    }


@router.post("/update/install")
def install_update():
    threading.Thread(target=update_service.download_and_install, daemon=True).start()
    return {
        "status": "started",
        "message": "Đang tải và tiến hành cài đặt bản cập nhật...",
    }
