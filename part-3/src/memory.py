import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver
from src.config import CHECKPOINT_DB_PATH

_sqlite_conn = None
_checkpointer = None

def get_checkpointer(db_path: Path = CHECKPOINT_DB_PATH):
    global _sqlite_conn, _checkpointer
    if _checkpointer is None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _sqlite_conn = sqlite3.connect(str(db_path), check_same_thread=False)
        _checkpointer = SqliteSaver(_sqlite_conn)
    return _checkpointer

def get_sqlite_conn(db_path: Path = CHECKPOINT_DB_PATH):
    global _sqlite_conn
    if _sqlite_conn is None:
        get_checkpointer(db_path)
    return _sqlite_conn
