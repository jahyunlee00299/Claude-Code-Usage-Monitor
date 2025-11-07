# 🚀 Claude 자동 승인 프로그램 - 빠른 시작 가이드

## 📦 설치 (단계별)

### 1단계: Python 확인

```bash
# Python 버전 확인 (3.7 이상 필요)
python --version
```

### 2단계: 프로젝트 클론

```bash
git clone <repository-url>
cd Claude-Code-Usage-Monitor/automation
```

### 3단계: 의존성 설치

#### 기본 버전 (모든 플랫폼)

```bash
pip install -r requirements.txt
```

#### 고급 버전 (Windows에서 권장)

```bash
pip install -r requirements_advanced.txt
```

## 🎯 사용 방법

### 방법 1: 기본 버전 (간단)

```bash
# 5분 타임아웃, 기본 설정
python auto_approver.py

# 커스텀 설정
python auto_approver.py --timeout 180 --responses 1 yes
```

**장점:**
- ✅ 간단하고 빠름
- ✅ 모든 플랫폼 지원
- ✅ 의존성 최소

**단점:**
- ❌ 창 포커스 기능 없음
- ❌ 알림 기능 없음

### 방법 2: 고급 버전 (Windows 권장)

```bash
# 기본 실행
python auto_approver_advanced.py

# 모든 기능 활성화
python auto_approver_advanced.py \
    --timeout 300 \
    --responses 2 yes y \
    --windows cmd pycharm python
```

**장점:**
- ✅ 자동 창 감지 및 포커스
- ✅ Windows 알림 지원
- ✅ 더 정확한 입력
- ✅ 상세한 통계

**단점:**
- ❌ 더 많은 의존성 필요

### 방법 3: 테스트 모드 (안전)

```bash
# 시뮬레이션 테스트 (실제 키 입력 없음)
python test_auto_approver.py --scenario2

# 전체 시뮬레이션 (25초 동안 테스트)
python test_auto_approver.py --full 25 10
```

## 💡 실전 시나리오

### 시나리오 1: PyCharm에서 개발 중

```bash
# PyCharm에서만 작동하도록 설정
python auto_approver_advanced.py \
    --timeout 180 \
    --responses 1 yes \
    --processes pycharm \
    --windows pycharm
```

### 시나리오 2: CMD/PowerShell 자동화

```bash
# CMD와 PowerShell에서 작동
python auto_approver_advanced.py \
    --timeout 300 \
    --responses 2 yes y \
    --processes cmd powershell \
    --windows cmd powershell
```

### 시나리오 3: 야간 자동화 (백그라운드)

```bash
# Windows
start /B python auto_approver_advanced.py --timeout 600

# Linux/Mac
nohup python auto_approver_advanced.py --timeout 600 &
```

### 시나리오 4: 빠른 테스트 (30초)

```bash
# 실제 키 입력 테스트
python auto_approver.py --timeout 30 --debug

# 시뮬레이션 테스트
python test_auto_approver.py --scenario2
```

## 🔧 고급 설정

### 환경 변수 사용

`.env` 파일 생성:

```env
AUTO_APPROVER_TIMEOUT=300
AUTO_APPROVER_RESPONSES=2,yes,y
AUTO_APPROVER_PROCESSES=cmd,pycharm,python
AUTO_APPROVER_CHECK_INTERVAL=10
```

### 설정 파일 사용 (config.json)

```json
{
  "timeout": 300,
  "responses": ["2", "yes", "y"],
  "processes": ["cmd", "pycharm", "python", "claude"],
  "windows": ["cmd", "pycharm", "python", "claude"],
  "check_interval": 10,
  "enable_window_focus": true,
  "enable_notifications": true
}
```

## 📊 로그 모니터링

### 실시간 로그 확인

```bash
# Linux/Mac
tail -f auto_approver.log

# Windows (PowerShell)
Get-Content auto_approver.log -Wait -Tail 20
```

### 로그 분석

```bash
# 승인 횟수 확인
grep "자동 승인 완료" auto_approver.log | wc -l

# 오류만 보기
grep ERROR auto_approver.log

# 최근 10개 이벤트
tail -10 auto_approver.log
```

## 🚨 문제 해결

### 문제 1: "pynput" 설치 오류

**해결:**
```bash
# 관리자 권한으로 설치
# Windows
pip install --user pynput

# Linux
sudo pip install pynput
```

