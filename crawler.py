from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import time
import hashlib


class Crawler:
    """
    General-purpose crawler.
    """
    RIGHT_ARROW_CLASS_NAME = 'coreSpriteRightPaginationArrow'

    def __init__(self, target_site: str='instagram'):
        self.driver = webdriver.Firefox()

        # different urls for different target sites
        if target_site == 'instagram':
            self.base_url = 'http://www.instagram.com/explore/tags/{}'

        self.save_folder_name = self.create_image_folder()
        self.launch_driver()
        self.main_window = self.init_crawl()

    def set_tag(self, tag='korea'):
        """
        Sets the tag to search.

        Args:
            tag (str): search tag

        Returns:
            complete url with tag included
        """
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
        # select rightmost picture (instagram pictures are organized in three columns)
        gateway_img_elem = self.get_elem_at_point(850, 300)
        gateway_img_elem.click()  # click the element
        time.sleep(2)  # required since popup may not have been loaded
        return self.driver.current_window_handle  # return current window (tab)

    def get_elem_at_point(self, x, y):
        """
        Get the web element located at browser coordinates.

        Args:
            x (num): x-coordinate
            y (num): y-coordinate

        Returns:
            web element at browser location (x, y)
        """
        return self.driver.execute_script(
            'return document.elementFromPoint({}, {});'.format(x, y))

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
        """
        # open the image in new tab
        self.driver.execute_script('window.open(\'{}\', \'_blank\');'.format(img_src))
        time.sleep(1)  # wait for tab to load
        self.driver.switch_to.window(self.driver.window_handles[1])  # focus on current tab

        # this will use the browser cache and not send another request to instagram server.
        larger_img = self.driver.find_elements_by_tag_name('img')[0]

        # hash the source to get image file name
        file_hash = hashlib.sha1(img_src.encode()).hexdigest()
        file_name = '{}.png'.format(file_hash)

        # take screenshot of the image and save
        print('Saving : {}'.format(file_name))  # log progress
        larger_img.screenshot(os.path.join(folder, file_name))
        self.driver.close()  # close the tab, not the driver itself

        # switch to main window
        self.driver.switch_to.window(self.main_window)

    def find_next_img(self):
        """
        Find next image to crawl and download.

        Returns:
            url (str): image source url
        """
        # find right arrow and click
        self.driver.find_element_by_class_name(self.RIGHT_ARROW_CLASS_NAME).click()
        time.sleep(1)

        # select image or video
        img_or_video = self.get_elem_at_point(250, 200)
        img_parent = img_or_video.find_elements(By.XPATH, '..')[0]  # go to parent

        img_elem_arr = img_parent.find_elements_by_tag_name('img')
        if len(img_elem_arr) > 0:
            img_elem = img_elem_arr[0]
        else:
            raise self.ImageNotFoundException('Image not found.')

        return img_elem.get_attribute('src')

    def crawl_loop(self):
        """
        Infinite loop of crawling.
        """
        while True:
            try:
                image_src = self.find_next_img()
            except self.ImageNotFoundException:
                # image not found for this step
                # (it might be video or the link might have been broken)
                continue

            self.download(img_src=image_src, folder=self.save_folder_name)
            self.rest()

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

    class ImageNotFoundException(Exception):
        """
        Exception to note that image has not been found.
        """
        def __init__(self, message):
            self.message = message


if __name__ == '__main__':
    crawler = Crawler(target_site='instagram')
    crawler.crawl_loop()  # begin crawl loop
    crawler.close()  # probably won't happen...
