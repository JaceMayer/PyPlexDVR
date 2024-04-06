import os
import threading
import time

from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

HandlerToObserver = {}
class WatchDogObserver:
    def __init__(self, baseDir, showDirs, channel):
        self.observer = None
        self.baseDir = baseDir
        self.showDirs = showDirs
        self.channel = channel
        self._thread = threading.Thread(target=self.startObeserver, args=())
        self._thread.start()

    def rebootChannel(self):
        self.channel.pendReboot()

    def startObeserver(self):
        self.observer = PollingObserver()
        event_handler = WatchDogHandler()
        HandlerToObserver[event_handler] = self
        for show in self.showDirs:
            watchDirectory = os.path.join(self.baseDir, show)
            self.observer.schedule(event_handler, watchDirectory, recursive=True)
        self.observer.start()


class WatchDogHandler(FileSystemEventHandler):

    def on_created(self, event):
        if event.is_directory:
            return None
        time.sleep(10)
        observer = HandlerToObserver[self]
        observer.rebootChannel()

    def on_deleted(self, event):
        if event.is_directory:
            return None
        time.sleep(10)
        observer = HandlerToObserver[self]
        observer.rebootChannel()
