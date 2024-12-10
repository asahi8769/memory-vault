import os
import subprocess
import sys
from dotenv import load_dotenv
import shutil

load_dotenv()

def build_exe():
    """exe 파일 빌드"""
    project_root = os.getenv('PROJECT_PATH')
    if not project_root:
        raise ValueError("PROJECT_PATH not found in .env file")
        
    project_name = os.getenv('PROJECT_NAME')
    if not project_name:
        raise ValueError("PROJECT_NAME not found in .env file")
        
    main_script = os.path.join(project_root, "main.py")
    dist_dir = os.path.join(project_root, "dist")
    icon_path = os.path.join(project_root, "ico", f"{project_name}.ico")
    
    # Create necessary directories in dist
    logs_dir = os.path.join(dist_dir, project_name, "logs")
    credentials_dir = os.path.join(dist_dir, project_name, "credentials")
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(credentials_dir, exist_ok=True)
    
    # Copy credentials if they exist
    src_credentials = os.path.join(project_root, "credentials")
    if os.path.exists(src_credentials):
        for file in os.listdir(src_credentials):
            src_file = os.path.join(src_credentials, file)
            dst_file = os.path.join(credentials_dir, file)
            shutil.copy2(src_file, dst_file)
    
    command = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--uac-admin",
        "--name", project_name,
        "--clean",
        # Add data files with correct paths
        "--add-data", f"{os.path.join(project_root, 'credentials')}/*;{project_name}/credentials",
        # Add hidden imports
        "--hidden-import", "google.auth.transport.requests",
        main_script
    ]
    
    try:
        # Try to convert icon if it exists, but continue even if it fails
        if os.path.exists(os.path.join(project_root, "ico", "icon.webp")):
            import icon_converter
            if icon_converter.convert_webp_to_ico():
                command.insert(-1, f"--icon={icon_path}")
            
        print('\n',command)
        subprocess.run(command, check=True)
        print("빌드 완료")
        return True
        
    except Exception as e:
        print(f"빌드 실패: {str(e)}")
        raise
        return False

if __name__ == "__main__":
    build_exe()