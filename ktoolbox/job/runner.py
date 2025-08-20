import asyncio
from asyncio import CancelledError
from functools import cached_property
from types import MappingProxyType
from typing import List, Set, Dict
from urllib.parse import urlunparse

import httpx
from loguru import logger
from tqdm import tqdm as std_tqdm

from ktoolbox._enum import RetCodeEnum
from ktoolbox.configuration import config
from ktoolbox.downloader import Downloader
from ktoolbox.job import Job
from ktoolbox.progress import ProgressManager, create_managed_tqdm_class, setup_logger_for_progress
from ktoolbox.utils import generate_msg

__all__ = ["JobRunner"]


class JobRunner:
    def __init__(self, *, job_list: List[Job] = None, tqdm_class: std_tqdm = None, progress: bool = True,
                 centralized_progress: bool = True, use_colors: bool = True, use_emojis: bool = True):
        """
        Create a job runner

        :param job_list: Jobs to initial ``self._job_queue``
        :param tqdm_class: ``tqdm`` class to replace default ``tqdm.asyncio.tqdm``
        :param progress: Show progress bar
        :param centralized_progress: Use centralized progress manager to prevent display chaos
        :param use_colors: Enable colorful progress bars (requires ANSI terminal support)
        :param use_emojis: Enable emoji indicators in progress bars
        """
        job_list = job_list or []
        self._job_queue: asyncio.Queue[Job] = asyncio.Queue()
        for job in job_list:
            self._job_queue.put_nowait(job)

        # Initialize progress management
        self._progress = progress
        self._centralized_progress = centralized_progress and progress

        if self._centralized_progress:
            # Use centralized progress manager with enhanced visuals
            self._progress_manager = ProgressManager(
                max_workers=config.job.count,
                use_colors=use_colors,
                use_emojis=use_emojis
            )
            self._tqdm_class = tqdm_class or create_managed_tqdm_class(self._progress_manager)
        else:
            # Use traditional tqdm
            self._progress_manager = None
            self._tqdm_class = tqdm_class

        self._downloaders_with_task: Dict[Downloader, asyncio.Task] = {}
        self._concurrent_tasks: Set[asyncio.Task] = set()
        self._lock = asyncio.Lock()
        self._total_jobs_count = len(job_list)

    @property
    def finished(self):
        """
        Check if all jobs finished

        :return: ``False`` if **in process**, ``False`` otherwise
        """
        return not self._lock.locked()

    @cached_property
    def downloaders(self):
        """Get downloaders with task"""
        return MappingProxyType(self._downloaders_with_task)

    @property
    def waiting_size(self) -> int:
        """Get the number of jobs waiting to be processed"""
        return self._job_queue.qsize()

    @property
    def done_size(self) -> int:
        """Get the number of jobs that done"""
        size = 0
        for downloader, task in self._downloaders_with_task.items():
            if downloader.finished or task.done():
                size += 1
        return size

    @property
    def processing_size(self) -> int:
        """Get the number of jobs that in process"""
        return len(self._downloaders_with_task) - self.done_size

    async def processor(self) -> int:
        """
        Process each job in ``self._job_queue``

        :return: Number of jobs that failed
        """
        failed_num = 0
        async with httpx.AsyncClient(
                verify=config.ssl_verify,
                cookies={"session": config.api.session_key} if config.api.session_key else None
        ) as client:
            while not self._job_queue.empty():
                job = await self._job_queue.get()

                # Create downloader
                url_parts = [config.downloader.scheme, config.api.files_netloc, job.server_path, '', '', '']
                url = str(urlunparse(url_parts))
                downloader = Downloader(
                    url=url,
                    path=job.path,
                    client=client,
                    designated_filename=job.alt_filename,
                    server_path=job.server_path,
                    post=job.post
                )

                # Create task
                task = asyncio.create_task(
                    downloader.run(
                        tqdm_class=self._tqdm_class,
                        progress=self._progress
                    )
                )
                self._downloaders_with_task[downloader] = task
                # task.add_done_callback(lambda _: self._downloaders_with_task.pop(downloader))
                #   Delete this for counting finished job tasks

                # Run task
                task_done_set, _ = await asyncio.wait([task], return_when=asyncio.FIRST_EXCEPTION)
                task_done = task_done_set.pop()
                try:
                    exception = task_done.exception()
                except CancelledError as e:
                    exception = e
                if not exception:  # raise Exception when cancelled or other exceptions
                    ret = task_done.result()
                    if ret.code == RetCodeEnum.FileExisted:
                        logger.info(ret.message)
                        # Treat file existed as successful download
                        if self._progress_manager:
                            self._progress_manager.update_job_progress(
                                completed=self.done_size + 1
                            )
                    elif ret.code != RetCodeEnum.Success:
                        logger.error(ret.message)
                        failed_num += 1
                        # Update progress manager with failed job
                        if self._progress_manager:
                            self._progress_manager.update_job_progress(
                                failed=failed_num
                            )
                    else:
                        # Update progress manager with completed job
                        if self._progress_manager:
                            self._progress_manager.update_job_progress(
                                completed=self.done_size + 1
                            )
                elif isinstance(exception, CancelledError):
                    logger.warning(
                        generate_msg(
                            "Download cancelled",
                            filename=job.alt_filename
                        )
                    )
                else:
                    logger.error(
                        generate_msg(
                            "Download failed",
                            filename=job.alt_filename,
                            exception=exception
                        )
                    )
                    failed_num += 1
                    # Update progress manager with failed job
                    if self._progress_manager:
                        self._progress_manager.update_job_progress(
                            failed=failed_num
                        )
                self._job_queue.task_done()
        await self._job_queue.join()
        return failed_num

    async def _watch_status(self):
        """
        Watch running, completed, failed jobs
        """
        while not self._job_queue.empty():
            await asyncio.sleep(30)
            logger.info(f"Waiting: {self.waiting_size} / "
                        f"Running: {self.processing_size} / "
                        f"Completed: {self.done_size} "
                        f"({(self.done_size / (self.waiting_size + self.processing_size + self.done_size)) * 100:.2f}%)")

    async def start(self) -> int:
        """
        Start processing jobs concurrently

        It will **Block** until other call of ``self.start()`` method finished

        :return: Number of jobs that failed
        """
        failed_num = 0

        # Initialize progress manager if using centralized progress
        if self._progress_manager:
            self._progress_manager.set_job_totals(self._total_jobs_count)
            self._progress_manager.start_display()
            # Setup logger integration to work with progress display
            setup_logger_for_progress(self._progress_manager)

        async with self._lock:
            self._concurrent_tasks.clear()
            for _ in range(config.job.count):
                task = asyncio.create_task(self.processor())
                self._concurrent_tasks.add(task)
                task.add_done_callback(self._concurrent_tasks.discard)

            # Start background display update if using centralized progress
            display_task = None
            if self._progress_manager:
                display_task = asyncio.create_task(self._update_display_loop())

            _, (task_done_set, _) = await asyncio.gather(
                self._watch_status(),
                asyncio.wait(self._concurrent_tasks)
            )

            if display_task:
                display_task.cancel()
                try:
                    await display_task
                except asyncio.CancelledError:
                    pass

            for task in task_done_set:
                try:
                    failed_num += task.result()
                except CancelledError:
                    pass

            # Clean up progress manager
            if self._progress_manager:
                self._progress_manager.stop_display()
                # Remove logger integration
                setup_logger_for_progress(None)

        if failed_num:
            logger.warning(f"{failed_num} jobs failed, download finished")
        else:
            logger.success("All jobs in queue finished")
        return failed_num

    async def _update_display_loop(self):
        """Background task to update the progress display"""
        try:
            while True:
                if self._progress_manager:
                    self._progress_manager.update_display()
                await asyncio.sleep(0.1)  # Update 10 times per second
        except asyncio.CancelledError:
            pass

    async def add_jobs(self, *jobs: Job):
        """Add jobs to ``self._job_queue``"""
        for job in jobs:
            await self._job_queue.put(job)

        # Update total job count for progress tracking
        self._total_jobs_count += len(jobs)
        if self._progress_manager:
            self._progress_manager.set_job_totals(self._total_jobs_count)

    @staticmethod
    async def _force_cancel(target: asyncio.Task, wait_time: float = None) -> bool:
        """
        Force cancel ``asyncio.Task`` after ``wait_time`` seconds

        :param target: Target task
        :param wait_time: Seconds to wait before cancel (``0`` for skip one event loop run cycle)
        :return: Whether cancelled successfully
        """
        if wait_time is not None:
            await asyncio.sleep(wait_time)
        return target.cancel()

    async def cancel_downloader(self, target: Downloader) -> bool:
        """
        Cancel downloader

        :return: Whether cancelled successfully
        """
        task = self._downloaders_with_task[target]
        if not task.done():
            target.cancel()
            return await self._force_cancel(task, 0) or task.done()
        return True
