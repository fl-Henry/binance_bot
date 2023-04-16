from time import sleep

from log_handler.log_handler import LogHandler
from selenium_handler import SeleniumHandler
from scrape_logic import script_process

if __name__ == '__main__':
    lh = LogHandler(name='myparts_ge',)
    sh = SeleniumHandler('main.cfg', lh.logger)
    script_process(sh, lh)
    sleep(10)
    sh.quit_browser()
