import asyncio
import json

from aiohttp import web_runner, web

from src import tasks_table, stack

HOST = "0.0.0.0"
PORT = 5000
TASK_SCRIPTS = ("test.py", "test_long_wait.py", "test_exit_100.py")


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
