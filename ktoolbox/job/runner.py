import asyncio
from asyncio import CancelledError
from functools import cached_property
from types import MappingProxyType
from typing import List, Set, Dict
from urllib.parse import urlunparse

from loguru import logger
from tqdm import tqdm as std_tqdm

from ktoolbox._enum import RetCodeEnum
from ktoolbox.configuration import config
from ktoolbox.downloader import Downloader
from ktoolbox.job import Job
from ktoolbox.utils import generate_msg

__all__ = ["JobRunner"]


class JobRunner:
    def __init__(self, *, job_list: List[Job] = None, tqdm_class: std_tqdm = None, progress: bool = True):
        """
        Create a job runner

        :param job_list: Jobs to initial ``self._job_queue``
        :param tqdm_class: ``tqdm`` class to replace default ``tqdm.asyncio.tqdm``
        :param progress: Show progress bar
        """
        job_list = job_list or []
        self._job_queue: asyncio.Queue[Job] = asyncio.Queue()
        for job in job_list:
            self._job_queue.put_nowait(job)
        self._tqdm_class = tqdm_class
        self._progress = progress
        self._downloaders_with_task: Dict[Downloader, asyncio.Task] = {}
        self._concurrent_tasks: Set[asyncio.Task] = set()
        self._lock = asyncio.Lock()

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
        while not self._job_queue.empty():
            job = await self._job_queue.get()

            # Create downloader
            url_parts = [config.downloader.scheme, config.api.files_netloc, job.server_path, '', '', '']
            url = str(urlunparse(url_parts))
            downloader = Downloader(
                url=url,
                path=job.path,
                designated_filename=job.alt_filename,
                server_path=job.server_path
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
                if ret.code == RetCodeEnum.Success:
                    logger.success(
                        generate_msg(
                            "Download success",
                            filename=ret.data
                        )
                    )
                elif ret.code == RetCodeEnum.FileExisted:
                    logger.warning(ret.message)
                else:
                    logger.error(ret.message)
                    failed_num += 1
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
            self._job_queue.task_done()
        await self._job_queue.join()
        return failed_num

    async def start(self):
        """
        Start processing jobs concurrently

        It will **Block** until other call of ``self.start()`` method finished
        """
        failed_num = 0
        async with self._lock:
            self._concurrent_tasks.clear()
            for _ in range(config.job.count):
                task = asyncio.create_task(self.processor())
                self._concurrent_tasks.add(task)
                task.add_done_callback(self._concurrent_tasks.discard)
            task_done_set, _ = await asyncio.wait(self._concurrent_tasks)
            for task in task_done_set:
                try:
                    failed_num += task.result()
                except CancelledError:
                    pass
        if failed_num:
            logger.warning(generate_msg(f"{failed_num} jobs failed, download finished"))
        else:
            logger.success(generate_msg("All jobs in queue finished"))
        return failed_num

    async def add_jobs(self, *jobs: Job):
        """Add jobs to ``self._job_queue``"""
        for job in jobs:
            await self._job_queue.put(job)

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
