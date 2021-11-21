from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from .events import watch_games
import os


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(watch_games, 'interval', seconds=5)
    scheduler.start()


