# Tickers

Proyecto para [ibillionaire](https://ibillionaire.com/), mediante el cual se podrá conectar a un websocket y obtener los valores de las acciones cada vez que se actualizan. Podes consultar el precio actual de una acción que cotiza en bolsa (ej aapl) si no la tiene registrada, devuelve 201 de acción creada con exito caso contrario nos devuelve el valor de la acción. El valor de las acciones puede ser consultada por api o websocket.

### Installation

```sh
$ sudo apt-get update
$ sudo apt-get install python3
$ sudo apt-get install python3-dev
$ sudo apt-get install redis-server
$ cd actions_prices/
$ pip install -r requirements.txt
$ python manage.py migrate
```

Para guardar en bd las principales acciones, ejecutamos:
```sh
$ python manage.py load_tickers
```
Luego para actualizar los valores de las acciones (importante aclarar que se actualizan si la hora actual esta entre las 10 y las 17 hs de USA), se debe correr:
```sh
$ python manage.py update_tickers
```
Para correr el servidor:
```sh
$ python manage.py runserver
```

### Información
Para consumir los valores, con servidor corriendo, por api:
http://127.0.0.1:8000/api/v1/tickers/AAPL

Para consumir los datos por websocket de manera rápida y sencilla es con Simple WebSocket Client es un complemento para Firefox o Chrome. 
En URL ponemos ws://127.0.0.1:8000/web_socket/ y en nos conectamos con el boton open, en la request se le puede enviar un string con ticker o una lista de tickers. 

La información proviene de la [API de yahoo](https://streamerapi.finance.yahoo.com/streamer/1.0) 

