from psycopg2 import connect, errors
from psycopg2.extras import RealDictCursor

CREATE_TABLE_TASKS = """
create table tasks
(
    id          serial not null
        constraint tasks_pk
            primary key,
    create_time timestamp default now(),
    start_time  timestamp,
    exec_time   interval second,
    pid         integer,
    name        text,
    status      text
);

comment on column tasks.id is 'первичный ключ, номер поставленной задачи';
comment on column tasks.create_time is 'время создания задачи';
comment on column tasks.start_time is 'время старта задачи';
comment on column tasks.exec_time is 'время выполнения задачи';

alter table tasks
    owner to postgres;

create unique index tasks_id_uindex
    on tasks (id);

"""


class TasksTableOperations(object):
    def __init__(self):
        self.conn = connect(dbname="postgres",
                            user="postgres",
                            password="",
                            host="localhost",
                            port="5431",
                            )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            self.cursor.execute(CREATE_TABLE_TASKS)
        except errors.DuplicateTable:
            pass

    def __del__(self):
        self.cursor.execute("drop table tasks;")
        self.cursor.close()
        self.conn.close()

    def select(self, task_id):
        self.cursor.execute("SELECT * FROM tasks WHERE id=" + str(task_id))
        return self.cursor.fetchone()

    def update(self, identifier, data, search_by="id"):
        q = "UPDATE tasks SET {colum} = %s WHERE {search_by}={identifier} RETURNING *"

        for item in data.items():
            self.cursor.execute(q.format(colum=item[0], search_by=search_by, identifier=identifier), (item[1],))
        return self.cursor.fetchone()

    def insert(self, data):
        placeholder = ", ".join(["%s"] * len(data))
        q = "INSERT INTO tasks ({colums}) VALUES ({placeholder}) RETURNING *"
        self.cursor.execute(q.format(colums=",".join(data.keys()), placeholder=placeholder), tuple(data.values()))
        return self.cursor.fetchone()

