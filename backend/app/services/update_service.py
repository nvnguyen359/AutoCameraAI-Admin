import json
import os
import sys
import time
import tempfile
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional

GITHUB_REPO = "nvnguyen359/AutoCameraAI-Admin"
VERSION_JSON_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
EXE_NAME = "AutoCameraAI-Admin.exe"
SETUP_FILENAME = "AutoCameraAI_Admin_Setup.exe"


def get_current_version() -> str:
    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "version.txt")
        if hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "version.txt")

    backend_dir = Path(__file__).resolve().parent.parent.parent
    candidates.extend([
        backend_dir / "version.txt",
        Path.cwd() / "version.txt",
    ])

    for p in candidates:
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8").strip().lstrip("vV")
            except Exception:
                pass
    return "1.0.0"


def _parse_version(ver_str: str) -> tuple:
    try:
        clean = str(ver_str).strip().lstrip("vV")
        return tuple(int(x) for x in clean.split(".") if x.isdigit())
    except Exception:
        return (0, 0, 0)


class UpdateService:
    def __init__(self):
        self.current_version = get_current_version()
        self.latest_info: Optional[dict] = None
        self.download_progress: int = 0
        self.is_downloading: bool = False

    def check_for_updates(self) -> Optional[dict]:
        self.current_version = get_current_version()
        # 1. Check version.json on main branch (fast, no API rate limit)
        try:
            url = f"{VERSION_JSON_URL}?t={int(time.time())}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as res:
                data = json.loads(res.read().decode("utf-8"))
                remote_ver = str(data.get("version", "")).strip().lstrip("vV")
                download_url = data.get("download_url", "")
                if remote_ver and download_url:
                    if _parse_version(remote_ver) > _parse_version(self.current_version):
                        self.latest_info = {
                            "version": remote_ver,
                            "download_url": download_url,
                        }
                        return self.latest_info
                    return None
        except Exception as e:
            print(f"[UpdateService] version.json check warning: {e}")

        # 2. Fallback to GitHub Releases API
        try:
            req = urllib.request.Request(RELEASES_API_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as res:
                data = json.loads(res.read().decode("utf-8"))
                remote_ver = str(data.get("tag_name", "")).strip().lstrip("vV")
                assets = data.get("assets", [])
                if remote_ver and assets and _parse_version(remote_ver) > _parse_version(self.current_version):
                    self.latest_info = {
                        "version": remote_ver,
                        "download_url": assets[0].get("browser_download_url"),
                    }
                    return self.latest_info
        except Exception as e:
            print(f"[UpdateService] GitHub Releases check error: {e}")

        return None

    def download_and_install(self, download_url: Optional[str] = None) -> bool:
        if self.is_downloading:
            return True

        target_url = download_url or (self.latest_info or {}).get("download_url")
        if not target_url:
            info = self.check_for_updates()
            if not info:
                return False
            target_url = info["download_url"]

        self.is_downloading = True
        self.download_progress = 0

        try:
            temp_dir = os.path.join(tempfile.gettempdir(), "AutoCameraAI_Admin_Updates")
            os.makedirs(temp_dir, exist_ok=True)
            installer_path = os.path.join(temp_dir, SETUP_FILENAME)

            req = urllib.request.Request(target_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as response:
                total_size = int(response.headers.get("content-length") or 0)
                downloaded = 0
                chunk_size = 32768
                with open(installer_path, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            self.download_progress = int(downloaded * 100 / total_size)

            self.download_progress = 100
            self.is_downloading = False
            self._run_silent_installer(installer_path)
            return True
        except Exception as e:
            print(f"[UpdateService] Download/Install error: {e}")
            self.is_downloading = False
            return False

    def _run_silent_installer(self, installer_path: str):
        if sys.platform != "win32":
            return

        if getattr(sys, "frozen", False):
            app_exe = os.path.abspath(sys.executable)
            app_dir = os.path.dirname(app_exe)
        else:
            app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            app_exe = os.path.join(app_dir, "dist", "AutoCameraAI-Admin", EXE_NAME)

        bat_path = os.path.join(tempfile.gettempdir(), "run_autocamera_admin_update.bat")
        bat_content = f"""@echo off
timeout /T 2 /NOBREAK >nul
taskkill /F /T /IM "{EXE_NAME}" >nul 2>&1
"{installer_path}" /SILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS /DIR="{app_dir}"
timeout /T 2 /NOBREAK >nul
if exist "{app_exe}" (
    start "" /D "{app_dir}" "{app_exe}"
)
(goto) 2>nul & del "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        CREATE_NO_WINDOW = 0x08000000
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )
        os._exit(0)


update_service = UpdateService()
