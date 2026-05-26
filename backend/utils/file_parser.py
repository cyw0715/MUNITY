"""文件解析工具 - 提取 docx 文件文本内容"""
import os

# 上传目录 - 与 staff.py 保持一致
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


def extract_text_from_docx(file_path: str) -> str:
    """从 docx 文件中提取文本内容"""
    if not os.path.exists(file_path):
        return ""
    
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"[FileParser] 解析 docx 失败: {e}")
        return ""


def extract_text_from_file(filename: str) -> str:
    """根据文件名提取文本（自动拼接上传目录）"""
    if not filename:
        return ""
    
    # 拼接完整路径
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        print(f"[FileParser] 文件不存在: {file_path}")
        return ""
    
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    else:
        return ""
