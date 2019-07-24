import asyncio

from src import tasks_table
from src.task_manager import TaskManager
from src.web_server import WebServer

loop = asyncio.get_event_loop()
WebServer(loop=loop)
TaskManager(loop=loop)

try:
    loop.run_forever()
except KeyboardInterrupt:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!")
    tasks = asyncio.gather(
        *asyncio.Task.all_tasks(loop=loop),
        loop=loop,
        return_exceptions=True
    )
    tasks.add_done_callback(lambda t: loop.stop())
    tasks_table.__del__()
    tasks.cancel()
