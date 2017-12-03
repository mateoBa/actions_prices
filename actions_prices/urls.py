"""actions_prices URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from tickers.views import TickerApi, TickerHistoricalApi

ticker_router = DefaultRouter()
ticker_router.register(r'tickers', TickerApi, base_name="tickers")
ticker_router.register(r'tickers_historical', TickerHistoricalApi, base_name="tickers_historical")

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', TemplateView.as_view(template_name='tickers/main.html'), name='main'),
    url(r'^api/v1/', include(ticker_router.urls)),
]
