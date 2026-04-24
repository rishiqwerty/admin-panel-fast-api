# Common database dependencies
from typing import Generator
from sqlalchemy.orm import Session

# This can be used as a default if none is provided, but usually the user provides their own get_db
def get_db_placeholder() -> Generator[Session, None, None]:
    yield None