### 문제 2: 키 입력이 작동하지 않음

**원인:**
- 대상 창이 포커스되지 않음
- 프로그램이 관리자 권한 필요

**해결:**
```bash
# Windows: 관리자 권한으로 실행
# PowerShell을 관리자 권한으로 열고
python auto_approver_advanced.py

# 또는 창 포커스 기능 사용
python auto_approver_advanced.py --windows cmd pycharm
```

### 문제 3: "pygetwindow" 오류 (Windows)

**해결:**
```bash
# Windows 전용 패키지 설치
pip install pygetwindow pywin32
```

### 문제 4: 프로그램이 너무 자주 승인함

**해결:**
```bash
# 타임아웃을 늘림
python auto_approver.py --timeout 600  # 10분

# 체크 간격을 늘림
python auto_approver.py --interval 30  # 30초마다 체크
```

### 문제 5: 백그라운드 프로세스 종료 방법

```bash
# Windows
tasklist | findstr python
taskkill /F /PID <PID>

# Linux/Mac
ps aux | grep auto_approver
kill <PID>

# 또는
pkill -f auto_approver
```

## 🎓 팁과 트릭

### Tip 1: 작업 스케줄러로 자동 시작 (Windows)

1. 작업 스케줄러 열기
2. "기본 작업 만들기" 클릭
3. 트리거: "컴퓨터 시작 시"
4. 동작: 프로그램 시작
5. 프로그램: `python.exe`
6. 인수: `C:\path\to\auto_approver_advanced.py --timeout 300`

### Tip 2: systemd 서비스로 실행 (Linux)

`/etc/systemd/system/claude-auto-approver.service`:

```ini
[Unit]
Description=Claude Auto Approver
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/automation
ExecStart=/usr/bin/python3 auto_approver_advanced.py --timeout 300
Restart=always

[Install]
WantedBy=multi-user.target
```

활성화:
```bash
sudo systemctl daemon-reload
sudo systemctl enable claude-auto-approver
sudo systemctl start claude-auto-approver
```

### Tip 3: 단축키로 빠르게 실행 (Windows)

1. `auto_approver.bat` 생성:
   ```batch
   @echo off
   cd /d "%~dp0"
   python auto_approver_advanced.py --timeout 300
   pause
   ```

2. 바로가기 만들기
3. 바로가기 속성 → 바로가기 키 설정 (예: Ctrl+Alt+A)

### Tip 4: 특정 시간에만 실행 (Python 스크립트)

```python
from datetime import datetime
import subprocess

# 오후 1시~5시에만 실행
current_hour = datetime.now().hour
if 13 <= current_hour < 17:
    subprocess.run(['python', 'auto_approver.py', '--timeout', '300'])
else:
    print("작동 시간이 아닙니다.")
```

## 📈 성능 최적화

### CPU 사용량 줄이기

```bash
# 체크 간격을 늘림
python auto_approver.py --interval 20  # 20초마다

# 마우스 이동 감지 비활성화 (코드 수정 필요)
```

### 메모리 사용량 줄이기

```bash
# 기본 버전 사용 (고급 기능 없음)
python auto_approver.py  # 대신 auto_approver_advanced.py
```

## 🔐 보안 권장사항

1. **신뢰할 수 있는 환경에서만 사용**
   - 테스트 환경
   - 개발 환경
   - 개인 PC

2. **로그 파일 보호**
   ```bash
   # 로그 파일 권한 설정
   chmod 600 auto_approver.log
   ```

3. **자동 시작 비활성화**
   - 필요할 때만 수동으로 실행
   - 작업 완료 후 종료

4. **프로세스 제한**
   ```bash
   # 특정 프로세스만 대상으로 지정
   python auto_approver.py --processes my_safe_app
   ```

## 📚 추가 리소스

- [Python pynput 문서](https://pynput.readthedocs.io/)
- [psutil 문서](https://psutil.readthedocs.io/)
- [pygetwindow 문서](https://pygetwindow.readthedocs.io/)

## 🆘 도움이 필요하신가요?

1. **로그 파일 확인**: `auto_approver.log` 또는 `auto_approver_advanced.log`
2. **디버그 모드 실행**: `python auto_approver.py --debug`
3. **이슈 리포트**: GitHub 이슈 트래커에 문의

---

**Happy Automating!** 🎉
