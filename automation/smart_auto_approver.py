#!/usr/bin/env python3
"""
Claude 스마트 자동 승인 프로그램
프롬프트를 자동으로 분석하고 적절한 응답을 입력합니다.
"""

import time
import logging
import platform
import re
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import sys
import os

try:
    from pynput import keyboard, mouse
    from pynput.keyboard import Key, Controller as KeyboardController
except ImportError:
    print("ERROR: pynput이 설치되어 있지 않습니다.")
    print("설치 명령: pip install pynput")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("WARNING: psutil이 설치되어 있지 않습니다.")
    psutil = None

# Windows 전용
if platform.system() == 'Windows':
    try:
        import pygetwindow as gw
        import pyautogui
        HAS_WINDOW_SUPPORT = True
    except ImportError:
        print("INFO: pygetwindow 또는 pyautogui가 없습니다.")
        print("설치: pip install pygetwindow pyautogui")
        HAS_WINDOW_SUPPORT = False

    try:
        import pywinauto
        from pywinauto import Application
        HAS_PYWINAUTO = True
    except ImportError:
        print("INFO: pywinauto가 없습니다. 고급 창 제어가 제한됩니다.")
        print("설치: pip install pywinauto")
        HAS_PYWINAUTO = False
else:
    HAS_WINDOW_SUPPORT = False
    HAS_PYWINAUTO = False


class PromptPatternMatcher:
    """프롬프트 패턴 매칭 및 응답 생성"""

    def __init__(self):
        # Git 프롬프트 패턴
        self.git_patterns = {
            # Yes/No 질문
            r'Continue\?\s*\(Y/n\)': 'Y',
            r'Continue\?\s*\(y/N\)': 'y',
            r'Proceed\?\s*\(Y/n\)': 'Y',
            r'\(y/n\)': 'y',
            r'\(yes/no\)': 'yes',

            # 선택 옵션 (1, 2, 3...)
            r'Select\s+(\d+)\)': '1',  # 기본값 1
            r'Choose\s+option\s*\((\d+)-(\d+)\)': '1',
            r'Enter\s+number\s*\((\d+)-(\d+)\)': '1',

            # 확인
            r'Press\s+Enter\s+to\s+continue': '',  # Enter만
            r'Press\s+any\s+key': '',

            # Git 특정
            r'Merge\s+conflict': 'c',  # continue
            r'Accept\s+changes\?': 'y',
            r'Overwrite\?': 'y',
            r'Delete\s+branch\?': 'y',
            r'Push\s+to\s+remote\?': 'y',
        }

        # Claude 프롬프트 패턴
        self.claude_patterns = {
            r'Approve\?\s*\(y/n\)': 'y',
            r'Accept\?\s*\(y/n\)': 'y',
            r'Continue\s+with\s+this\s+action\?': 'y',
            r'Select\s+option:\s*1\).*2\)': '2',  # 기본적으로 2 선택
        }

        # CMD/PowerShell 패턴
        self.cmd_patterns = {
            r'Terminate\s+batch\s+job\s*\(Y/N\)': 'N',
            r'Delete\s+.*\s*\(Y/N\)': 'Y',
            r'Are\s+you\s+sure\s*\(Y/N\)': 'Y',
        }

        # PyCharm 패턴
        self.pycharm_patterns = {
            r'Confirm': 'Yes',
            r'Overwrite': 'Yes',
            r'Replace': 'Yes',
        }

    def analyze_prompt(self, text: str) -> Optional[str]:
        """프롬프트 텍스트 분석하고 적절한 응답 반환"""
        if not text:
            return None

        # 순서 보장을 위해 직접 매칭 (구체적 → 일반적)
        patterns_ordered = [
            # 1. CMD/PowerShell - 가장 구체적 (대문자 Y/N)
            (r'Terminate\s+batch\s+job\s*\(Y/N\)', 'N', 'CMD'),
            (r'Delete\s+.*\s*\(Y/N\)', 'Y', 'CMD'),
            (r'Are\s+you\s+sure\s*\(Y/N\)', 'Y', 'CMD'),

            # 2. Git 구체적 패턴
            (r'Press\s+Enter\s+to\s+continue', '', 'Git'),
            (r'Press\s+any\s+key', '', 'Git'),
            (r'Merge\s+conflict', 'c', 'Git'),

            # 3. Claude 선택 옵션
            (r'Select\s+option:\s*1\).*2\)', '2', 'Claude'),

            # 4. Git/일반 - Y/n 패턴 (Y 기본값)
            (r'Continue\?\s*\(Y/n\)', 'Y', 'Git'),
            (r'Proceed\?\s*\(Y/n\)', 'Y', 'Git'),
            (r'Overwrite.*\?\s*\(Y/n\)', 'Y', 'Git'),
            (r'\?\s*\(Y/n\)', 'Y', 'General'),

            # 5. Git/일반 - y/N 패턴 (y 선택, N 기본값)
            (r'Continue\?\s*\(y/N\)', 'y', 'Git'),
            (r'Proceed\?\s*\(y/N\)', 'y', 'Git'),
            (r'\?\s*\(y/N\)', 'y', 'General'),

            # 6. Git 구체적 질문들
            (r'Delete\s+branch\?', 'y', 'Git'),
            (r'Push\s+to\s+remote\?', 'y', 'Git'),
            (r'Accept\s+changes\?', 'y', 'Git'),
            (r'Overwrite\?', 'y', 'Git'),

            # 7. CMD 일반 Y/N
            (r'\(Y/N\)', 'Y', 'CMD'),

            # 8. 일반 y/n, yes/no
            (r'\(y/n\)', 'y', 'General'),
            (r'\(yes/no\)', 'yes', 'General'),

            # 9. PyCharm 패턴
            (r'Confirm', 'Yes', 'PyCharm'),
            (r'Overwrite', 'Yes', 'PyCharm'),
            (r'Replace', 'Yes', 'PyCharm'),

            # 10. 선택 옵션
            (r'Choose\s+option\s*\((\d+)-(\d+)\)', '1', 'General'),
            (r'Enter\s+number\s*\((\d+)-(\d+)\)', '1', 'General'),
        ]

        for pattern, response, category in patterns_ordered:
            if re.search(pattern, text, re.IGNORECASE):
                logging.info(f"프롬프트 감지: {category} - 패턴: {pattern}")
                return response

        return None


