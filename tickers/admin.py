# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from tickers.models import TickerHistorical, Ticker

admin.site.register(Ticker)
admin.site.register(TickerHistorical)
