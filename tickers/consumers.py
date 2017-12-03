import pickle
import simplejson as json
from simplejson import JSONDecodeError

from channels import Group

from tickers.models import redis_db


def ws_connect(message):
    message.reply_channel.send({"accept": True})


def websocket_receive(message):
    tickers = message.content.get('text')
    if not tickers:
        Group('Error').add(message.reply_channel)
        Group('Error').send({'text': 'Error: No data'})
        return
    try:
        tickers = json.loads(tickers)
    except JSONDecodeError:
        Group('Error').add(message.reply_channel)
        Group('Error').send({'text': 'Error: Malformed data. Only receive an string or strings list, examples: "a", ["a", "b"]'})
        return

    tickers = set(tickers) if isinstance(tickers, list) else [tickers]

    redis = pickle.loads(redis_db.get('tickers_list')) if redis_db.get('tickers_list') else set()

    not_found_tickers = set()
    for ticker in tickers:
        tic = ticker.upper()
        ticker_in_redis = redis_db.get(tic)
        if ticker_in_redis:
            Group(tic).add(message.reply_channel)
            unpacked_ticker = pickle.loads(ticker_in_redis)
            Group(tic).send({'text': json.dumps({tic: unpacked_ticker.to_dict()})})
            redis.add(tic)
        else:
            not_found_tickers.add(ticker)

    if not_found_tickers:
        Group('Error').add(message.reply_channel)
        Group('Error').send({'text': json.dumps({'Error': 'Not found: %s' % not_found_tickers})})

    if not_found_tickers != tickers:
        redis_db.set('redis_tickers', pickle.dumps(redis))


def ws_disconnect(message):
    tickers_list = redis_db.get('tickers_list')
    if tickers_list:
        tickers_list = pickle.dumps(tickers_list)
        for ticker in tickers_list:
            Group(ticker).discard(message.reply_channel)
