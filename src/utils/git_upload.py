import os
import requests
import subprocess
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def run_git_command(command, error_message=None, check=True):
    """Git 명령어 실행 및 에러 처리"""
    try:
        result = subprocess.run(command, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        error_msg = error_message or f"Git command failed: {' '.join(command)}"
        print(f"에러났다ㅠ: {error_msg}")
        print(f"자세한 내용: {e.output}")
        raise

def check_git_changes():
    """Git 변경사항 체크"""
    status_result = run_git_command(["git", "status", "--porcelain"], check=False)
    changes = status_result.stdout.strip()
    
    if not changes:
        print("앗... 변경된 파일이 하나도 없네?")
        print("커밋할 게 없어서 종료할게!")
        return False
        
    print("\n현재 변경사항:")
    print(changes)
    return True

def check_repo_exists(token, repo_name):
    """GitHub API를 사용하여 레포지토리 존재 여부 확인"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(
        f"https://api.github.com/user/repos",
        headers=headers
    )
    
    if response.status_code == 200:
        repos = response.json()
        return any(repo["name"] == repo_name for repo in repos)
    else:
        return False

def create_github_repo(token, repo_name, description):
    """GitHub API를 사용하여 새 레포지토리 생성"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": repo_name,
        "description": description,
        "private": True,  # 프라이빗으로 변경
        "auto_init": True  # README 자동 생성
    }
    
    response = requests.post(
        "https://api.github.com/user/repos",
        headers=headers,
        data=json.dumps(data)
    )
    
    if response.status_code == 201:
        return response.json()["clone_url"]
    else:
        raise Exception(f"레포 만들기 실패ㅠㅠ: {response.json().get('message', '알 수 없는 에러')}")

def get_repo_url(token, repo_name):
    """GitHub API를 사용하여 레포지토리 URL 가져오기"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    user_response = requests.get(
        "https://api.github.com/user",
        headers=headers
    )
    
    if user_response.status_code != 200:
        raise Exception("GitHub 유저 정보를 못 가져왔어ㅠ")
        
    username = user_response.json()["login"]
    
    response = requests.get(
        f"https://api.github.com/repos/{username}/{repo_name}",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()["clone_url"]
    else:
        raise Exception("레포 URL을 못 찾겠어...")

def ensure_gitignore():
    """기본 .gitignore 파일 생성"""
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Credentials
credentials/
token.json
.env

# Logs
logs/
*.log
    """
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content.strip())

def add_placeholder_files(directory):
    """빈 디렉토리를 위한 .gitkeep 파일 추가"""
    for root, dirs, files in os.walk(directory):
        if not files and not dirs:  # 빈 디렉토리인 경우
            gitkeep_path = os.path.join(root, '.gitkeep')
            with open(gitkeep_path, 'w') as f:
                pass

def sync_with_remote():
    """원격 저장소와 싱크 맞추기"""
    try:
        print("원격 저장소랑 싱크 맞추는 중...")
        run_git_command(["git", "fetch", "origin"], check=False)
        run_git_command(["git", "pull", "--ff-only"], check=False)
        return True
    except Exception as e:
        print(f"싱크 맞추다가 문제 생김ㅠㅠ: {e}")
        return False

def upload_to_github():
    """코드베이스를 GitHub에 업로드"""
    try:
        token = os.getenv('GITHUB_TOKEN')
        default_repo_name = os.getenv('PROJECT_NAME')
        default_description = os.getenv('REPO_DESCRIPTION', 'Google Drive 기반의 메모리 백업 시스템')
        
        if not token:
            raise Exception("GitHub 토큰이 없네? .env 파일 확인해봐!")
            
        repo_name = input(f"레포지토리 이름 뭘로 할래? (그냥 엔터치면 {default_repo_name}): ").strip()
        if not repo_name:
            repo_name = default_repo_name
            
        description = input(f"레포지토리 설명은? (그냥 엔터치면 기본값 씀!): ").strip()
        if not description:
            description = default_description

        # 프로젝트 루트 디렉토리로 이동
        project_root = os.getenv('PROJECT_PATH')
        if not project_root:
            raise ValueError("어... PROJECT_PATH를 못 찾겠는데? .env 파일 확인해봐!")
        os.chdir(project_root)
        
        # .gitignore 파일 생성
        ensure_gitignore()
        print(".gitignore 파일 준비 완료!")
        
        # 빈 디렉토리 처리
        add_placeholder_files(project_root)
        print("빈 디렉토리 처리 완료!")
        
        # Git 초기화
        if not os.path.exists(".git"):
            run_git_command(["git", "init"], "Git 초기화 실패ㅠㅠ")
            print("Git 초기화 완료!")
        
        # 레포지토리 존재 여부 확인
        repo_exists = check_repo_exists(token, repo_name)
        
        if repo_exists:
            print(f"앗! '{repo_name}' 레포가 이미 있네?")
            choice = input("덮어써버릴까? (Y/n): ").strip().lower()
            if choice == 'n':
                print("그래, 그럼 종료할게!")
                return False
            repo_url = get_repo_url(token, repo_name)
            
            # 기존 레포면 싱크 맞추기
            sync_with_remote()
        else:
            # 새 레포지토리 생성
            print("새로운 레포지토리 만드는 중...")
            repo_url = create_github_repo(token, repo_name, description)

        # 변경사항 체크
        if not check_git_changes():
            return False

        # 현재 시간을 포함한 커밋 메시지 생성
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        commit_message = f"Upload: {timestamp}"
        
        # Git 커밋 및 푸시
        print("변경사항 커밋하는 중...")
        run_git_command(["git", "add", "-A"])  # 모든 파일 추가 (삭제된 파일도 포함)
        run_git_command(["git", "commit", "-m", commit_message])
        run_git_command(["git", "branch", "-M", "master"])  # master 대신 main 사용
        
        # remote 확인 및 설정
        try:
            run_git_command(["git", "remote", "remove", "origin"], check=False)
        except:
            pass
            
        run_git_command(["git", "remote", "add", "origin", repo_url])
        
        # 강제 푸시 (기존 레포지토리인 경우)
        print("GitHub로 푸시하는 중...")
        if repo_exists:
            run_git_command(["git", "push", "-f", "-u", "origin", "main"])
        else:
            run_git_command(["git", "push", "-u", "origin", "main"])
        
        print(f"\n굿~ 다 됐다! 🎉")
        print(f"여기가 레포 주소야: {repo_url}")
        return True
        
    except Exception as e:
        print(f"앗... 문제가 생겼네ㅠㅠ: {str(e)}")
        # 에러 발생 시 Git 초기화 시도
        try:
            if os.path.exists(".git"):
                print("원래대로 되돌리는 중...")
                run_git_command(["git", "reset", "--hard"], check=False)
        except:
            pass
        raise

if __name__ == "__main__":
    upload_to_github()