import logging as log
import requests
from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management import BaseCommand

from tickers.models import Ticker, TickerHistorical


def update():
    tickers = Ticker.objects.all()
    today = datetime.now().strftime('%Y-%m-%d')
    tickers_to_notify = []

    for ticker in tickers:
        ticker_symbol = ticker.symbol.replace('/', '_').replace('-', '_').replace('.', '_')
        url = 'https://www.quandl.com/api/v3/datasets/WIKI/%s.json?start_date=%s&end_date=%s&' \
              'api_key=%s' % (ticker_symbol, today, today, settings.QUANDL_API_TOKEN)

        response = requests.get(url=url)
        if response.status_code != 200:
            log.error('Error in Quandle request. Status code: %s with content: %s. '
                      'Request: %s' % (response.status_code, response.content, ticker_symbol))
            continue

        content = response.json().get('dataset')
        if content['newest_available_date'] != today or not content.get('data'):
            log.exception('Check date %s. The market did not trade?'
                          'Content Quandl: %s' % (today, content))
            continue

        first = content.get('data')[0]
        date = datetime.strptime(today, '%Y-%m-%d')
        price = float(first[content['column_names'].index('Close')])
        volume = int(first[content['column_names'].index('Volume')])

        if TickerHistorical.create(ticker=ticker, date=date, price=price, volume=volume):
            tickers_to_notify.append(ticker.symbol)

    if tickers_to_notify:
        text = '\n'.join(tickers_to_notify)
        email = EmailMessage('[Historical Difference] %s Alert' % today,
                             'Historical difference mayor than %s, in the next tickers: \n'
                             '%s' % (settings.PERCENTAGE_DIFFERENCE_TO_SEND_ALERT, text),
                             to=settings.MANAGERS_EMAIL)
        email.send()


class Command(BaseCommand):
    help = "Command for Updating Tickers Historical"

    def handle(self, *args, **options):
        try:
            update()
        except Exception as e:
            log.error('Error Updating Tickers Historical, error: %s' % str(e), exc_info=True)
