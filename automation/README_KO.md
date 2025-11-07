# 🤖 Claude 자동 승인 프로그램

사용자가 5분 이상 자리를 비우면 자동으로 승인 프롬프트에 응답하는 스마트 자동화 도구입니다.

## 📋 목차

- [기능 소개](#-기능-소개)
- [작동 원리](#-작동-원리)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [설정 옵션](#-설정-옵션)
- [사용 예시](#-사용-예시)
- [보안 고려사항](#-보안-고려사항)
- [문제 해결](#-문제-해결)

## ✨ 기능 소개

### 주요 기능

- **🕐 자동 활동 감지**: 키보드, 마우스 활동을 실시간으로 모니터링
- **⏰ 타임아웃 설정**: 사용자 정의 대기 시간 (기본값: 5분)
- **⌨️ 자동 키 입력**: 승인 프롬프트에 자동으로 "2", "yes" 등 입력
- **🎯 프로세스 감지**: CMD, PyCharm, Terminal 등 대상 프로그램 자동 감지
- **📊 로깅 시스템**: 모든 활동을 파일로 기록
- **🔧 커스터마이징**: 응답, 타임아웃, 체크 간격 등 모든 것을 설정 가능

### 사용 시나리오

1. **긴 작업 중 자리를 비워야 할 때**
   - 회의, 점심 식사, 휴식 시간
   - 자동으로 승인 프롬프트에 응답

2. **야간 자동화 작업**
   - 밤새 실행되는 스크립트
   - 주기적인 승인이 필요한 작업

3. **반복적인 승인 작업**
   - 여러 번의 승인이 필요한 배치 작업
   - 테스트 자동화

## 🔍 작동 원리

### 시스템 아키텍처

```
┌─────────────────────────────────────────┐
│         사용자 활동 모니터링             │
│   (키보드 입력, 마우스 클릭/이동)        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       비활성 시간 계산 엔진              │
│   (마지막 활동으로부터 경과 시간 측정)   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      타임아웃 체크 (기본: 5분)          │
│         비활성 시간 >= 설정 시간?       │
└──────────────┬──────────────────────────┘
               │ YES
               ▼
┌─────────────────────────────────────────┐
│       대상 프로세스 확인                 │
│   (CMD, PyCharm, Terminal 등)           │
└──────────────┬──────────────────────────┘
               │ 실행 중
               ▼
┌─────────────────────────────────────────┐
│        자동 키 입력 실행                 │
│   (설정된 응답: "2", "yes", "y" 등)     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      로그 기록 및 카운터 업데이트        │
│        (승인 횟수, 시간 등 기록)         │
└─────────────────────────────────────────┘
```

### 활동 감지 메커니즘

1. **키보드 리스너**: 모든 키 입력을 감지
2. **마우스 리스너**: 클릭 및 이동을 감지
3. **타임스탬프 업데이트**: 활동 발생 시 마지막 활동 시간 갱신
4. **주기적 체크**: 설정된 간격(기본 10초)마다 비활성 시간 확인

## 🚀 설치 방법

### 1. 필수 요구사항

- Python 3.7 이상
- pip (Python 패키지 관리자)

### 2. 의존성 설치

```bash
# automation 디렉토리로 이동
cd automation

# 필수 패키지 설치
pip install -r requirements.txt
```

또는 개별 설치:

```bash
pip install pynput psutil
```

### 3. 스크립트 실행 권한 부여 (Linux/Mac)

```bash
chmod +x auto_approver.py
```

## 📖 사용 방법

### 기본 사용

```bash
# 기본 설정으로 실행 (5분 타임아웃)
python auto_approver.py

# 또는 실행 권한이 있는 경우
./auto_approver.py
```

### 백그라운드 실행

```bash
# Linux/Mac
nohup python auto_approver.py &

# 로그 파일 확인
tail -f auto_approver.log
```

### 프로그램 종료

```bash
# Ctrl+C를 눌러서 안전하게 종료
# 또는 백그라운드 프로세스 종료
pkill -f auto_approver.py
```

## ⚙️ 설정 옵션

### 명령줄 인자

| 옵션 | 설명 | 기본값 | 예시 |
|------|------|--------|------|
| `--timeout` | 자동 승인까지의 대기 시간 (초) | 300 (5분) | `--timeout 600` (10분) |
| `--responses` | 자동으로 입력할 응답 리스트 | `2 yes y` | `--responses 1 yes ok` |
| `--interval` | 활동 체크 간격 (초) | 10 | `--interval 5` |
| `--processes` | 대상 프로세스 이름 리스트 | `cmd pycharm terminal python claude` | `--processes cmd python` |
| `--debug` | 디버그 모드 활성화 | False | `--debug` |

### 상세 옵션 설명

#### 1. 타임아웃 설정 (`--timeout`)

사용자 비활성 후 자동 승인까지의 대기 시간을 설정합니다.

```bash
# 3분 (180초)
python auto_approver.py --timeout 180

# 10분 (600초)
python auto_approver.py --timeout 600

# 30초 (테스트용)
python auto_approver.py --timeout 30
```

#### 2. 승인 응답 커스터마이징 (`--responses`)

자동으로 입력할 응답을 지정합니다. 여러 개를 순차적으로 입력할 수 있습니다.

```bash
# "1"만 입력
python auto_approver.py --responses 1

# "yes"와 "ok" 입력
python auto_approver.py --responses yes ok

# 숫자와 텍스트 혼합
python auto_approver.py --responses 2 yes confirm
```

#### 3. 체크 간격 설정 (`--interval`)

비활성 상태를 확인하는 주기를 설정합니다.

```bash
# 5초마다 체크 (더 빠른 응답)
python auto_approver.py --interval 5

# 30초마다 체크 (CPU 부하 감소)
python auto_approver.py --interval 30
```

#### 4. 대상 프로세스 지정 (`--processes`)

자동 승인을 수행할 대상 프로그램을 지정합니다.

```bash
# CMD와 Python만
python auto_approver.py --processes cmd python

# PyCharm만
python auto_approver.py --processes pycharm

# 모든 터미널 프로그램
python auto_approver.py --processes cmd powershell terminal bash
```

## 💡 사용 예시

### 예시 1: 빠른 테스트 (30초)

```bash
# 30초 후 자동 승인 테스트
python auto_approver.py --timeout 30 --debug
```

**사용 시나리오**: 프로그램이 제대로 작동하는지 빠르게 확인

### 예시 2: 점심 시간 자동화 (1시간)

```bash
# 1시간 타임아웃, "yes"만 입력
python auto_approver.py --timeout 3600 --responses yes
```

**사용 시나리오**: 점심 식사 중 긴 작업 자동 승인

### 예시 3: 야간 자동화

```bash
# 10분 타임아웃, 여러 응답
nohup python auto_approver.py --timeout 600 --responses 2 yes y confirm &
```

**사용 시나리오**: 밤새 실행되는 배치 작업

### 예시 4: PyCharm 전용

```bash
# PyCharm에서만 작동
python auto_approver.py --processes pycharm --responses 1 yes
```

**사용 시나리오**: PyCharm에서 개발 중 반복적인 승인 작업

### 예시 5: 커스텀 설정

```bash
# 3분 타임아웃, 5초마다 체크, 디버그 모드
python auto_approver.py \
    --timeout 180 \
    --interval 5 \
    --responses 2 yes ok \
    --processes cmd python claude \
    --debug
```

**사용 시나리오**: 세밀한 제어가 필요한 프로젝트

## 🔒 보안 고려사항

### ⚠️ 중요한 보안 주의사항

1. **자동 승인의 위험성**
   - 이 프로그램은 사용자 확인 없이 자동으로 승인을 수행합니다
   - 중요한 작업이나 민감한 데이터 처리 시 주의가 필요합니다
   - 프로그램이 의도하지 않은 작업을 승인할 수 있습니다

2. **권장 사용 환경**
   - ✅ 테스트 환경
   - ✅ 개발 환경
   - ✅ 반복적이고 안전한 작업
   - ❌ 프로덕션 환경
   - ❌ 중요한 시스템 변경
   - ❌ 금융 거래 등 민감한 작업

3. **로그 관리**
   - 모든 자동 승인 활동은 `auto_approver.log`에 기록됩니다
   - 정기적으로 로그를 확인하여 예상치 못한 동작을 감지하세요
   - 로그 파일에 민감한 정보가 포함될 수 있으니 주의하세요

4. **접근 권한**
   - 프로그램이 실행 중인 시스템에 물리적/원격 접근을 제한하세요
   - 다른 사용자가 이 프로그램을 악용할 수 없도록 관리하세요

### 🛡️ 안전한 사용 가이드

```bash
# 1. 항상 로그를 확인하세요
tail -f auto_approver.log

# 2. 짧은 타임아웃으로 시작하세요
python auto_approver.py --timeout 60  # 1분부터 시작

# 3. 디버그 모드로 동작을 확인하세요
python auto_approver.py --debug

# 4. 특정 프로세스만 대상으로 지정하세요
python auto_approver.py --processes my_safe_app

# 5. 테스트 환경에서 먼저 사용하세요
python auto_approver.py --timeout 30 --debug  # 테스트
```

## 🐛 문제 해결

### 자주 발생하는 문제

#### 1. `pynput` 설치 오류

**증상**: `ImportError: No module named 'pynput'`

**해결**:
```bash
pip install pynput

# 또는 관리자 권한으로
sudo pip install pynput  # Linux/Mac
```

#### 2. 권한 오류 (Linux)

**증상**: `Permission denied` 또는 키보드 입력이 작동하지 않음

**해결**:
```bash
# 사용자를 input 그룹에 추가
sudo usermod -a -G input $USER

# 로그아웃 후 다시 로그인
```

#### 3. `psutil` 설치 오류

**증상**: `WARNING: psutil이 설치되어 있지 않습니다`

**해결**:
```bash
pip install psutil
```

**참고**: psutil이 없어도 프로그램은 작동하지만, 프로세스 감지 기능이 제한됩니다.

#### 4. 자동 승인이 작동하지 않음

**가능한 원인 및 해결**:

1. **대상 프로세스가 실행 중이 아님**
   ```bash
   # 실행 중인 프로세스 확인
   ps aux | grep -E 'cmd|pycharm|python'

   # 대상 프로세스 직접 지정
   python auto_approver.py --processes 실제프로세스명
   ```

2. **타임아웃이 너무 길음**
   ```bash
   # 짧은 타임아웃으로 테스트
   python auto_approver.py --timeout 30 --debug
   ```

3. **활동이 계속 감지됨**
   ```bash
   # 로그를 확인하여 활동 감지 상태 확인
   tail -f auto_approver.log
   ```

#### 5. 로그 파일 권한 문제

**증상**: `PermissionError: [Errno 13] Permission denied: 'auto_approver.log'`

**해결**:
```bash
# 로그 파일 권한 변경
chmod 644 auto_approver.log

# 또는 다른 위치에 로그 저장 (코드 수정 필요)
```

### 디버그 모드 사용

문제가 지속되면 디버그 모드를 활성화하여 자세한 정보를 확인하세요:

```bash
python auto_approver.py --debug
```

디버그 모드에서는 다음 정보를 확인할 수 있습니다:
- 현재 비활성 시간
- 프로세스 감지 상태
- 키 입력 시도
- 오류 스택 트레이스

### 로그 파일 분석

```bash
# 최근 로그 확인
tail -20 auto_approver.log

# 오류만 필터링
grep ERROR auto_approver.log

# 자동 승인 횟수 확인
grep "자동 승인 완료" auto_approver.log | wc -l
```

## 📊 로그 예시

### 정상 동작 로그

```
2025-11-07 18:00:00 - INFO - ============================================================
2025-11-07 18:00:00 - INFO - Claude 자동 승인 프로그램 시작
2025-11-07 18:00:00 - INFO - 비활성 타임아웃: 300초 (5.0분)
2025-11-07 18:00:00 - INFO - 체크 간격: 10초
2025-11-07 18:00:00 - INFO - 승인 응답: 2, yes, y
2025-11-07 18:00:00 - INFO - 대상 프로세스: cmd, pycharm, terminal, python
2025-11-07 18:00:00 - INFO - ============================================================
2025-11-07 18:05:30 - INFO - 사용자 비활성 감지 (330초). 자동 승인 시작...
2025-11-07 18:05:30 - INFO - 자동 승인 시도: '2'
2025-11-07 18:05:31 - INFO - 자동 승인 완료 (총 1회)
2025-11-07 18:05:32 - INFO - 자동 승인 시도: 'yes'
2025-11-07 18:05:33 - INFO - 자동 승인 완료 (총 2회)
```

## 🔧 고급 설정

### 코드 커스터마이징

프로그램의 동작을 더 세밀하게 제어하고 싶다면 `auto_approver.py` 파일을 직접 수정할 수 있습니다:

#### 1. 응답 간 대기 시간 조정

```python
# auto_approver.py의 send_approval 메서드에서
time.sleep(0.5)  # 이 값을 조정 (초 단위)
```

#### 2. 특정 창 제목 감지 (고급)

`psutil`을 사용하여 특정 창 제목을 가진 프로세스만 감지하도록 수정 가능합니다.

#### 3. 로그 레벨 변경

```python
# logging.basicConfig에서
level=logging.DEBUG  # 더 자세한 로그
level=logging.WARNING  # 경고 이상만
```

## 🤝 기여 및 피드백

이 프로그램에 대한 개선 사항이나 버그 리포트는 언제든지 환영합니다!

### 개선 아이디어

- GUI 인터페이스 추가
- 웹 대시보드로 원격 모니터링
- 더 스마트한 프롬프트 감지
- 조건부 승인 규칙

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

---

## 📞 지원

문제가 있거나 질문이 있으시면:

1. 이슈 트래커에 문제 등록
2. 로그 파일 (`auto_approver.log`) 첨부
3. 사용한 명령어와 환경 정보 제공

**즐거운 자동화 되세요!** 🚀
