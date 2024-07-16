# services/file_service.py

import re
from io import BytesIO
from flask import send_file

def generate_filename(content, prefix='minutes'):
    """
    議事録の内容からファイル名を生成する関数

    Args:
        content (str): 議事録の内容
        prefix (str): ファイル名のプレフィックス（デフォルトは'minutes'）

    Returns:
        str: 生成されたファイル名
    """
    # 最初の見出しを取得
    title_match = re.search(r'^#\s*(.+)$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1)
    else:
        title = "Untitled"
    
    # タイトルを半角英数字に変換
    filename = re.sub(r'[^\w\s-]', '', title.lower())
    filename = re.sub(r'[-\s]+', '_', filename)
    
    return f"{prefix}_{filename[:50]}"

def format_content(content):
    """
    コンテンツをフォーマットする関数

    Args:
        content (str): フォーマットする内容

    Returns:
        str: フォーマットされた内容
    """
    # 行間に空行を追加
    formatted_content = re.sub(r'\n(?!\n)', '\n\n', content)
    return formatted_content

def prepare_download_file(minutes, file_type):
    """
    ダウンロード用のファイルを準備する関数

    Args:
        minutes (str): 議事録の内容
        file_type (str): ファイルタイプ ('text' または 'markdown')

    Returns:
        tuple: (ファイル名, ファイルコンテンツ, MIMEタイプ)
        または None（無効なファイルタイプの場合）
    """
    if file_type == 'text':
        filename = generate_filename(minutes, 'minutes_text') + '.txt'
        content = re.sub(r'#+ ', '', minutes)  # 見出しの '#' を削除
        content = format_content(content)
        mimetype = 'text/plain'
    elif file_type == 'markdown':
        filename = generate_filename(minutes, 'minutes_md') + '.md'
        content = format_content(minutes)
        mimetype = 'text/markdown'
    else:
        return None

    return filename, content, mimetype

def create_download_file(filename, content, mimetype):
    """
    ダウンロード可能なファイルオブジェクトを作成する関数

    Args:
        filename (str): ファイル名
        content (str): ファイルの内容
        mimetype (str): ファイルのMIMEタイプ

    Returns:
        flask.send_file: ダウンロード可能なファイルオブジェクト
    """
    return send_file(
        BytesIO(content.encode('utf-8')),
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )