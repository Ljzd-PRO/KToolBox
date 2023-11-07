import asyncio
from typing import List, Set
from urllib.parse import urlunparse

from ktoolbox.configuration import config
from ktoolbox.downloader import download
from ktoolbox.job import Job

__all__ = ["JobRunner"]


class JobRunner:
    def __init__(self, job_list: List[Job] = None):
        """
        Create a job runner

        :param job_list: Jobs to initial `self.job_queue`
        """
        job_list = job_list or []
        self.job_queue: asyncio.Queue[Job] = asyncio.Queue()
        for job in job_list:
            self.job_queue.put_nowait(job)
        self.tasks: Set[asyncio.Task] = set()
        self.lock = asyncio.Lock()

    async def processor(self):
        """Process each job in `self.job_queue`"""
        while not self.job_queue.empty():
            job = await self.job_queue.get()
            url_parts = [config.downloader.scheme, config.api.attachment_netloc, job.server_path, '', '', '']
            url = urlunparse(url_parts)
            await download(
                url=url,
                path=job.path
            )
            # TODO: finished log
            self.job_queue.task_done()

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
