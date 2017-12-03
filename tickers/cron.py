import datetime
import threading
import socket
from queue import Queue

from multiprocessing import cpu_count
from django.conf import settings

from tickers.models import Ticker
from tickers.threads import ThreadForYahoo, ThreadHandler


def subscribe(data, event, queue):
    if not data:
        return False

    thread = ThreadHandler.get_thread_less_loaded()
    thread.stop()
    thread.add_ticker(data.upper())
    thread.start_again(event, queue)
    return True


def listen_socket(event, queue, host="127.0.0.1", port=8001):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15)
    sock.bind((host, port))

    sock.listen(5)
    client = None
    while True:
        if not event.is_set():
            break
        try:
            client, address = sock.accept()
            client.settimeout(15)
            data = client.recv(1024).decode()
            if subscribe(data, event, queue):
                client.send('ok'.encode())

        except socket.timeout:
            continue
        except KeyboardInterrupt:
            if client:
                client.close()
            break


class UpdateTickers(object):
    def __init__(self, threads=None):
        self.threads_num = threads if threads and isinstance(threads, int) else cpu_count()
        self.tickers = Ticker.objects.all()

    def main(self, run_event):
        queue = Queue()
        end = 0
        tickers_by_thread = self.tickers.count() // self.threads_num
        tickers = [ticker.symbol for ticker in self.tickers]

        for thread_number in range(self.threads_num):
            start = 0 if thread_number == 0 else end
            end = None if thread_number + 1 == self.threads_num else end + tickers_by_thread
            partial_tickers = tickers[start:end]

            thread = ThreadForYahoo(daemon=True, tickers=partial_tickers,
                                    event=run_event, queue=queue)
            thread.start()
            ThreadHandler.add(thread)

        # ####### thread with socket listening #########
        thread_socket = threading.Thread(target=listen_socket, args=(run_event, queue))
        thread_socket.start()

        now = datetime.datetime.now()
        while now.hour < settings.HOUR_TO_STOP_PRICES_WORKER:
            Ticker.save_or_update_ticker(queue.get())
            now = datetime.datetime.now()

        close_connections(run_event)


def close_connections(event):
    event.clear()

    threads = threading.enumerate()
    for thread in threads:
        if thread != threading.main_thread():
            thread.join()
