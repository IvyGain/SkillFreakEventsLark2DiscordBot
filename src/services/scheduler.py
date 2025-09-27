"""
スケジューラーサービス
定期実行タスクの管理
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import pytz

from ..config.settings import settings

logger = logging.getLogger(__name__)


class SchedulerService:
    """スケジューラーサービス"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            timezone=pytz.timezone(settings.timezone)
        )
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """スケジューラーイベントリスナーの設定"""
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )
    
    def _job_executed_listener(self, event):
        """ジョブ実行完了リスナー"""
        logger.info(f"Job executed successfully: {event.job_id}")
    
    def _job_error_listener(self, event):
        """ジョブエラーリスナー"""
        logger.error(f"Job {event.job_id} failed: {event.exception}")
    
    def start(self):
        """スケジューラー開始"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
    
    def shutdown(self):
        """スケジューラー停止"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def add_daily_notification_job(self, func: Callable, job_id: str = "daily_notification"):
        """日次通知ジョブを追加"""
        try:
            # 既存のジョブを削除
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Cron式をパース
            cron_parts = settings.daily_notification_cron.split()
            if len(cron_parts) != 5:
                raise ValueError("Invalid cron format")
            
            minute, hour, day, month, day_of_week = cron_parts
            
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=pytz.timezone(settings.timezone)
            )
            
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name="Daily Event Notification",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300  # 5分の猶予時間
            )
            
            logger.info(f"Daily notification job added: {settings.daily_notification_cron}")
            
        except Exception as e:
            logger.error(f"Failed to add daily notification job: {str(e)}")
            raise
    
    def add_archive_job(self, func: Callable, job_id: str = "archive_events"):
        """アーカイブジョブを追加"""
        try:
            # 既存のジョブを削除
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Cron式をパース
            cron_parts = settings.archive_cron.split()
            if len(cron_parts) != 5:
                raise ValueError("Invalid cron format")
            
            minute, hour, day, month, day_of_week = cron_parts
            
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=pytz.timezone(settings.timezone)
            )
            
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name="Archive Events",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=600  # 10分の猶予時間
            )
            
            logger.info(f"Archive job added: {settings.archive_cron}")
            
        except Exception as e:
            logger.error(f"Failed to add archive job: {str(e)}")
            raise
    
    def add_interval_job(self, func: Callable, seconds: int, job_id: str, **kwargs):
        """インターバルジョブを追加"""
        try:
            # 既存のジョブを削除
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            trigger = IntervalTrigger(seconds=seconds)
            
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                max_instances=1,
                coalesce=True,
                **kwargs
            )
            
            logger.info(f"Interval job added: {job_id} (every {seconds}s)")
            
        except Exception as e:
            logger.error(f"Failed to add interval job {job_id}: {str(e)}")
            raise
    
    def add_ended_events_archive_job(self, func: Callable, hours_interval: int = 1, job_id: str = "ended_events_archive"):
        """終了したイベントのアーカイブジョブを追加（定期実行）"""
        try:
            # 既存のジョブを削除
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # 指定時間間隔でトリガー
            trigger = IntervalTrigger(hours=hours_interval)
            
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name="Archive Recently Ended Events",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=1800  # 30分の猶予時間
            )
            
            logger.info(f"Ended events archive job added: every {hours_interval} hour(s)")
            
        except Exception as e:
            logger.error(f"Failed to add ended events archive job: {str(e)}")
            raise
    
    def add_peatix_event_check_job(self, func: Callable, minutes_interval: int = 30, job_id: str = "peatix_event_check"):
        """Peatix公開済みイベントをチェックしてDiscordイベントを作成するジョブを追加"""
        try:
            # 既存のジョブを削除
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # 指定分間隔でトリガー
            trigger = IntervalTrigger(minutes=minutes_interval)
            
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name="Check Peatix Published Events",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=900  # 15分の猶予時間
            )
            
            logger.info(f"Peatix event check job added: every {minutes_interval} minute(s)")
            
        except Exception as e:
            logger.error(f"Failed to add Peatix event check job: {str(e)}")
            raise
    
    def remove_job(self, job_id: str):
        """ジョブを削除"""
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Job removed: {job_id}")
            else:
                logger.warning(f"Job not found: {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {str(e)}")
    
    def get_job_info(self, job_id: str) -> Optional[dict]:
        """ジョブ情報を取得"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger),
                    'func': job.func.__name__ if job.func else None
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get job info {job_id}: {str(e)}")
            return None
    
    def list_jobs(self) -> list:
        """全ジョブのリストを取得"""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger)
                })
            return jobs
        except Exception as e:
            logger.error(f"Failed to list jobs: {str(e)}")
            return []
    
    def pause_job(self, job_id: str):
        """ジョブを一時停止"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job paused: {job_id}")
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {str(e)}")
    
    def resume_job(self, job_id: str):
        """ジョブを再開"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job resumed: {job_id}")
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {str(e)}")
    
    def modify_job(self, job_id: str, **changes):
        """ジョブを変更"""
        try:
            self.scheduler.modify_job(job_id, **changes)
            logger.info(f"Job modified: {job_id}")
        except Exception as e:
            logger.error(f"Failed to modify job {job_id}: {str(e)}")
    
    async def run_job_now(self, job_id: str):
        """ジョブを即座に実行"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                await job.func()
                logger.info(f"Job executed manually: {job_id}")
            else:
                logger.warning(f"Job not found: {job_id}")
        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {str(e)}")
            raise


class TaskManager:
    """タスク管理クラス"""
    
    def __init__(self):
        self.running_tasks = {}
    
    async def run_task_with_timeout(self, 
                                   coro: Callable, 
                                   timeout: int = 300,
                                   task_name: str = "unnamed_task") -> Any:
        """タイムアウト付きでタスクを実行"""
        try:
            # 既存のタスクをキャンセル
            if task_name in self.running_tasks:
                self.running_tasks[task_name].cancel()
            
            # 新しいタスクを開始
            task = asyncio.create_task(coro)
            self.running_tasks[task_name] = task
            
            result = await asyncio.wait_for(task, timeout=timeout)
            
            # 完了したタスクを削除
            if task_name in self.running_tasks:
                del self.running_tasks[task_name]
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task_name} timed out after {timeout}s")
            if task_name in self.running_tasks:
                self.running_tasks[task_name].cancel()
                del self.running_tasks[task_name]
            raise
            
        except Exception as e:
            logger.error(f"Task {task_name} failed: {str(e)}")
            if task_name in self.running_tasks:
                del self.running_tasks[task_name]
            raise
    
    def cancel_task(self, task_name: str):
        """タスクをキャンセル"""
        if task_name in self.running_tasks:
            self.running_tasks[task_name].cancel()
            del self.running_tasks[task_name]
            logger.info(f"Task cancelled: {task_name}")
    
    def cancel_all_tasks(self):
        """全タスクをキャンセル"""
        for task_name, task in self.running_tasks.items():
            task.cancel()
            logger.info(f"Task cancelled: {task_name}")
        self.running_tasks.clear()
    
    def get_running_tasks(self) -> list:
        """実行中のタスクリストを取得"""
        return list(self.running_tasks.keys())


# グローバルインスタンス
scheduler_service = SchedulerService()
task_manager = TaskManager()