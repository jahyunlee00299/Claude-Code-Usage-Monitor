# 🧠 Claude 스마트 자동 승인 프로그램

## 개요

**스마트 자동 승인**은 단순히 정해진 키를 누르는 것이 아니라, **화면의 프롬프트를 읽고 분석해서 적절한 응답을 자동으로 선택**하는 지능형 자동화 도구입니다.

## 🌟 기본 버전과의 차이점

| 기능 | 기본 버전 | 스마트 버전 |
|------|-----------|-------------|
| 키 입력 | ✅ 고정된 응답 ("2", "yes") | ✅ 상황에 맞는 응답 |
| 프롬프트 분석 | ❌ 없음 | ✅ **자동 분석** |
| Git 인식 | ❌ 없음 | ✅ Git 특화 패턴 |
| 화면 읽기 | ❌ 없음 | ✅ OCR/접근성 API |
| 학습 | ❌ 없음 | ✅ 패턴 매칭 |

## 🎯 작동 방식

### 1단계: 창 감지
```
Git Bash 또는 CMD/PowerShell 창을 자동으로 찾습니다
  ↓
"Git Bash" 또는 "Windows PowerShell" 제목 감지
```

### 2단계: 화면 텍스트 읽기
```python
# 방법 1: Windows 접근성 API (pywinauto)
창의 텍스트 컨트롤 직접 읽기

# 방법 2: OCR (pytesseract)
화면 캡처 → 텍스트 추출

# 방법 3: 클립보드
마지막 복사된 텍스트 확인
```

### 3단계: 프롬프트 분석
```python
텍스트에서 다음 패턴 찾기:

✅ "Continue? (Y/n)" → 응답: Y
✅ "Select option: 1) ... 2) ..." → 응답: 2
✅ "Proceed? (y/n)" → 응답: y
✅ "Press Enter to continue" → 응답: Enter
✅ "Merge conflict detected" → 응답: c (continue)
```

### 4단계: 적절한 응답 입력
```
분석된 응답을 자동으로 입력하고 Enter
```

## 🔧 설치 방법

### 1. 기본 설치
```bash
pip install -r requirements_smart.txt
```

### 2. Tesseract OCR 설치 (화면 읽기용)

#### Windows
```bash
# 1. Tesseract 다운로드
https://github.com/UB-Mannheim/tesseract/wiki

# 2. 설치 (기본 경로: C:\Program Files\Tesseract-OCR)

# 3. 환경 변수 설정 (선택적)
# 시스템 변수 Path에 추가: C:\Program Files\Tesseract-OCR
```

#### Linux
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

#### Mac
```bash
brew install tesseract
```

### 3. 설치 확인
```bash
tesseract --version
python -c "import pytesseract; print('OK')"
```

## 🚀 사용 방법

### 기본 실행
```bash
# 5분 타임아웃, 스마트 감지 활성화
python smart_auto_approver.py

# 3분 타임아웃
python smart_auto_approver.py --timeout 180

# 디버그 모드
python smart_auto_approver.py --debug
```

### 고급 옵션
```bash
# Git만 대상으로 지정
python smart_auto_approver.py \
    --processes git bash \
    --windows "git bash" "git cmd"

# 클립보드 체크 활성화
python smart_auto_approver.py --enable-clipboard

# 스마트 감지 비활성화 (기본 모드로 동작)
python smart_auto_approver.py --no-smart
```

## 📝 지원하는 프롬프트 패턴

### Git 프롬프트

| 프롬프트 | 자동 응답 |
|---------|-----------|
| `Continue? (Y/n)` | `Y` |
| `Proceed? (y/N)` | `y` |
| `Delete branch? (y/n)` | `y` |
| `Push to remote? (y/n)` | `y` |
| `Merge conflict detected` | `c` (continue) |
| `Accept changes?` | `y` |
| `Overwrite?` | `y` |

### 일반 프롬프트

| 프롬프트 | 자동 응답 |
|---------|-----------|
| `Select option: 1) ... 2) ...` | `2` |
| `Choose (1-3):` | `1` |
| `Press Enter to continue` | `Enter` |
| `(y/n)` | `y` |
| `(yes/no)` | `yes` |

### CMD/PowerShell

| 프롬프트 | 자동 응답 |
|---------|-----------|
| `Terminate batch job (Y/N)?` | `N` |
| `Delete ... (Y/N)?` | `Y` |
| `Are you sure (Y/N)?` | `Y` |

### PyCharm

| 프롬프트 | 자동 응답 |
|---------|-----------|
| `Confirm` | `Yes` |
| `Overwrite` | `Yes` |
| `Replace` | `Yes` |

## 🎨 커스텀 패턴 추가

코드를 수정하여 자신만의 패턴을 추가할 수 있습니다:

```python
# smart_auto_approver.py 파일 수정

class PromptPatternMatcher:
    def __init__(self):
        # 기존 패턴...

        # 커스텀 패턴 추가
        self.custom_patterns = {
            r'내_특별한_프롬프트': '내_응답',
            r'확인하시겠습니까\?': 'y',
            r'계속 진행': 'yes',
        }
```

## 💡 실전 예시

### 예시 1: Git 작업 자동화
```bash
# 시나리오: Git push 중 여러 확인 프롬프트
# "Push to remote? (y/n)" → 자동 응답: y
# "Continue? (Y/n)" → 자동 응답: Y

python smart_auto_approver.py \
    --timeout 180 \
    --processes git bash \
    --windows "git bash"
```

