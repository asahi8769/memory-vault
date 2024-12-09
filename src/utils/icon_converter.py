from PIL import Image
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def convert_webp_to_ico():
    """webp 파일를 ICO 파일로 변환"""
    try:
        project_root = os.getenv('PROJECT_PATH')
        if not project_root:
            print("PROJECT_PATH not found in .env file")
            return False
            
        project_name = os.getenv('PROJECT_NAME')
        if not project_name:
            print("PROJECT_NAME not found in .env file")
            return False
            
        input_path = os.path.join(project_root, "ico", "icon.webp")
        output_path = os.path.join(project_root, "ico", f"{project_name}.ico")
        
        if not os.path.exists(input_path):
            print(f"아이콘 파일을 찾을 수 없습니다: {input_path}")
            return False
            
        img = Image.open(input_path)
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        sizes = [(16,16), (32,32), (48,48), (256,256)]
        
        img_list = []
        for size in sizes:
            resized_img = img.resize(size, Image.Resampling.LANCZOS)
            img_list.append(resized_img)
        
        img_list[0].save(
            output_path,
            format='ICO',
            sizes=[(img.size[0], img.size[1]) for img in img_list],
            append_images=img_list[1:]
        )
        
        print(f"변환 완료: {output_path}")
        return True
        
    except Exception as e:
        print(f"아이콘 변환 실패: {str(e)}")
        return False

if __name__ == "__main__":
    convert_webp_to_ico()