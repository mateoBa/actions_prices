# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json
import pickle
import redis
import logging as log

from django.conf import settings
from channels import Group
from django.db import models, IntegrityError

redis_db = redis.StrictRedis(host='localhost', port=6379, db=0)


class Ticker(models.Model):

    symbol = models.CharField(max_length=8, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text='l84', null=True)
    change = models.DecimalField(max_digits=6, decimal_places=2, help_text='c63', null=True)
    change_perc = models.DecimalField(max_digits=6, decimal_places=2, help_text='p43', null=True)
    market_cap = models.CharField(max_length=12, help_text='j10', null=True)
    volume = models.BigIntegerField(help_text='v53', null=True)
    last_update = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.symbol

    def update_ticker(self, data):
        self.price = data['price']
        self.change = data['change']
        if data.get('change_perc'):
            self.change_perc = data['change_perc']
        if data.get('market_cap'):
            self.market_cap = data['market_cap']
        if data.get('volume'):
            volume = data['volume']
            self.volume = volume

        # it makes django orm, now we have to do this for redis
        self.last_update = datetime.datetime.now()
        pickled_ticker = pickle.dumps(self)
        redis_db.set(data['symbol'], pickled_ticker)
        # self.save()

    @classmethod
    def save_or_update_ticker(cls, data):
        if not ('l84' in data and 'c63' in data):
            return

        data_to_save = {'symbol': str(data['symbol'])}
        data_to_save.update({'price': float(data['l84'])})
        data_to_save.update({'change': float(data['c63'])})
        if data.get('p43'):
            data_to_save.update({'change_perc': float(data['p43'])})
        if data.get('j10'):
            data_to_save.update({'market_cap': data['j10']})
        if data.get('v53'):
            data_to_save.update({'volume': int(data['v53'].replace(',', ''))})

        ticker_in_redis = redis_db.get(data['symbol'])
        if ticker_in_redis:
            ticker = pickle.loads(ticker_in_redis)
            ticker.update_ticker(data_to_save)
        else:
            ticker = Ticker(**data_to_save)
            # we have to charge datetime.now, because now it is saved in redis and not en bd
            ticker.last_update = datetime.datetime.now()
            pickled_ticker = pickle.dumps(ticker)
            redis_db.set(data['symbol'], pickled_ticker)
            # ticker.save()

        ticker.send_data_to_websocket(data['symbol'])

    def send_data_to_websocket(self, symbol):
        tickers_list = redis_db.get('redis_tickers')
        if not tickers_list:
            return

        tickers_list = pickle.loads(tickers_list)
        if symbol in tickers_list:
            Group(symbol).send({'text': json.dumps({symbol: self.to_dict()})})

    @classmethod
    def subscribe_ticker(cls, symbol):
        Ticker.objects.create(symbol=symbol)

        now = datetime.datetime.now()
        if settings.HOUR_TO_START_PRICES_WORKER <= now.hour < settings.HOUR_TO_STOP_PRICES_WORKER:
            return send_ticker_to_socket(symbol=symbol)

        return True

    @classmethod
    def get_object(cls, symbol):
        ticker = Ticker.objects.filter(symbol=symbol)
        if not ticker:
            return None

        try:
            return pickle.loads(redis_db.get(symbol))
        except TypeError:
            return ticker.first()

    def to_dict(self):
        return {'symbol': self.symbol, 'price': self.price, 'change': self.change,
                'percentage_change': self.change_perc, 'market_cap': self.market_cap,
                'volume': self.volume, 'last_update': self.last_update.strftime('%Y/%m/%dT%H:%M:%S')}


def send_ticker_to_socket(symbol, host="127.0.0.1", port=8001):
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.send(symbol.encode())
    data = sock.recv(1024).decode()
    sock.close()

    return data == 'ok'


class TickerHistorical(models.Model):
    ticker = models.ForeignKey(Ticker)
    date = models.DateField()
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text='l84')
    volume = models.BigIntegerField(help_text='v53', null=True)

    def __unicode__(self):
        return '%s - %s' % (self.ticker.symbol, self.date)

    class Meta:
        unique_together = (("ticker", "date"),)

    @classmethod
    def create(cls, ticker, date, price, volume):
        last_historical = cls.objects.filter(ticker=ticker).last()
        try:
            cls.objects.create(ticker=ticker, date=date, price=price, volume=volume)
        except IntegrityError as e:
            log.exception('Exception %s, saving ticker historical %s, date %s. Price and Volume '
                          'to save: %s, %s' % (str(e), ticker.symbol, date, price, volume))
            return False

        if last_historical:
            values = [last_historical.price, price]
            percentage_diff = (float(min(values)) / float(max(values))) * 100
            return percentage_diff >= settings.PERCENTAGE_DIFFERENCE_TO_SEND_ALERT

        return False
