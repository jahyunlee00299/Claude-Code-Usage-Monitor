#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 시작 폴더에 Claude Monitor 바로가기를 생성하는 스크립트
pywin32 없이도 작동하는 PowerShell 기반 방법을 사용합니다.
"""

import os
import sys
import subprocess
from pathlib import Path


def create_shortcut_with_powershell(shortcut_path, target_path, arguments="", working_dir="", icon_location=""):
    """PowerShell을 사용하여 바로가기 생성"""

    # PowerShell 스크립트 생성
    ps_script = f"""
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target_path}"
$Shortcut.Arguments = "{arguments}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.IconLocation = "{icon_location}"
$Shortcut.Save()
"""

    try:
        # PowerShell 실행
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True
        else:
            print(f"PowerShell 오류: {result.stderr}")
            return False

    except Exception as e:
        print(f"PowerShell 실행 오류: {e}")
        return False


def create_startup_shortcut_pywin32():
    """pywin32를 사용한 바로가기 생성 (선택적)"""

    try:
        from win32com.client import Dispatch

        # 시작 폴더 경로
        startup_folder = Path(os.getenv('APPDATA')) / "Microsoft/Windows/Start Menu/Programs/Startup"
        startup_folder.mkdir(parents=True, exist_ok=True)

        shortcut_path = startup_folder / "ClaudeMonitor.lnk"

        # 바로가기 생성
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.TargetPath = sys.executable
        shortcut.Arguments = "-m claude_monitor --tray"
        shortcut.WorkingDirectory = str(Path.home())
        shortcut.IconLocation = sys.executable
        shortcut.save()

        return True, shortcut_path

    except ImportError:
        return False, None


def create_startup_shortcut():
    """시작 폴더에 바로가기 생성 (메인 함수)"""

    # 시작 폴더 경로
    startup_folder = Path(os.getenv('APPDATA')) / "Microsoft/Windows/Start Menu/Programs/Startup"
    startup_folder.mkdir(parents=True, exist_ok=True)

    shortcut_path = startup_folder / "ClaudeMonitor.lnk"

    # Python 실행 경로 확인
    python_exe = sys.executable

    # claude-monitor 설치 확인
    try:
        import claude_monitor
        arguments = "-m claude_monitor --tray"
    except ImportError:
        # 개발 모드
        project_dir = Path(__file__).parent.parent
        main_script = project_dir / "src" / "claude_monitor" / "cli" / "main.py"

        if main_script.exists():
            arguments = f'"{main_script}" --tray'
        else:
            print("Error: Claude Monitor가 설치되어 있지 않습니다.")
            print("먼저 'pip install claude-monitor' 또는 'uv tool install claude-monitor'를 실행하세요.")
            return False

    # 먼저 pywin32 방법 시도
    success, path = create_startup_shortcut_pywin32()

    if success:
        print(f"[SUCCESS] pywin32를 사용하여 바로가기가 생성되었습니다: {path}")
        return True

    # pywin32가 없으면 PowerShell 사용
    print("pywin32가 설치되어 있지 않습니다. PowerShell을 사용합니다...")

    success = create_shortcut_with_powershell(
        shortcut_path=str(shortcut_path),
        target_path=python_exe,
        arguments=arguments,
        working_dir=str(Path.home()),
        icon_location=python_exe
    )

    if success:
        print(f"[SUCCESS] 시작 폴더에 바로가기가 생성되었습니다:")
        print(f"   경로: {shortcut_path}")
        print(f"   대상: {python_exe}")
        print(f"   인수: {arguments}")
        print("\n다음 Windows 시작 시 자동으로 시스템 트레이에서 실행됩니다.")
        return True
    else:
        print("[ERROR] 바로가기 생성에 실패했습니다.")
        return False


def remove_startup_shortcut():
    """시작 폴더에서 바로가기 제거"""

    startup_folder = Path(os.getenv('APPDATA')) / "Microsoft/Windows/Start Menu/Programs/Startup"
    shortcut_path = startup_folder / "ClaudeMonitor.lnk"

    if shortcut_path.exists():
        try:
            shortcut_path.unlink()
            print(f"[SUCCESS] 바로가기가 제거되었습니다: {shortcut_path}")
            return True
        except Exception as e:
            print(f"[ERROR] 바로가기 제거 실패: {e}")
            return False
    else:
        print("[INFO] 바로가기가 존재하지 않습니다.")
        return False


def check_shortcut_status():
    """바로가기 존재 여부 확인"""

    startup_folder = Path(os.getenv('APPDATA')) / "Microsoft/Windows/Start Menu/Programs/Startup"
    shortcut_path = startup_folder / "ClaudeMonitor.lnk"

    if shortcut_path.exists():
        print(f"[SUCCESS] 바로가기가 존재합니다: {shortcut_path}")
        return True
    else:
        print("[NOT FOUND] 바로가기가 존재하지 않습니다.")
        return False


def open_startup_folder():
    """시작 폴더 열기"""

    startup_folder = Path(os.getenv('APPDATA')) / "Microsoft/Windows/Start Menu/Programs/Startup"

    try:
        os.startfile(str(startup_folder))
        print(f"[SUCCESS] 시작 폴더가 열렸습니다: {startup_folder}")
    except Exception as e:
        print(f"[ERROR] 시작 폴더 열기 실패: {e}")


def main():
    """메인 함수"""

    # Windows가 아닌 경우 종료
    if sys.platform != "win32":
        print("이 스크립트는 Windows에서만 실행 가능합니다.")
        return

    print("=== Claude Monitor 시작 폴더 바로가기 설정 ===\n")

    # 현재 상태 확인
    is_exists = check_shortcut_status()
    print()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--remove":
            remove_startup_shortcut()
        elif sys.argv[1] == "--status":
            pass  # 이미 상태를 출력했음
        elif sys.argv[1] == "--open":
            open_startup_folder()
        else:
            print("사용법:")
            print("  python create_startup_shortcut.py           # 바로가기 생성")
            print("  python create_startup_shortcut.py --remove  # 바로가기 제거")
            print("  python create_startup_shortcut.py --status  # 상태 확인")
            print("  python create_startup_shortcut.py --open    # 시작 폴더 열기")
    else:
        # 기본 동작: 생성 또는 업데이트
        if is_exists:
            print("기존 바로가기를 업데이트하시겠습니까? (y/n): ", end="")
            response = input().strip().lower()
            if response == 'y':
                remove_startup_shortcut()
                create_startup_shortcut()
        else:
            create_startup_shortcut()

        print("\nTip: pywin32를 설치하면 더 안정적으로 작동합니다:")
        print("  pip install pywin32")


if __name__ == "__main__":
    main()