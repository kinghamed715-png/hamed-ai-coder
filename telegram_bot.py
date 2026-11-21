
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from main import ask_ai, search_ai, load_json, save_json
from core.code_executor import execute_python
from core.workspace import safe_path, write_file


BASE_DIR = Path(__file__).parent
MEMORY_DIR = BASE_DIR / "memory" / "telegram"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OWNER_ID = int(os.getenv("TELEGRAM_OWNER_ID", "0"))

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

def get_session(user_id):
    path = MEMORY_DIR / f"{user_id}.json"
    data = load_json(path, {})
    return path, data.get("previous_interaction_id")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(
        "سلام! HAMED AI آماده است.\n"
        "پیامت را بفرست.\n"
        "/reset برای شروع گفتگوی تازه\n"
        "/search <English query> برای جست‌وجوی وب"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    path, _ = get_session(OWNER_ID)
    save_json(path, {})

    await update.message.reply_text("حافظه گفتگوی تلگرام پاک شد.")


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    query = " ".join(context.args).strip()

    if not query:
        await update.message.reply_text(
            "عبارت جست‌وجو را به انگلیسی وارد کن.\n"
            "مثال: /search latest artificial intelligence news"
        )
        return

    path, session_id = get_session(OWNER_ID)
    status = await update.message.reply_text(
        "در حال جست‌وجوی وب و تحلیل نتایج..."
    )

    try:
        import asyncio

        answer, new_session_id, error = await asyncio.to_thread(
            context.application.bot_data["search_ai"],
            query,
            session_id
        )

        if error:
            await status.edit_text(f"خطای جست‌وجو: {error[:3000]}")
            return

        save_json(
            path,
            {"previous_interaction_id": new_session_id}
        )

        for start_index in range(0, len(answer), 4000):
            chunk = answer[start_index:start_index + 4000]

            if start_index == 0:
                await status.edit_text(chunk)
            else:
                await update.message.reply_text(chunk)

    except Exception:
        logging.exception("Telegram search error")
        await status.edit_text("خطای داخلی هنگام جست‌وجو رخ داد.")



async def run_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "نام فایل را وارد کن.\n"
            "مثال: /run test_executor.py"
        )
        return

    filename = " ".join(context.args).strip()

    try:
        target = safe_path(filename)

        if not target.is_file():
            await update.message.reply_text("فایل پیدا نشد.")
            return

        if target.suffix.lower() != ".py":
            await update.message.reply_text(
                "فعلاً فقط فایل‌های Python قابل اجرا هستند."
            )
            return

        context.user_data["pending_run"] = filename

        await update.message.reply_text(
            f"درخواست اجرای فایل:\n"
            f"{filename}\n\n"
            "توجه: اجرای کد می‌تواند به فایل‌ها و امکانات "
            "Termux دسترسی داشته باشد. فقط کد مورد اعتماد را اجرا کن.\n\n"
            "برای تأیید: /confirm_run\n"
            "برای لغو: /cancel_run"
        )

    except Exception as error:
        await update.message.reply_text(
            f"خطا در بررسی فایل: {error}"
        )


async def confirm_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    filename = context.user_data.pop("pending_run", None)

    if not filename:
        await update.message.reply_text(
            "درخواست اجرای تأییدنشده‌ای وجود ندارد."
        )
        return

    import asyncio

    status = await update.message.reply_text(
        f"در حال اجرای {filename} ..."
    )

    try:
        success, output = await asyncio.to_thread(
            execute_python,
            filename
        )

        result = (
            "اجرای موفق" if success else "اجرای ناموفق"
        ) + "\n\n" + output

        for index in range(0, len(result), 3900):
            chunk = result[index:index + 3900]

            if index == 0:
                await status.edit_text(chunk)
            else:
                await update.message.reply_text(chunk)

    except Exception as error:
        await status.edit_text(
            f"خطای اجرای برنامه: {error}"
        )


async def cancel_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    context.user_data.pop("pending_run", None)

    await update.message.reply_text(
        "درخواست اجرای برنامه لغو شد."
    )


