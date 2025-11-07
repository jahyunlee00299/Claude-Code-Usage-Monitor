# 윈도우 작업표시줄 알림 영역(시스템 트레이) 기능 추가 가이드

## 개요

이 가이드는 Claude Code Usage Monitor를 윈도우 작업표시줄 우측 하단의 알림 영역(시스템 트레이)에 작게 표시하는 방법을 설명합니다.

## 필요한 라이브러리

### 1. pystray (추천)
가장 간단하고 가벼운 크로스 플랫폼 시스템 트레이 라이브러리입니다.

```bash
pip install pystray pillow
```

### 2. 대안: PyQt5 / PySide6
더 강력한 기능이 필요한 경우 Qt 기반 라이브러리를 사용할 수 있습니다.

```bash
pip install PyQt5
# 또는
pip install PySide6
```

## 구현 방법

### 방법 1: pystray 사용 (추천)

#### 1단계: 트레이 아이콘 이미지 준비

```python
# src/claude_monitor/ui/tray_icon.py
from PIL import Image, ImageDraw

def create_icon_image():
    """트레이 아이콘 이미지 생성"""
    # 64x64 아이콘 생성
    width = 64
    height = 64
    color1 = "#5865F2"  # Claude 테마 색상
    color2 = "white"

    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)

    # 'C' 글자 그리기 (Claude의 C)
    dc.ellipse([8, 8, 56, 56], fill=color2)
    dc.ellipse([16, 16, 48, 48], fill=color1)
    dc.rectangle([32, 16, 56, 48], fill=color1)

    return image
```

#### 2단계: 시스템 트레이 매니저 클래스 생성

```python
# src/claude_monitor/ui/system_tray.py
import pystray
from pystray import MenuItem as item
from PIL import Image
import threading
import logging
from typing import Optional, Dict, Any

from claude_monitor.monitoring.orchestrator import MonitoringOrchestrator
from claude_monitor.ui.tray_icon import create_icon_image

logger = logging.getLogger(__name__)


class SystemTrayManager:
    """시스템 트레이 관리 클래스"""

    def __init__(self, orchestrator: MonitoringOrchestrator):
        self.orchestrator = orchestrator
        self.icon: Optional[pystray.Icon] = None
        self.current_status = "대기 중..."
        self._stop_event = threading.Event()

    def create_menu(self):
        """트레이 메뉴 생성"""
        return pystray.Menu(
            item('상태 보기', self.show_status),
            item('설정', self.open_settings),
            pystray.Menu.SEPARATOR,
            item('실시간 모니터링', self.toggle_monitoring),
            pystray.Menu.SEPARATOR,
            item('종료', self.quit_app)
        )

    def show_status(self, icon, item):
        """현재 상태를 알림으로 표시"""
        try:
            # 최신 모니터링 데이터 가져오기
            data = self.orchestrator.get_current_data()
            if data and 'blocks' in data:
                blocks = data.get('blocks', [])
                active_blocks = [b for b in blocks if b.get('isActive')]

                if active_blocks:
                    block = active_blocks[0]
                    tokens = block.get('totalTokens', 0)
                    cost = block.get('totalCost', 0)
                    message = f"토큰: {tokens:,}\n비용: ${cost:.2f}"
                else:
                    message = "활성 세션이 없습니다"
            else:
                message = "데이터를 불러올 수 없습니다"

            # 윈도우 알림 표시
            self.icon.notify(message, "Claude 사용량 모니터")

        except Exception as e:
            logger.error(f"상태 표시 오류: {e}")
            self.icon.notify("오류가 발생했습니다", "Claude 모니터")

    def open_settings(self, icon, item):
        """설정 창 열기 (추후 구현)"""
        self.icon.notify("설정 기능은 개발 중입니다", "Claude 모니터")

    def toggle_monitoring(self, icon, item):
        """모니터링 시작/중지"""
        if self.orchestrator.is_running():
            self.orchestrator.stop()
            self.icon.notify("모니터링이 중지되었습니다", "Claude 모니터")
        else:
            self.orchestrator.start()
            self.icon.notify("모니터링이 시작되었습니다", "Claude 모니터")

    def quit_app(self, icon, item):
        """애플리케이션 종료"""
        logger.info("사용자가 트레이에서 종료를 선택했습니다")
        self.orchestrator.stop()
        self._stop_event.set()
        icon.stop()

    def update_tooltip(self, monitoring_data: Dict[str, Any]):
        """툴팁 업데이트 (마우스 오버 시 표시되는 텍스트)"""
        try:
            data = monitoring_data.get('data', {})
            blocks = data.get('blocks', [])
            active_blocks = [b for b in blocks if b.get('isActive')]

            if active_blocks and self.icon:
                block = active_blocks[0]
                tokens = block.get('totalTokens', 0)
                cost = block.get('totalCost', 0)
                self.icon.title = f"Claude 모니터 | 토큰: {tokens:,} | ${cost:.2f}"
            elif self.icon:
                self.icon.title = "Claude 모니터 | 활성 세션 없음"

        except Exception as e:
            logger.error(f"툴팁 업데이트 오류: {e}")

    def run(self):
        """시스템 트레이 실행"""
        try:
            # 아이콘 이미지 생성
            image = create_icon_image()

            # 트레이 아이콘 생성
            self.icon = pystray.Icon(
                "claude_monitor",
                image,
                "Claude Code Usage Monitor",
                self.create_menu()
            )

            # 모니터링 데이터 업데이트 콜백 등록
            self.orchestrator.register_update_callback(self.update_tooltip)

            # 모니터링 시작
            self.orchestrator.start()

            logger.info("시스템 트레이 모드로 시작합니다")

            # 트레이 아이콘 실행 (블로킹)
            self.icon.run()

        except Exception as e:
            logger.error(f"시스템 트레이 실행 오류: {e}", exc_info=True)
            raise

    def stop(self):
        """트레이 매니저 중지"""
        if self.icon:
            self.icon.stop()
        self.orchestrator.stop()
```

