from aiobotocore.session import get_session as get_boto_session
from config import SQS_QUEUE_URL

session = get_boto_session()
sqs_client = None

async def get_sqs_client():
    """
    Returns a singleton instance of an asynchronous SQS client.

    If the SQS client does not already exist, it creates and initializes one.
    The client is stored in the global variable `sqs_client` to ensure only one instance is used.

    Returns:
        An initialized asynchronous SQS client.
    """
    global sqs_client
    if sqs_client is None:
        async with session.create_client('sqs') as client:
            sqs_client = client
    return sqs_client


async def send_to_sqs(message: str, queue_url: str = SQS_QUEUE_URL):
    """
    Sends a message to an Amazon SQS queue.

    Args:
        message (str): The message to be sent to the SQS queue.
    Returns:
        dict: The response from the SQS `send_message` API call.
    """
    client = await get_sqs_client()
    response = await client.send_message(
        QueueUrl=queue_url,
        MessageBody=message,
    )
    return response