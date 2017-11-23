from crawler_engine_abc import CrawlerEngine
from insta_crawler import InstagramCrawlerEngine, BetterDriver
from threading import Thread, Event
from logger import Logger
import signal
import queue
import time
import data_filter


class Crawler:
    """
    Crawler system class. Comprises all modules required for crawling.
    """
    def __init__(self, crawler_engine_cls, webdriver_cls, logger=None):
        if not issubclass(crawler_engine_cls, CrawlerEngine):
            raise self.CrawlerEngineMismatchError
        self.crawler_engine_cls = crawler_engine_cls
        self.webdriver_cls = webdriver_cls
        self.log_queue = queue.Queue(maxsize=100)
        self.logger = logger
        self.stopper = Event()

        image_set = input("Image set(eg. face): ")  # Desired image set (eg. face, cat, dog)
        self.data_filter = data_filter.Data_Filter(image_set)
        self.hashtag_queue = queue.Queue()
        self.hashtag_duplicate = set()
        self.workers = self.create_workers()
        self.logger_thread = Thread(target=self.log, args=(self.log_queue, ), daemon=True)

        # end gracefully upon Ctrl+C
        handler = SignalHandler(self.stopper, self.workers, self.logger)
        signal.signal(signal.SIGINT, handler)

    def create_workers(self, num_workers=2):
        """
        Args:
            num_workers (int): number of workers

        Returns:
            workers (Set[Thread]): set of workers
        """
        for _ in range(num_workers):
            keyword = input("keyword: ")
            self.hashtag_queue.put(keyword)
            self.hashtag_duplicate.add(keyword)

        # create workers
        workers = set()
        for _ in range(num_workers):
            if issubclass(self.crawler_engine_cls, Thread):
                crawler_engine_inst = self.crawler_engine_cls(
                        self.webdriver_cls(),
                        log_queue=self.log_queue,
                        hashtag_queue=self.hashtag_queue,
                        hashtag_duplicate=self.hashtag_duplicate,
                        data_filter=self.data_filter,
                        thread_stopper=self.stopper)
                workers.add(crawler_engine_inst)
            else:
                workers.add(Thread(
                    target=self.crawler_engine_cls(self.webdriver_cls()),
                    kwargs={
                        'log_queue': self.log_queue,
                        'hashtag_queue': self.hashtag_queue,
                        'hashtag_duplicate': self.hashtag_duplicate,
                        'data_filter': self.data_filter
                    }))
        return workers

    def log(self, log_queue: queue.Queue):
        """
        Gets a log information from the queue and logs the result.

        Args:
            log_queue: synchronous queue that stores log data
        """
        while True:
            if not log_queue.empty():
                log_info = log_queue.get()
                self.logger.log(log_info)
            else:
                time.sleep(2)

    def start(self):
        """
        Start crawling.
        """
        for i, worker in enumerate(self.workers):
            worker.start()
            print('Worker {} started'.format(i))
        self.logger_thread.start()
        print('Logger thread started')
        self.log_queue.join()  # block control indefinitely

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
    def __init__(self, stopper: Event, workers, logger):
        self.stopper = stopper
        self.workers = workers
        self.logger = logger

    def __call__(self, signum, frame):
        print('SIGINT received')
        self.stopper.set()  # set stop thread event
        for worker in self.workers:
            worker.join()  # wait for threads to exit
        self.logger.close()  # close logger


if __name__ == '__main__':
    # prepare the logger
    logger = Logger(('time', 'type', 'name'))
    logger.add_agg_type('SAVED', 'speed')
    logger.add_agg_type('SAVED', 'sum')

    # create a crawler and start crawling
    crawler = Crawler(crawler_engine_cls=InstagramCrawlerEngine, webdriver_cls=BetterDriver, logger=logger)
    crawler.start()

