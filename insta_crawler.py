import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from crawler_engine_abc import CrawlerEngine
import threading
from threading import Thread
import os
import time
import hashlib
import queue
import requests
import http
import base64


class PhotoImgLoaded(object):
    """
    Callable class for finding photo image in instagram post.
    """
    def __init__(self, location):
        self.location = location

    def __call__(self, driver):
        try:
            # select image or video
            x, y = self.location
            img_or_video = driver.get_elem_at_point(x, y)
            img_parent = img_or_video.find_elements(By.XPATH, '..')[0]  # go to parent
            img_elem_arr = img_parent.find_elements_by_tag_name('img')

            if len(img_elem_arr) > 0:
                img_elem = img_elem_arr[0]
                return img_elem
            else:
                return False
        except:
            # catch all exception and simply return false
            # do not delegate exceptions since timeout WILL occur
            return False

class DownloadableImgLoaded(object):
    """
    Callable class for finding downloadable image on new tab.
    """
    def __init__(self):
        pass

    def __call__(self, driver):
        try:
            driver.switch_to.window(driver.window_handles[1])  # focus on current tab
            # this will use the browser cache and not send another request to instagram server.
            larger_img = driver.find_elements_by_tag_name('img')[0]
            return larger_img
        except:
            return False


class BetterDriver(webdriver.Firefox):
    """
    Class that extends the Firefox webdriver and adds other functionalities.
    """
    def __init__(self):
        super().__init__()

    def get_elem_at_point(self, x, y):
        """
        Get the web element located at browser coordinates.

        Args:
            x (num): x-coordinate
            y (num): y-coordinate

        Returns:
            web element at browser location (x, y)
        """
        return self.execute_script(
            'return document.elementFromPoint({}, {});'.format(x, y))


