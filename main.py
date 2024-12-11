from src.backup_manager import DriveBackupManager
from src.folder_manager import FolderManager
from src.config import config
import logging
import warnings
import os
import sys
from googleapiclient.discovery import logger as googleapiclient_logger
from datetime import datetime
from dotenv import load_dotenv
import ctypes

# Load environment variables
load_dotenv()
project_name = os.getenv('PROJECT_NAME')

# 구글 API 클라이언트의 불필요한 경고 메시지 숨기기
googleapiclient_logger.setLevel(logging.ERROR)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

def show_message_box(title, message, style=0):
    """메시지 박스 표시 (exe 모드에서만)"""
    if getattr(sys, 'frozen', False):
        return ctypes.windll.user32.MessageBoxW(0, message, title, style)

# Get the application path (works for both script and frozen exe)
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# 로그 디렉토리 생성
log_dir = os.path.join(application_path, project_name, "logs")
os.makedirs(log_dir, exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f"{project_name}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(project_name)

def main():
    try:
        # 백업 매니저 초기화
        manager = DriveBackupManager(config.CREDENTIALS_PATH)
        
        # 인증 및 백업 실행
        manager.authenticate()
        file_id = manager.backup_memory_file(config.MEMORY_SOURCE_PATH, config.DRIVE_FOLDER_NAME)
        
        success_msg = f"백업이 성공적으로 완료되었습니다.\nFile ID: {file_id}"
        logger.info(success_msg)
        show_message_box("백업 성공", success_msg)
        
    except Exception as e:
        error_msg = f"백업 실패: {str(e)}"
        logger.error(error_msg)
        show_message_box("백업 실패", error_msg, 0x10)  # 0x10 = MB_ICONERROR
        raise

if __name__ == "__main__":
    main()