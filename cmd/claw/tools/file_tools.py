"""
文件操作工具：read_file / write_file / edit_file
所有路径都相对于 workspace 目录
"""
import os

WORKSPACE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "workspace")


def _safe_path(filename: str):
    """
    把用户给的相对路径解析到 workspace 目录下
    :return: (绝对路径, 错误信息)。路径非法时路径为 None
    """
    full = os.path.normpath(os.path.join(WORKSPACE, filename))
    root = os.path.normpath(WORKSPACE)
    # 必须严格落在 workspace 目录内
    if full != root and not full.startswith(root + os.sep):
        return None, f"禁止访问 workspace 以外的路径: {filename}"
    return full, None


def read_file(filename: str) -> str:
    """
    读取文件内容（只读操作）
    :param filename: 相对 workspace 的文件名
    :return: 文件文本内容
    """
    path, err = _safe_path(filename)
    if err:
        return f"[错误] {err}"
    if not os.path.exists(path):
        return f"[错误] 文件不存在: {filename}"
    if os.path.isdir(path):
        return f"[错误] 这是一个目录，不是文件: {filename}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return f"文件 {filename} 内容如下：\n{content}"


def write_file(filename: str, content: str) -> str:
    """
    写入文件（写操作，会覆盖已有内容）
    :param filename: 相对 workspace 的文件名
    :param content: 要写入的完整内容
    """
    path, err = _safe_path(filename)
    if err:
        return f"[错误] {err}"
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"成功写入文件 {filename}（共 {len(content)} 字符）"


def edit_file(filename: str, old_text: str, new_text: str) -> str:
    """
    编辑文件：把 old_text 替换成 new_text（写操作）
    :param filename: 相对 workspace 的文件名
    :param old_text: 要被替换的原文
    :param new_text: 替换后的新内容
    """
    path, err = _safe_path(filename)
    if err:
        return f"[错误] {err}"
    if not os.path.exists(path):
        return f"[错误] 文件不存在: {filename}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if old_text not in content:
        return f"[错误] 在 {filename} 中找不到要替换的内容"
    new_content = content.replace(old_text, new_text, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return f"成功编辑文件 {filename}"
