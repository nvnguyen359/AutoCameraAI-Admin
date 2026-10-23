import os
import re
import json
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
CLIENT_DIR = ROOT_DIR / "client"
BACKEND_DIR = ROOT_DIR / "backend"
CLIENT_DIST = BACKEND_DIR / "client"
HASH_FILE = CLIENT_DIST / ".frontend_build_hash"

GITHUB_REPO = "nvnguyen359/AutoCameraAI-Admin"
SPEC_FILE = "AutoCameraAI-Admin.spec"
ISS_FILE = "installer.iss"
SETUP_EXE_PATH = ROOT_DIR / "Output" / "AutoCameraAI_Admin_Setup.exe"


def run_cmd(cmd: str, cwd=None, check=True):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, shell=True)
    if check and result.returncode != 0:
        print(f"Error executing: {cmd}")
        sys.exit(1)
    return result.returncode


def compute_frontend_hash(src_dir: Path) -> str:
    if not src_dir.exists():
        return ""
    h = hashlib.md5()
    for p in sorted(src_dir.rglob("*")):
        if p.is_file():
            stat = p.stat()
            h.update(f"{p.relative_to(src_dir)}:{stat.st_size}:{int(stat.st_mtime)}|".encode("utf-8"))
    return h.hexdigest()


def find_inno_setup() -> str:
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 7\ISCC.exe",
        r"C:\Program Files\Inno Setup 7\ISCC.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    print("Cannot find Inno Setup Compiler (ISCC.exe)!")
    sys.exit(1)


def find_gh_cli() -> str:
    default_gh = r"C:\Program Files\GitHub CLI\gh.exe"
    if os.path.exists(default_gh):
        return f'"{default_gh}"'
    return "gh"


def main():
    print("==================================================")
    print("   AUTOCAMERA-ADMIN: BUILD & RELEASE PIPELINE     ")
    print("==================================================")

    # 1. Bump version in backend/version.txt & version.json
    version_txt_path = BACKEND_DIR / "version.txt"
    old_raw = version_txt_path.read_text(encoding="utf-8").strip() if version_txt_path.exists() else "v1.0.0"
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", old_raw)
    if not m:
        print(f"Invalid version format in {version_txt_path}: {old_raw}")
        sys.exit(1)

    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3)) + 1
    new_ver = f"{major}.{minor}.{patch}"
    new_tag = f"v{new_ver}"

    print(f"\n[1/6] Bumping version: {old_raw} -> {new_tag}...")
    version_txt_path.write_text(f"{new_tag}\n", encoding="utf-8")

    version_json_path = ROOT_DIR / "version.json"
    v_data = {
        "version": new_ver,
        "download_url": f"https://github.com/{GITHUB_REPO}/releases/download/{new_tag}/AutoCameraAI_Admin_Setup.exe",
    }
    version_json_path.write_text(json.dumps(v_data, indent=4) + "\n", encoding="utf-8")

    # 2. Build Angular Client (with smart hash cache)
    print("\n[2/6] Checking & Building Angular Client...")
    if not (CLIENT_DIR / "node_modules").exists():
        print("[*] Installing Angular dependencies (npm install)...")
        run_cmd("npm install", cwd=CLIENT_DIR)

    current_hash = compute_frontend_hash(CLIENT_DIR / "src")
    last_hash = HASH_FILE.read_text(encoding="utf-8").strip() if HASH_FILE.exists() else ""
    has_bundle = (CLIENT_DIST / "browser" / "index.html").is_file() or (CLIENT_DIST / "index.html").is_file()

    if has_bundle and current_hash and current_hash == last_hash:
        print(f"[*] Frontend unchanged (Hash: {current_hash[:10]}...) -> Skipping ng build!")
    else:
        print("[*] Building Angular Frontend -> backend/client...")
        run_cmd("npx ng build", cwd=CLIENT_DIR)
        CLIENT_DIST.mkdir(parents=True, exist_ok=True)
        if current_hash:
            HASH_FILE.write_text(current_hash, encoding="utf-8")

    # 3. Build Backend Python EXE with PyInstaller
    print(f"\n[3/6] Building Python Backend EXE ({SPEC_FILE})...")
    run_cmd(f'"{sys.executable}" -m PyInstaller {SPEC_FILE} --clean -y', cwd=BACKEND_DIR)

    # Ensure client & version.txt are synced into dist/AutoCameraAI-Admin
    dist_app_dir = BACKEND_DIR / "dist" / "AutoCameraAI-Admin"
    if CLIENT_DIST.exists():
        shutil.copytree(CLIENT_DIST, dist_app_dir / "client", dirs_exist_ok=True)
    shutil.copy2(version_txt_path, dist_app_dir / "version.txt")

    # 4. Build Inno Setup Installer
    print(f"\n[4/6] Building Inno Setup Installer ({ISS_FILE})...")
    inno_path = find_inno_setup()
    run_cmd(f'"{inno_path}" /DMyAppVersion="{new_ver}" {ISS_FILE}', cwd=BACKEND_DIR)

    if not SETUP_EXE_PATH.exists():
        print(f"Error: Setup file not found at {SETUP_EXE_PATH}")
        sys.exit(1)

    # 5. Commit & Push source + version.json to GitHub
    print(f"\n[5/6] Committing and pushing to {GITHUB_REPO}...")
    commit_msg = sys.argv[1] if len(sys.argv) > 1 else f"Release {new_tag}"
    run_cmd("git add .", cwd=ROOT_DIR)
    run_cmd(f'git commit -m "release: {new_tag} - {commit_msg}"', cwd=ROOT_DIR)
    run_cmd("git branch -M main", cwd=ROOT_DIR)
    run_cmd("git push -u origin main", cwd=ROOT_DIR)

    # 6. Upload Setup EXE to GitHub Releases
    print(f"\n[6/6] Uploading {SETUP_EXE_PATH.name} to GitHub Releases ({new_tag})...")
    gh_cmd = find_gh_cli()
    release_cmd = (
        f'{gh_cmd} release create {new_tag} "{SETUP_EXE_PATH}" '
        f'--title "Release {new_tag}" '
        f'--notes "{commit_msg}" '
        f'--repo {GITHUB_REPO}'
    )
    run_cmd(release_cmd, cwd=ROOT_DIR)

    print("\n==================================================")
    print(f"DONE! Version {new_tag} published to GitHub Releases!")
    print("==================================================")


if __name__ == "__main__":
    main()
