import os

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, MoveTargetOutOfBoundsException, \
    NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from time import sleep


from selenium_handler import SeleniumHandler
from log_handler.log_handler import LogHandler


def print_compact_list(list_data, cols_count=4):
    max_len = max([len(str(x)) for x in list_data])
    counter = 0
    for item in list_data:
        counter += 1
        if counter < cols_count:
            print(f"{str(item):>{max_len + 2}}", end="")
        else:
            print(f"{str(item):>{max_len + 2}}")
            counter = 0
    print()


def script_process(sh: SeleniumHandler, lh: LogHandler):
    sb = sh.browser
    logs = lh.logger
    base_path = str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]
    symbols_path = f"{base_path}/symbols.txt"

    # open url https://www.binance.com/en/markets/trading_data
    for counter in range(3):
        url = 'https://www.binance.com/en/markets/trading_data'
        try:
            logs.info(f"Loading URL:{url}")
            print(f"Loading URL:{url}")
            sb.get(url)
            logs.debug(f"URL is loaded:{url}")
            break

        except WebDriverException as _ex:
            sleep(2)
            print(f"Try: {counter} | Exception: {repr(_ex)}")
            sh.reinitialize()
            sb = sh.browser

    symbols_list = []

    # get Top Gainers list
    # //div[@class="css-o86req" and contains(text(), "Top Gainers" )]
    logs.info(f"Getting Top Gainers list")
    print(f"Getting Top Gainers list")
    for counter in range(3):
        try:
            xpath = '//div[@class="css-o86req" and contains(text(), "Top Gainers" )]/parent::div/parent::div' \
                    '//div[@class="css-lzsise"]'
            WebDriverWait(sb, poll_frequency=1, timeout=10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            top_gainers_divs = sb.find_elements(By.XPATH, xpath)

            for top_gainer in top_gainers_divs:
                top_gainers_css = 'div.css-y361ow'
                symbol = top_gainer.find_element(By.CSS_SELECTOR, top_gainers_css).text.strip()
                print(symbol, end=" ")
                if ("USD" not in symbol) and (symbol not in symbols_list):
                    print("added", end="")
                    symbols_list.append(symbol)
                print()
            break

        except TimeoutException as _ex:
            print(f"Try: {counter} | Exception: {repr(_ex)}")
            sb.refresh()

    # get Top Volume list
    # //div[@class="css-o86req" and contains(text(), "Top Volume" )]
    logs.info(f"Getting Top Volume list")
    print(f"Getting Top Volume list")
    for counter in range(3):
        try:
            xpath = '//div[@class="css-o86req" and contains(text(), "Top Volume" )]/parent::div/parent::div' \
                    '//div[@class="css-lzsise"]'
            WebDriverWait(sb, poll_frequency=1, timeout=10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            top_volume_divs = sb.find_elements(By.XPATH, xpath)

            for top_volume in top_volume_divs:
                top_volume_css = 'div.css-y361ow'
                symbol = top_volume.find_element(By.CSS_SELECTOR, top_volume_css).text.strip()
                print(symbol, end=" ")
                if ("USD" not in symbol) and (symbol not in symbols_list):
                    print("added", end="")
                    symbols_list.append(symbol)
                print()
            break

        except TimeoutException as _ex:
            print(f"Try: {counter} | Exception: {repr(_ex)}")
            sb.refresh()

    # print_compact_list(symbols_list, cols_count=5)

    # Saving to file

    with open(symbols_path, 'w') as f:
        f.write(str(symbols_list))

    # # open url https://www.binance.com/en/markets/spot
    # for counter in range(3):
    #     url = 'https://www.binance.com/en/markets/spot'
    #     try:
    #         logs.info(f"Loading URL:{url}")
    #         print(f"Loading URL:{url}")
    #         sb.get(url)
    #         # while sb.execute_script("return document.readyState;") != "complete":
    #         #     sleep(0.5)
    #         #     print('.', end='')
    #
    #         logs.debug(f"URL is loaded:{url}")
    #         break
    #     except WebDriverException as _ex:
    #         sleep(2)
    #         print(f"Try: {counter} | Exception: {repr(_ex)}")
    #         sh.reinitialize()
    #         sb = sh.browser
    #
    # # get Markets list
    # # //div[@class="css-vlibs4"]
    # logs.info(f"Getting Markets list")
    # print(f"Getting Markets list")
    # markets_list = []
    # for counter in range(3):
    #     try:
    #         xpath = '//div[@class="css-vlibs4"]'
    #         WebDriverWait(sb, poll_frequency=1, timeout=10).until(
    #             EC.presence_of_element_located((By.XPATH, xpath))
    #         )
    #         markets_divs = sb.find_elements(By.XPATH, xpath)
    #
    #         for market in markets_divs:
    #             market_css = 'div.css-17wnpgm'
    #             symbol = market.find_element(By.CSS_SELECTOR, market_css).text.strip()
    #             if not "USD" in symbol:
    #                 markets_list.append(symbol)
    #         break
    #
    #     except TimeoutException as _ex:
    #         print(f"Try: {counter} | Exception: {repr(_ex)}")
    #         sb.refresh()
    # print(markets_list)

    # # close modal container
    # # print(sb.find_element(By.CSS_SELECTOR, ".custom-modal-container"))
    # try:
    #     if sb.find_element(By.CSS_SELECTOR, ".custom-modal-container").is_displayed():
    #         logs.info(f"Closing modal container")
    #         print(f"Closing modal container")
    #         close_button = sb.find_element(By.CSS_SELECTOR, "button.close-popup")
    #         close_button.click()
    #         logs.debug(f"Modal container is closed")
    # except NoSuchElementException:
    #     pass
    #
    # # click on Manufacturer
    # logs.info(f"Click on Manufacturer")
    # print(f"Click on Manufacturer")
    # xpath = '//div[text()="Manufacturer"]/parent::*/input'
    #
    # for counter in range(3):
    #     try:
    #         WebDriverWait(sb, poll_frequency=1, timeout=10).until(EC.presence_of_element_located((By.XPATH, xpath)))
    #         manufacturer_input = sb.find_element(By.XPATH, xpath)
    #         actions = ActionChains(sb)
    #         actions.move_to_element(manufacturer_input).click().perform()
    #         actions.reset_actions()
    #         logs.debug(f"Click on Manufacturer is done")
    #         break
    #     except TimeoutException as _ex:
    #         print(f"Try: {counter} | Exception: {repr(_ex)}")
    #         sb.refresh()
    #

    # # Choosing Manufacturer
    # print(manufacturers_list)
    # print('\nChoose one Manufacturer or press enter to scrape every Manufacturer: ')
    # manufacturer = input()
    # if manufacturer.upper() in manufacturers_list_upper:
    #     manufacturer_index = manufacturers_list_upper.index(manufacturer.upper())
    #     manufacturer = manufacturers_list[manufacturer_index]
    #     print(f"Your choice is: {manufacturer}")
    #
    #     for counter in range(3):
    #         try:
    #             actions.move_to_element(manufacturer_input).click().perform()
    #             actions.reset_actions()
    #             xpath = '//div[contains(@class, "cursor-pointer")]/parent::div[contains(@class, "custom-scroll-bar")]'
    #             drop_choice = sb.find_element(By.XPATH, xpath)
    #             xpath = f'//div[contains(text(), "{manufacturer}")]'
    #             manufacturer_div = sb.find_element(By.XPATH, xpath)
    #
    #             key_to_exit = True
    #             while_counter = 0
    #             while key_to_exit and (while_counter < 1000):
    #                 try:
    #                     actions.move_to_element(manufacturer_div).perform()
    #                     actions.reset_actions()
    #                     key_to_exit = False
    #                 except MoveTargetOutOfBoundsException:
    #                     while_counter += 1
    #                     print(".", end='')
    #                     actions.move_to_element(drop_choice).scroll_by_amount(delta_x=0, delta_y=100)
    #
    #             actions.move_to_element(manufacturer_div).click().perform()
    #             actions.reset_actions()
    #
    #             # click on Model
    #             logs.info(f"Click on Model")
    #             print(f"Click on Model")
    #             xpath = '//div[text()="Model"]/parent::*/input'
    #
    #             WebDriverWait(sb, poll_frequency=1, timeout=10).until(EC.presence_of_element_located((By.XPATH, xpath)))
    #             model_input = sb.find_element(By.XPATH, xpath)
    #             actions.move_to_element(model_input).click().perform()
    #             actions.reset_actions()
    #             logs.debug(f"Click on Model is done")
    #             break
    #         except TimeoutException as _ex:
    #             print(f"Try: {counter} | Exception: {repr(_ex)}")
    #             sb.refresh()
    #             sleep(3)
    #
    #     # get Model list
    #     logs.info(f"Getting Model list")
    #     print(f"Getting Model list")
    #     models_list = []
    #     models_list_upper = []
    #     for counter in range(3):
    #         try:
    #             xpath = '//div[contains(@class, "cursor-pointer")]/parent::div[contains(@class, "custom-scroll-bar")]'
    #             WebDriverWait(sb, poll_frequency=1, timeout=10).until(
    #                 EC.presence_of_element_located((By.XPATH, xpath))
    #             )
    #             model_divs = sb.find_element(By.XPATH, xpath)
    #
    #             for model in str(model_divs.text).split('\n'):
    #                 models_list.append(model.strip())
    #                 models_list_upper.append(model.strip().upper())
    #             sleep(1)
    #             break
    #
    #         except TimeoutException as _ex:
    #             print(f"Try: {counter} | Exception: {repr(_ex)}")
    #             sb.refresh()
    #
    #     # Choosing Model
    #     print(models_list)
    #     print('\nChoose one Model or press enter to scrape every Model: ')
    #     model = input()
    #     if model.upper() in models_list_upper:
    #         for counter in range(3):
    #             model_index = models_list_upper.index(model.upper())
    #             model = models_list[model_index]
    #             print(f"Your choice is: {model}")
    #             try:
    #                 actions.move_to_element(model_input).click().perform()
    #                 actions.reset_actions()
    #                 xpath = '//div[contains(@class, "cursor-pointer")]/parent::div[contains(@class, "custom-scroll-bar")]'
    #                 drop_choice = sb.find_element(By.XPATH, xpath)
    #                 xpath = f'//div[contains(text(), "{model}")]'
    #                 model_div = sb.find_element(By.XPATH, xpath)
    #
    #                 key_to_exit = True
    #                 while_counter = 0
    #                 while key_to_exit and (while_counter < 1000):
    #                     try:
    #                         actions.move_to_element(model_div).perform()
    #                         actions.reset_actions()
    #                         key_to_exit = False
    #                     except MoveTargetOutOfBoundsException:
    #                         while_counter += 1
    #                         print(".", end='')
    #                         actions.move_to_element(drop_choice).scroll_by_amount(delta_x=0, delta_y=100)
    #
    #                 actions.move_to_element(model_div).click().perform()
    #                 actions.reset_actions()
    #
    #                 # click on Year
    #                 logs.info(f"Click on Year")
    #                 print(f"Click on Year")
    #                 xpath = '//div[text()="Year"]/parent::*/input'
    #
    #                 WebDriverWait(sb, poll_frequency=1, timeout=10).until(
    #                     EC.presence_of_element_located((By.XPATH, xpath))
    #                 )
    #                 year_input = sb.find_element(By.XPATH, xpath)
    #                 ActionChains(sb).move_to_element(year_input).click().perform()
    #                 logs.debug(f"Click on Year is done")
    #                 break
    #             except TimeoutException as _ex:
    #                 print(f"Try: {counter} | Exception: {repr(_ex)}")
    #                 sb.refresh()
    #
    #         # get Year list
    #         logs.info(f"Getting Year list")
    #         print(f"Getting Year list")
    #         years_list = []
    #         years_list_upper = []
    #         for counter in range(3):
    #             try:
    #                 xpath = '//div[contains(@class, "cursor-pointer")]/parent::div[contains(@class, "custom-scroll-bar")]'
    #                 WebDriverWait(sb, poll_frequency=1, timeout=10).until(
    #                     EC.presence_of_element_located((By.XPATH, xpath))
    #                 )
    #                 year_divs = sb.find_element(By.XPATH, xpath)
    #
    #                 for year in str(year_divs.text).split('\n'):
    #                     years_list.append(year.strip())
    #                     years_list_upper.append(year.strip().upper())
    #                 sleep(1)
    #                 break
    #
    #             except TimeoutException as _ex:
    #                 print(f"Try: {counter} | Exception: {repr(_ex)}")
    #                 sb.refresh()
    #
    #         # Choosing Year
    #         print(years_list)
    #         print('\nChoose one Year or press enter to scrape every Year: ')
    #         year = input()
    #         if year.upper() in years_list_upper:
    #             for counter in range(3):
    #                 year_index = years_list_upper.index(year.upper())
    #                 year = years_list[year_index]
    #                 print(f"Your choice is: {year}")
    #                 try:
    #                     actions.move_to_element(year_input).click().perform()
    #                     actions.reset_actions()
    #                     xpath = '//div[contains(@class, "cursor-pointer")]/parent::div[contains(@class, "custom-scroll-bar")]'
    #                     drop_choice = sb.find_element(By.XPATH, xpath)
    #                     xpath = f'//div[contains(text(), "{year}")]'
    #                     year_div = sb.find_element(By.XPATH, xpath)
    #
    #                     key_to_exit = True
    #                     while_counter = 0
    #                     while key_to_exit and (while_counter < 1000):
    #                         try:
    #                             actions.move_to_element(year_div).perform()
    #                             actions.reset_actions()
    #                             key_to_exit = False
    #                         except MoveTargetOutOfBoundsException:
    #                             while_counter += 1
    #                             print(".", end='')
    #                             actions.move_to_element(drop_choice).scroll_by_amount(delta_x=0, delta_y=100)
    #
    #                     actions.move_to_element(year_div).click().perform()
    #                     actions.reset_actions()
    #                     break
    #                 except TimeoutException as _ex:
    #                     print(f"Try: {counter} | Exception: {repr(_ex)}")
    #                     sb.refresh()
