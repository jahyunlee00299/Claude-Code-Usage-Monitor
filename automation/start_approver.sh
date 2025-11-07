#!/bin/bash
# Claude 자동 승인 프로그램 - Linux/Mac 실행 스크립트

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  Claude 자동 승인 프로그램"
echo "========================================"
echo ""

# 현재 디렉토리로 이동
cd "$(dirname "$0")"

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python3이 설치되어 있지 않습니다.${NC}"
    echo "Python 3.7 이상을 설치해주세요."
    exit 1
fi

echo -e "${GREEN}Python 확인 완료!${NC}"
PYTHON_VERSION=$(python3 --version)
echo "버전: $PYTHON_VERSION"
echo ""

# 의존성 확인
if ! python3 -c "import pynput" 2>/dev/null; then
    echo -e "${YELLOW}필수 패키지가 설치되어 있지 않습니다.${NC}"
    echo "설치 중..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: 패키지 설치 실패${NC}"
        exit 1
    fi
    echo -e "${GREEN}패키지 설치 완료!${NC}"
    echo ""
fi

# 메뉴 표시
echo "실행 옵션을 선택하세요:"
echo "  1. 기본 버전 (5분 타임아웃)"
echo "  2. 기본 버전 (3분 타임아웃)"
echo "  3. 고급 버전 (5분 타임아웃, 창 포커스)"
echo "  4. 테스트 모드 (시뮬레이션)"
echo "  5. 백그라운드 실행 (5분 타임아웃)"
echo "  6. 커스텀 설정"
echo "  0. 종료"
echo ""

read -p "선택 (0-6): " choice

case $choice in
    1)
        echo -e "${BLUE}기본 버전 실행 중... (5분 타임아웃)${NC}"
        python3 auto_approver.py --timeout 300
        ;;
    2)
        echo -e "${BLUE}기본 버전 실행 중... (3분 타임아웃)${NC}"
        python3 auto_approver.py --timeout 180
        ;;
    3)
        echo -e "${BLUE}고급 버전 실행 중... (5분 타임아웃)${NC}"
        python3 auto_approver_advanced.py --timeout 300
        ;;
    4)
        echo -e "${BLUE}테스트 모드 실행 중...${NC}"
        python3 test_auto_approver.py --scenario2
        ;;
    5)
        echo -e "${BLUE}백그라운드 실행 중... (5분 타임아웃)${NC}"
        nohup python3 auto_approver.py --timeout 300 > /dev/null 2>&1 &
        PID=$!
        echo -e "${GREEN}백그라운드 프로세스 시작됨 (PID: $PID)${NC}"
        echo "로그 확인: tail -f auto_approver.log"
        echo "프로세스 종료: kill $PID 또는 pkill -f auto_approver"
        ;;
    6)
        echo ""
        read -p "타임아웃 (초): " timeout
        read -p "응답 (공백으로 구분, 예: 2 yes y): " responses
        echo -e "${BLUE}커스텀 설정으로 실행 중...${NC}"
        python3 auto_approver.py --timeout $timeout --responses $responses
        ;;
    0)
        echo -e "${YELLOW}종료합니다.${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}잘못된 선택입니다.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}프로그램 종료됨${NC}"
