#!/usr/bin/env python3
"""
Claude 자동 승인 프로그램 테스트 스크립트
시뮬레이션 모드로 동작을 확인합니다.
"""

import time
from datetime import datetime


class AutoApproverSimulator:
    """자동 승인 시뮬레이터 (실제 키 입력 없이 테스트)"""

    def __init__(self, timeout=30, responses=None):
        self.timeout = timeout
        self.responses = responses or ['2', 'yes', 'y']
        self.last_activity = datetime.now()
        self.approval_count = 0

    def simulate_activity(self):
        """활동 시뮬레이션"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 사용자 활동 감지됨")
        self.last_activity = datetime.now()

    def get_inactive_duration(self):
        """비활성 시간 계산"""
        return (datetime.now() - self.last_activity).total_seconds()

    def simulate_approval(self):
        """승인 시뮬레이션"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  비활성 타임아웃 감지!")
        print(f"비활성 시간: {self.get_inactive_duration():.1f}초")
        print(f"{'='*60}")

        for response in self.responses:
            self.approval_count += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 자동 승인: '{response}' 입력 시뮬레이션")
            print(f"   → 총 승인 횟수: {self.approval_count}")
            time.sleep(0.5)

        # 승인 후 활동 시간 리셋
        self.simulate_activity()
        print()

    def run_test(self, duration=60):
        """테스트 실행"""
        print("="*60)
        print("🤖 Claude 자동 승인 프로그램 - 시뮬레이션 모드")
        print("="*60)
        print(f"설정:")
        print(f"  - 비활성 타임아웃: {self.timeout}초")
        print(f"  - 승인 응답: {', '.join(self.responses)}")
        print(f"  - 테스트 시간: {duration}초")
        print("="*60)
        print()

        start_time = datetime.now()
        check_count = 0

        try:
            while (datetime.now() - start_time).total_seconds() < duration:
                check_count += 1
                inactive = self.get_inactive_duration()

                # 상태 출력
                print(f"[체크 #{check_count}] 현재 비활성 시간: {inactive:.1f}초 / {self.timeout}초", end='')

                if inactive >= self.timeout:
                    print(" → 🚨 타임아웃!")
                    self.simulate_approval()
                else:
                    remaining = self.timeout - inactive
                    print(f" → ⏰ 남은 시간: {remaining:.1f}초")

                time.sleep(2)  # 2초마다 체크

        except KeyboardInterrupt:
            print("\n\n⏹️  테스트 중단됨")

        # 결과 출력
        print("\n" + "="*60)
        print("📊 테스트 결과")
        print("="*60)
        print(f"총 체크 횟수: {check_count}")
        print(f"총 승인 횟수: {self.approval_count}")
        print(f"실행 시간: {(datetime.now() - start_time).total_seconds():.1f}초")
        print("="*60)


def demo_with_activity():
    """활동이 있는 시나리오 데모"""
    print("\n\n" + "="*60)
    print("📝 시나리오 1: 중간에 사용자 활동이 발생하는 경우")
    print("="*60)
    print()

    sim = AutoApproverSimulator(timeout=10, responses=['2', 'yes'])

    print("5초 대기 중...")
    time.sleep(5)

    print("\n💡 사용자 활동 발생!")
    sim.simulate_activity()

    print("계속 대기 중...")
    time.sleep(6)

    print("\n비활성 확인...")
    if sim.get_inactive_duration() >= sim.timeout:
        sim.simulate_approval()
    else:
        print(f"아직 타임아웃 전입니다. (현재: {sim.get_inactive_duration():.1f}초)")


def demo_quick_timeout():
    """빠른 타임아웃 데모"""
    print("\n\n" + "="*60)
    print("📝 시나리오 2: 빠른 타임아웃 테스트 (5초)")
    print("="*60)
    print()

    sim = AutoApproverSimulator(timeout=5, responses=['2', 'yes', 'y'])

    print("5초 대기 중...")
    for i in range(5):
        print(f"  {i+1}초...")
        time.sleep(1)

    print("\n타임아웃 확인...")
    if sim.get_inactive_duration() >= sim.timeout:
        sim.simulate_approval()


def main():
    """메인 함수"""
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--scenario1':
            demo_with_activity()
            return
        elif sys.argv[1] == '--scenario2':
            demo_quick_timeout()
            return
        elif sys.argv[1] == '--full':
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            sim = AutoApproverSimulator(timeout=timeout)
            sim.run_test(duration=duration)
            return

    # 기본 데모
    print("🎯 Claude 자동 승인 프로그램 데모\n")
    print("사용 가능한 옵션:")
    print("  --scenario1  : 중간에 활동이 발생하는 시나리오")
    print("  --scenario2  : 빠른 타임아웃 테스트")
    print("  --full [duration] [timeout] : 전체 시뮬레이션")
    print()
    print("기본 데모 실행 중...\n")

    # 빠른 데모
    sim = AutoApproverSimulator(timeout=8, responses=['2', 'yes'])
    sim.run_test(duration=20)


if __name__ == '__main__':
    main()
