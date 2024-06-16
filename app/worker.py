import asyncio
import json
from aiobotocore.session import get_session as get_boto_session
from config import SQS_QUEUE_URL
from routers.logs import LogEntryRequest
from db.models import write_logs 
from db.models import LogEntry
from db import AsyncSessionLocal


async def process_messages():
    """
    Continuously processes log messages from the Amazon SQS queue in config.SQS_QUEUE_URL and stores them in a PostgreSQL database.
    """
    boto_session = get_boto_session()
    async with boto_session.create_client('sqs') as client:
        while True:
            response = await client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=10,
                MessageAttributeNames=['All']
            )

            if 'Messages' in response:
                async with AsyncSessionLocal() as db_session:
                    delete_entries = []  # Entries to be deleted from the SQS queue
                    add_logs = []  # Log entries to be added to the database
                    for message in response['Messages']:
                        msg_body = message['Body']
                        msg = LogEntryRequest(**json.loads(msg_body))
                        add_logs.append(LogEntry(message=msg.message, level=msg.level, timestamp=msg.timestamp))
                        delete_entries.append({
                            'Id': message['MessageId'],
                            'ReceiptHandle': message['ReceiptHandle']
                        })
                    await write_logs(db_session, add_logs)
                    await client.delete_message_batch(
                        QueueUrl=SQS_QUEUE_URL,
                        Entries=delete_entries
                    )
  

if __name__ == "__main__":
    asyncio.run(process_messages())