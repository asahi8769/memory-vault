from pathlib import Path
from dataclasses import dataclass
from typing import List
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
project_name = os.getenv('PROJECT_NAME')

def get_application_path():
    """Get the application path for both script and frozen exe"""
    if getattr(sys, 'frozen', False):
        # If running as exe
        base_path = Path(sys.executable).parent / project_name
    else:
        # If running in development
        base_path = Path(__file__).parent.parent
    return base_path

@dataclass
class Config:
    """Application configuration"""
    # Project paths
    ROOT_DIR: Path = get_application_path()
    CREDENTIALS_DIR: Path = ROOT_DIR / 'credentials'  
    CREDENTIALS_PATH: Path = CREDENTIALS_DIR / 'credentials.json'
    TOKEN_PATH: Path = CREDENTIALS_DIR / 'token.json'
    FOLDER_CACHE_PATH: Path = CREDENTIALS_DIR / 'folder_cache.json'
    
    # Memory file path
    MEMORY_SOURCE_PATH: str = r"C:\Users\asahi\AppData\Roaming\npm\node_modules\@modelcontextprotocol\server-memory\dist\memory.json"
    
    # Google Drive settings
    DRIVE_FOLDER_NAME: str = 'claude-memory'
    DEFAULT_MIME_TYPE: str = 'application/json'
    
    # Backup settings
    BACKUP_PATHS: List[str] = None  # Optional: Add paths if needed
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration"""
        return cls()

# Create a global config instance
config = Config.load()