#!/bin/bash
# Claude 자동 승인 프로그램 사용 예시 스크립트

echo "=========================================="
echo "Claude Auto-Approver Example Usage"
echo "=========================================="
echo ""

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 예시 1: 빠른 테스트 (30초)
echo -e "${BLUE}예시 1: 빠른 테스트 (30초 타임아웃)${NC}"
echo "명령어: python auto_approver.py --timeout 30 --debug"
echo ""

# 예시 2: 기본 설정 (5분)
echo -e "${BLUE}예시 2: 기본 설정 (5분 타임아웃)${NC}"
echo "명령어: python auto_approver.py"
echo ""

# 예시 3: 점심 시간 자동화 (1시간)
echo -e "${BLUE}예시 3: 점심 시간 자동화 (1시간 타임아웃)${NC}"
echo "명령어: python auto_approver.py --timeout 3600 --responses yes"
echo ""

# 예시 4: 야간 자동화 (백그라운드)
echo -e "${BLUE}예시 4: 야간 자동화 (백그라운드 실행)${NC}"
echo "명령어: nohup python auto_approver.py --timeout 600 --responses 2 yes y confirm &"
echo ""

# 예시 5: PyCharm 전용
echo -e "${BLUE}예시 5: PyCharm 전용${NC}"
echo "명령어: python auto_approver.py --processes pycharm --responses 1 yes"
echo ""

# 예시 6: 커스텀 설정
echo -e "${BLUE}예시 6: 커스텀 설정${NC}"
echo "명령어: python auto_approver.py --timeout 180 --interval 5 --responses 2 yes ok --processes cmd python claude --debug"
echo ""

echo "=========================================="
echo -e "${GREEN}실행할 예시 번호를 선택하세요 (1-6):${NC}"
read -p "번호 입력: " choice

case $choice in
    1)
        echo -e "${YELLOW}예시 1 실행 중...${NC}"
        python auto_approver.py --timeout 30 --debug
        ;;
    2)
        echo -e "${YELLOW}예시 2 실행 중...${NC}"
        python auto_approver.py
        ;;
    3)
        echo -e "${YELLOW}예시 3 실행 중...${NC}"
        python auto_approver.py --timeout 3600 --responses yes
        ;;
    4)
        echo -e "${YELLOW}예시 4 실행 중...${NC}"
        nohup python auto_approver.py --timeout 600 --responses 2 yes y confirm &
        echo "백그라운드에서 실행 중입니다."
        echo "로그 확인: tail -f auto_approver.log"
        echo "프로세스 종료: pkill -f auto_approver.py"
        ;;
    5)
        echo -e "${YELLOW}예시 5 실행 중...${NC}"
        python auto_approver.py --processes pycharm --responses 1 yes
        ;;
    6)
        echo -e "${YELLOW}예시 6 실행 중...${NC}"
        python auto_approver.py --timeout 180 --interval 5 --responses 2 yes ok --processes cmd python claude --debug
        ;;
    *)
        echo -e "${YELLOW}잘못된 선택입니다. 프로그램을 종료합니다.${NC}"
        exit 1
        ;;
esac
