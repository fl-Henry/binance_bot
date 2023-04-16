import os
import sys
import time
import itertools
import configparser
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By
from selenium import webdriver
from logging import Logger


class ProxyRotator:
    def __init__(self, proxies):
        # create iterator, which will cycle through the proxies
        self.proxies = itertools.cycle(proxies)
        self.current_proxy = None
        self.good_proxy = {}
        # counter of request to change proxy
        self.request_counter = 0

    def change_proxy(self):
        # Change the proxy to the next one and reset the counter
        self.current_proxy = next(self.proxies)
        self.request_counter = 0
        return self.current_proxy

    def get_proxy(self):
        # check if the proxy has to be changed ("2" means change after every second request)
        if self.request_counter % 2 == 0:
            self.change_proxy()
        self.request_counter += 1
        return self.current_proxy


class SeleniumHandler:

    def __init__(self, config_name, logger: Logger = None):
        self.browser = None
        self.config = None

        if config_name is None:
            self.config_name = 'main.cfg'
        else:
            self.config_name = config_name

        print("Initializing Browser Instance!")
        if logger is not None:
            self.logger = logger
            self.logger.info("Initializing Browser Instance!")

        # path to selenium_handler.py dir
        self.base_path = str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]
        self.config_path = f"{self.base_path}/{self.config_name}"

        if not os.path.exists(self.config_path):
            print("[Warning] SeleniumHandler.__init__: Config_file doesn't exist")
            print("Could you create the default config file? Y/N: ")
            answer = input()
            if answer in ['Y', 'y']:
                self.create_default_config()
            else:
                print("[ERROR] SeleniumHandler.__init__: Config_file doesn't exist")
                sys.exit(1)

        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        # browser_path = config.get('DEFAULT', 'browser_path')
        # if self.logger is not None:
        #     self.logger.debug("browser_path: %s", browser_path)
        driver_path = self.config.get('DEFAULT', 'driver_path')
        if self.logger is not None:
            self.logger.debug("driver_path: %s", driver_path)

        self.initialize()

    def create_default_config(self):
        with open(f"{self.base_path}/{self.config_name}", 'w') as cfg:
            with open(f"{self.base_path}/default.cfg", 'r') as default_cfg:
                cfg.write(default_cfg.read())

    def initialize(self):
        self.browser = None
        options = uc.ChromeOptions()
        if self.config.get('OPTIONS', 'headless') == 'YES':
            options.add_argument("--headless")
            if self.logger is not None:
                self.logger.debug("--headless mode enabled")

        if self.config.get('OPTIONS', 'incognito') == 'YES':
            options.add_argument("--incognito")
            if self.logger is not None:
                self.logger.debug("--incognito mode enabled")

        if self.config.get('OPTIONS', 'no-sandbox') == 'YES':
            options.add_argument("--no-sandbox")
            if self.logger is not None:
                self.logger.debug("--no-sandbox mode enabled")

        if self.config.get('OPTIONS', 'random_ua') == 'YES':
            ua = UserAgent()
            options.add_argument(f'user-agent={ua.random}')
            if self.logger is not None:
                self.logger.debug("user-agent is randomized")

        # if self.config.get('OPTIONS', 'use_proxy') == 'YES':
        #     ua = UserAgent()
        #     options.add_argument(f'user-agent={ua.random}')
        #     if self.logger is not None:
        #         self.logger.debug("user-agent is randomized")

        if self.config.get('OPTIONS', 'disable-setuid-sandbox') == 'YES':
            options.add_argument(f'--disable-setuid-sandbox')
            if self.logger is not None:
                self.logger.debug("--disable-setuid-sandbox mode enabled")

        if self.config.get('OPTIONS', 'ignore-certificate-errors') == 'YES':
            options.add_argument(f'--ignore-certificate-errors')
            if self.logger is not None:
                self.logger.debug("--ignore-certificate-errors mode enabled")

        browser_executable_path = self.config.get('OPTIONS', 'browser_executable_path')

        scale_factor = 1
        if self.config.get('OPTIONS', 'force-device') == 'YES':
            scale_factor = float(self.config.get('OPTIONS', 'force-device-scale-factor'))
            options.add_argument(f"--force-device-scale-factor={scale_factor}")

        # Create new Instance of Browser
        self.browser = uc.Chrome(browser_executable_path=browser_executable_path, options=options)

        width = int(round(1200 / scale_factor))
        height = int(round(720 / scale_factor))
        self.browser.set_window_size(width, height)

        print("Browser has been initialized!")
        if self.logger is not None:
            self.logger.info("Browser has been initialized!")

    def reinitialize(self):
        print("Reinitializing Browser Instance!")
        if self.logger is not None:
            self.logger.info("Reinitializing Browser Instance!")

        try:
            self.quit_browser()
        except Exception as _ex:
            print(f"[ERROR] Closing | Exception: {_ex}")

        time.sleep(2)
        self.initialize()

        if self.logger is not None:
            self.logger.info("Browser has been reinitialized")

    def quit_browser(self):
        print("Quitting Browser Instance!")
        if self.logger is not None:
            self.logger.info("Quitting Browser Instance! - Finished")

        self.browser.quit()

    def exit(self, x):
        self.quit_browser()
        sys.exit(x)

    def login(self):
        # open login url in browser
        self.browser.get(self.config.get('LOGIN', 'url'))

        username = self.browser.find_element(By.ID, 'username')
        username.send_keys(self.config.get('LOGIN', 'username'))

        password = self.browser.find_element(By.ID, 'password')
        password.send_keys(self.config.get('LOGIN', 'password'))

        log_in_button = self.browser.find_element(By.XPATH, '//*[@type="submit"]')
        log_in_button.click()

        # wait time
        time.sleep(self.config.getint('LOGIN', 'wait_time'))

        # validate success url
        if self.logger is not None:
            self.logger.debug("current_url: %s", self.browser.current_url)
            self.logger.debug("success_url: %s", self.config.get('LOGIN', 'success'))

        if self.browser.current_url == self.config.get('LOGIN', 'success'):
            print("Login Successful!")
            if self.logger is not None:
                self.logger.info("Login Successful!")
        else:
            print("Login Failed!")
            print("Current URL:", self.browser.current_url)
            if self.logger is not None:
                self.logger.info("Login Failed!")
                self.logger.info(f"Current URL: {self.browser.current_url}")
            # exit(1)



if __name__ == '__main__':
    sh = SeleniumHandler('main.cfg')
