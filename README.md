# Memory Vault

Anthropic의 Claude AI 어시스턴트의 MCP MEMORY 기능을 통해 생성된 memory.json 파일을 Google Drive에 자동으로 백업하고 관리하는 시스템입니다. 이를 통해 Claude와의 대화 기록과 컨텍스트를 안전하게 보관하고 필요할 때 복원할 수 있습니다.

## 주요 기능

- Google Drive를 이용한 자동 백업
- 기존 파일 자동 백업 (타임스탬프 포함)
- 로깅 시스템을 통한 백업 상태 모니터링
- 프로젝트 전체 로컬 백업 기능
- GitHub 자동 업로드 기능
- 독립 실행 파일(exe) 빌드 지원

## 시작하기

### 필수 요구사항

- Python 3.x
- Google Cloud Platform 프로젝트 및 API 인증 정보
- Google Drive API 활성화
- (선택) GitHub 계정 및 개인 액세스 토큰

### 설치

1. 저장소를 클론합니다:
```bash
git clone [repository-url]
cd memory-vault
```

2. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

3. Google Cloud Platform에서 credentials.json 파일을 다운로드하고 프로젝트의 credentials 디렉토리에 저장합니다.

### 환경 설정

1. `.env` 파일을 생성하고 다음 설정을 추가합니다:
```
PROJECT_PATH=프로젝트_경로
PROJECT_NAME=memory-vault
GITHUB_TOKEN=your_github_token
REPO_DESCRIPTION=Google Drive 기반의 메모리 백업 시스템
```

## 사용 방법

### 메모리 파일 백업

```python
from src.backup_manager import DriveBackupManager
from src.config import config

manager = DriveBackupManager(config.CREDENTIALS_PATH)
manager.authenticate()
file_id = manager.backup_memory_file(config.MEMORY_SOURCE_PATH)
```

### 프로젝트 로컬 백업

```python
from src.utils.backup import backup_project

success, result = backup_project()
if success:
    print(f"백업 완료: {result}")
```

### GitHub 업로드

```python
from src.utils.git_upload import upload_to_github

success = upload_to_github()
if success:
    print("GitHub 업로드 완료")
```

### 실행 파일 빌드

```python
from src.utils.build_exe import build_exe

success = build_exe()
if success:
    print("exe 파일 빌드 완료")
```

## 프로젝트 구조

- `src/`: 소스 코드
  - `backup_manager.py`: Google Drive 백업 관리
  - `folder_manager.py`: Drive 폴더 관리
  - `config.py`: 설정 관리
  - `utils/`: 유틸리티 함수들
    - `backup.py`: 로컬 백업 기능
    - `logger.py`: 로깅 시스템
    - `git_upload.py`: GitHub 업로드 기능
    - `build_exe.py`: 실행 파일 빌드
    - `icon_converter.py`: 아이콘 변환

## 실행 파일 (exe) 사용

1. 빌드된 exe 파일을 실행하면 자동으로 필요한 디렉토리가 생성됩니다.
2. 첫 실행 시 Google 인증 과정이 필요합니다.
3. 백업 성공/실패 여부를 메시지 창으로 확인할 수 있습니다.
4. 로그 파일은 `[실행파일위치]/[프로젝트명]/logs/` 디렉토리에 저장됩니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.
