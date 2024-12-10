from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

if __name__ != "__main__":
    from src.folder_manager import FolderManager
    from src.config import config
else:
    from folder_manager import FolderManager
    from config import config

class DriveBackupManager:
    """구글 드라이브에 메모리 파일을 백업하는 매니저 클래스"""
    
    def __init__(self, credentials_path=None):
        """
        DriveBackupManager 초기화
        
        Args:
            credentials_path (str): Google OAuth credentials.json 파일 경로
        """
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.credentials_path = credentials_path or config.CREDENTIALS_PATH
        self.creds = None
        self.drive_service = None
        self.folder_manager = None
        
    def authenticate(self):
        """Google Drive API 인증 처리"""
        if os.path.exists(config.TOKEN_PATH):
            logger.info("Using existing token")
            self.creds = Credentials.from_authorized_user_file(config.TOKEN_PATH, self.SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                logger.info("Token expired. Refreshing...")
                self.creds.refresh(Request())
            else:
                logger.info("Initial authentication required. Opening browser for authorization...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # 토큰 저장
            with open(config.TOKEN_PATH, 'w') as token:
                token.write(self.creds.to_json())
                logger.info("Token saved successfully")
                
        # Drive 서비스 생성
        self.drive_service = build('drive', 'v3', credentials=self.creds)
                
        # FolderManager 초기화 (drive_service 전달)
        self.folder_manager = FolderManager(self.drive_service)
    
    def backup_memory_file(self, source_path, folder_name=config.DRIVE_FOLDER_NAME):
        """
        메모리 파일을 구글 드라이브에 백업
        
        Args:
            source_path (str): 백업할 memory.json 파일 경로
            folder_name (str): 구글 드라이브의 대상 폴더 이름
            
        Returns:
            str: 업로드된 파일의 ID
        """
        try:            
            # 폴더 확인/생성
            folder_id = self.folder_manager.get_or_create_folder(folder_name)
            if not folder_id:
                raise Exception(f"'{folder_name}' 폴더 생성이나 찾기 실패ㅠㅠ")
            
            # 기존 파일 백업 처리
            self._backup_existing_file(self.drive_service, folder_id)
            
            # 새 파일 업로드
            return self._upload_new_file(self.drive_service, source_path, folder_id)
            
        except Exception as e:
            raise Exception(f"백업 중에 문제가 생겼어ㅠㅠ: {str(e)}")
    
    def _backup_existing_file(self, service, folder_id):
        """기존 파일을 복사하여 타임스탬프가 있는 백업 생성"""
        results = service.files().list(
            q=f"name='memory.json' and '{folder_id}' in parents",
            spaces='drive'
        ).execute()
        
        if results.get('files'):
            existing_file = results['files'][0]
            backup_name = f"memory_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            
            # 기존 파일을 복사하여 새로운 이름으로 저장
            service.files().copy(
                fileId=existing_file['id'],
                body={'name': backup_name, 'parents': [folder_id]}
            ).execute()
            
            logger.info(f"Created backup copy: {backup_name}")
    
    def _upload_new_file(self, service, source_path, folder_id):
        """새 파일 업로드 또는 기존 파일 업데이트"""
        # 기존 파일 찾기
        results = service.files().list(
            q=f"name='memory.json' and '{folder_id}' in parents",
            spaces='drive'
        ).execute()
        
        media = MediaFileUpload(
            source_path,
            mimetype=config.DEFAULT_MIME_TYPE,
            resumable=True
        )
        
        if results.get('files'):
            # 기존 파일이 있으면 업데이트
            existing_file = results['files'][0]
            file = service.files().update(
                fileId=existing_file['id'],
                media_body=media
            ).execute()
            logger.info("Existing file updated successfully")
        else:
            # 새 파일 생성
            file_metadata = {
                'name': 'memory.json',
                'parents': [folder_id]
            }
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            logger.info("New file created successfully")
        
        return file.get('id')


if __name__ == "__main__":
    # 테스트용 메인 코드

    from config import config
    
    try:
        manager = DriveBackupManager()
        manager.authenticate()
        file_id = manager.backup_memory_file(config.MEMORY_SOURCE_PATH)
        print(f"성공적으로 처리했어! 파일 ID: {file_id}")
    except Exception as e:
        print(f"에러가 났네ㅠㅠ: {str(e)}")
