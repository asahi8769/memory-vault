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
        
        # 제목 추가
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': f"Memory Vault Backup\n생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            }
        })
        
        # 제목 스타일 적용
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': 1, 'endIndex': 17},
                'paragraphStyle': {
                    'namedStyleType': 'HEADING_1',
                    'alignment': 'CENTER'
                },
                'fields': 'namedStyleType,alignment'
            }
        })
        
        current_index = len("Memory Vault Backup\n생성일시: YYYY-MM-DD HH:MM:SS\n\n")
        
        # 엔티티 섹션
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': "=== 엔티티 ===\n\n"
            }
        })
        current_index += len("=== 엔티티 ===\n\n")
        
        # 엔티티 내용 추가
        for entity in memory_data.get('entities', []):
            entity_text = (f"엔티티: {entity.get('name', 'Unknown')}\n"
                         f"유형: {entity.get('entityType', 'Unknown')}\n"
                         "관찰:\n")
            
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': entity_text
                }
            })
            current_index += len(entity_text)
            
            for obs in entity.get('observations', []):
                obs_text = f"- {obs}\n"
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': obs_text
                    }
                })
                current_index += len(obs_text)
            
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': "\n"
                }
            })
            current_index += 1
        
        # 관계 섹션
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': "=== 관계 ===\n\n"
            }
        })
        current_index += len("=== 관계 ===\n\n")
        
        # 관계 내용 추가
        for relation in memory_data.get('relations', []):
            relation_text = f"{relation.get('from', 'Unknown')} -> {relation.get('relationType', 'Unknown')} -> {relation.get('to', 'Unknown')}\n"
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': relation_text
                }
            })
            current_index += len(relation_text)
        
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

            # 기존 파일 백업 처리
            self._backup_existing_file(self.drive_service, folder_id)
            
            # 새 문서 생성 또는 업데이트
            return self._create_or_update_doc(memory_data, folder_id)
            
        except Exception as e:
            logger.error(f"백업 중 에러: {str(e)}")
            raise Exception(f"백업 중에 문제가 생겼어ㅠㅠ: {str(e)}")
    
    def _backup_existing_file(self, service, folder_id):
        """기존 파일을 복사하여 타임스탬프가 있는 백업 생성"""
        results = service.files().list(
            q=f"name='memory.doc' and '{folder_id}' in parents and mimeType='application/vnd.google-apps.document'",
            spaces='drive'
        ).execute()
        
        if results.get('files'):
            existing_file = results['files'][0]
            backup_name = f"memory_{datetime.now().strftime('%Y%m%d%H%M%S')}.doc"
            
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
            q=f"name='memory.doc' and '{folder_id}' in parents and mimeType='application/vnd.google-apps.document'",
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
                body={'title': 'memory.doc'}
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
