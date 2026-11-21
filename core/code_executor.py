import os
import sys
import subprocess
from pathlib import Path

from core.workspace import WORKSPACE, safe_path


MAX_FILE_SIZE = 1_000_000
MAX_OUTPUT_SIZE = 12_000
DEFAULT_TIMEOUT = 30


def execute_python(relative_path, timeout=DEFAULT_TIMEOUT):
    try:
        target = safe_path(relative_path)

        if not target.is_file():
            return False, "فایل پیدا نشد."

        if target.suffix.lower() != ".py":
            return False, "فعلاً فقط فایل‌های Python قابل اجرا هستند."

        if target.stat().st_size > MAX_FILE_SIZE:
            return False, "حجم فایل بیش از حد مجاز است."

        WORKSPACE.mkdir(parents=True, exist_ok=True)

        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "TMPDIR": os.environ.get("TMPDIR", ""),
            "PREFIX": os.environ.get("PREFIX", ""),
            "LANG": "C.UTF-8",
            "PYTHONIOENCODING": "utf-8",
        }

        result = subprocess.run(
            [sys.executable, str(target)],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            check=False,
        )

        output = (
            (result.stdout or "")
            + ("\n" + result.stderr if result.stderr else "")
        ).strip()

        if not output:
            output = "برنامه اجرا شد و خروجی متنی نداشت."

        if len(output) > MAX_OUTPUT_SIZE:
            output = output[:MAX_OUTPUT_SIZE] + "\n... خروجی کوتاه شد."

        return result.returncode == 0, (
            f"Exit code: {result.returncode}\n\n{output}"
        )

    except subprocess.TimeoutExpired:
        return False, f"زمان اجرای برنامه از {timeout} ثانیه بیشتر شد."

    except (ValueError, OSError, RuntimeError) as error:
        return False, f"خطای اجرا: {error}"

    except Exception as error:
        return False, f"خطای غیرمنتظره: {error}"