#### 3단계: CLI에 트레이 모드 추가

```python
# src/claude_monitor/cli/main.py에 추가

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point with direct pydantic-settings integration."""
    if argv is None:
        argv = sys.argv[1:]

    if "--version" in argv or "-v" in argv:
        print(f"claude-monitor {__version__}")
        return 0

    try:
        settings = Settings.load_with_last_used(argv)

        setup_environment()
        ensure_directories()

        if settings.log_file:
            setup_logging(settings.log_level, settings.log_file, disable_console=True)
        else:
            setup_logging(settings.log_level, disable_console=True)

        init_timezone(settings.timezone)

        args = settings.to_namespace()

        # 트레이 모드 확인
        if hasattr(args, 'tray') and args.tray:
            _run_tray_mode(args)
        else:
            _run_monitoring(args)

        return 0

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        return 0
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Monitor failed: {e}", exc_info=True)
        traceback.print_exc()
        return 1


def _run_tray_mode(args: argparse.Namespace) -> None:
    """시스템 트레이 모드 실행"""
    from claude_monitor.ui.system_tray import SystemTrayManager

    try:
        data_paths: List[Path] = discover_claude_data_paths()
        if not data_paths:
            print_themed("No Claude data directory found", style="error")
            return

        data_path: Path = data_paths[0]
        logger = logging.getLogger(__name__)
        logger.info(f"Using data path: {data_path}")

        # 오케스트레이터 생성
        orchestrator = MonitoringOrchestrator(
            update_interval=getattr(args, "refresh_rate", 10),
            data_path=str(data_path),
        )
        orchestrator.set_args(args)

        # 트레이 매니저 생성 및 실행
        tray_manager = SystemTrayManager(orchestrator)
        tray_manager.run()

    except Exception as e:
        logger.error(f"트레이 모드 실행 오류: {e}", exc_info=True)
        raise
```

#### 4단계: Settings에 트레이 옵션 추가

```python
# src/claude_monitor/core/settings.py에 추가

class Settings(BaseSettings):
    # 기존 필드들...

    tray: bool = Field(
        default=False,
        description="시스템 트레이 모드로 실행"
    )

    # CLI 인자 매핑에 추가
    model_config = SettingsConfigDict(
        # 기존 설정...
        cli_parse_args=True,
        cli_prog_name="claude-monitor",
    )
```

### 사용 방법

```bash
# 시스템 트레이 모드로 실행
claude-monitor --tray

# 특정 플랜과 함께 트레이 모드 실행
claude-monitor --tray --plan max5

# 트레이 모드 + 로그 파일
claude-monitor --tray --log-file ~/claude-monitor.log
```

## 방법 2: PyQt5 사용 (고급 기능)

PyQt5를 사용하면 더 풍부한 UI를 제공할 수 있습니다.

```python
# src/claude_monitor/ui/qt_tray.py
import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer


class QtSystemTray:
    """PyQt5 기반 시스템 트레이"""

    def __init__(self, orchestrator):
        self.app = QApplication(sys.argv)
        self.orchestrator = orchestrator

        # 트레이 아이콘 생성
        self.tray_icon = QSystemTrayIcon(QIcon('icon.png'), self.app)

        # 메뉴 생성
        menu = QMenu()

        status_action = QAction("상태 보기", self.app)
        status_action.triggered.connect(self.show_status)
        menu.addAction(status_action)

        quit_action = QAction("종료", self.app)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

        # 타이머 설정 (주기적 업데이트)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)  # 5초마다 업데이트

    def show_status(self):
        """상태 표시"""
        data = self.orchestrator.get_current_data()
        # 상태 윈도우 표시 로직

    def update_status(self):
        """주기적 상태 업데이트"""
        data = self.orchestrator.get_current_data()
        if data:
            # 툴팁 업데이트
            self.tray_icon.setToolTip(f"Claude Monitor - 토큰: {data.get('tokens', 0)}")

    def quit_app(self):
        """앱 종료"""
        self.orchestrator.stop()
        self.app.quit()

    def run(self):
        """트레이 실행"""
        self.tray_icon.show()
        self.orchestrator.start()
        sys.exit(self.app.exec_())
```

