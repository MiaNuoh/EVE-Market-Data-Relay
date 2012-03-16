"""
Functions to facilitate pushing jobs into the market order SQS queue, and
popping them back out. These are primarily used by the gateway and the
economist daemons, but may be useful elsewhere.
"""
from boto.sqs.connection import SQSConnection

import settings
from src.core.market_data import MarketOrder

# Don't access these directly. Used for lazy-loading.
_SQS_CONNECTION = None
_SQS_QUEUE = None

def get_sqs_queue():
    """
    Lazy-loads and returns a boto SQS queue.

    :rtype: boto.sqs.queue.Queue
    """
    global _SQS_CONNECTION, _SQS_QUEUE

    if not _SQS_CONNECTION:
        _SQS_CONNECTION = SQSConnection(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY)

    if not _SQS_QUEUE:
        _SQS_QUEUE = _SQS_CONNECTION.create_queue(
            settings.MARKET_ORDER_QUEUE_NAME,
            visibility_timeout=settings.MARKET_ORDER_QUEUE_VIS_TIMEOUT,
        )

    return _SQS_QUEUE

def enqueue_order(order):
    """
    Given a market order, stuff said order into the queue for an economist
    daemon to pop and process.

    :type order: src.core.market_data.MarketOrder
    :param order: The order to enqueue.
    """
    queue = get_sqs_queue()
    # This is the JSON representation of the order that will be pushed to
    # the queue.
    msg = queue.new_message(body=order.to_json())
    # Bombs away.
    if not queue.write(msg):
        raise Exception("Unknown error while enqueing market order.")

def pop_order(max_num_orders=1):
    """
    Pop up to the specified number of jobs from the order queue. This is
    almost always done by an economist daemon, who then analyzes the data,
    works it into regional averages, calculates all sorts of fun things, then
    saves the resulting numbers to the DB.

    :keyword int max_num_orders: The maximum number of orders to pop from the
        queue at a time. Be careful setting this too high, it can prevent
        other workers from getting to the jobs and getting them out of the
        way faster.
    :rtype: generator
    :returns: A generator of :py:class:`src.core.market_data.MarketOrder`
        instances.
    """
    queue = get_sqs_queue()
    messages = queue.get_messages(num_messages=max_num_orders)
    for message in messages:
        # The message body is a JSON representation of the order.
        order = MarketOrder.from_json(message.get_body())
        # Delete the order from the queue to avoid re-processing.
        message.delete()
        yield order