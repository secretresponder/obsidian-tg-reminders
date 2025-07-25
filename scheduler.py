# scheduler.py
#!/usr/bin/env python3
import asyncio
import logging
import sys
from telegram import Bot
from telegram.ext import Application, ApplicationBuilder, CallbackQueryHandler

from done_handler import handle_done_button
from utils import load_config
from memory import load_sent_flags
from notifier import notification_loop, task_list
from heartbeat import heartbeat
from sender import build_send_notification

sys.stdout.reconfigure(encoding='utf-8')  # 💡 добавь это до логгера

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

log = logging.getLogger("scheduler")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)

def build_application(config) -> Application:
    app = ApplicationBuilder().token(config["TELEGRAM_TOKEN"]).build()
    app.add_handler(CallbackQueryHandler(lambda u, c: handle_done_button(u, c, task_list), pattern=r"^done::"))
    return app

async def safe_polling(app_factory):
    while True:
        try:
            log.info("🚀 Launching polling manually")
            app = app_factory()

            try:
                await app.initialize()
                log.info("✅ Initialized application")
            except Exception as init_error:
                log.error(f"❌ Initialization failed: {init_error}", exc_info=True)
                raise init_error

            await app.start()
            await app.updater.start_polling()
            log.info("📡 Polling started")

            while True:
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            log.warning("⚠️ Polling manually cancelled")
            break

        except Exception as e:
            log.error(f"🔥 Polling crashed: {e}", exc_info=True)
            log.info("⏳ Restarting in 5 seconds…")
            await asyncio.sleep(5)

        finally:
            try:
                if 'app' in locals() and app.running:
                    log.info("🛑 Stopping application...")
                    await app.updater.stop()
                    await app.stop()
                    await app.shutdown()
                    log.info("✅ Application stopped cleanly")
            except Exception as shutdown_error:
                log.error(f"🧹 Error during shutdown: {shutdown_error}", exc_info=True)

async def main():
    config = load_config()

    required_keys = [
        "TELEGRAM_TOKEN",
        "CHAT_ID",
        "TASKS_FOLDER",
        "default_warn_before_start",
        "default_warn_during",
        "default_warn_overdue",
    ]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing required config key: {key}")

    sent_flags = load_sent_flags()
    bot = Bot(token=config["TELEGRAM_TOKEN"])
    send_func = build_send_notification(bot)
    app = build_application(config)

    await asyncio.gather(
        notification_loop(
            folder_path=config["TASKS_FOLDER"],
            warn_before=config["default_warn_before_start"],
            warn_during=config["default_warn_during"],
            warn_overdue=config["default_warn_overdue"],
            send_func=send_func,
            sent_flags=sent_flags,
        ),
        heartbeat(bot),
        safe_polling(lambda: build_application(config))
    )

if __name__ == "__main__":
    asyncio.run(main())
