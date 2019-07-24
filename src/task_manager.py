import asyncio
from subprocess import Popen, PIPE

from psycopg2._psycopg import AsIs

from src import stack, tasks_table
from src.databases.redis_db import Semaphore


class TaskManager(object):
    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        asyncio.ensure_future(self.task_process(), loop=self.loop)

    async def task_process(self):
        semaphore = Semaphore(2)
        running_procs = []

        while self.loop.is_running():
            if semaphore > 0:
                task = stack.blpop()
                if task:
                    process = Popen(["python3", "task_scripts/" + task["name"]], stdout=PIPE, stderr=PIPE)
                    tasks_table.update(identifier=task["id"], data={"status": "run", "start_time": "now()", "pid": process.pid})
                    running_procs.append(process)
                    semaphore.decr()  # выполняем задачу из стека

            for proc in running_procs:
                retcode = proc.poll()

                if retcode is not None:  # Процесс завершился.
                    print("Process finished, retcode: ", retcode, "args:", proc.args)
                    running_procs.remove(proc)
                    tasks_table.update(identifier=proc.pid, data={"status": "completed", "exec_time": AsIs("now() - start_time")}, search_by="pid")
                    semaphore.incr()
                    break
                else:  # Спим и проверяем ещё раз.
                    await asyncio.sleep(.1)

            await asyncio.sleep(.1)