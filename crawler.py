from crawler_engine_abc import CrawlerEngine
from insta_crawler import InstagramCrawlerEngine, BetterDriver
from threading import Thread
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

        image_set = input("Image set(eg. face): ")  # Desired image set (eg. face, cat, dog)
        self.data_filter = data_filter.Data_Filter(image_set)
        self.hashtag_queue = queue.Queue()
        self.hashtag_duplicate = set()
        self.workers = self.create_workers()
        self.logger_thread = Thread(target=self.log, args=(self.log_queue, ), daemon=True)

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
        workers = set()
        for _ in range(num_workers):
            if issubclass(self.crawler_engine_cls, Thread):
                workers.add(self.crawler_engine_cls(self.webdriver_cls(), self.log_queue))
            else:
                workers.add(Thread(
                    target=self.crawler_engine_cls(self.webdriver_cls()),
                    kwargs={'log_queue': self.log_queue, 'hashtag_queue': self.hashtag_queue,
                            'hashtag_duplicate': self.hashtag_duplicate, 'data_filter': self.data_filter}))
        return workers

    def log(self, log_queue: queue.Queue):
        """
        Gets a log information from the queue and logs the result.

        log_queue: synchronous queue that stores log data
        """
        while True:
            if not log_queue.empty():
                log_info = log_queue.get()
                # TODO: actually use the logger!
                print(log_info)  # debug message
                # self.logger.log(log_info)
            else:
                time.sleep(2)

    def start(self):
        """
        Start crawling.
        """
        for thread in self.workers:
            print('start')
            thread.start()
        self.logger_thread.start()
        self.log_queue.join()  # block control indefinitely

    def close(self):
        """
        Stop crawling and close any additional running functionalities.
        """
        self.crawler_engine.close()
        if self.logger is not None:
            # TODO: fit to logger specifications
            logger.close()

    class CrawlerEngineMismatchError(Exception):
        """
        Exception indicating that crawler engine is not type of CrawlerEngine.
        """
        def __init__(self, message=''):
            self.message = message


if __name__ == '__main__':
    crawler = Crawler(crawler_engine_cls=InstagramCrawlerEngine, webdriver_cls=BetterDriver)
    crawler.start()

