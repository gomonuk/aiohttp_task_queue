import json
from subprocess import Popen, PIPE

import asyncio
from aiohttp import web, web_runner
from psycopg2.extensions import AsIs

from databases.tasks_table_operations import TasksTableOperations
from databases.redis_db import Semaphore, Stack

HOST = "0.0.0.0"
PORT = 5000
TASK_SCRIPTS = ("test.py", "test_long_wait.py", "test_exit_100.py")

tasks_table = TasksTableOperations()
stack = Stack()


class WebRunnerTCPSite(web_runner.BaseSite):
    def __init__(self, runner, host=None, port=None, loop=None):
        super().__init__(runner)
        self.loop = loop
        self._host = host
        self._port = port

    @property
    def name(self):
        return "my_server"

    async def start(self):
        await super().start()
        self._server = await self.loop.create_server(protocol_factory=self._runner.server,
                                                     host=self._host,
                                                     port=self._port)


class WebServer(object):
    def __init__(self, address=HOST, port=PORT, loop=None):
        self.address = address
        self.port = port
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        asyncio.ensure_future(self.start(), loop=self.loop)

    async def start(self):
        app = web.Application(loop=self.loop, debug=True)
        app.router.add_post("/make_task", self.make_task)
        app.router.add_post("/get_status", self.get_status)

        runner = web.AppRunner(app)
        await runner.setup()
        site = WebRunnerTCPSite(runner=runner,
                                host=self.address,
                                port=self.port,
                                loop=self.loop)
        await site.start()
        print("------ serving on %s:%d ------" % (self.address, self.port))

    async def make_task(self, request):
        data = await request.json()
        resp = None
        error = None

        if data["scripts"] in TASK_SCRIPTS:
            row = tasks_table.insert({"name": data["scripts"], "status": "in_queue"})
            resp = {"name": data["scripts"], "id": row["id"]}
            stack.rpush(resp)
        else:
            error = "Вы пытаетесь вызвать не зарегистрированный скрипт\n"

        return web.Response(body=json.dumps({"result": resp, "error": error}))

    async def get_status(self, request):
        data = await request.json()
        row = tasks_table.select(data["id"])

        result = {"status": row["status"], "create_time": row["create_time"], "start_time": row["start_time"],
                  "time_to_execute": row["exec_time"]}
        return web.Response(body=json.dumps({"result": result, "error": None}, default=str))


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


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    WebServer(loop=loop)
    TaskManager(loop=loop)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        tasks = asyncio.gather(
            *asyncio.Task.all_tasks(loop=loop),
            loop=loop,
            return_exceptions=True
        )
        tasks.add_done_callback(lambda t: loop.stop())
        tasks.cancel()
