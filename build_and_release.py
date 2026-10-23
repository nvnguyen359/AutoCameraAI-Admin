import os
import re
import json
import subprocess
import sys

GITHUB_REPO = "nvnguyen359/AutoCameraAI-Admin"
SPEC_FILE = "AutoCameraAI-Admin.spec"
ISS_FILE = "installer.iss"
SETUP_EXE_PATH = os.path.join("Output", "AutoCameraAI_Admin_Setup.exe")


def run_cmd(cmd, cwd=None, check=True):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if check and result.returncode != 0:
        print(f"Error executing: {cmd}")
        sys.exit(1)
    return result.returncode


def find_inno_setup():
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


def find_gh_cli():
    default_gh = r"C:\Program Files\GitHub CLI\gh.exe"
    if os.path.exists(default_gh):
        return f'"{default_gh}"'
    return "gh"


def main():
    print("=========================================")
    print("   STARTING BUILD AND RELEASE PIPELINE   ")
    print("=========================================")

    if not os.path.exists("main.py"):
        print("Error: main.py not found! Please add main.py before building.")
        sys.exit(1)

    # 1. Bump version in updater.py
    updater_path = "updater.py"
    with open(updater_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r'CURRENT_VERSION\s*=\s*"(.*?)"', content)
    if not match:
        print("Cannot find CURRENT_VERSION in updater.py")
        sys.exit(1)

    old_ver = match.group(1)
    parts = old_ver.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    new_ver = '.'.join(parts)

    print(f"\n[1/6] Bumping version: {old_ver} -> {new_ver}...")
    content = re.sub(
        r'CURRENT_VERSION\s*=\s*".*?"',
        f'CURRENT_VERSION = "{new_ver}"',
        content
    )
    with open(updater_path, "w", encoding="utf-8") as f:
        f.write(content)

    # 2. Update installer.iss AppVersion
    if os.path.exists(ISS_FILE):
        with open(ISS_FILE, "r", encoding="utf-8") as f:
            iss_content = f.read()
        iss_content = re.sub(r'AppVersion=.*', f'AppVersion={new_ver}', iss_content)
        with open(ISS_FILE, "w", encoding="utf-8") as f:
            f.write(iss_content)
        print(f"Updated {ISS_FILE} -> AppVersion={new_ver}")

    # 3. Update version.json
    version_json_path = "version.json"
    v_data = {
        "version": new_ver,
        "download_url": f"https://github.com/{GITHUB_REPO}/releases/download/v{new_ver}/AutoCameraAI_Admin_Setup.exe"
    }
    with open(version_json_path, "w", encoding="utf-8") as f:
        json.dump(v_data, f, indent=4)
    print(f"[2/6] Updated {version_json_path} -> v{new_ver}")

    # 4. Build PyInstaller EXE
    print(f"\n[3/6] Building PyInstaller ({SPEC_FILE})...")
    run_cmd(f'"{sys.executable}" -m PyInstaller {SPEC_FILE} --clean -y')

    # 5. Build Inno Setup Installer
    print(f"\n[4/6] Building Inno Setup ({ISS_FILE})...")
    inno_path = find_inno_setup()
    run_cmd(f'"{inno_path}" {ISS_FILE}')

    if not os.path.exists(SETUP_EXE_PATH):
        print(f"Error: Setup file not found at {SETUP_EXE_PATH}")
        sys.exit(1)

    # 6. Commit & Push source code + version.json to GitHub
    print(f"\n[5/6] Committing and pushing to {GITHUB_REPO}...")
    commit_msg = sys.argv[1] if len(sys.argv) > 1 else f"Release v{new_ver}"
    run_cmd("git add .")
    run_cmd(f'git commit -m "release: v{new_ver} - {commit_msg}"')
    run_cmd("git branch -M main")
    run_cmd("git push -u origin main")

    # 7. Create GitHub Release & Upload Setup EXE
    print(f"\n[6/6] Uploading {SETUP_EXE_PATH} to GitHub Releases (v{new_ver})...")
    gh_cmd = find_gh_cli()
    release_cmd = (
        f'{gh_cmd} release create v{new_ver} "{SETUP_EXE_PATH}" '
        f'--title "Release v{new_ver}" '
        f'--notes "{commit_msg}" '
        f'--repo {GITHUB_REPO}'
    )
    run_cmd(release_cmd)

    print("\n=========================================")
    print(f"DONE! Version v{new_ver} built and published to GitHub Releases!")
    print("=========================================")


if __name__ == "__main__":
    main()
