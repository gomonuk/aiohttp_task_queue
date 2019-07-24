import json

import redis


class Semaphore(object):
    def __init__(self, width):
        self.r = redis.Redis(host="localhost", port=6378, db=0)
        self.r.set("semaphore", width)

    def __gt__(self, operand):
        self.r.set_response_callback("GET", int)
        return self.r.get("semaphore") > operand

    def decr(self):
        self.r.decr("semaphore", 1)

    def incr(self):
        self.r.incr("semaphore", 1)


class Stack(object):
    def __init__(self):
        self.r = redis.Redis(host="localhost", port=6378, db=0)

    def rpush(self, data):
        self.r.rpush("queue", json.dumps(data))

    def blpop(self):
        data = self.r.blpop(["queue"], timeout=1)
        return None if not data else json.loads(data[1].decode("utf-8"))



