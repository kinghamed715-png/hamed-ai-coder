from pathlib import Path
from datetime import datetime
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE = (BASE_DIR / "projects").resolve()
BACKUPS = (BASE_DIR / "backups").resolve()

def safe_path(relative_path):
    target = (WORKSPACE / relative_path).resolve()

    if target != WORKSPACE and WORKSPACE not in target.parents:
        raise ValueError("دسترسی به خارج از پوشه projects مجاز نیست.")

    return target

def list_files():
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    return [
        str(path.relative_to(WORKSPACE))
        for path in WORKSPACE.rglob("*")
        if path.is_file()
    ]

def read_file(relative_path):
    target = safe_path(relative_path)

    if not target.is_file():
        raise FileNotFoundError("فایل پیدا نشد.")

    if target.stat().st_size > 1_000_000:
        raise ValueError("حجم فایل بیشتر از حد مجاز است.")

    return target.read_text(encoding="utf-8")

def write_file(relative_path, content):
    target = safe_path(relative_path)

    if not isinstance(content, str):
        raise TypeError("محتوای فایل باید متن باشد.")

    if len(content.encode("utf-8")) > 1_000_000:
        raise ValueError("حجم فایل بیشتر از حد مجاز است.")

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        if not target.is_file():
            raise ValueError("مسیر مقصد یک فایل معمولی نیست.")

        BACKUPS.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup = BACKUPS / f"{timestamp}_{target.name}"
        shutil.copy2(target, backup)

    target.write_text(content, encoding="utf-8")
    return str(target.relative_to(WORKSPACE))
