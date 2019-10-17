import schedule
import time
import threading


def clean_users():
    print('TODO : Cleaning users')


def init_scheduling():
    def run():
        schedule.every(5).seconds.do(clean_users)
        while True:
            schedule.run_pending()
            time.sleep(1)

    thread = threading.Thread(target=run, args=())
    thread.daemon = True
    thread.start()
