import json
import urllib.request
import os
import sys
import subprocess
import tempfile
import time
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QSystemTrayIcon

APP_NAME = "AutoCameraAI-Admin"
EXE_NAME = "AutoCameraAI-Admin.exe"
SETUP_FILENAME = "AutoCameraAI_Admin_Setup.exe"
CURRENT_VERSION = "1.0.0"
GITHUB_REPO = "nvnguyen359/AutoCameraAI-Admin"
VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json"


class UpdateCheckerThread(QThread):
    update_available = pyqtSignal(str, str)  # version, download_url
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            # Add cache-busting query param to ensure latest version.json is fetched
            url = f"{VERSION_URL}?t={int(time.time())}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))

                remote_version = data.get("version")
                download_url = data.get("download_url")

                if remote_version and download_url:
                    if self.is_newer(remote_version, CURRENT_VERSION):
                        self.update_available.emit(remote_version, download_url)
                    else:
                        self.no_update.emit()
                else:
                    self.no_update.emit()
        except Exception as e:
            print(f"Update check failed: {e}")
            self.error_occurred.emit(str(e))

    def is_newer(self, remote: str, local: str) -> bool:
        def parse_v(v: str):
            v = v.lstrip('vV').strip()
            return [int(x) for x in v.split('.')]
        try:
            return parse_v(remote) > parse_v(local)
        except Exception:
            return remote.strip() != local.strip()


class DownloaderThread(QThread):
    progress = pyqtSignal(int)
    progress_text = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url: str, version: str = None):
        super().__init__()
        self.url = url
        self.version = version

    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                total_length = response.headers.get('content-length')

                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, SETUP_FILENAME)

                ver_prefix = f" v{self.version}" if self.version else ""
                with open(file_path, 'wb') as f:
                    if total_length is None:
                        f.write(response.read())
                        self.progress.emit(100)
                        self.progress_text.emit(f"Đang tải bản cập nhật{ver_prefix}... 100%")
                    else:
                        total_length = int(total_length)
                        total_mb = total_length / (1024 * 1024)
                        downloaded = 0
                        chunk_size = 32768
                        last_emit_time = 0
                        while True:
                            buffer = response.read(chunk_size)
                            if not buffer:
                                break
                            downloaded += len(buffer)
                            f.write(buffer)
                            percent = int(downloaded * 100 / total_length)
                            self.progress.emit(percent)

                            now = time.time()
                            if now - last_emit_time > 0.08 or percent == 100:
                                last_emit_time = now
                                downloaded_mb = downloaded / (1024 * 1024)
                                self.progress_text.emit(
                                    f"Đang tải{ver_prefix}: {downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percent}%)"
                                )
                self.finished.emit(file_path)
        except Exception as e:
            self.error.emit(str(e))


def apply_update_and_restart(installer_path: str):
    """Chạy bộ cài đặt Inno Setup ở chế độ silent và tự khởi động lại ứng dụng."""
    if getattr(sys, 'frozen', False):
        app_exe = os.path.abspath(sys.executable)
        app_dir = os.path.dirname(app_exe)
    else:
        app_dir = os.path.abspath(os.path.dirname(__file__))
        app_exe = os.path.join(app_dir, "dist", APP_NAME, EXE_NAME)

    bat_path = os.path.join(tempfile.gettempdir(), "run_autocamera_admin_update.bat")
    bat_content = f"""@echo off
ping 127.0.0.1 -n 3 >nul
taskkill /f /im {EXE_NAME} >nul 2>&1
"{installer_path}" /SILENT /SP- /CLOSEAPPLICATIONS /DIR="{app_dir}"
ping 127.0.0.1 -n 2 >nul
tasklist /fi "IMAGENAME eq {EXE_NAME}" 2>nul | find /i "{EXE_NAME}" >nul
if errorlevel 1 (
    start "" "{app_exe}"
)
(goto) 2>nul & del "%~f0"
"""
    try:
        with open(bat_path, "w", encoding="cp1252", errors="replace") as f:
            f.write(bat_content)
    except Exception:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

    CREATE_NO_WINDOW = 0x08000000
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    subprocess.Popen(
        ["cmd.exe", "/c", bat_path],
        creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        close_fds=True
    )
    os._exit(0)
