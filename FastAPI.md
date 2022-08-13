# FastAPI, Docker

## Environment and Setup

```
# App Structure

|-- backend
|   |-- app
|       |-- api
|       |-- core
|       |-- db
|       |-- emails
|       |-- models
|       |-- services
|       |-- utils
|   |-- tests
|       |-- conftest.py
|   |-- .env
|   |-- Dockerfile
|   |-- requirements.txt
|-- .flake8
|-- .gitignore
|-- docker-compose.yml
|-- README.md
```

```
$ mkdir -p backend/tests backend/app/api backend/app/core
$ touch .flake8 .gitignore docker-compose.yml
$ touch backend/.env backend/Dockerfile backend/requirements.txt
```

### requirements.txt

```
# app
fastapi==0.55.1
uvicorn==0.11.3
pydantic==1.4
email-validator==1.1.1
```

- fastapi: 백엔드 프레임워크
- uvicorn: ASGI 서버
- pydantic: 애플리케이션 전체의 여러 단계에서 데이터 모델을 처리할 때 사용하는 유효성 검사 라이브러리
- email-validator: pydantic이 이메일 유효성을 검사하도록 지원

## 서버 생성

```
$ touch backend/app/api/__init__.py backend/app/api/server.py
```

```python
# server.py
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

def get_application():
    app = FastAPI(title="Zen", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app

app = get_application()
```