class SmartAutoApprover:
    """스마트 자동 승인 클래스"""

    def __init__(
        self,
        inactivity_timeout: int = 300,
        check_interval: int = 10,
        target_processes: List[str] = None,
        window_titles: List[str] = None,
        custom_responses: Dict[str, str] = None,
        enable_smart_detection: bool = True,
        enable_clipboard_check: bool = False
    ):
        """
        Args:
            inactivity_timeout: 자동 승인까지의 대기 시간 (초)
            check_interval: 활동 체크 간격 (초)
            target_processes: 대상 프로세스 이름 리스트
            window_titles: 대상 창 제목 키워드 리스트
            custom_responses: 커스텀 패턴-응답 매핑
            enable_smart_detection: 스마트 프롬프트 감지 활성화
            enable_clipboard_check: 클립보드 체크 활성화
        """
        self.inactivity_timeout = inactivity_timeout
        self.check_interval = check_interval
        self.target_processes = target_processes or [
            'cmd', 'powershell', 'git', 'bash', 'terminal',
            'pycharm', 'python', 'claude'
        ]
        self.window_titles = window_titles or [
            'cmd', 'powershell', 'git', 'bash', 'terminal',
            'pycharm', 'python', 'claude'
        ]
        self.enable_smart_detection = enable_smart_detection
        self.enable_clipboard_check = enable_clipboard_check

        self.last_activity_time = datetime.now()
        self.keyboard_controller = KeyboardController()
        self.is_running = False
        self.approval_count = 0

        # 프롬프트 매처
        self.prompt_matcher = PromptPatternMatcher()

        # 커스텀 패턴 추가
        if custom_responses:
            self.prompt_matcher.claude_patterns.update(custom_responses)

        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('smart_auto_approver.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # 통계
        self.stats = {
            'total_checks': 0,
            'total_approvals': 0,
            'smart_detections': 0,
            'fallback_responses': 0,
            'start_time': datetime.now()
        }

    def on_activity(self):
        """사용자 활동 감지"""
        self.last_activity_time = datetime.now()

    def on_press(self, key):
        """키보드 입력 감지"""
        self.on_activity()

    def on_click(self, x, y, button, pressed):
        """마우스 클릭 감지"""
        if pressed:
            self.on_activity()

    def on_move(self, x, y):
        """마우스 이동 감지"""
        self.on_activity()

    def get_inactive_duration(self) -> float:
        """비활성 시간 반환"""
        return (datetime.now() - self.last_activity_time).total_seconds()

    def find_target_window(self) -> Optional[object]:
        """대상 창 찾기"""
        if not HAS_WINDOW_SUPPORT:
            return None

        try:
            all_windows = gw.getAllWindows()
            for window in all_windows:
                title_lower = window.title.lower()
                for keyword in self.window_titles:
                    if keyword.lower() in title_lower and window.visible:
                        self.logger.debug(f"대상 창 발견: {window.title}")
                        return window
        except Exception as e:
            self.logger.error(f"창 찾기 오류: {e}")

        return None

    def read_window_text(self, window) -> Optional[str]:
        """
        창의 텍스트 읽기 (다양한 방법 시도)
        """
        text = None

        # 방법 1: pywinauto (가장 정확)
        if HAS_PYWINAUTO and platform.system() == 'Windows':
            try:
                # 창 핸들 가져오기
                hwnd = window._hWnd if hasattr(window, '_hWnd') else None
                if hwnd:
                    app = Application().connect(handle=hwnd)
                    # 텍스트 추출 시도
                    # 주의: 모든 창이 지원하는 것은 아님
                    text = "pywinauto를 통한 텍스트 읽기 구현 중"
            except Exception as e:
                self.logger.debug(f"pywinauto 읽기 실패: {e}")

        # 방법 2: 스크린샷 + OCR (pyautogui + pytesseract)
        # 주의: pytesseract는 별도 설치 필요
        try:
            import pytesseract
            from PIL import Image

            # 창 영역 캡처
            if window:
                screenshot = pyautogui.screenshot(
                    region=(window.left, window.top, window.width, window.height)
                )
                # OCR
                text = pytesseract.image_to_string(screenshot)
                self.logger.debug(f"OCR 텍스트: {text[:100]}...")
        except ImportError:
            self.logger.debug("pytesseract 미설치 - OCR 사용 불가")
        except Exception as e:
            self.logger.debug(f"OCR 읽기 실패: {e}")

        # 방법 3: 클립보드 (활성화된 경우)
        if self.enable_clipboard_check and not text:
            try:
                import pyperclip
                text = pyperclip.paste()
                self.logger.debug("클립보드에서 텍스트 읽기")
            except:
                pass

        return text

    def is_target_process_running(self) -> bool:
        """대상 프로세스 실행 확인"""
        if not psutil:
            return True

        try:
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'].lower()
                for target in self.target_processes:
                    if target.lower() in proc_name:
                        return True
        except Exception as e:
            self.logger.warning(f"프로세스 체크 오류: {e}")
            return True

        return False

    def send_response(self, response: str, window=None):
        """응답 전송"""
        try:
            # 창 포커스
            if window and HAS_WINDOW_SUPPORT:
                try:
                    window.activate()
                    time.sleep(0.5)
                except:
                    pass

            self.logger.info(f"📝 응답 입력: '{response}'")

            # 응답 타입
            if response:
                time.sleep(0.3)
                self.keyboard_controller.type(response)
                time.sleep(0.2)

            # Enter 키
            self.keyboard_controller.press(Key.enter)
            self.keyboard_controller.release(Key.enter)

            self.approval_count += 1
            self.stats['total_approvals'] += 1

            self.logger.info(f"✅ 응답 완료 (총 {self.approval_count}회)")
            self.on_activity()

        except Exception as e:
            self.logger.error(f"❌ 응답 실패: {e}")

    def check_and_approve(self):
        """스마트 체크 및 승인"""
        self.stats['total_checks'] += 1
        inactive_duration = self.get_inactive_duration()

        if inactive_duration >= self.inactivity_timeout:
            if not self.is_target_process_running():
                self.logger.debug("대상 프로세스 미실행")
                return

            self.logger.info(
                f"⚠️  비활성 감지 ({inactive_duration:.0f}초). "
                f"스마트 승인 시작..."
            )

            # 대상 창 찾기
            target_window = self.find_target_window()
            if not target_window:
                self.logger.warning("대상 창을 찾을 수 없습니다.")
                # 기본 응답 사용
                self.send_response('y')
                self.stats['fallback_responses'] += 1
                return

            self.logger.info(f"🎯 대상 창: {target_window.title}")

            # 스마트 감지 활성화된 경우
            if self.enable_smart_detection:
                # 창 텍스트 읽기
                window_text = self.read_window_text(target_window)

                if window_text:
                    # 프롬프트 분석
                    smart_response = self.prompt_matcher.analyze_prompt(window_text)

                    if smart_response is not None:
                        self.logger.info(f"🧠 스마트 감지 성공! 응답: '{smart_response}'")
                        self.send_response(smart_response, target_window)
                        self.stats['smart_detections'] += 1
                        return
                    else:
                        self.logger.warning("프롬프트 패턴 매칭 실패")

            # 기본 응답 (폴백)
            self.logger.info("기본 응답 사용: '2', 'yes', 'y'")
            for response in ['2', 'yes', 'y']:
                self.send_response(response, target_window)
                time.sleep(1)

            self.stats['fallback_responses'] += 1

    def print_stats(self):
        """통계 출력"""
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()
        self.logger.info("=" * 60)
        self.logger.info("📊 스마트 자동 승인 통계")
        self.logger.info("=" * 60)
        self.logger.info(f"실행 시간: {runtime:.0f}초 ({runtime/60:.1f}분)")
        self.logger.info(f"총 체크: {self.stats['total_checks']}")
        self.logger.info(f"총 승인: {self.stats['total_approvals']}")
        self.logger.info(f"스마트 감지 성공: {self.stats['smart_detections']}")
        self.logger.info(f"기본 응답 사용: {self.stats['fallback_responses']}")
        if self.stats['smart_detections'] > 0:
            success_rate = (self.stats['smart_detections'] /
                          max(self.stats['total_approvals'], 1)) * 100
            self.logger.info(f"스마트 감지 성공률: {success_rate:.1f}%")
        self.logger.info("=" * 60)

    def start(self):
        """모니터링 시작"""
        self.is_running = True
        self.logger.info("=" * 60)
        self.logger.info("🧠 Claude 스마트 자동 승인 프로그램")
        self.logger.info("=" * 60)
        self.logger.info(f"시스템: {platform.system()}")
        self.logger.info(f"타임아웃: {self.inactivity_timeout}초")
        self.logger.info(f"체크 간격: {self.check_interval}초")
        self.logger.info(f"대상 프로세스: {', '.join(self.target_processes)}")
        self.logger.info(f"스마트 감지: {'활성화' if self.enable_smart_detection else '비활성화'}")
        self.logger.info(f"창 지원: {'활성화' if HAS_WINDOW_SUPPORT else '비활성화'}")
        self.logger.info(f"고급 제어: {'활성화' if HAS_PYWINAUTO else '비활성화'}")
        self.logger.info("=" * 60)

        # 리스너 시작
        keyboard_listener = keyboard.Listener(on_press=self.on_press)
        mouse_listener = mouse.Listener(
            on_click=self.on_click,
            on_move=self.on_move
        )

        keyboard_listener.start()
        mouse_listener.start()

        try:
            while self.is_running:
                self.check_and_approve()
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("\n⏹️  프로그램 종료 요청")
        finally:
            self.stop()
            keyboard_listener.stop()
            mouse_listener.stop()

    def stop(self):
        """모니터링 중지"""
        self.is_running = False
        self.print_stats()
        self.logger.info("🛑 스마트 자동 승인 프로그램 종료")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Claude 스마트 자동 승인 프로그램 - 프롬프트를 자동으로 분석하고 적절한 응답을 입력합니다.'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='타임아웃 (초, 기본값: 300)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='체크 간격 (초, 기본값: 10)'
    )
    parser.add_argument(
        '--processes',
        nargs='+',
        default=['cmd', 'powershell', 'git', 'bash', 'terminal', 'pycharm', 'python'],
        help='대상 프로세스'
    )
    parser.add_argument(
        '--windows',
        nargs='+',
        default=['cmd', 'powershell', 'git', 'terminal', 'pycharm'],
        help='대상 창 키워드'
    )
    parser.add_argument(
        '--no-smart',
        action='store_true',
        help='스마트 감지 비활성화'
    )
    parser.add_argument(
        '--enable-clipboard',
        action='store_true',
        help='클립보드 체크 활성화'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='디버그 모드'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    approver = SmartAutoApprover(
        inactivity_timeout=args.timeout,
        check_interval=args.interval,
        target_processes=args.processes,
        window_titles=args.windows,
        enable_smart_detection=not args.no_smart,
        enable_clipboard_check=args.enable_clipboard
    )

    approver.start()


if __name__ == '__main__':
    main()