class InstagramCrawlerEngine(Thread):
    """
    Crawler engine targeted for crawling instagram photos.
    """
    RIGHT_ARROW_CLASS_NAME = 'coreSpriteRightPaginationArrow'

    def __init__(self, webdriver, log_queue=None, hashtag_queue=None,
                 hashtag_duplicate=None, thread_stopper=None):
        super().__init__()
        self.driver = webdriver
        # different urls for different target sites
        self.base_url = 'http://www.instagram.com/explore/tags/{}'
        self.save_folder_name = self.create_image_folder()
        self.log_queue = log_queue
        self.hashtag_queue = hashtag_queue
        self.hashtag_duplicate = hashtag_duplicate
        self.main_window = None
        self.thread_stopper = thread_stopper

    def set_tag(self, tag='korea'):
        """
        Sets the tag to search.

        Args:
            tag (str): search tag

        Returns:
            complete url with tag included
        """
        tag = self.hashtag_queue.get()
        return self.base_url.format(tag)

    def launch_driver(self):
        """
        Launch the web driver (selenium) to start crawling.
        """
        landing_url = self.set_tag()
        self.driver.get(landing_url)
        self.driver.set_window_size(900, 600)

    def init_crawl(self):
        """
        Set up and get ready for crawling.

        Returns:
            main window (tab) that becomes the base for crawling
        """
        try:
            # select rightmost picture (instagram pictures are organized in three columns)
            gateway_img_elem = self.driver.get_elem_at_point(850, 300)
            gateway_img_elem.click()  # click the element
            self.rest()
        except selenium.common.exceptions.NoSuchElementException:
            print("no element exception")
        return self.driver.current_window_handle  # return current window (tab)

    @staticmethod
    def create_image_folder(folder_name: str='images'):
        """
        Create folder to save image at.

        Args:
            folder_name (str): folder name to save images at

        Returns:
            name of folder
        """
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

        return folder_name

    def download(self, img_src: str, folder: str):
        """
        Download image provided by source and save folder path.
        Args:
            img_src (str): image url
            folder (str): folder name

        Returns:
            success (bool): whether download succeeded or not
            file_name (str): saved file name
        """
        # open the image in new tab
        self.driver.execute_script('window.open(\'{}\', \'_blank\');'.format(img_src))
        file_name = ''
        success = False

        try:
            # Wait for 2 seconds until image is loaded on the new tab
            larger_img = WebDriverWait(self.driver, 2).until(
                    DownloadableImgLoaded())

            # hash the source to get image file name
            file_hash = hashlib.sha1(img_src.encode()).hexdigest()
            file_name = '{}.png'.format(file_hash)

            # take screenshot of the image and save
            print('Saving : {}'.format(file_name))  # log progress
            larger_img.screenshot(os.path.join(folder, file_name))
            success = True
        except TimeoutException:
            print('Failed to retrieve downloadable image')
        finally:
            self.driver.close()  # close the tab, not the driver itself
            # switch to main window
            self.driver.switch_to.window(self.main_window)
        return success, file_name

    def find_next_img(self):
        """
        Find next image to crawl and download.

        Returns:
            url (str): image source url
        """
        try:
            img_elem = WebDriverWait(self.driver, 2).until(
                    PhotoImgLoaded(location=(250, 200)))
        except TimeoutException:
            raise self.ImageNotFoundException('Image Not Found')
        return img_elem.get_attribute('src')

    def go_next_post(self):
        """
        Proceed to next post of instagram.
        """
        # find right arrow and click. if not found, start again
        try:
            self.driver.find_element_by_class_name(self.RIGHT_ARROW_CLASS_NAME).click()
        except selenium.common.exceptions.NoSuchElementException:
            self.start_crawl()

    def find_text(self):
        """
        Find text of instagram post.
        """
        img_or_video = self.driver.get_elem_at_point(250, 200)
        parent_dom = img_or_video.find_elements(By.XPATH, '..')[0]  # go to parent
        while not parent_dom.tag_name == 'article':
            parent_dom = parent_dom.find_elements(By.XPATH, '..')[0]

        text_area = parent_dom.find_elements_by_tag_name('ul')[0]
        children_list_elems = text_area.find_elements_by_tag_name('li')
        main_post_texts = children_list_elems[0]
        main_text_elem = main_post_texts.find_elements_by_tag_name('span')
        main_text = []
        for main_span in main_text_elem:
            main_text.append(main_span.text)

        other_comments = children_list_elems[1:]
        comment_text = []

        for li in other_comments:
            links = li.find_elements_by_tag_name('a')
            for lin in links:
                comment_text.append(lin.text)
            spans = li.find_elements_by_tag_name('span')
            for sp in spans:
                comment_text.append(sp.text)

        return main_text, comment_text

    def add_hashtag(self):
        """
        Add hashtags of the post to queue.
        """
        img_or_video = self.driver.get_elem_at_point(250, 200)
        parent_dom = img_or_video.find_elements(By.XPATH, '..')[0]  # go to parent

        while not parent_dom.tag_name == 'article':
            parent_dom = parent_dom.find_elements(By.XPATH, '..')[0]

        text_area = parent_dom.find_elements_by_tag_name('ul')[0]
        children_list_elems = text_area.find_elements_by_tag_name('li')
        main_post_texts = children_list_elems[0]
        main_text_elem = main_post_texts.find_elements_by_tag_name('span')
        for main_span in main_text_elem:
            main_span_splits = main_span.text.split(" ")
            for word in main_span_splits:
                if (len(word) > 0
                        and word[0] == '#'
                        and word[1:] not in self.hashtag_duplicate
                        and not self.hashtag_queue.empty()):
                    self.hashtag_queue.put(word[0:])
                    self.hashtag_duplicate.add(word[1:])

    def close(self):
        """
        Close and stop crawling.
        """
        self.driver.close()

    def rest(self):
        """
        Rest for 2 seconds.
        """
        time.sleep(2)

    def __call__(self, log_queue=None, hashtag_queue=None, hashtag_duplicate=None):
        """
        Make the class instance callable.

        Args:
            log_queue (queue.Queue): thread-safe queue for collecting download status.
        """
        self.log_queue = log_queue
        self.hashtag_queue = hashtag_queue
        self.hashtag_duplicate = hashtag_duplicate
        self.start_crawl()

    def run(self):
        """
        Overrides Thread's run() method, which is called upon start() on a separately
        controllable thread.
        """
        self.start_crawl()

    def start_crawl(self):
        """
        Infinite loop of crawling.

        Args:
            log_queue (queue.Queue): thread-safe queue for collecting download status.
        """
        self.launch_driver()
        self.main_window = self.init_crawl()

        count = 0  # keep track of crawl count
        while not self.thread_stopper.is_set():
            count += 1
            try:
                self.go_next_post()
                image_src = self.find_next_img()
                success, filename = self.download(
                        img_src=image_src, folder=self.save_folder_name)
                self.add_hashtag()  # add to hashtag queue

                # log the download event
                log_entry = {
                    'time': time.time(),
                    'name': filename,
                    'filepath': os.path.join(self.save_folder_name, filename),
                    'success': success,
                }
                print(log_entry)

                if self.log_queue is not None:
                    self.log_queue.put(log_entry)
            except (self.ImageNotFoundException,
                selenium.common.exceptions.StaleElementReferenceException):
                # image not found for this step
                # (it might be video or the link might have been broken)
                # StaelElementReferenceException occurs when DOM element is modified
                # just before retrieving image source.
                continue
            except (ConnectionRefusedError, http.client.RemoteDisconnected):
                print('Driver closed by SIGINT or connection refused from target host.')
                break
        print('RETURNING from start_crawl() and closing thread id : {}.'.format(threading.get_ident()))

    class ImageNotFoundException(Exception):
        """
        Exception to note that image has not been found.
        """
        def __init__(self, message):
            self.message = message



if __name__ == '__main__':
    # ensures InstagramCrawlerEngine is a crawler engine
    assert issubclass(InstagramCrawlerEngine, CrawlerEngine)
    driver = BetterDriver()
    crawler = InstagramCrawlerEngine(driver)
    crawler.start_crawl()  # begin crawling
    crawler.close()  # probably won't happen...