### 예시 2: 배치 파일 실행
```bash
# 시나리오: 긴 배치 파일 실행 중 중간 확인
# "Continue? (Y/n)" → 자동 응답: Y
# "Press Enter to continue" → 자동 응답: Enter

python smart_auto_approver.py \
    --timeout 300 \
    --processes cmd \
    --windows cmd
```

### 예시 3: PyCharm 리팩토링
```bash
# 시나리오: 대규모 리팩토링 작업
# "Confirm refactoring?" → 자동 응답: Yes
# "Overwrite existing?" → 자동 응답: Yes

python smart_auto_approver.py \
    --timeout 240 \
    --processes pycharm \
    --windows pycharm
```

## 🔍 작동 확인

### 로그 확인
```bash
# 실시간 로그 보기
tail -f smart_auto_approver.log

# Windows (PowerShell)
Get-Content smart_auto_approver.log -Wait -Tail 20
```

### 로그 예시
```
2025-11-07 18:30:00 - INFO - 🧠 Claude 스마트 자동 승인 프로그램
2025-11-07 18:30:00 - INFO - 스마트 감지: 활성화
2025-11-07 18:35:30 - INFO - ⚠️  비활성 감지 (330초). 스마트 승인 시작...
2025-11-07 18:35:30 - INFO - 🎯 대상 창: Git Bash
2025-11-07 18:35:31 - INFO - 프롬프트 감지: Git - 패턴: Continue\?\s*\(Y/n\)
2025-11-07 18:35:31 - INFO - 🧠 스마트 감지 성공! 응답: 'Y'
2025-11-07 18:35:31 - INFO - 📝 응답 입력: 'Y'
2025-11-07 18:35:32 - INFO - ✅ 응답 완료 (총 1회)
```

## 📊 통계 확인

프로그램 종료 시 자동으로 통계가 표시됩니다:

```
============================================================
📊 스마트 자동 승인 통계
============================================================
실행 시간: 600초 (10.0분)
총 체크: 60
총 승인: 5
스마트 감지 성공: 4
기본 응답 사용: 1
스마트 감지 성공률: 80.0%
============================================================
```

## ⚙️ 문제 해결

### 문제 1: OCR이 작동하지 않음

**증상**: "pytesseract 미설치" 메시지

**해결**:
```bash
# 1. pytesseract 설치
pip install pytesseract Pillow

# 2. Tesseract OCR 엔진 설치
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr
# Mac: brew install tesseract

# 3. 환경 변수 설정 (Windows)
# pytesseract.pytesseract.tesseract_cmd 경로 확인
```

### 문제 2: 창을 찾을 수 없음

**증상**: "대상 창을 찾을 수 없습니다"

**해결**:
```bash
# 1. 창 제목 확인
# Windows PowerShell에서:
Get-Process | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object MainWindowTitle

# 2. 올바른 창 키워드 지정
python smart_auto_approver.py --windows "실제_창_제목"
```

### 문제 3: 프롬프트 인식 실패

**증상**: "프롬프트 패턴 매칭 실패"

**해결**:
```bash
# 1. 디버그 모드로 실행하여 읽은 텍스트 확인
python smart_auto_approver.py --debug

# 2. 로그에서 읽은 텍스트 확인
grep "OCR 텍스트" smart_auto_approver.log

# 3. 필요시 커스텀 패턴 추가 (코드 수정)
```

### 문제 4: pywinauto 설치 오류

**해결**:
```bash
# Windows 전용 패키지 설치
pip install pywinauto
pip install comtypes

# 또는 고급 기능 없이 사용
python smart_auto_approver.py
# (pywinauto 없어도 기본 동작)
```

## 🔒 보안 및 주의사항

### ⚠️ 중요 경고

1. **OCR의 한계**
   - OCR은 100% 정확하지 않습니다
   - 잘못된 텍스트 인식 가능
   - 중요한 작업에는 주의 필요

2. **패턴 매칭의 한계**
   - 모든 프롬프트를 인식할 수 없음
   - 예상치 못한 프롬프트에 기본 응답 사용

3. **권장 사용 환경**
   - ✅ 반복적인 Git 작업
   - ✅ 테스트 자동화
   - ✅ 개발 환경
   - ❌ 프로덕션 배포
   - ❌ 민감한 시스템 변경

## 🎓 고급 기능

### 프롬프트 학습 모드 (향후 구현 예정)

```python
# 사용자의 응답을 학습하여 패턴 자동 생성
# 예: 5회 이상 동일한 프롬프트에 동일한 응답
#     → 자동으로 패턴 추가
```

### AI 기반 응답 선택 (향후 구현 예정)

```python
# GPT 모델을 사용하여 프롬프트 분석
# 더 정확한 응답 생성
```

## 📚 참고 자료

- [pywinauto 문서](https://pywinauto.readthedocs.io/)
- [pytesseract 문서](https://pypi.org/project/pytesseract/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [pyautogui 문서](https://pyautogui.readthedocs.io/)

## 🤝 기여

새로운 프롬프트 패턴을 발견하시면 공유해주세요!

```python
# 예시: 새로운 패턴 제안
r'당신의_프롬프트_패턴': '적절한_응답'
```

---

**Happy Automating with Intelligence!** 🧠🚀
