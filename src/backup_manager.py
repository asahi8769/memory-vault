from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import os
from datetime import datetime
import logging
import io
import json

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
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/documents'
        ]
        self.credentials_path = credentials_path or config.CREDENTIALS_PATH
        self.creds = None
        self.drive_service = None
        self.docs_service = None
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
                
        # Drive와 Docs 서비스 생성
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)
                
        # FolderManager 초기화 (drive_service 전달)
        self.folder_manager = FolderManager(self.drive_service)
    
    def parse_memory_file(self, file_content):
        """
        메모리 파일의 내용을 파싱하여 엔티티와 관계 목록으로 반환
        
        Args:
            file_content (str): 파일 내용
            
        Returns:
            dict: 파싱된 데이터 {'entities': [...], 'relations': [...]}
        """
        entities = []
        relations = []
        
        for line in file_content.strip().split('\n'):
            if line.strip():  # 빈 줄 무시
                try:
                    data = json.loads(line)
                    if data.get('type') == 'entity':
                        entities.append(data)
                    elif data.get('type') == 'relation':
                        relations.append(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line: {line[:100]}...")
                    continue
                    
        return {
            'entities': entities,
            'relations': relations
        }

    def format_json_to_doc_requests(self, memory_data):
        """
        메모리 데이터를 Google Docs 요청 형식으로 변환
        
        Args:
            memory_data (dict): 변환할 메모리 데이터
            
        Returns:
            list: Google Docs API 요청 목록
        """
        requests = []
        
        # JSON 데이터를 문자열로 변환하되, 들여쓰기 적용
        json_content = json.dumps(memory_data, ensure_ascii=False, indent=2)
        
        # JSON 내용을 그대로 문서에 삽입
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': json_content
            }
        })
        
        return requests

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
            
            # JSON 파일 읽기 및 파싱
            with open(source_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
                memory_data = self.parse_memory_file(file_content)

            # 폴더 내 모든 파일 확인
            results = self.drive_service.files().list(
                q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document'",
                spaces='drive'
            ).execute()

            if results.get('files'):  # 폴더에 파일이 있으면
                memory_exists = any(file['name'] == 'memory' for file in results['files'])
                if memory_exists:
                    # memory 파일이 있으면 백업 처리
                    self._backup_existing_file(self.drive_service, folder_id)
            
            # 새 문서 생성 또는 업데이트
            return self._create_or_update_doc(memory_data, folder_id)
            
        except Exception as e:
            logger.error(f"백업 중 에러: {str(e)}")
            raise Exception(f"백업 중에 문제가 생겼어ㅠㅠ: {str(e)}")
    
    def _backup_existing_file(self, service, folder_id):
        """기존 파일을 복사하여 타임스탬프가 있는 백업 생성"""
        results = service.files().list(
            q=f"name='memory' and '{folder_id}' in parents and mimeType='application/vnd.google-apps.document'",
            spaces='drive'
        ).execute()
        
        if results.get('files'):
            existing_file = results['files'][0]
            backup_name = f"memory_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 기존 파일을 복사하여 새로운 이름으로 저장
            service.files().copy(
                fileId=existing_file['id'],
                body={'name': backup_name, 'parents': [folder_id]}
            ).execute()
            
            logger.info(f"Created backup copy: {backup_name}")
    
    def _create_or_update_doc(self, memory_data, folder_id):
        """새 문서 생성 또는 기존 문서 업데이트"""
        # 기존 문서 찾기
        results = self.drive_service.files().list(
            q=f"name='memory' and '{folder_id}' in parents and mimeType='application/vnd.google-apps.document'",
            spaces='drive'
        ).execute()

        doc_requests = self.format_json_to_doc_requests(memory_data)
        
        if results.get('files'):
            # 기존 문서가 있으면 내용 삭제 후 업데이트
            doc_id = results['files'][0]['id']
            
            # 문서 내용 초기화
            current_content = self.docs_service.documents().get(documentId=doc_id).execute()
            if current_content.get('body', {}).get('content'):
                end_index = current_content['body']['content'][-1]['endIndex'] - 1
                self.docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={
                        'requests': [{
                            'deleteContentRange': {
                                'range': {
                                    'startIndex': 1,
                                    'endIndex': end_index
                                }
                            }
                        }]
                    }
                ).execute()
            
            # 새 내용 추가
            self.docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': doc_requests}
            ).execute()
            
            logger.info("Existing document updated successfully")
            return doc_id
        else:
            # 새 문서 생성
            doc = self.docs_service.documents().create(
                body={'title': 'memory'}  # .doc 확장자 제거
            ).execute()
            
            # 문서를 지정된 폴더로 이동
            self.drive_service.files().update(
                fileId=doc['documentId'],
                addParents=folder_id,
                removeParents='root',
                fields='id, parents'
            ).execute()
            
            # 내용 추가
            self.docs_service.documents().batchUpdate(
                documentId=doc['documentId'],
                body={'requests': doc_requests}
            ).execute()
            
            logger.info("New document created successfully")
            return doc['documentId']


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
