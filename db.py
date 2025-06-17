from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy import text

class Base(DeclarativeBase):
    pass

def _get_server_version_info(self, connection):
    version = connection.scalar(text("SELECT version()"))
    if 'CockroachDB' in version:
        # Return a compatible PostgreSQL version
        return (9, 5, 0)
    return super(PGDialect, self)._get_server_version_info(connection)

PGDialect._get_server_version_info = _get_server_version_info

db = SQLAlchemy(model_class=Base) 