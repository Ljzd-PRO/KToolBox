import asyncio
from typing import List, Set
from urllib.parse import urlunparse

from tqdm import tqdm as std_tqdm

from ktoolbox.configuration import config
from ktoolbox.downloader import Downloader
from ktoolbox.job import Job

__all__ = ["JobRunner"]


class JobRunner:
    def __init__(self, job_list: List[Job] = None, tqdm_class: std_tqdm = None):
        """
        Create a job runner

        :param job_list: Jobs to initial `self.job_queue`
        :param tqdm_class: `tqdm` class to replace default `tqdm.asyncio.tqdm`
        """
        job_list = job_list or []
        self.job_queue: asyncio.Queue[Job] = asyncio.Queue()
        for job in job_list:
            self.job_queue.put_nowait(job)
        self.tqdm_class = tqdm_class
        self.tasks: Set[asyncio.Task] = set()
        self.downloaders: List[Downloader] = []
        self.lock = asyncio.Lock()

    @property
    def finished(self):
        """
        Check if all jobs finished

        :return: `False` if **in process**, `False` otherwise
        """
        return not self.lock.locked()

    async def processor(self):
        """Process each job in `self.job_queue`"""
        while not self.job_queue.empty():
            job = await self.job_queue.get()
            url_parts = [config.downloader.scheme, config.api.attachment_netloc, job.server_path, '', '', '']
            url = urlunparse(url_parts)
            downloader = Downloader(
                url=url,
                path=job.path
            )
            self.downloaders.append(downloader)
            await downloader.run(
                sync_callable=self.downloaders.remove,
                tqdm_class=self.tqdm_class
            )
            # TODO: finished log
            self.job_queue.task_done()
        await self.job_queue.join()

    async def start(self):
        """
        Start processing jobs concurrently

        It will **Block** until other call of `self.start()` method finished
        """
        async with self.lock:
            self.tasks.clear()
            for _ in range(config.job.count):
                task = asyncio.create_task(self.processor())
                self.tasks.add(task)
                task.add_done_callback(self.tasks.discard)
            await asyncio.wait(self.tasks)
        # TODO: finished log
