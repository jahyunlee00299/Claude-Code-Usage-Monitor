#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 시작 프로그램에 Claude Monitor를 추가하는 스크립트
레지스트리를 통해 시스템 시작 시 자동 실행되도록 설정합니다.
"""

import os
import sys
import winreg
from pathlib import Path


def add_to_startup():
    """Windows 시작 프로그램에 Claude Monitor 추가"""

    # 레지스트리 키 경로
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "ClaudeMonitor"

    # Python 실행 경로와 claude-monitor 명령어 조합
    # 먼저 claude-monitor가 설치되어 있는지 확인
    try:
        # claude-monitor가 pip로 설치되어 있는 경우
        import claude_monitor
        # 트레이 모드로 실행하는 명령어
        app_path = f'"{sys.executable}" -m claude_monitor --tray'
    except ImportError:
        # 개발 모드에서 실행하는 경우
        project_dir = Path(__file__).parent.parent
        main_script = project_dir / "src" / "claude_monitor" / "cli" / "main.py"

        if main_script.exists():
            app_path = f'"{sys.executable}" "{main_script}" --tray'
        else:
            print("Error: Claude Monitor가 설치되어 있지 않습니다.")
            print("먼저 'pip install claude-monitor' 또는 'uv tool install claude-monitor'를 실행하세요.")
            return False

    try:
        # 레지스트리 키 열기
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_SET_VALUE
        )

        # 값 설정
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(key)

        print("[SUCCESS] Windows 시작 프로그램에 성공적으로 추가되었습니다!")
        print(f"   프로그램 이름: {app_name}")
        print(f"   실행 명령: {app_path}")
        print("\n다음 Windows 시작 시 자동으로 시스템 트레이에서 실행됩니다.")
        return True

    except PermissionError:
        print("[ERROR] 오류: 관리자 권한이 필요합니다.")
        print("   관리자 권한으로 실행하거나 시작 폴더 방법을 사용하세요.")
        return False
    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        return False


def remove_from_startup():
    """Windows 시작 프로그램에서 Claude Monitor 제거"""

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "ClaudeMonitor"

    try:
        # 레지스트리 키 열기
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_SET_VALUE
        )

        # 값 삭제
        try:
            winreg.DeleteValue(key, app_name)
            print(f"[SUCCESS] {app_name}이(가) 시작 프로그램에서 제거되었습니다.")
        except FileNotFoundError:
            print(f"[INFO] {app_name}이(가) 시작 프로그램에 등록되어 있지 않습니다.")

        winreg.CloseKey(key)
        return True

    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        return False


def check_startup_status():
    """현재 시작 프로그램 등록 상태 확인"""

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "ClaudeMonitor"

    try:
        # 레지스트리 키 열기 (읽기 전용)
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_READ
        )

        try:
            # 값 읽기
            value, _ = winreg.QueryValueEx(key, app_name)
            print(f"[SUCCESS] {app_name}이(가) 시작 프로그램에 등록되어 있습니다.")
            print(f"   실행 명령: {value}")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            print(f"[NOT FOUND] {app_name}이(가) 시작 프로그램에 등록되어 있지 않습니다.")
            winreg.CloseKey(key)
            return False

    except Exception as e:
        print(f"[ERROR] 상태 확인 중 오류 발생: {e}")
        return False


def main():
    """메인 함수"""

    # Windows가 아닌 경우 종료
    if sys.platform != "win32":
        print("이 스크립트는 Windows에서만 실행 가능합니다.")
        return

    print("=== Claude Monitor Windows 시작 프로그램 설정 ===\n")

    # 현재 상태 확인
    is_registered = check_startup_status()
    print()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--remove":
            remove_from_startup()
        elif sys.argv[1] == "--status":
            pass  # 이미 상태를 출력했음
        else:
            print("사용법:")
            print("  python add_to_startup.py        # 시작 프로그램에 추가")
            print("  python add_to_startup.py --remove   # 시작 프로그램에서 제거")
            print("  python add_to_startup.py --status   # 현재 상태 확인")
    else:
        # 기본 동작: 추가 또는 업데이트
        if is_registered:
            print("기존 등록을 업데이트하시겠습니까? (y/n): ", end="")
            response = input().strip().lower()
            if response == 'y':
                add_to_startup()
        else:
            add_to_startup()


if __name__ == "__main__":
    main()