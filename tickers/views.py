import requests

from rest_framework import viewsets, status
from rest_framework.response import Response
from django.conf import settings

from tickers.models import Ticker, TickerHistorical
from tickers.serializers import TickerSerializer, TickerHistoricalSerializer


class TickerApi(viewsets.ReadOnlyModelViewSet):
    """ Show Tickers """
    queryset = Ticker.objects.all()
    serializer_class = TickerSerializer

    def retrieve(self, request, *args, **kwargs):
        symbol = kwargs.get('pk')
        if not symbol:
            return Response('Error!', status=status.HTTP_204_NO_CONTENT)

        symbol = symbol.upper()
        ticker = Ticker.get_object(symbol=symbol)
        if ticker:
            serializer = TickerSerializer(ticker)
            return Response(serializer.data)
        else:
            uri = settings.YAHOO_ENDPOINT % symbol
            response = requests.get(uri, stream=True)
            if response.status_code == status.HTTP_200_OK:
                if Ticker.subscribe_ticker(symbol):
                    return Response('%s created' % symbol.upper(), status=status.HTTP_201_CREATED)
                return Response('Error, could not subscribe the %s' % symbol,
                                status=status.HTTP_423_LOCKED)
            return Response('Error! not found. ', status=status.HTTP_404_NOT_FOUND)


class TickerHistoricalApi(viewsets.ReadOnlyModelViewSet):
    """ Show Tickers Historical """
    queryset = TickerHistorical.objects.all()
    serializer_class = TickerHistoricalSerializer
