import threading
import traceback

from django.core.management import BaseCommand

from tickers.cron import UpdateTickers, close_connections


class Command(BaseCommand):
    help = "Command for loading tickers"

    def handle(self, *args, **options):
        self.stdout.write('Empezando....')
        run_event = threading.Event()
        run_event.set()
        update = UpdateTickers()
        try:
            update.main(run_event)
        except (SystemExit, KeyboardInterrupt):
            print('exeption de SystemExit o Keybordinterrupt, NO le des de nuevo que ya termina!')
        except Exception as e:
            traceback.print_exc()
            print('Unexpected error %s' % e)
        finally:
            close_connections(run_event)

        self.stdout.write('... Finalizando')
