#!/usr/bin/env python3
"""
Claude 자동 승인 프로그램 - 고급 버전
Windows/Linux에서 특정 창을 찾아 자동으로 승인합니다.
"""

import time
import logging
import platform
from datetime import datetime, timedelta
from typing import Optional, List
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
    print("WARNING: psutil이 설치되어 있지 않습니다. 프로세스 감지 기능이 제한됩니다.")
    psutil = None

# Windows 전용 라이브러리
if platform.system() == 'Windows':
    try:
        import pygetwindow as gw
        HAS_WINDOW_SUPPORT = True
    except ImportError:
        print("INFO: pygetwindow가 설치되지 않았습니다. 창 감지 기능이 제한됩니다.")
        print("설치: pip install pygetwindow")
        HAS_WINDOW_SUPPORT = False
else:
    HAS_WINDOW_SUPPORT = False


class AdvancedAutoApprover:
    """고급 자동 승인 클래스"""

    def __init__(
        self,
        inactivity_timeout: int = 300,
        approval_responses: List[str] = None,
        check_interval: int = 10,
        target_processes: List[str] = None,
        window_titles: List[str] = None,
        enable_window_focus: bool = True,
        enable_notifications: bool = True
    ):
        """
        Args:
            inactivity_timeout: 자동 승인까지의 대기 시간 (초)
            approval_responses: 자동으로 입력할 응답 리스트
            check_interval: 활동 체크 간격 (초)
            target_processes: 대상 프로세스 이름 리스트
            window_titles: 대상 창 제목 키워드 리스트
            enable_window_focus: 창 포커스 기능 활성화
            enable_notifications: 알림 기능 활성화
        """
        self.inactivity_timeout = inactivity_timeout
        self.approval_responses = approval_responses or ['2', 'yes', 'y']
        self.check_interval = check_interval
        self.target_processes = target_processes or ['cmd', 'pycharm', 'terminal', 'python', 'claude']
        self.window_titles = window_titles or ['cmd', 'pycharm', 'terminal', 'python', 'claude', 'powershell']
        self.enable_window_focus = enable_window_focus and HAS_WINDOW_SUPPORT
        self.enable_notifications = enable_notifications

        self.last_activity_time = datetime.now()
        self.keyboard_controller = KeyboardController()
        self.is_running = False
        self.approval_count = 0
        self.last_approval_time = None

        # 통계
        self.stats = {
            'total_checks': 0,
            'total_approvals': 0,
            'total_window_focuses': 0,
            'start_time': datetime.now()
        }

        # 로깅 설정
        log_file = 'auto_approver_advanced.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def on_activity(self):
        """사용자 활동 감지 시 호출"""
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
        """비활성 시간 반환 (초)"""
        return (datetime.now() - self.last_activity_time).total_seconds()

    def find_target_window(self) -> Optional[object]:
        """대상 창 찾기 (Windows only)"""
        if not self.enable_window_focus:
            return None

        try:
            all_windows = gw.getAllWindows()
            for window in all_windows:
                window_title_lower = window.title.lower()
                for keyword in self.window_titles:
                    if keyword.lower() in window_title_lower:
                        self.logger.debug(f"대상 창 발견: {window.title}")
                        return window
        except Exception as e:
            self.logger.error(f"창 찾기 오류: {e}")

        return None

    def focus_window(self, window) -> bool:
        """창에 포커스 주기"""
        try:
            if window and not window.isMinimized:
                window.activate()
                self.stats['total_window_focuses'] += 1
                self.logger.info(f"창 활성화: {window.title}")
                time.sleep(0.5)
                return True
        except Exception as e:
            self.logger.error(f"창 포커스 오류: {e}")

        return False

    def is_target_process_running(self) -> bool:
        """대상 프로세스가 실행 중인지 확인"""
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

    def send_approval(self, response: str, window=None):
        """승인 응답 전송"""
        try:
            # 창 포커스
            if window and self.enable_window_focus:
                if not self.focus_window(window):
                    self.logger.warning("창 포커스 실패, 그래도 키 입력 시도...")

            self.logger.info(f"자동 승인 시도: '{response}'")
            time.sleep(0.5)

            # 응답 타입
            if response.isdigit():
                self.keyboard_controller.type(response)
            else:
                self.keyboard_controller.type(response)

            # Enter 키
            time.sleep(0.2)
            self.keyboard_controller.press(Key.enter)
            self.keyboard_controller.release(Key.enter)

            self.approval_count += 1
            self.stats['total_approvals'] += 1
            self.last_approval_time = datetime.now()

            self.logger.info(f"✅ 자동 승인 완료 (총 {self.approval_count}회)")

            # 승인 후 활동 시간 업데이트
            self.on_activity()

        except Exception as e:
            self.logger.error(f"❌ 자동 승인 실패: {e}")

    def show_notification(self, title: str, message: str):
        """알림 표시 (선택적)"""
        if not self.enable_notifications:
            return

        try:
            if platform.system() == 'Windows':
                # Windows 알림
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=5, threaded=True)
                except ImportError:
                    self.logger.debug("win10toast 미설치")
            elif platform.system() == 'Darwin':
                # macOS 알림
                os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
            else:
                # Linux 알림
                os.system(f'notify-send "{title}" "{message}"')
        except Exception as e:
            self.logger.debug(f"알림 표시 오류: {e}")

    def check_and_approve(self):
        """비활성 상태 확인 및 자동 승인"""
        self.stats['total_checks'] += 1
        inactive_duration = self.get_inactive_duration()

        if inactive_duration >= self.inactivity_timeout:
            if self.is_target_process_running():
                self.logger.info(
                    f"⚠️  사용자 비활성 감지 ({inactive_duration:.0f}초). "
                    f"자동 승인 시작..."
                )

                # 알림
                self.show_notification(
                    "🤖 Claude 자동 승인",
                    f"비활성 {inactive_duration:.0f}초 감지. 자동 승인 시작..."
                )

                # 대상 창 찾기
                target_window = self.find_target_window()
                if target_window:
                    self.logger.info(f"대상 창 발견: {target_window.title}")
                else:
                    self.logger.info("대상 창을 찾을 수 없어 현재 활성 창에 입력합니다.")

                # 모든 응답 시도
                for i, response in enumerate(self.approval_responses):
                    self.send_approval(response, target_window)
                    if i < len(self.approval_responses) - 1:
                        time.sleep(1)

                # 승인 완료 알림
                self.show_notification(
                    "✅ 자동 승인 완료",
                    f"{len(self.approval_responses)}개 응답 입력 완료"
                )

            else:
                self.logger.debug("대상 프로세스가 실행 중이지 않습니다.")

    def print_stats(self):
        """통계 출력"""
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()
        self.logger.info("=" * 60)
        self.logger.info("📊 실행 통계")
        self.logger.info("=" * 60)
        self.logger.info(f"실행 시간: {runtime:.0f}초 ({runtime/60:.1f}분)")
        self.logger.info(f"총 체크 횟수: {self.stats['total_checks']}")
        self.logger.info(f"총 승인 횟수: {self.stats['total_approvals']}")
        if self.enable_window_focus:
            self.logger.info(f"총 창 포커스 횟수: {self.stats['total_window_focuses']}")
        if self.last_approval_time:
            time_since_last = (datetime.now() - self.last_approval_time).total_seconds()
            self.logger.info(f"마지막 승인 이후: {time_since_last:.0f}초")
        self.logger.info("=" * 60)

    def start(self):
        """자동 승인 모니터링 시작"""
        self.is_running = True
        self.logger.info("=" * 60)
        self.logger.info("🤖 Claude 자동 승인 프로그램 - 고급 버전")
        self.logger.info("=" * 60)
        self.logger.info(f"시스템: {platform.system()} {platform.release()}")
        self.logger.info(f"비활성 타임아웃: {self.inactivity_timeout}초 ({self.inactivity_timeout/60:.1f}분)")
        self.logger.info(f"체크 간격: {self.check_interval}초")
        self.logger.info(f"승인 응답: {', '.join(self.approval_responses)}")
        self.logger.info(f"대상 프로세스: {', '.join(self.target_processes)}")
        if self.enable_window_focus:
            self.logger.info(f"대상 창 키워드: {', '.join(self.window_titles)}")
            self.logger.info("창 포커스: 활성화")
        else:
            self.logger.info("창 포커스: 비활성화")
        self.logger.info(f"알림: {'활성화' if self.enable_notifications else '비활성화'}")
        self.logger.info("=" * 60)

        # 시작 알림
        self.show_notification(
            "🤖 Claude 자동 승인 시작",
            f"타임아웃: {self.inactivity_timeout/60:.0f}분"
        )

        # 리스너 시작
        keyboard_listener = keyboard.Listener(on_press=self.on_press)
        mouse_listener = mouse.Listener(
            on_click=self.on_click,
            on_move=self.on_move
        )

        keyboard_listener.start()
        mouse_listener.start()

        try:
            last_stats_time = datetime.now()

            while self.is_running:
                self.check_and_approve()
                time.sleep(self.check_interval)

                # 1분마다 상태 로그
                if (datetime.now() - last_stats_time).total_seconds() >= 60:
                    inactive_mins = self.get_inactive_duration() / 60
                    self.logger.debug(
                        f"현재 상태 - 비활성: {inactive_mins:.1f}분, "
                        f"승인 횟수: {self.approval_count}, "
                        f"체크 횟수: {self.stats['total_checks']}"
                    )
                    last_stats_time = datetime.now()

        except KeyboardInterrupt:
            self.logger.info("\n⏹️  프로그램 종료 요청")
        finally:
            self.stop()
            keyboard_listener.stop()
            mouse_listener.stop()

    def stop(self):
        """자동 승인 모니터링 중지"""
        self.is_running = False
        self.print_stats()
        self.logger.info("🛑 Claude 자동 승인 프로그램 종료")
        self.show_notification(
            "🛑 Claude 자동 승인 종료",
            f"총 {self.approval_count}회 승인 완료"
        )


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Claude 자동 승인 프로그램 - 고급 버전'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='자동 승인까지의 대기 시간 (초, 기본값: 300 = 5분)'
    )
    parser.add_argument(
        '--responses',
        nargs='+',
        default=['2', 'yes', 'y'],
        help='자동으로 입력할 응답 리스트'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='활동 체크 간격 (초, 기본값: 10)'
    )
    parser.add_argument(
        '--processes',
        nargs='+',
        default=['cmd', 'pycharm', 'terminal', 'python', 'claude'],
        help='대상 프로세스 이름 리스트'
    )
    parser.add_argument(
        '--windows',
        nargs='+',
        default=['cmd', 'pycharm', 'terminal', 'python', 'claude', 'powershell'],
        help='대상 창 제목 키워드 리스트'
    )
    parser.add_argument(
        '--no-window-focus',
        action='store_true',
        help='창 포커스 기능 비활성화'
    )
    parser.add_argument(
        '--no-notifications',
        action='store_true',
        help='알림 기능 비활성화'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='디버그 모드 활성화'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # 자동 승인 인스턴스 생성 및 시작
    approver = AdvancedAutoApprover(
        inactivity_timeout=args.timeout,
        approval_responses=args.responses,
        check_interval=args.interval,
        target_processes=args.processes,
        window_titles=args.windows,
        enable_window_focus=not args.no_window_focus,
        enable_notifications=not args.no_notifications
    )

    approver.start()


if __name__ == '__main__':
    main()
