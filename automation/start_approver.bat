@echo off
REM Claude 자동 승인 프로그램 - Windows 실행 스크립트

echo ========================================
echo   Claude 자동 승인 프로그램
echo ========================================
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM Python 버전 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
    echo Python 3.7 이상을 설치해주세요: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python 확인 완료!
echo.

REM 의존성 확인
python -c "import pynput" >nul 2>&1
if %errorlevel% neq 0 (
    echo 필수 패키지가 설치되어 있지 않습니다.
    echo 설치 중...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: 패키지 설치 실패
        pause
        exit /b 1
    )
)

echo.
echo 실행 옵션을 선택하세요:
echo   1. 기본 버전 (5분 타임아웃)
echo   2. 기본 버전 (3분 타임아웃)
echo   3. 고급 버전 (5분 타임아웃, 창 포커스)
echo   4. 테스트 모드 (시뮬레이션)
echo   5. 커스텀 설정
echo   0. 종료
echo.

set /p choice="선택 (0-5): "

if "%choice%"=="1" (
    echo 기본 버전 실행 중... ^(5분 타임아웃^)
    python auto_approver.py --timeout 300
) else if "%choice%"=="2" (
    echo 기본 버전 실행 중... ^(3분 타임아웃^)
    python auto_approver.py --timeout 180
) else if "%choice%"=="3" (
    echo 고급 버전 실행 중... ^(5분 타임아웃^)
    pip install -q pygetwindow win10toast >nul 2>&1
    python auto_approver_advanced.py --timeout 300
) else if "%choice%"=="4" (
    echo 테스트 모드 실행 중...
    python test_auto_approver.py --scenario2
) else if "%choice%"=="5" (
    echo.
    set /p timeout="타임아웃 (초): "
    set /p responses="응답 (공백으로 구분, 예: 2 yes y): "
    echo 커스텀 설정으로 실행 중...
    python auto_approver.py --timeout %timeout% --responses %responses%
) else if "%choice%"=="0" (
    echo 종료합니다.
    exit /b 0
) else (
    echo 잘못된 선택입니다.
    pause
    exit /b 1
)

pause
