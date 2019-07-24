db_run:
	docker run --name postgres_db -p 5431:5432 -d postgres
	docker run --name some_redis  -p 6378:6379 -d redis

make_tasks:
	curl -X POST 0.0.0.0:5000/make_task -d '{"scripts": "test_long_wait.py"}'
	curl -X POST 0.0.0.0:5000/make_task -d '{"scripts": "test.py"}'
	curl -X POST 0.0.0.0:5000/make_task -d '{"scripts": "test_long_wait.py"}'
	curl -X POST 0.0.0.0:5000/make_task -d '{"scripts": "test_exit_100.py"}'
	curl -X POST 0.0.0.0:5000/make_task -d '{"scripts": "test.py"}'
	curl -X POST 0.0.0.0:5000/make_task -d '{"scripts": "test_long_wait.py"}'
	curl -X POST 0.0.0.0:5000/make_task -d '{"scripts": "test.py"}'
	curl -X POST 0.0.0.0:5000/make_task -d '{"scripts": "test_long_wait.py"}'
	curl -X POST 0.0.0.0:5000/make_task -d '{"scripts": "test_exit_100.py"}'
	curl -X POST 0.0.0.0:5000/make_task -d '{"scripts": "test.py"}'

get_status:
	curl -X POST 0.0.0.0:5000/get_status -d '{"id": "28"}'

