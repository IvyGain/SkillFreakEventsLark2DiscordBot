"""
メインアプリケーション
Lark to Discord Events Bot のエントリーポイント
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings
from src.utils.logger import setup_application_logging, get_logger
from src.discord.bot import EventsBot
from src.services.scheduler import scheduler_service, task_manager
from src.webhook.service import webhook_service
from src.utils.helpers import timing_decorator

logger = get_logger(__name__)


class Application:
    """メインアプリケーションクラス"""
    
    def __init__(self):
        self.bot = None
        self.shutdown_event = asyncio.Event()
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """シグナルハンドラーの設定"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    @timing_decorator
    async def initialize(self):
        """アプリケーションの初期化"""
        logger.info("Initializing Lark to Discord Events Bot...")
        
        try:
            # 設定の検証
            await self._validate_settings()
            
            # Botの初期化
            self.bot = EventsBot()
            
            # スケジューラーの設定
            await self._setup_scheduler()
            
            # Webhookサーバーの初期化
            await self._setup_webhook_server()
            
            logger.info("Application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            raise
    
    async def _validate_settings(self):
        """設定の検証"""
        logger.info("Validating configuration...")
        
        # 必須設定のチェック
        required_settings = [
            ('discord.bot_token', settings.discord.bot_token),
            ('discord.guild_id', settings.discord.guild_id),
            ('discord.notification_channel_id', settings.discord.notification_channel_id),
            ('discord.archive_forum_id', settings.discord.archive_forum_id),
            ('lark.app_id', settings.lark.app_id),
            ('lark.app_secret', settings.lark.app_secret),
            ('lark.table_id', settings.lark.table_id),
        ]
        
        missing_settings = []
        for name, value in required_settings:
            if not value:
                missing_settings.append(name)
        
        if missing_settings:
            raise ValueError(f"Missing required settings: {', '.join(missing_settings)}")
        
        logger.info("Configuration validation completed")
    
    async def _setup_scheduler(self):
        """スケジューラーの設定"""
        logger.info("Setting up scheduler...")
        
        try:
            # 日次通知ジョブ
            scheduler_service.add_daily_notification_job(
                self.bot.send_today_events_notification,
                "daily_notification"
            )
            
            # アーカイブジョブ（日次）
            scheduler_service.add_archive_job(
                self.bot.create_archive_threads,
                "archive_events"
            )
            
            # 終了したイベントのアーカイブジョブ（1時間間隔）
            scheduler_service.add_ended_events_archive_job(
                self.bot.create_recently_ended_archive_threads,
                hours_interval=1,
                job_id="ended_events_archive"
            )
            
            # Peatix公開済みイベントチェックジョブ（30分間隔）
            scheduler_service.add_peatix_event_check_job(
                self.bot.check_and_create_events_for_published_peatix,
                minutes_interval=30,
                job_id="peatix_event_check"
            )
            
            # スケジューラー開始
            scheduler_service.start()
            
            logger.info("Scheduler setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup scheduler: {str(e)}")
            raise
    
    async def _setup_webhook_server(self):
        """Webhookサーバーの設定"""
        logger.info("Setting up webhook server...")
        
        try:
            # Webhookサーバーの開始
            webhook_host = getattr(settings, 'webhook_host', '0.0.0.0')
            webhook_port = getattr(settings, 'webhook_port', 8000)
            
            await webhook_service.start(
                bot=self.bot,
                lark_client=self.bot.lark_client,
                host=webhook_host,
                port=webhook_port
            )
            
            # Webhook URLsをログに出力
            webhook_urls = webhook_service.get_webhook_urls(
                host=webhook_host if webhook_host != '0.0.0.0' else 'localhost',
                port=webhook_port
            )
            
            logger.info("Webhook server setup completed")
            logger.info("Available webhook endpoints:")
            for name, url in webhook_urls.items():
                logger.info(f"  {name}: {url}")
            
        except Exception as e:
            logger.error(f"Failed to setup webhook server: {str(e)}")
            raise
    
    @timing_decorator
    async def run(self):
        """アプリケーションの実行"""
        logger.info("Starting Lark to Discord Events Bot...")
        
        try:
            # Botの開始
            bot_task = asyncio.create_task(self.bot.start(settings.discord.bot_token))
            
            # シャットダウンイベントの待機
            shutdown_task = asyncio.create_task(self.shutdown_event.wait())
            
            # いずれかのタスクが完了するまで待機
            done, pending = await asyncio.wait(
                [bot_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 残りのタスクをキャンセル
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # 完了したタスクの例外をチェック
            for task in done:
                if task.exception():
                    raise task.exception()
            
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            raise
        finally:
            await self.cleanup()
    
    async def shutdown(self):
        """アプリケーションのシャットダウン"""
        logger.info("Shutting down application...")
        
        try:
            # シャットダウンイベントを設定
            self.shutdown_event.set()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
    
    async def cleanup(self):
        """リソースのクリーンアップ"""
        logger.info("Cleaning up resources...")
        
        try:
            # Webhookサーバーの停止
            await webhook_service.stop()
            
            # スケジューラーの停止
            if scheduler_service.scheduler.running:
                scheduler_service.shutdown()
            
            # 実行中タスクのキャンセル
            task_manager.cancel_all_tasks()
            
            # Botの停止
            if self.bot and not self.bot.is_closed():
                await self.bot.close()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


async def main():
    """メイン関数"""
    # ログ設定
    setup_application_logging()
    
    logger.info("=" * 50)
    logger.info("Lark to Discord Events Bot Starting")
    logger.info("=" * 50)
    
    app = Application()
    
    try:
        # アプリケーションの初期化
        await app.initialize()
        
        # アプリケーションの実行
        await app.run()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Application failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Application stopped")


def run_bot():
    """Bot実行用の関数（外部から呼び出し可能）"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Bot failed to start: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run_bot()