## 윈도우 시작 시 자동 실행 설정

### 1. 레지스트리 사용 (Python 스크립트)

```python
# scripts/add_to_startup.py
import os
import sys
import winreg

def add_to_startup():
    """윈도우 시작 프로그램에 추가"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "ClaudeMonitor"
    app_path = f'"{sys.executable}" -m claude_monitor --tray'

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(key)
        print("시작 프로그램에 성공적으로 추가되었습니다!")
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    add_to_startup()
```

### 2. 시작 폴더에 바로가기 생성

```python
# scripts/create_startup_shortcut.py
import os
import sys
from pathlib import Path

def create_startup_shortcut():
    """시작 폴더에 바로가기 생성"""
    try:
        from win32com.client import Dispatch

        startup_folder = Path(os.getenv('APPDATA')) / "Microsoft/Windows/Start Menu/Programs/Startup"
        shortcut_path = startup_folder / "ClaudeMonitor.lnk"

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.TargetPath = sys.executable
        shortcut.Arguments = "-m claude_monitor --tray"
        shortcut.WorkingDirectory = str(Path.home())
        shortcut.IconLocation = sys.executable
        shortcut.save()

        print(f"바로가기가 생성되었습니다: {shortcut_path}")
    except ImportError:
        print("pywin32가 필요합니다: pip install pywin32")
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    create_startup_shortcut()
```

## 추가 기능 구현 아이디어

### 1. 알림 기능
```python
def send_notification(title, message):
    """윈도우 알림 전송"""
    if self.icon:
        self.icon.notify(message, title)
```

### 2. 임계값 알림
```python
def check_thresholds(self, data):
    """토큰 사용량 임계값 확인"""
    tokens = data.get('totalTokens', 0)
    limit = data.get('tokenLimit', 0)

    if limit > 0:
        usage_percent = (tokens / limit) * 100

        if usage_percent >= 90:
            self.icon.notify(
                f"토큰 사용량: {usage_percent:.1f}%\n제한에 가까워졌습니다!",
                "⚠️ Claude 모니터 경고"
            )
```

### 3. 클릭 이벤트 처리
```python
def on_clicked(self, icon, item):
    """트레이 아이콘 클릭 시"""
    # 더블클릭: 상세 윈도우 열기
    # 단일클릭: 간단한 상태 표시
    pass
```

## 패키징 (실행 파일 만들기)

### PyInstaller 사용

```bash
# PyInstaller 설치
pip install pyinstaller

# 실행 파일 생성
pyinstaller --name="Claude Monitor" \
            --onefile \
            --windowed \
            --icon=icon.ico \
            --add-data "icon.png:." \
            src/claude_monitor/cli/main.py
```

### 설정 파일 예시 (claude_monitor.spec)
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/claude_monitor/cli/main.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.png', '.')],
    hiddenimports=['pystray', 'PIL'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ClaudeMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 콘솔 창 숨기기
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)
```

## 테스트

```bash
# 트레이 모드 테스트
python -m claude_monitor --tray

# 백그라운드 로그 확인
python -m claude_monitor --tray --log-file ~/claude-tray.log --log-level DEBUG
```

## 문제 해결

### 아이콘이 보이지 않는 경우
1. 윈도우 설정 > 시스템 > 알림 > "작업 표시줄에 표시할 아이콘 선택" 확인
2. 아이콘 이미지 형식 확인 (.ico 또는 .png)
3. 아이콘 크기 확인 (16x16 또는 32x32 권장)

### 알림이 표시되지 않는 경우
1. 윈도우 알림 설정 확인
2. 포커스 지원 모드 확인
3. 앱 알림 권한 확인

## 다음 단계

1. ✅ 기본 트레이 아이콘 구현
2. ✅ 메뉴 및 알림 기능
3. ⬜ 설정 UI 창 추가
4. ⬜ 차트/그래프 표시 기능
5. ⬜ 다중 세션 관리
6. ⬜ 테마 선택 기능

## 참고 자료

- [pystray 공식 문서](https://pystray.readthedocs.io/)
- [PyQt5 공식 문서](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Windows 알림 가이드](https://docs.microsoft.com/en-us/windows/apps/design/shell/tiles-and-notifications/)