- [starlette](https://www.starlette.io/): Python에서 비동기 웹 서비스를 구축하는 경량 ASGI 프레임워크

## 도커 컨테이너

- Dockerfile

```
FROM python:3.8-slim-buster

WORKDIR /backend

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc postgresql \
  && apt-get clean
  
# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /backend/requirements.txt
RUN pip install -r requirements.txt

COPY . /backend
```

1. 파이썬 3.8 슬림 버스터 도커 이미지 가져오기
2. 작업 디렉터리 설정
3. 파이썬이 디스크에 pyc 파일을 쓰는 것을 방지하고 stdout, stderr를 버퍼링하지 않도록 환경변수를 추가
4. requirements.txt를 복사하고 필요한 종속성을 설치
5. 앱을 backend 폴더에 복사

- docker-compose.yml

```yml
version: '3.8'

services:
  server:
    build:
      context: ./backend
      dockerfile: Dockerfile
    volumes:
      - ./backend/:/backend/
    command: uvicorn app.api.server:app --reload --workers 1 --host 0.0.0.0 --port 8000
    env_file:
      - ./backend/.env
    ports:
      - 8000:8000
```
	- 서버를 설정하고 Dockerfile을 사용하여 빌드하도록 지시
	- backend 파일을 봄륨에 저장
	- uvicorn으로 애플리케이션을 제공하고 localhost:8000으로 백엔드를 호스팅
	- 환경변수는 .env 파일에서 로드

- Docker 컨테이터 빌드
	- `docker-compose up -d --build`

```
$ docker-compose up -d --build
WARNING: Found orphan containers (fastapi_study_db_1) for this project. If you removed or renamed this service in your compose file, you can run this command with the --remove-orphans flag to clean it up.
Building server
[+] Building 5.0s (12/12) FINISHED
 => [internal] load build definition from Dockerfile                                                                              0.0s
 => => transferring dockerfile: 37B                                                                                               0.0s
 => [internal] load .dockerignore                                                                                                 0.0s
 => => transferring context: 2B                                                                                                   0.0s
 => [internal] load metadata for docker.io/library/python:3.8-slim-buster                                                         0.0s
 => [1/7] FROM docker.io/library/python:3.8-slim-buster                                                                           0.0s
 => [internal] load build context                                                                                                 0.0s
 => => transferring context: 349B                                                                                                 0.0s
 => CACHED [2/7] WORKDIR /backend                                                                                                 0.0s
 => CACHED [3/7] RUN apt-get update     && apt-get -y install netcat gcc postgresql     && apt-get clean                          0.0s
 => CACHED [4/7] RUN pip install --upgrade pip                                                                                    0.0s
 => [5/7] COPY ./requirements.txt /backend/requirements.txt                                                                       0.0s
 => [6/7] RUN pip install -r requirements.txt                                                                                     3.7s
 => [7/7] COPY . /backend                                                                                                         0.0s
 => exporting to image                                                                                                            1.2s
 => => exporting layers                                                                                                           1.2s
 => => writing image sha256:726db78f9275ec637269325082885ac2c3fc57986bed3d99884a487a39719c22                                      0.0s
 => => naming to docker.io/library/fastapi_study_server                                                                           0.0s

Use 'docker scan' to run Snyk tests against images to find vulnerabilities and learn how to fix them
Recreating fastapi_study_server_1 ... done
```

- 빌드 완료후 컨테이너 실행
	- `docker-compose up`
	- localhost:8000 에 접속하여 json 응답확인
		- `$ curl localhost:8000.   ->.   {"detail":"Not Found"}`

## Routing

```
$ mkdir backend/app/api/routes
$ touch backend/app/api/routes/__init__.py backend/app/api/routes/cleanings.py
```

- api/routes/cleanings.py

```python
from typing import List
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_all_cleanings() -> List[dict]:
    cleanings = [
        {"id": 1, "name": "My house", "cleaning_type": "full_clean", "price_per_hour": 29.99},
        {"id": 2, "name": "Someone else's house", "cleaning_type": "spot_clean", "price_per_hour": 19.99}
    ]
    return cleanings
```

- api/routers/__init__.py

```python
from fastapi import APIRouter
from app.api.routes.cleanings import router as cleanings_router

router = APIRouter()

router.include_router(cleanings_router, prefix="/cleanings", tags=["cleanings"])
```

- api/server.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

def get_application():
    app = FastAPI(title="Phresh", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")
    return app

app = get_application()
```

```
$ curl localhost:8000/api/cleanings/
[{"id":1,"name":"My house","cleaning_type":"full_clean","price_per_hour":29.99},{"id":2,"name":"someone else's house","cleaning_type":"spot_clean","price_per_hour":19.99}]
```

# Dockerized FastAPI, PostgreSQL DB

- docker-compose.yml

```
version: '3.8'

services:
  server:
    build:
      context: ./backend
      dockerfile: Dockerfile
    volumes:
      - ./backend/:/backend/
    command: uvicorn app.api.server:app --reload --workers 1 --host 0.0.0.0 --port 8000
    env_file:
      - ./backend/.env
    ports:
      - 8000:8000
    depends_on:
      - db

  db:
    image: postgres:13-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - ./backend/.env
    ports:
      - 5432:5432

volumes:
    postgres_data:
```

- db 서비스 추가
- postgres 이미지 가져오기
- postgres_data 컨테이너 볼륨 추가
	- 컨테이너 종료시 데이터베이스 삭제 방지

- update requirements.txt

```
# app
fastapi==0.55.1
uvicorn==0.11.3
pydantic==1.4
email-validator==1.1.1
# db
databases[postgresql]==0.4.2
SQLAlchemy==1.3.16
alembic==1.4.2
```
	- databases: 데이터베이스에 대한 비동기 인터페이스
	- SQLAlchemy: python용 SQL 툴킷
	- alembic: SQLAlchemy와 함께 사용하는 데이터베이스 마이그레이션 툴

새 컨테이너 생성
`docker-compose up --build`

빌드 프로세스가 완료되면 데이터베이스에 비밀번호가 설정되지 않았다는 경고와 함께 컨테이너 실행을 확인 할 수 있다.
`docker ps`를 통해 2개의 컨테이너 실행을 확인할 수 있는데, 하나는 서버용이고, 하나는 데이터베이스이다.

```
$  docker ps
CONTAINER ID   IMAGE                  COMMAND                  CREATED          STATUS          PORTS                    NAMES
095fd6059c10   fastapi_study_server   "uvicorn app.api.ser…"   42 seconds ago   Up 42 seconds   0.0.0.0:8000->8000/tcp   fastapi_study_server_1
df23954a4c94   postgres:13-alpine     "docker-entrypoint.s…"   43 seconds ago   Up 42 seconds   0.0.0.0:5432->5432/tcp   fastapi_study_db_1
```

## FastAPI 구성

.gitignore에 다음을 추가한다.

```
# Byte-compiled files
__pycache__/

# Environment files
.env
```

.env에 데이터를 추가한다.

```
SECRET_KEY=supersecret
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=postgres
```

.env는 레포를 복제할때마다 다시 생성해야 하기 때문에 레포에 필요한 환경 변수의 이름으로 파일을 만드는 것이 좋다.

config.py 파일을 추가하자.

- backend/app/core/config.py

```python
from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

PROJECT_NAME = "phresh"
VERSION = "1.0.0"
API_PREFIX = "/api"

SECRET_KEY = config("SECRET_KEY", cast=Secret, default="CHANGEME")

POSTGRES_USER = config("POSTGRES_USER", cast=str)
POSTGRES_PASSWORD = config("POSTGRES_PASSWORD", cast=Secret)
POSTGRES_SERVER = config("POSTGRES_SERVER", cast=str, default="db")
POSTGRES_PORT = config("POSTGRES_PORT", cast=str, default="5432")
POSTGRES_DB = config("POSTGRES_DB", cast=str)

DATABASE_URL = config(
  "DATABASE_URL",
  cast=DatabaseURL,
  default=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
```

Starlette는 환경 변수를 찾기 위해 Config 파일을 지정할 수 있는 객체를 제공한다.

## PostgreSQL 연결

db 관련 코드와 함께 사용할 tasks.py를 생성. 
core/tasks.py는 앱의 시작 및 종료 이벤트를 래핑한다.

```
$ mkdir backend/app/db
$ touch backend/app/db/__init__.py backend/app/db/tasks.py
$ touch backend/app/core/tasks.py
```

- core/tasks.py

```python
from typing import Callable
from fastapi import FastAPI
from app.db.tasks import connect_to_db, close_db_connection

def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        await connect_to_db(app)
    return start_app

def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        await close_db_connection(app)
    return stop_app
```

응용 프로그램이 시작될 때 와 종료될 떄 실행할 두 가지 함수를 정의함
각각은 데이터베이스 연결 생성 및 종료를 담당하는 비동기 함수를 반환한다.
db/tasks.py에 작성할 `connect_to_db`, `close_db_connection`을 가져온다.

- db/tasks.py

```python
from fastapi import FastAPI
from databases import Database
from app.core.config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)


async def connect_to_db(app: FastAPI) -> None:
    database = Database(DATABASE_URL, min_size=2, max_size=10)  # these can be configured in config as well

    try:
        await database.connect()
        app.state._db = database
    except Exception as e:
        logger.warn("--- DB CONNECTION ERROR ---")
        logger.warn(e)
        logger.warn("--- DB CONNECTION ERROR ---")


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception as e:
        logger.warn("--- DB DISCONNECT ERROR ---")
        logger.warn(e)
        logger.warn("--- DB DISCONNECT ERROR ---")
```

`connect_to_db`는 데이터베이스 패키지를 사용하여 파일에서 구상한 데이터베이스 URL 문자열로 postgresql db에 대한 연결을 설정한다.
주어진 시간에 가질 수 있는 최소/최대 연결 수에 대한 키워드 인수를 추가했다.

FastAPI 앱은 연결이 성공적으로 완료될 때까지 기다렸다가 이를 `_db`의 개체에 키로 연결한다.
state은 앱이 종료되면 깔끔하게 정리하기 위해 데이터베이스 연결을 끊는다.

이제 server.py에 이러한 이벤트 처리기를 등록하자. 그리고 메타데이터 중 일부를 구성 파일의 상수로 교체하자.

- server.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import config, tasks  <-- add

from app.api.routes import router as api_router


def get_application():
    app = FastAPI(title=config.PROJECT_NAME, version=config.VERSION)   <-- update

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_event_handler("startup", tasks.create_start_app_handler(app))   <--- add
    app.add_event_handler("shutdown", tasks.create_stop_app_handler(app))   <--- add

    app.include_router(api_router, prefix="/api")

    return app
    
app = get_application()
```

실행 중인 컨테이너를 중지하고 다시 실행하자.

```
docker-compose up
```

모두 잘 되었다면 아래 로그가 표시될 것이다.

```
server_1  | INFO:     Connected to database postgresql://postgres:********@db:5432/postgres
```

> password 에러가 난다면 postgres 컨테이너에 접속해서 비번을 셋팅해주자.

```
$ sudo -u postgres psql
psql (14.1 (Ubuntu 14.1-2.pgdg20.04+1))
Type "help" for help.

postgres=# \password postgres
Enter new password: 
Enter it again: 
```

## SQLAlchemy, alembic을 사용하여 DB 테이블, 마이그레이션 구성하기

db 안에 migrations, repositories 디렉터리를 생성한다.
마이그레이션을 위해 alembic 파일과 base.py를 생성한다.

```
$ mkdir backend/app/db/migrations backend/app/db/repositories
$ touch backend/app/db/migrations/script.py.mako backend/app/db/migrations/env.py
$ touch backend/app/db/repositories/__init__.py backend/app/db/repositories/base.py
```

Alembic 문서에 따른 마이그레이션 환경을 설정이다.
- https://alembic.sqlalchemy.org/en/latest/tutorial.html#the-migration-environment
`script.py.mako` 파일은 [Mako 템플릿](https://www.makotemplates.org/)으로, 새 마이그레이션 스크립트를 생성하는 방법을 alembic에 지시하고, `env.py` 파일은 alembic 마이그레이션 도구가 호출될 때마다 실행되는 python 스크립트이다.

마이그레이션이 있어야 하는 디렉터리를 지정한다.

```
$ mkdir backend/app/db/migrations/versions
```

alembic 환경을 구성한다. 일반적으로 기본 디렉터리에 있는 alembic.ini 파일에서 실행한다.

```
$ vi backend/alembic.ini


# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = ./app/db/migrations

# version location specification; this defaults
# to alembic/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path
version_locations = ./app/db/migrations/versions

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

파일의 대부분은 alembic이 터미널에 정보를 기록하는 방법을 기술한 것이다.
우리가 봐야하는 부분은 `script_location`이다.

db/migrations/script.py.mako도 작성하자.

```python
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

템플릿 파일은 embic에서 생성하도록 요청할 때마다 마이그레이션 스크립트를 생성하는데 사용한다.

db/migrations/env.py 를 작성하자.

```python
import pathlib
import sys
import alembic
from sqlalchemy import engine_from_config, pool

from logging.config import fileConfig
import logging

# we're appending the app directory to our path here so that we can import config easily
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

from app.core.config import DATABASE_URL  # noqa

# Alembic Config object, which provides access to values within the .ini file
config = alembic.context.config

# Interpret the config file for logging
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode
    """
    connectable = config.attributes.get("connection", None)
    config.set_main_option("sqlalchemy.url", str(DATABASE_URL))

    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        
    with connectable.connect() as connection:
        alembic.context.configure(
            connection=connection,
            target_metadata=None
        )

        with alembic.context.begin_transaction():
            alembic.context.run_migrations()


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    """
    alembic.context.configure(url=str(DATABASE_URL))

    with alembic.context.begin_transaction():
        alembic.context.run_migrations()


if alembic.context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    run_migrations_online()
```

## 데이터베이스 마이그레이션

서버 컨테이너로 접속하자.

```
$ docker exec -it [컨테이너 ID] bash
```

컨테이너에 복사한 모든 파일과 디렉터리가 있어야 한다.

```
Dockerfile  alembic.ini  app  requirements.txt	tests
```

컨테이너의 쉘에서 embic 명령을 사용할 수 있다.
첫 번째 마이그레이션 스크립트를 생성하자.

```
$ alembic revision -m "create_main_tables"
 Generating
  /backend/app/db/migrations/versions/743ed34c9e41_create_main_tables.py ...  done
root@e5e0d2
```

설정이 잘되었다면 db/migrations/versions 안에 파일이 생성되었을 것이다.
생성된 마이그레이션 파일의 내용이다.

```python
"""create_main_tables

Revision ID: 743ed34c9e41
Revises:
Create Date: 2022-08-12 15:29:25.259205

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '743ed34c9e41'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
```

두 가지 주요 기능(upgrade, downgrade)은 데이터베이스 테이블을 생성/삭제하고, SQL 명령을 실행하고, 마이그레이션 할 때마다 사용된다.

가장 먼저 할 일은 테이블을 만들기 위한 추가 함수를 정의하는 것이다.
그 후에 함수 내부에서 해당 함수를 실행하고, 함수 upgrade에서 반대 동작은 만든다.

```python
"""create_main_tables

Revision ID: 743ed34c9e41
Revises:
Create Date: 2022-08-12 15:29:25.259205

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '743ed34c9e41'
down_revision = None
branch_labels = None
depends_on = None


def create_cleanings_table() -> None:
    op.create_table(
        "cleanings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("cleaning_type", sa.Text, nullable=False, server_default="spot_clean"),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
    )

def upgrade() -> None:
    pass

def downgrade() -> None:
    op.drop_table("cleanings")
```

	- id: 기본 키 열. 각 항목을 고유하게 식별하는 자동 증가 정수
	- name: index=True으로 더 빠르게 조회하도록 인덱스 설정
	- description: 요구사항 설명. nullable이다. 즉, 생성시 필수 입력값은 아니다.
	- cleaning_type: 청소의 강도를 구분한다.
	- price: 청소부에게 지불할 시간당 가격

SQLAlchemy를 사용하여 각 열에 대해 서로 다른 데이터 유형을 생성한다.
ID는 정소이다. price는 소수점 이하 2자리의 부동 소수점이다. 나머지는 텍스트이다.

마이그레이션을 실행하자.

```
$ alembic upgrade head
INFO  [alembic.env] Running migrations online
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 743ed34c9e41, create_main_tables
```

> 그 전에 psycopg2 를 설치해야 한다. requirements.txt로는 제대로 설치가 되지 않는다.
> Dockerfile에서 requirements.txt를 설치한 이후에 pip 설치를 추가해주어야 한다.
> `RUN pip install psycopg2-binary`

## DB와 상호작용

데이터베이스가 올바르게 적용되었는지 확인하기 위해 db 컨테이너에 접속하자. 

```
$ docker-compose exec db psql -h localhost -U postgres --dbname=postgres
```

- psql 기본 명령어
	- \l : 모든 데이터베이스 나열
	- \d+: 현재 데이터베이스의 모든 테이블 나열
	- \c postgres: postgres 데이터베이스에 연결
	- \d cleanings: cleanings 테이블 관련 열 설명

```
postgres=# \d cleanings
                                   Table "public.cleanings"
    Column     |     Type      | Collation | Nullable |                Default
---------------+---------------+-----------+----------+---------------------------------------
 id            | integer       |           | not null | nextval('cleanings_id_seq'::regclass)
 name          | text          |           | not null |
 description   | text          |           |          |
 cleaning_type | text          |           | not null | 'spot_clean'::text
 price         | numeric(10,2) |           | not null |
Indexes:
    "cleanings_pkey" PRIMARY KEY, btree (id)
    "ix_cleanings_name" btree (name)
```

데이터베이스에 직접 SQL 쿼리를 실행할 수도 있다.

```
postgres=# select id, name, price from cleanings;
 id | name | price
----+------+-------
(0 rows)
```

# hooking fastapi endpoints up to a postgres database

게시물에서 CRUD endpoint를 추가하고 DB를 연결한다.
또한 db와 인터페이스하고 관련 SQL 쿼리를 실행하는 정리 저장소를 만든다.
데이터 유효성 검사를 위해 pydantic을 사용하여 리소스에 대한 모델을 구성한다.

## Pydantic

"데이터의 '모양'을 속성이 있는 클래스로 선언합니다. 그리고 각 속성에는 유형이 있습니다.
그런 다음 일부 값을 사용하여 해당 클래스의 인스턴스를 생성하면 값의 유효성을 검사하고 적절한 유형으로 변환하고 모든 데이터가 포함된 개체를 제공합니다." - FastAPI doc

Pydantic 모델은 자체 디렉터리에 이썽야 하며, 리소스에 따라 namespace가 지정되어야 한다.
모든 모델에서 공유되는 공통 논리를 저장하기 위해 core.py를 만든다.

```
mkdir backend/app/models
touch backend/app/models/__init__.py backend/app/models/core.py backend/app/models/cleaning.py
```

- models/core.py

```python
from pydantic import BaseModel


class CoreModel(BaseModel):
    """
    Any common logic to be shared by all models goes here.
    """
    pass


class IDModelMixin(BaseModel):
    id: int
```

Pydantic BaseModel은 데이터 클래스 기반으로 데이터 유효성 검사 및 데이터 형식 강제 변환과 관련된 추가 기능을 제공합니다.

"모델은 엄격하게 형식화된 언어의 형식과 유사하거나 API의 단일 endpoint 요구 사항으로 생각할 수 있습니다.
신뢰할 수 없는 데이터는 모델에 전달할 수 있으며 구문 분석 및 유효성 검사 후 pydantic은 결과 모델 인스턴스의 필드가 모델에 정의된 필드 유형을 준수하도록 보장합니다." - Pydantic docs

CoreModel은 어느 시점에서든 모델 간에 논리를 공유할 수 있도록 상속된다.
IDModelMixin 클래스는 데이터베이스에서 나오는 모든 리소스에 사용된다.
속성에 대한 기본값을 제공하지 않음으로써 id가 모든 새 인스턴스에 필요하다는 것을 Pydantic에 알린다.
int 유형으로 선언했기 때문에 "문자열, 바이트 또는 부동 소수점은 가능한 경우 int로 강제 변환하고, 안되면 예외가 발생하다.

- models/cleaning.py

```python
from typing import Optional
from enum import Enum

from app.models.core import IDModelMixin, CoreModel


class CleaningType(str, Enum):
    dust_up = "dust_up"
    spot_clean = "spot_clean"
    full_clean = "full_clean"


class CleaningBase(CoreModel):
    """
    All common characteristics of our Cleaning resource
    """
    name: Optional[str]
    description: Optional[str]
    price: Optional[float]
    cleaning_type: Optional[CleaningType] = "spot_clean"


class CleaningCreate(CleaningBase):
    name: str
    price: float


class CleaningUpdate(CleaningBase):
    cleaning_type: Optional[CleaningType]


class CleaningInDB(IDModelMixin, CleaningBase):
    name: str
    price: float
    cleaning_type: CleaningType


class CleaningPublic(IDModelMixin, CleaningBase):
    pass

```

Optional을 하용하여 모델 인스턴스를 생성할 때 전달되지 않은 속성은 None으로 설정되도록 지정한다.

```python
# 두 클래스는 기능적으로 동일하다.

class CleaningBase(CoreModel):
    """
    All common characteristics of our Cleaning resource
    """
    name: Optional[str]
    description: Optional[str]
    price: Optional[float]
    cleaning_type: Optional[CleaningType] = "spot_clean"


class CleaningBase(CoreModel):
    """
    All common characteristics of our Cleaning resource
    """
    name: str = None
    description: str = None
    price: float = None
    cleaning_type: CleaningType = "spot_clean"
```

CleaningType은 3개의 값만 사용하도록 커스텀 클래스를 정의했다.
유효한 입력의 수를 명시적 집합으로 제한하려면 Enum 을 상속받아야 한다.

## 레포지토리

레포지토리의 목적은 데이터베이스 작업 위에 추상화 레이어 역할을 하는 것이다.
각 레포는 특정 리소스에 해당하는 데이터베이스 기능을 캡슐화한다.
그렇게 애플리케이션 로직에서 지속성 로직을 분리한다.
여기서는 레포지토리를 ORM의 대안으로 취급한다.

- db/repositories/base.py

```python
from databases import Database


class BaseRepository:
    def __init__(self, db: Database) -> None:
        self.db = db
```

BaseRepository는 데이터베이스 연결에 대한 참조를 유지하는 데만 필요한 간단한 클래스이다.
일반적인 db 작업에 대한 기능을 추가할 수도 있다.

- repositories/cleanings.py

```python
from app.db.repositories.base import BaseRepository
from app.models.cleaning import CleaningCreate, CleaningUpdate, CleaningInDB


CREATE_CLEANING_QUERY = """
    INSERT INTO cleanings (name, description, price, cleaning_type)
    VALUES (:name, :description, :price, :cleaning_type)
    RETURNING id, name, description, price, cleaning_type;
"""


class CleaningsRepository(BaseRepository):
    """"
    All database actions associated with the Cleaning resource
    """

    async def create_cleaning(self, *, new_cleaning: CleaningCreate) -> CleaningInDB:
        query_values = new_cleaning.dict()
        cleaning = await self.db.fetch_one(query=CREATE_CLEANING_QUERY, values=query_values)

        return CleaningInDB(**cleaning)
```

데이터베이스 패키지가 기대하는 스타일로 첫 번째 SQL 쿼리를 작성했다.
Repository 패턴의 장점중 하나는 ORM의 깨끗한 인터페이스로 순수한 SQL의 유연성을 얻을 수 있는 것이다.

CleaningRepository는 BaseRepository를 상속하고, postgres 데이터베이스에 새로운 리소스를 삽입하기 위한 단일 메서드를 정의한다.
먼저 모델에서 메서드를 호출하여 dict로 변환한다. (`CleaningCreate.dict()`)
- https://pydantic-docs.helpmanual.io/usage/exporting_models/#modeldict

다시 정리하면 Pydantic 모델을 만들고 호출할때 발생하는 일은 다음과 같다.

```
new_cleaning = CleaningCreate(name="Clean My House", cleaning_type="full_clean", price="29.99")
query_values = new_cleaning.dict()
print(query_values)
# {"name": "Clean My House", "cleaning_type": "full_clean", "price": 29.99, "description": None}
```

Pydantic은 입력을 구문 분석 및 검증하고, 기본값을 채우고, 모델을 dict로 변환한다.
이 dict의 각 키는 SQL 쿼리의 쿼리 인수로 매핑된다.(`CREATE_CLEANING_QUERY`)
`db.fetch_one()`으로 실행하려는 쿼리와 연결된 쿼리 인수를 전달한다.
마지막으로 SQL 쿼리에서 반환된 데이터베이스 레코드를 가져와 unpacking 을 사용하여 압축을 푼다.
레코드의 각 키-값 쌍을 가져와서 CleaningInDB 인스턴스의 키워드 인수와 바꾼다.

## Dependencies in FastAPI endpoints

"'종속성 주입'은 프로그래밍에서 코드가 작동하고 사용하는데 필요한 '종속성'을 선언하는 방법이 있음을 의미합니다." - FastAPI docs

여기서 만들 모든 API endpoint는 데이터베이스에 대한 액세스가 필요하기 때문에 postgres db를 종속성에 대한 후보로 만들어야 한다. FastAPI가 익숙하지 않다면 [문서](https://fastapi.tiangolo.com/tutorial/dependencies/)를 읽어야 합니다. 

```
mkdir backend/app/api/dependencies
touch backend/app/api/dependencies/__init__.py backend/app/api/dependencies/database.py
```

- dependencies/database.py

```python
from typing import Callable, Type
from databases import Database

from fastapi import Depends
from starlette.requests import Request

from app.db.repositories.base import BaseRepository


def get_database(request: Request) -> Database:
    return request.app.state._db


def get_repository(Repo_type: Type[BaseRepository]) -> Callable:
    def get_repo(db: Database = Depends(get_database)) -> Type[BaseRepository]:
        return Repo_type(db)

    return get_repo
```

2개의 종속성을 구현했다.(`get_database`, `get_repository`)
FastAPI 종속성은 API endpoint 경로 매개변수 Callables라는 함수일 뿐이다.
- https://fastapi.tiangolo.com/tutorial/path-params/

`get_repository` 함수에서 단일 `Repo_type` 매개변수를 선언하고 `get_repo`라는 다른 함수를 반환한다.
`get_repo`에는 단일 매개변수로 선언된 자체 종속성(db)이 있다.
이건 FastAPI에서 하위 종속성으로 알려져 있고, 앱의 시작 이벤트 처리기에서 설정한 데이터베이스 연결에 대한 참조를 가져오는 `get_database` 함수에 따라 다르다.

`Request` 객체는 `starlette` 프레임워크에서 직접 제공하며, FastAPI는 이를 전달하는 작업을 처리한다.
- https://fastapi.tiangolo.com/advanced/using-request-directly/
그 후에 해당 데이터베이스 참조를 `CleaningsRepository`에 전달하고 필요에 따라 repo가 postgres db와 인터페이스하도록 한다.

- api/routes/cleanings.py

```python
from typing import List

from fastapi import APIRouter, Body, Depends  <-- update
from starlette.status import HTTP_201_CREATED  <-- add

from app.models.cleaning import CleaningCreate, CleaningPublic  <-- add
from app.db.repositories.cleanings import CleaningsRepository  <-- add
from app.api.dependencies.database import get_repository  <-- add

router = APIRouter()

@router.get("/")
async def get_all_cleanings() -> List[dict]:
    cleanings = [
        {"id": 1, "name": "My house", "cleaning_type": "full_clean", "price_per_hour": 29.99},
        {"id": 2, "name": "Someone else's house", "cleaning_type": "spot_clean", "price_per_hour": 19.99}
    ]
    return cleanings

# add
@router.post("/", response_model=CleaningPublic, name="cleanings:create-cleaning", status_code=HTTP_201_CREATED)
async def create_new_cleaning(
    new_cleaning: CleaningCreate = Body(..., embed=True),
    cleanings_repo: CleaningsRepository = Depends(get_repository(CleaningsRepository)),
) -> CleaningPublic:
    created_cleaning = await cleanings_repo.create_cleaning(new_cleaning=new_cleaning)
    return created_cleaning
```

localhost:8000/docs으로 접속해 자동 대화형 API를 확인해보자.

새로 생성된 POST 경로(녹색)을 클릭해보자.

"요청 본문은 클라이언트가 API로 보낸 데이터입니다. 응답 본문은 API가 클라이언트로 보내는 데이터입니다." -> FastAPI

여기에는 성공적인 요청을 위해 본문에 필요한 것과 유효성 검사 오류 또는 성공적인 실행에 대해 기대하는 응답 유형이 모두 표시된다.

성공 응답 스키마는 `response_model=CleaningPublic`에서 가져오고, 성공 상태는 `status_code=HTTP_201_CREATED`에서 가져온다.
라우트의 이름은 `name="cleanings:create-cleaning"`이다.

`create_new_cleaning` 함수의 첫번째 매개변수는 `new_cleaning`으로 주석처리된다.
CleaningCreate는 기본적으로 게시 요청의 본문을 예상한다.
key가 있는 JSON을 예상하고, `new_cleaning` 안에 모델 내용을 포함하려면 기본 매개변수에 특수 Body 매개변수(embed)를 사용한다.

- CleaningCreate
	- 요청 본문을 JSON으로 읽는다.
	- 해당 유형을 변환한다.
	- 데이터를 검증한다.
	- 유효성 검사가 실패하면 오류로 응답하거나 필요한 모델 인스턴스와 함께 경로를 제공한다.

두 번째 매개변수 `cleanings_repo`는 데이터베이스 인터페이스리며, route의 유일한 종속성이다.
route에서 액세스할 수 있고, 함수가 실행될 때마다 새 리소스를 만들 수 있도록 기본값을 `Depends(get_repository(CleaningsRepository))`로 설정한다.
FastAPI는 `created_cleaning`을 자동으로 유효성 검사를 하고, `CleaningPublic` 모델의 인스턴스로 변환하고 적절한 JSON을 응답으로 보낸다.

## Testing our Route

OpenAPI 문서는 일부 더미 데이터로 요청을 실행하는 버튼을 제공한다.
경로를 클릭하고 API에 보낼 데이터로 JSON을 편집하고 실행하면 위에서 생성한 경로에 대해 POST 요청을 발행한다.

"데이터베이스 마이그레이션을 잊어버린 경우 `asyncpg.exceptions.UndefinedTableError`에서 500 내부 서버 오류가 발생한다.
그 뒤에 오는 힌트는 데이터베이스에 테이블을 생성하기 위해 마이그레이션을 실행해야 함을 알려준다."

db 컨테이너에서 psql으로 계획대로 작동하는지 확인해보자.

```
docker-compose exec db psql -h localhost -U postgres --dbname=postgres
```

모든 cleaning 기록에 대해 쿼리하자.

```
SELECT id, name, description, cleaning_type, price FROM cleanings;
 id |  name  | description | cleaning_type | price
----+--------+-------------+---------------+-------
  1 | string | string      | spot_clean    |  0.00
(1 row)
```

# Docker, Pytest로 FastAPI endpoint 테스트

TDD 접근 방식을 따르고 표준 GET endpoint를 만든다.
테스트 환경을 가동하고 새로운 PostgreSQL 데이터베이스에 대해 모든 테스트를 실행하여 애플리케이션이 예상대로 작동하는지 확인한다.

## 테스트 정보

- https://github.com/tiangolo/full-stack-fastapi-postgresql
- https://github.com/fastapi-users/fastapi-users
- https://github.com/nsidnev/fastapi-realworld-example-app

## TDD, Pytest

- requirements.txt

```
# app
fastapi==0.55.1
uvicorn==0.11.3
pydantic==1.4
email-validator==1.1.1
# db
databases[postgresql]==0.4.2
SQLAlchemy==1.3.16
alembic==1.4.2

# dev
pytest==6.2.1
pytest-asyncio==0.14.0
httpx==0.16.1
asgi-lifespan==1.0.1
```

- pytest: 테스트 프레임워크
- pytest-asyncio: 비동기 코드 테스트를 위한 유틸리티 제공
- httpx: endpoint 테스트를 위한 비동기 요청 클라이언트 제공
- asgi-lifespan: ASGI 서버를 가동하지 않고도 비동기 애플리케이션을 테스트

컨테이너 재빌드

```
$ docker-compose up --build
```

테스트를 위한 파일 생성

```
touch backend/tests/__init__.py 
touch backend/tests/conftest.py
touch backend/tests/test_cleanings.py
```

테스트 환경 구성
- conftest.py

```python
import warnings
import os

import pytest
from asgi_lifespan import LifespanManager

from fastapi import FastAPI
from httpx import AsyncClient
from databases import Database

import alembic
from alembic.config import Config


# Apply migrations at beginning and end of testing session
@pytest.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")

    alembic.command.upgrade(config, "head")
    yield
    alembic.command.downgrade(config, "base")


# Create a new application for testing
@pytest.fixture
def app(apply_migrations: None) -> FastAPI:
    from app.api.server import get_application

    return  get_application()


# Grab a reference to our database when needed
@pytest.fixture
def db(app: FastAPI) -> Database:
    return app.state._db


# Make requests in our tests
@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    async with LifespanManager(app):
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            headers={"Content-Type": "application/json"}
        ) as client:
            yield client
```

데이터베이스 마이그레이션을 처리할 `apply_migrations` 픽스처를 정의하는 것부터 시작한다.
db가 테스트하는 동안 세션을 지속하도록 범위를 session으로 설정한다.

각 테스트에 대해 마이그레이션을 적용 및 롤백하지 않기 때문에 테스트 속도가 상당히 빨라진다.

픽스처는 TESTING 환경 변수를 "1"로 설정하여 표준 db 대신 테스트 데이터베이스를 마이그레이션 할 수 있다.
그런 다음 Alembic 마이그레이션 구성을 잡고 모든 테스트를 실행 할 수 있도록 양보하기 전에 모든 마이그레이션을 실행한다.

app와 db 픽스처는 표준이다.
새로운 FastAPI 앱을 인스턴스화하고 필요한 경우 데이터베이스 연결에 대한 참조를 가져온다.
클라이언트 픽스처에서 LifespanManager와 AsyncClient를 결합하여 실행중인 FastAPI 애플리케이션에 요청을 보낼 수 있는 깨끗한 테스트 클라이언트를 제공한다. 이 패턴은 [asgi-lifespan](https://github.com/florimondmanca/asgi-lifespan)에 적용되었다.

pytest에서 테스트 환경을 설정이 끝났다.

## 데이터베이스 구성 업데이트

- db/tasks.py

```python
import os  <-- add
from fastapi import FastAPI
from databases import Database
from app.core.config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)


async def connect_to_db(app: FastAPI) -> None:

    DB_URL = f"{DATABASE_URL}_test" if os.environ.get("TESTING") else DATABASE_URL <-- add
    database = Database(DB_URL, min_size=2, max_size=10) <-- update


    try:
        await database.connect()
        app.state._db = database
    except Exception as e:
        logger.warn("--- DB CONNECTION ERROR ---")
        logger.warn(e)
        logger.warn("--- DB CONNECTION ERROR ---")


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception as e:
        logger.warn("--- DB DISCONNECT ERROR ---")
        logger.warn(e)
        logger.warn("--- DB DISCONNECT ERROR ---")
```

데이터베이스 URL 문자열을 테스트 환경일 경우 접미사를 변경한다.

- db/migrations/env.py

```python
import pathlib
import sys
import os  <-- add

import alembic  <-- add
from sqlalchemy import engine_from_config, create_engine, pool <-- update
from psycopg2 import DatabaseError  <-- add

from logging.config import fileConfig
import logging

# we're appending the app directory to our path here so that we can import config easily
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

from app.core.config import DATABASE_URL, POSTGRES_DB  # noqa <-- update

# Alembic Config object, which provides access to values within the .ini file
config = alembic.context.config

# Interpret the config file for logging
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode
    """
    <-- add
    DB_URL = f"{DATABASE_URL}_test" if os.environ.get("TESTING") else str(DATABASE_URL)

    # handle testing config for migrations
    if os.environ.get("TESTING"):
        # connect to primary db
        default_engine = create_engine(str(DATABASE_URL), isolation_level="AUTOCOMMIT")
        # drop testing db if it exists and create a fresh one
        with default_engine.connect() as default_conn:
            default_conn.execute(f"DROP DATABASE IF EXISTS {POSTGRES_DB}_test")
            default_conn.execute(f"CREATE DATABASE {POSTGRES_DB}_test")


    connectable = config.attributes.get("connection", None)
    config.set_main_option("sqlalchemy.url", DB_URL)  -->

    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    
    with connectable.connect() as connection:
        alembic.context.configure(
            connection=connection,
            target_metadata=None
        )

        with alembic.context.begin_transaction():
            alembic.context.run_migrations()


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    """
    if os.environ.get("TESTING"): <-- add
        raise DatabaseError("Running testing migrations offline currently not permitted.")


    alembic.context.configure(url=str(DATABASE_URL))

    with alembic.context.begin_transaction():
        alembic.context.run_migrations()


if alembic.context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    run_migrations_online()
```

테스트 데이터베이스 생성 및 연결을 지원하도록 마이그레이션 파일을 구성했다.
TESTING 환경변수가 설정되면 `postgres_test` 데이터베이스가 생성될 것이다.
그 후에 테스트가 실행되기 전에 해당 데이터베이스에 대해 마이그레이션이 실행될 것이다.

```python
if os.environ.get("TESTING"):
    # connect to primary db
    default_engine = create_engine(str(DATABASE_URL), isolation_level="AUTOCOMMIT")
    # drop testing db if it exists and create a fresh one
    with default_engine.connect() as default_conn:
        default_conn.execute(f"DROP DATABASE IF EXISTS {POSTGRES_DB}_test")
        default_conn.execute(f"CREATE DATABASE {POSTGRES_DB}_test")
```

먼저 유효한 자격 증명을 사용하여 기본 데이터베이스에 연결한다.
데이터베이스를 생성할 때 수동 트랜잭션 관리르 피하기 위해 `isolation_level`에 AUTOCOMMIT 옵션을 지정한다.
SQLAlchemy는 항상 트랜잭션에서 쿼리를 실행하려고 시도하며, postgres는 사용자가 트랜잭션 내에서 데이터베이스를 생성하는 것을 허용하지 않는다.
이 문제를 해결하기 위해 실행 후 열려 있는 각 트랜잭션을 자동으로 종료한다.
이를 통해 데이터베이스를 삭제한 다음 기본 연결 내부에 새 데이터베이스를 생성할 수 있다.

작업이 완료되면 즉시 원하는 데이터베이스에 연결하고 시작된다.

## 쓰기 테스트

- tests/test_cleanings.py

```python
import pytest

from httpx import AsyncClient
from fastapi import FastAPI

from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

class TestCleaningsRoutes:
    @pytest.mark.asyncio
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.post(app.url_path_for("cleanings:create-cleaning"), json={})
        assert res.status_code != HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_invalid_input_raises_error(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.post(app.url_path_for("cleanings:create-cleaning"), json={})
        assert res.status_code != HTTP_422_UNPROCESSABLE_ENTITY
```

cleaning 리소스와 연결된 경로가 존재하는지, 예상한 대로 동작하는 테스트하는데 사용할 클래스를 작성했다.
pytest가 비동기 테스트 기능을 처리할 수 있도록 `@pytest.mark.asyncio` 데코레이터를 사용했다.
각 클래스 메서드는 app, client 2개의 매개변수를 지정했다.
conftest.py 파일에 같은 이름으로 만들었기 때문에 Pytest는 모든 테스트 함수에서 이를 사용할 수 있도록 한다.

"Fixtures는 명시적인 이름을 가지며 테스트 기능, 모듈, 클래스 또는 전체 프로젝트에서 사용을 선언하여 활성화됩니다.
Fixture는 각 Fixture 이름이 다른 Fixture를 사용할 수 있는 Fixture 기능을 트리거하므로 모듈 방식으로 구현됩니다.
테스트 기능은 다음을 수신할 수 있습니다. 픽스처 객체를 입력 인수로 명명함으로써." - pytest

첫 번째 테스트는 httpx 클라이언트를 사용하고 "cleanings:create-cleaning"이라는 이름의 경로에 대한 POST 요청을 실행한다.
app/api/routes/cleanings.py 파일을 보면 POST 경로의 데코레이터에서 해당 이름을 확인할 수 있다.(Django의 URL reversing system을 반영한다.)
이 패턴을 사용하면 정확한 경로를 기억할 필요 없이 HTTP 요청을 보내기 위한 경로 이름에 의존할 수 있다.

이 요청은 404 응답을 받지 못한다고 주장할 것이며, 이 테스트가 통과할 것으로 기대한다.

두 번째 테스트는 동일한 요청을 보내지만 422 상태 코드가 포함되지 않을 겻을 기대한다.
FastAPI는 POST 본문에 잘못된 형식의 입력이 포함되면 422를 반환한다.(Pydantic)

FastAPI는 빈 사전이 이전에 정의한 CleaningCreate 모델의 모양을 가질 것으로 예상하기 때문에 이 테스트는 오류가 발생해야 한다.

서버 컨테이너로 접속해 pytest를 실행한다.

```
docker ps
docker exec -it [CONTAINER_ID] bash

$ pytest -v
```

서버 컨테이너는 테스트를 실행한다. 첫 번째는 통과, 두 번째는 실패해야 한다.
실패하면 다음과 같은 출력이 표시될 것이다.

```
==================================================================== test session starts =====================================================================
platform linux -- Python 3.8.13, pytest-6.2.1, py-1.11.0, pluggy-0.13.1 -- /usr/local/bin/python
cachedir: .pytest_cache
rootdir: /backend
plugins: anyio-3.6.1, asyncio-0.14.0
collected 2 items

tests/test_cleanings.py::TestCleaningsRoutes::test_routes_exist PASSED                                                                                 [ 50%]
tests/test_cleanings.py::TestCleaningsRoutes::test_invalid_input_raises_error FAILED                                                                   [100%]

========================================================================== FAILURES ==========================================================================
____________________________________________________ TestCleaningsRoutes.test_invalid_input_raises_error _____________________________________________________

self = <tests.test_cleanings.TestCleaningsRoutes object at 0xffffa849cf10>, app = <fastapi.applications.FastAPI object at 0xffffa849c8e0>
client = <httpx.AsyncClient object at 0xffffa84aca60>

    @pytest.mark.asyncio
    async def test_invalid_input_raises_error(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.post(app.url_path_for("cleanings:create-cleaning"), json={})
>       assert res.status_code != HTTP_422_UNPROCESSABLE_ENTITY
E       assert 422 != 422
E        +  where 422 = <Response [422 Unprocessable Entity]>.status_code

tests/test_cleanings.py:18: AssertionError
```

정확히 기대한 대로 동작하고, 실패한 테스트의 오류 위치와 실패한 이유를 알려준다. 422 != 422 를 422 == 422로 수정하자.

다시 테스트하면 모두 통과할 것이다.

## POST 경로 확인

## TDD 방식으로 엔드포인트 생성




