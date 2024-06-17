import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, Text, DateTime
from db import AsyncSession, Base


class LogEntry(Base):
    __tablename__ = 'log_entries'

    id = Column(Integer, primary_key=True)
    message = Column(Text)
    level = Column(String)
    timestamp = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC))


async def write_logs(session: AsyncSession, logs: list[LogEntry]):
    """
        Write a list of log entries to the database.  
    
        :param session: The database session to use.
        :param logs: The list of log entries to write.
        
        :return: None
    """
    session.add_all(logs)
    await session.commit()