async def generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "روش استفاده:\n"
            "/code filename.py description\n\n"
            "Example:\n"
            "/code calculator.py Build a Python calculator"
        )
        return

    filename = context.args[0].strip()
    description = " ".join(context.args[1:]).strip()

    try:
        target = safe_path(filename)

        if target.suffix.lower() != ".py":
            await update.message.reply_text(
                "فعلاً فقط فایل Python با پسوند .py مجاز است."
            )
            return

        if target.exists() and not target.is_file():
            await update.message.reply_text(
                "مسیر مقصد یک فایل معمولی نیست."
            )
            return

    except Exception as error:
        await update.message.reply_text(
            f"مسیر فایل معتبر نیست: {error}"
        )
        return

    import asyncio

    status = await update.message.reply_text(
        "در حال تولید کد با هوش مصنوعی..."
    )

    path, session_id = get_session(OWNER_ID)

    prompt = (
        "You are a professional Python programmer.\n"
        "Create a complete, working Python source file.\n"
        "Return ONLY the raw Python code. No Markdown fences, "
        "no explanations, and no introductory text.\n"
        "Use clear variable names and handle common errors.\n\n"
        f"Required filename: {filename}\n"
        f"User requirements: {description}"
    )

    try:
        answer, new_session_id, error = await asyncio.to_thread(
            context.application.bot_data["ask_ai"],
            prompt,
            session_id
        )

        if error:
            await status.edit_text(
                f"خطای هوش مصنوعی:\n{str(error)[:3000]}"
            )
            return

        if not answer or not answer.strip():
            await status.edit_text("هوش مصنوعی کدی تولید نکرد.")
            return

        import re

        candidate = answer.strip()

        match = re.fullmatch(
            r"```(?:python)?\s*(.*?)```",
            candidate,
            flags=re.DOTALL | re.IGNORECASE
        )

        if match:
            candidate = match.group(1).strip()

        if len(candidate.encode("utf-8")) > 100_000:
            await status.edit_text(
                "حجم کد تولیدشده بیش از حد مجاز است."
            )
            return

        if not candidate:
            await status.edit_text("کد تولیدشده خالی است.")
            return

        context.user_data["pending_code"] = {
            "filename": filename,
            "content": candidate,
        }

        save_json(
            path,
            {"previous_interaction_id": new_session_id}
        )

        preview = candidate[:2500]

        message = (
            f"کد با موفقیت تولید شد.\n\n"
            f"نام فایل: {filename}\n"
            f"حجم کد: {len(candidate.encode('utf-8'))} bytes\n\n"
            f"پیش‌نمایش:\n\n{preview}\n\n"
            "برای ذخیره فایل:\n"
            "/confirm_code\n\n"
            "برای لغو:\n"
            "/cancel_code"
        )

        if len(candidate) > 2500:
            message += "\n\nادامه کد در پیش‌نمایش نمایش داده نشده است."

        await status.edit_text(message)

    except Exception:
        logging.exception("Code generation error")
        await status.edit_text(
            "خطای داخلی هنگام تولید کد رخ داد."
        )


async def confirm_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    pending = context.user_data.get("pending_code")

    if not pending:
        await update.message.reply_text(
            "کد تأییدنشده‌ای برای ذخیره وجود ندارد."
        )
        return

    filename = pending["filename"]
    content = pending["content"]

    try:
        target = safe_path(filename)

        if target.suffix.lower() != ".py":
            raise ValueError("پسوند فایل مجاز نیست.")

        saved_path = write_file(filename, content)

        context.user_data.pop("pending_code", None)

        await update.message.reply_text(
            f"فایل با موفقیت ذخیره شد.\n"
            f"مسیر: projects/{saved_path}\n\n"
            f"برای بررسی و اجرای فایل:\n"
            f"/run {filename}"
        )

    except Exception as error:
        logging.exception("Code saving error")
        await update.message.reply_text(
            f"ذخیره فایل ناموفق بود:\n{error}"
        )


