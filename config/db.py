import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SQLITE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

POSTGRESQL = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

MYSQL = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3307'),
    }
}

_oracle_host = os.getenv('DB_HOST', '127.0.0.1')
_oracle_port = os.getenv('DB_PORT', '1521')
_oracle_name = os.getenv('DB_NAME', 'FREEPDB1')

if '/' in _oracle_name:
    _oracle_dsn = _oracle_name
elif _oracle_host and _oracle_port:
    _oracle_dsn = f"{_oracle_host}:{_oracle_port}/{_oracle_name}"
elif _oracle_host:
    _oracle_dsn = f"{_oracle_host}/{_oracle_name}"
else:
    _oracle_dsn = _oracle_name

ORACLE = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': _oracle_dsn,
        'USER': os.getenv('DB_USER', 'SAGIS_DEV'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': '',
        'PORT': '',
    }
}