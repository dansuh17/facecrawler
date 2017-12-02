from crawler_engine_abc import CrawlerEngine
from insta_crawler import InstagramCrawlerEngine, BetterDriver
from threading import Thread, Event
from logger import Logger
import os
import signal
import queue
import time
import data_filter
import argparse


class Crawler:
    """
    Crawler system class. Comprises all modules required for crawling.
    """
    def __init__(self, crawler_engine_cls, webdriver_cls, logger=None,
            data_filter=None, data_filter_folder='./faces'):
        if not issubclass(crawler_engine_cls, CrawlerEngine):
            raise self.CrawlerEngineMismatchError
        self.crawler_engine_cls = crawler_engine_cls
        self.webdriver_cls = webdriver_cls
        self.logger = logger
        self.stopper = Event()
        self.data_filter = data_filter  # filter that selects wanted data only
        self.target_queue = queue.Queue(maxsize=100)  # queue collecting target keywords
        self.hashtag_duplicate = set()

        # create logger thread
        self.logger_thread = None
        self.log_queue = None
        if self.data_filter is not None:
            self.data_filter_folder = data_filter_folder
            if not os.path.exists(data_filter_folder):
                os.makedirs(data_filter_folder)

        if self.logger is not None:
            self.log_queue = queue.Queue(maxsize=1000)
            self.logger_thread = Thread(
                    target=self.log,
                    kwargs={
                        'log_queue': self.log_queue,
                    })

        # create worker threads
        self.workers = self.create_workers()

        # end gracefully upon Ctrl+C
        handler = SignalHandler(self.stopper, self.workers, self.logger, self.logger_thread)
        signal.signal(signal.SIGINT, handler)


    def create_workers(self, num_workers=2):
        """
        Args:
            num_workers (int): number of workers

        Returns:
            workers (set[Thread]): set of workers
        """
        for _ in range(num_workers):
            keyword = input("keyword: ")
            self.target_queue.put(keyword)
            self.hashtag_duplicate.add(keyword)

        # create workers
        workers = set()
        for _ in range(num_workers):
            if issubclass(self.crawler_engine_cls, Thread):
                crawler_engine_inst = self.crawler_engine_cls(
                        self.webdriver_cls(),
                        log_queue=self.log_queue,
                        hashtag_queue=self.target_queue,
                        hashtag_duplicate=self.hashtag_duplicate,
                        thread_stopper=self.stopper)
                workers.add(crawler_engine_inst)
            else:
                workers.add(Thread(
                    target=self.crawler_engine_cls(self.webdriver_cls()),
                    kwargs={
                        'log_queue': self.log_queue,
                        'hashtag_queue': self.target_queue,
                        'hashtag_duplicate': self.hashtag_duplicate,
                    }))
        return workers

    def log(self, log_queue: queue.Queue):
        """
        Gets a log information from the queue and logs the result.

        Args:
            log_queue: synchronous queue that stores log data
        """
        while True:
            if self.stopper.is_set():
                # break if stopper has been set
                break

            if not log_queue.empty():
                log_info = log_queue.get()

                if not log_info['success']:  # image retrieval was not successful
                    log_info['type'] = 'FAILED'
                else:
                    filepath = log_info['filepath']
                    # check whether wanted data is in the image
                    is_wanted = self.data_filter.detect_face(filepath)

                    # determine the data status
                    if is_wanted:
                        data_status = 'FILTERED'

                        # move the file to separate folder
                        new_filepath = os.path.join(self.data_filter_folder, log_info['name'])
                        os.rename(filepath, new_filepath)
                        log_info['filepath'] = new_filepath
                    else:
                        data_status = 'SAVED'

                    log_info['type'] = data_status
                print('Final log : {}'.format(log_info))
                self.logger.log(log_info)
                self.logger.send_status()
            else:
                time.sleep(3)  # sleep for a while if log queue is empty
        print('Log queue dead')

    def start(self):
        """
        Start crawling.
        """
        for i, worker in enumerate(self.workers):
            worker.start()
            print('Worker {} started'.format(i))
        self.logger_thread.start()
        print('Logger thread started')

    def close(self):
        """
        Stop crawling and close any additional running functionalities.
        """
        if self.logger is not None:
            logger.close()

    class CrawlerEngineMismatchError(Exception):
        """
        Exception indicating that crawler engine is not type of CrawlerEngine.
        """
        def __init__(self, message=''):
            self.message = message


class SignalHandler:
    """
    Signal handler for crawler.
    """
    def __init__(self, stopper: Event, workers, logger, logger_thread):
        self.stopper = stopper
        self.workers = workers
        self.logger = logger
        self.logger_thread = logger_thread

    def __call__(self, signum, frame):
        print('SIGINT received')
        self.stopper.set()  # set stop thread event

        print('Closing logger..')
        self.logger.close()  # close logger

        for worker in self.workers:
            worker.join()
        self.logger_thread.join()


if __name__ == '__main__':
    # prepare data filter
    image_set = input("Image set(eg. face): ")  # Desired image set (eg. face, cat, dog)
    data_filter = data_filter.DataFilter(image_set)

    # prepare the logger
    logger = Logger(('time', 'name', 'filepath', 'type'), log_folder='./log')
    logger.add_agg_type('SAVED', 'speed')
    logger.add_agg_type('SAVED', 'sum')

    # create a crawler and start crawling
    crawler = Crawler(crawler_engine_cls=InstagramCrawlerEngine,
            webdriver_cls=BetterDriver, logger=logger, data_filter=data_filter)
    crawler.start()