async def cancel_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    pending = context.user_data.pop("pending_code", None)

    if pending:
        await update.message.reply_text(
            "درخواست تولید و ذخیره کد لغو شد."
        )
    else:
        await update.message.reply_text(
            "درخواست تأییدنشده‌ای وجود ندارد."
        )


async def fix_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "روش استفاده:\n/fix filename.py"
        )
        return

    filename = " ".join(context.args).strip()

    try:
        target = safe_path(filename)

        if target.suffix.lower() != ".py":
            raise ValueError("فقط فایل Python مجاز است.")

        if not target.is_file():
            raise FileNotFoundError("فایل پیدا نشد.")

        if target.stat().st_size > 1_000_000:
            raise ValueError("حجم فایل بیش از حد مجاز است.")

        content = target.read_text(encoding="utf-8")

        context.user_data["pending_fix_run"] = {
            "filename": filename,
            "content": content,
        }

        await update.message.reply_text(
            f"فایل آماده بررسی است:\n{filename}\n\n"
            "برای اجرای فایل و تشخیص خطا:\n"
            "/confirm_fix_run\n\n"
            "برای لغو:\n/cancel_fix\n\n"
            "توجه: اجرای فایل ممکن است به امکانات Termux دسترسی داشته باشد."
        )

    except Exception as error:
        await update.message.reply_text(f"خطا: {error}")


async def confirm_fix_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    pending = context.user_data.pop("pending_fix_run", None)

    if not pending:
        await update.message.reply_text(
            "درخواست بررسی تأییدنشده‌ای وجود ندارد."
        )
        return

    import asyncio

    filename = pending["filename"]
    status = await update.message.reply_text(
        f"در حال بررسی و اجرای {filename} ..."
    )

    try:
        success, output = await asyncio.to_thread(
            execute_python, filename
        )

        if success:
            await status.edit_text(
                "اجرای فایل موفق بود؛ خطایی برای اصلاح گزارش نشد.\n\n"
                + output[:3000]
            )
            return

        await status.edit_text(
            "خطا شناسایی شد. در حال ارسال کد و خروجی خطا به هوش مصنوعی..."
        )

        prompt = (
            "You are an expert Python debugging assistant.\n"
            "Analyze the Python source and execution error below.\n"
            "Return ONLY the complete corrected Python source code.\n"
            "Do not use Markdown fences or explanations.\n"
            "Preserve the original intended behavior. Do not add "
            "dangerous operations, network calls, or file deletion.\n\n"
            "FILENAME:\n" + filename + "\n\n"
            "SOURCE CODE:\n" + pending["content"] + "\n\n"
            "EXECUTION ERROR:\n" + output
        )

        answer, _, error = await asyncio.to_thread(
            context.application.bot_data["ask_ai"],
            prompt,
            None
        )

        if error:
            await status.edit_text(
                f"خطای هوش مصنوعی:\n{str(error)[:3000]}"
            )
            return

        candidate = (answer or "").strip()

        import re
        match = re.fullmatch(
            r"```(?:python)?\s*(.*?)```",
            candidate,
            flags=re.DOTALL | re.IGNORECASE
        )
        if match:
            candidate = match.group(1).strip()

        if not candidate:
            await status.edit_text("کد اصلاح‌شده خالی است.")
            return

        if len(candidate.encode("utf-8")) > 100_000:
            await status.edit_text("حجم کد اصلاح‌شده بیش از حد مجاز است.")
            return

        try:
            compile(candidate, filename, "exec")
        except SyntaxError as syntax_error:
            await status.edit_text(
                "کد پیشنهادی هنوز خطای نحوی دارد:\n"
                f"{syntax_error}"
            )
            return

        context.user_data["pending_fix"] = {
            "filename": filename,
            "content": candidate,
        }

        preview = candidate[:2500]
        message = (
            "نسخه پیشنهادی تولید شد و بررسی نحوی آن موفق بود.\n\n"
            f"فایل: {filename}\n\n"
            f"پیش‌نمایش:\n{preview}\n\n"
            "برای جایگزینی فایل اصلی و ایجاد پشتیبان:\n"
            "/confirm_fix\n\n"
            "برای لغو:\n/cancel_fix"
        )

        if len(candidate) > 2500:
            message += "\nادامه کد در پیش‌نمایش نمایش داده نشده است."

        await status.edit_text(message)

    except Exception as error:
        logging.exception("Automatic code fix error")
        await status.edit_text(f"خطا در فرایند اصلاح:\n{str(error)[:2500]}")


