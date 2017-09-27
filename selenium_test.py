from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

# open the web driver and go to a specific website (instagram)
driver = webdriver.Firefox()
driver.get('http://www.instagram.com/explore/tags/haha')
driver.set_window_size(900, 680)
# print(driver.get_window_size())
# driver.maximize_window()

# example usages of executing javascript
print(driver.execute_script('return document.title;'))

# select rightmost picture (instagram pictures are organized in three columns)
elem = driver.execute_script('return document.elementFromPoint(850, 300);')
print(elem.get_attribute('class'))
elem.click()  # click the element
time.sleep(2)  # required because the popup may not have been loaded

# select image or video
img_or_video = driver.execute_script(
        'return document.elementFromPoint(250, 200)')
img_parent = img_or_video.find_elements(By.XPATH, '..')[0]  # go to parent
img_elem = img_parent.find_elements_by_tag_name('img')[0]

# obtain the source
img_src = img_elem.get_attribute('src')
print(img_src)

# save current window
main_window = driver.current_window_handle

# open the image in new tab
driver.execute_script('window.open(\'{}\', \'_blank\');'.format(img_src))
time.sleep(1)  # wait for tab to load
print(driver.window_handles)
driver.switch_to_window(driver.window_handles[1])  # focus on current tab

# take screenshot of the image and save
larger_img = driver.find_elements_by_tag_name('img')[0]
larger_img.screenshot('screenshot.png')
driver.close()  # close the tab

# close popup
driver.switch_to_window(main_window)
actionChains = webdriver.ActionChains(driver)
actionChains.send_keys(Keys.ESCAPE).perform()

time.sleep(2)
driver.close()
