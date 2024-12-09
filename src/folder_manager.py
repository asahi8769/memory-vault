from googleapiclient.discovery import build

class FolderManager:
    def __init__(self, drive_service):
        self.drive_service = drive_service
        self.folder_cache = {}
        
    def get_or_create_folder(self, folder_name):
        """폴더 가져오기 또는 생성"""
        # 캐시에 있으면 반환
        if folder_name in self.folder_cache:
            return self.folder_cache[folder_name]
            
        # Drive에서 폴더 검색
        response = self.drive_service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        # 폴더가 있으면 ID 반환
        if response.get('files'):
            folder_id = response['files'][0]['id']
            self.folder_cache[folder_name] = folder_id
            return folder_id
            
        # 없으면 새로 생성
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = self.drive_service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        folder_id = folder.get('id')
        self.folder_cache[folder_name] = folder_id
        return folder_id