#!/usr/bin/env python3
"""
Claude 자동 승인 프로그램
사용자가 5분 이상 자리를 비우면 자동으로 승인 프롬프트에 응답합니다.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional
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
    print("설치 명령: pip install psutil")
    psutil = None


class AutoApprover:
    """자동 승인 클래스"""

    def __init__(
        self,
        inactivity_timeout: int = 300,  # 5분 (초 단위)
        approval_responses: list = None,
        check_interval: int = 10,  # 10초마다 체크
        target_processes: list = None
    ):
        """
        Args:
            inactivity_timeout: 자동 승인까지의 대기 시간 (초)
            approval_responses: 자동으로 입력할 응답 리스트
            check_interval: 활동 체크 간격 (초)
            target_processes: 대상 프로세스 이름 리스트 (cmd, pycharm 등)
        """
        self.inactivity_timeout = inactivity_timeout
        self.approval_responses = approval_responses or ['2', 'yes', 'y']
        self.check_interval = check_interval
        self.target_processes = target_processes or ['cmd', 'pycharm', 'terminal', 'python']

        self.last_activity_time = datetime.now()
        self.keyboard_controller = KeyboardController()
        self.is_running = False
        self.approval_count = 0

        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('auto_approver.log'),
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

    def is_target_process_running(self) -> bool:
        """대상 프로세스가 실행 중인지 확인"""
        if not psutil:
            return True  # psutil이 없으면 항상 True 반환

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

    def send_approval(self, response: str):
        """승인 응답 전송"""
        try:
            self.logger.info(f"자동 승인 시도: '{response}'")

            # 응답 타입
            time.sleep(0.5)

            if response.isdigit():
                # 숫자인 경우
                self.keyboard_controller.type(response)
            else:
                # 문자열인 경우
                self.keyboard_controller.type(response)

            # Enter 키 입력
            time.sleep(0.2)
            self.keyboard_controller.press(Key.enter)
            self.keyboard_controller.release(Key.enter)

            self.approval_count += 1
            self.logger.info(f"자동 승인 완료 (총 {self.approval_count}회)")

            # 승인 후 활동 시간 업데이트
            self.on_activity()

        except Exception as e:
            self.logger.error(f"자동 승인 실패: {e}")

    def check_and_approve(self):
        """비활성 상태 확인 및 자동 승인"""
        inactive_duration = self.get_inactive_duration()

        if inactive_duration >= self.inactivity_timeout:
            if self.is_target_process_running():
                self.logger.info(
                    f"사용자 비활성 감지 ({inactive_duration:.0f}초). "
                    f"자동 승인 시작..."
                )

                # 모든 응답 시도
                for response in self.approval_responses:
                    self.send_approval(response)
                    time.sleep(1)  # 각 응답 사이 대기

            else:
                self.logger.debug("대상 프로세스가 실행 중이지 않습니다.")

    def start(self):
        """자동 승인 모니터링 시작"""
        self.is_running = True
        self.logger.info("=" * 60)
        self.logger.info("Claude 자동 승인 프로그램 시작")
        self.logger.info(f"비활성 타임아웃: {self.inactivity_timeout}초 ({self.inactivity_timeout/60:.1f}분)")
        self.logger.info(f"체크 간격: {self.check_interval}초")
        self.logger.info(f"승인 응답: {', '.join(self.approval_responses)}")
        self.logger.info(f"대상 프로세스: {', '.join(self.target_processes)}")
        self.logger.info("=" * 60)

        # 키보드 및 마우스 리스너 시작
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

                # 상태 로그 (1분마다)
                if int(self.get_inactive_duration()) % 60 == 0:
                    inactive_mins = self.get_inactive_duration() / 60
                    self.logger.debug(
                        f"현재 상태 - 비활성: {inactive_mins:.1f}분, "
                        f"승인 횟수: {self.approval_count}"
                    )

        except KeyboardInterrupt:
            self.logger.info("\n프로그램 종료 요청")
        finally:
            self.stop()
            keyboard_listener.stop()
            mouse_listener.stop()

    def stop(self):
        """자동 승인 모니터링 중지"""
        self.is_running = False
        self.logger.info("=" * 60)
        self.logger.info(f"총 자동 승인 횟수: {self.approval_count}")
        self.logger.info("Claude 자동 승인 프로그램 종료")
        self.logger.info("=" * 60)


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Claude 자동 승인 프로그램 - 사용자 부재 시 자동으로 승인 프롬프트에 응답합니다.'
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
        help='자동으로 입력할 응답 리스트 (기본값: 2 yes y)'
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
        '--debug',
        action='store_true',
        help='디버그 모드 활성화'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # 자동 승인 인스턴스 생성 및 시작
    approver = AutoApprover(
        inactivity_timeout=args.timeout,
        approval_responses=args.responses,
        check_interval=args.interval,
        target_processes=args.processes
    )

    approver.start()


if __name__ == '__main__':
    main()
