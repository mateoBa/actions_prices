# Tickers

Proyecto para [ibillionaire](https://ibillionaire.com/), podes consultar el precio actual de una acción que cotiza en bolsa (ej tsla) si no la tiene registrada, devuelve 201 de acción creada con exito caso contrario nos devuelve el valor de la acción.

Para consultar un ticker por ejemplo TSLA:
http://127.0.0.1:8000/api/v1/tickers/tsla (obtiene la última información actualida del ticker tsla)

La información proviene de la [API de yahoo](https://streamerapi.finance.yahoo.com/streamer/1.0) 

