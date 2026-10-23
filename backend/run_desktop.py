import sys
import os
import socket
import time
import threading
import subprocess
import multiprocessing
import traceback
import urllib.request

if getattr(sys, "frozen", False):
    app_root_dir = os.path.dirname(sys.executable)
    base_path = getattr(sys, "_MEIPASS", app_root_dir)
    os.chdir(app_root_dir)
    if base_path not in sys.path:
        sys.path.insert(0, base_path)
else:
    app_root_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = app_root_dir
    os.chdir(app_root_dir)
    if app_root_dir not in sys.path:
        sys.path.insert(0, app_root_dir)

logs_dir = os.path.join(app_root_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)
debug_log_path = os.path.join(logs_dir, "Admin_DebugLog.txt")

APP_PORT = 8388


def get_free_port(start_port=8388, max_port=8410) -> int:
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


def get_asset(filename: str) -> str:
    if getattr(sys, "frozen", False):
        p_exe = os.path.join(os.path.dirname(sys.executable), filename)
        if os.path.exists(p_exe):
            return p_exe
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, filename)
    return os.path.join(app_root_dir, filename)


def run_server(port: int):
    try:
        from app.main_core import app as main_app
        import uvicorn
        config = uvicorn.Config(main_app, host="127.0.0.1", port=port, log_config=None)
        server = uvicorn.Server(config)
        server.install_signal_handlers = lambda: None
        server.run()
    except Exception:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write("\n=== SERVER ERROR ===\n")
            f.write(traceback.format_exc())


def run_gui(port: int, is_silent: bool):
    import webview

    loading_path = get_asset("loading.html")
    loading_url = f"file:///{loading_path.replace(chr(92), '/')}" if os.path.exists(loading_path) else f"http://127.0.0.1:{port}"

    webview.settings["ALLOW_DOWNLOADS"] = True
    window = webview.create_window(
        "AutoCameraAI Admin",
        url=loading_url,
        width=1280,
        height=760,
        hidden=is_silent,
    )

    def wait_and_redirect(win):
        target_url = f"http://127.0.0.1:{port}"
        for _ in range(60):
            try:
                res = urllib.request.urlopen(f"{target_url}/api/system/version", timeout=1)
                if res.getcode() == 200:
                    win.load_url(target_url)
                    return
            except Exception:
                pass
            time.sleep(0.5)

    storage_dir = os.path.join(os.path.expanduser("~"), f".autocamera_admin_data_{port}")
    webview.start(func=wait_and_redirect, args=(window,), storage_path=storage_dir, private_mode=False)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    port = get_free_port(APP_PORT)
    is_silent = "--silent" in sys.argv or "--minimized" in sys.argv

    threading.Thread(target=run_server, args=(port,), daemon=True).start()
    run_gui(port, is_silent)
