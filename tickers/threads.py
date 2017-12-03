import ast
import re
import threading
import requests

from operator import attrgetter

from django.conf import settings


class ThreadHandler(object):
    threads = []

    @classmethod
    def add(cls, thread):
        if isinstance(thread, ThreadForYahoo):
            cls.threads.append(thread)

    @classmethod
    def get_thread_less_loaded(cls):
        return min(cls.threads, key=attrgetter('tickers_count'))

    @classmethod
    def get_threads(cls):
        return cls.threads


class ThreadForYahoo(threading.Thread):

    def __init__(self, daemon, tickers, queue, event):
        self._tickers = tickers
        self._running = False
        self._daemon = daemon
        self._res = requests.get(settings.YAHOO_ENDPOINT % self._get_tickers_str(), stream=True)
        super(ThreadForYahoo, self).__init__(target=self.convert_chunk, args=(event, queue))
        self.setDaemon(daemon)

    def start(self):
        self._running = True
        super(ThreadForYahoo, self).start()

    def convert_chunk(self, event, queue):
        for chunk in self._res.iter_content(chunk_size=None):
            if not event.is_set() or not self._running:
                break
            if not chunk:
                continue
            chunk = chunk.decode('utf-8')
            for symbol in self._tickers:
                code_exist = re.search('%s":{' % symbol, chunk)
                if not code_exist:
                    continue
                line = ''
                happy_ending = False
                for letter in chunk[code_exist.end() - 1:]:
                    line += letter
                    if letter == '}':
                        happy_ending = True
                        break

                if happy_ending:
                    line = line.replace('",', '","').replace('{', '{"').replace(':', '":')
                    line = ast.literal_eval(line)
                    line.update({'symbol': symbol})
                    queue.put(line)

    def _get_tickers_str(self):
        tickers_str = ''
        for ticker in self._tickers:
            tickers_str += '%s,' % ticker

        return tickers_str[:-1]

    @property
    def tickers_count(self):
        return len(self._tickers)

    def add_ticker(self, ticker_symbol):
        self._tickers.append(ticker_symbol)

    def stop(self):
        self._running = False
        self._tstate_lock = None
        self._stop()
        # self.join()

    def start_again(self, event, queue):
        self.__init__(self._daemon, self._tickers, queue, event)
        self.start()
