from datetime import datetime
import requests
import logging as log

from django.core.management import BaseCommand
from django.conf import settings
from django.db import IntegrityError

from tickers.models import Ticker, TickerHistorical


def load():
    tickers = Ticker.objects.all()
    for ticker in tickers:
        ticker_symbol = ticker.symbol.replace('/', '_').replace('-', '_').replace('.', '_')
        url = 'https://www.quandl.com/api/v3/datasets/WIKI/%s/' \
              'data.json?api_key=%s' % (ticker_symbol, settings.QUANDL_API_TOKEN)

        response = requests.get(url=url)
        if response.status_code != 200:
            log.error('Error in Quandle request. Status code: %s with content: %s. '
                      'Request: %s' % (response.status_code, response.content, ticker_symbol))
            continue

        content = response.json().get('dataset_data')
        for history in content.get('data'):
            date = datetime.strptime(history[content['column_names'].index('Date')], '%Y-%m-%d')
            price = float(history[content['column_names'].index('Close')])
            volume = int(history[content['column_names'].index('Volume')])
            try:
                TickerHistorical.objects.create(ticker=ticker, date=date,
                                                price=price, volume=volume)
            except IntegrityError as e:
                log.exception('Exception %s, saving ticker historical %s, date %s. '
                              'Data to save: %s' % (str(e), ticker.symbol, date, history))
                continue


class Command(BaseCommand):
    help = "Command for loading tickers"

    def handle(self, *args, **options):
        try:
            load()
        except Exception as e:
            log.error('Error Loading Tickers Historical, error: %s' % str(e), exc_info=True)
