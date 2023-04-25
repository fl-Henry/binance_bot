from time import sleep

from log_handler.log_handler import LogHandler
from selenium_handler import SeleniumHandler
from scrape_logic import trading_data, markets_overview

if __name__ == '__main__':
    lh = LogHandler(name='binance_markets_spot',)
    sh = SeleniumHandler('main.cfg', lh.logger)

    # Scraping mode
    # mode = "Trading Data"
    mode = "Markets Overview"
    if mode == "Trading Data":
        trading_data(sh, lh)
    elif mode == "Markets Overview":
        markets_overview(sh, lh, page_counter_limit=4)

    sleep(10)
    sh.quit_browser()
