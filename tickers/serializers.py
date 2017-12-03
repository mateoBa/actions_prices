from rest_framework import serializers

from tickers.models import Ticker, TickerHistorical


class TickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticker
        fields = ('symbol', 'price', 'change', 'change_perc',
                  'market_cap', 'volume', 'last_update')


class TickerHistoricalSerializer(serializers.ModelSerializer):
    ticker = serializers.ReadOnlyField(source='ticker.symbol')

    class Meta:
        model = TickerHistorical
        fields = ('ticker', 'date', 'price', 'volume')