async def confirm_fix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    pending = context.user_data.get("pending_fix")

    if not pending:
        await update.message.reply_text(
            "نسخه اصلاح‌شده‌ای برای تأیید وجود ندارد."
        )
        return

    try:
        filename = pending["filename"]
        target = safe_path(filename)

        if not target.is_file():
            raise FileNotFoundError(
                "فایل اصلی دیگر وجود ندارد؛ جایگزینی انجام نشد."
            )

        saved_path = write_file(filename, pending["content"])
        context.user_data.pop("pending_fix", None)

        await update.message.reply_text(
            "نسخه اصلاح‌شده ذخیره شد.\n"
            f"مسیر: projects/{saved_path}\n"
            "اگر فایل قبلی وجود داشته، نسخه پشتیبان ساخته شده است.\n\n"
            f"برای آزمایش نسخه جدید:\n/run {filename}"
        )

    except Exception as error:
        logging.exception("Fix confirmation error")
        await update.message.reply_text(
            f"ذخیره نسخه اصلاح‌شده ناموفق بود:\n{error}"
        )


async def cancel_fix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    context.user_data.pop("pending_fix", None)
    context.user_data.pop("pending_fix_run", None)

    await update.message.reply_text(
        "درخواست اصلاح خطا لغو شد. فایل اصلی تغییر نکرد."
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    prompt = update.message.text.strip()
    if not prompt:
        return

    path, session_id = get_session(OWNER_ID)

    status = await update.message.reply_text("در حال دریافت پاسخ...")

    try:
        import asyncio

        answer, new_session_id, error = await asyncio.to_thread(
            context.application.bot_data["ask_ai"],
            prompt,
            session_id
        )

        if error:
            await status.edit_text(f"خطا: {error[:3000]}")
            return

        save_json(
            path,
            {"previous_interaction_id": new_session_id}
        )

        for start_index in range(0, len(answer), 4000):
            chunk = answer[start_index:start_index + 4000]

            if start_index == 0:
                await status.edit_text(chunk)
            else:
                await update.message.reply_text(chunk)

    except Exception:
        logging.exception("Telegram chat error")
        await status.edit_text("خطای داخلی رخ داد.")

def main():
    if not TOKEN or not OWNER_ID:
        raise RuntimeError("تنظیمات تلگرام در فایل .env ناقص است.")

    telegram_request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        pool_timeout=30,
    )

    updates_request = HTTPXRequest(
        connection_pool_size=1,
        connect_timeout=30,
        read_timeout=45,
        write_timeout=30,
        pool_timeout=30,
    )

    app = (
        Application.builder()
        .token(TOKEN)
        .request(telegram_request)
        .get_updates_request(updates_request)
        .build()
    )
    app.bot_data["ask_ai"] = ask_ai
    app.bot_data["search_ai"] = search_ai

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("run", run_code))
    app.add_handler(CommandHandler("code", generate_code))
    app.add_handler(CommandHandler("confirm_code", confirm_code))
    app.add_handler(CommandHandler("cancel_code", cancel_code))
    app.add_handler(CommandHandler("confirm_run", confirm_run))
    app.add_handler(CommandHandler("cancel_run", cancel_run))
    app.add_handler(CommandHandler("fix", fix_code))
    app.add_handler(CommandHandler("confirm_fix_run", confirm_fix_run))
    app.add_handler(CommandHandler("confirm_fix", confirm_fix))
    app.add_handler(CommandHandler("cancel_fix", cancel_fix))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    )

    print("HAMED AI TELEGRAM is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
