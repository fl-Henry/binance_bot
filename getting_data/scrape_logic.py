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


def script_process(sh: SeleniumHandler, lh: LogHandler):
    sb = sh.browser
    logs = lh.logger

    # open url https://www.binance.com/en/markets/spot
    for counter in range(3):
        url = 'https://www.binance.com/en/markets/spot'
        try:
            logs.info(f"Loading URL:{url}")
            print(f"Loading URL:{url}")
            sb.get(url)
            while sb.execute_script("return document.readyState;") != "complete":
                sleep(0.5)
                print('.', end='')

            logs.debug(f"URL is loaded:{url}")
            break
        except WebDriverException as _ex:
            sleep(2)
            print(f"Try: {counter} | Exception: {repr(_ex)}")
            sh.reinitialize()
            sb = sh.browser

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
    # # get Manufacturer list
    # # //div[contains(@class, "cursor-pointer")]/parent::div[contains(@class, "custom-scroll-bar")]
    # logs.info(f"Getting Manufacturer list")
    # print(f"Getting Manufacturer list")
    # manufacturers_list = []
    # manufacturers_list_upper = []
    # for counter in range(3):
    #     try:
    #         xpath = '//div[contains(@class, "cursor-pointer")]/parent::div[contains(@class, "custom-scroll-bar")]'
    #         WebDriverWait(sb, poll_frequency=1, timeout=10).until(
    #             EC.presence_of_element_located((By.XPATH, xpath))
    #         )
    #         manufacturer_divs = sb.find_element(By.XPATH, xpath)
    #
    #         for manufacturer in str(manufacturer_divs.text).split('\n'):
    #             manufacturers_list.append(manufacturer.strip())
    #             manufacturers_list_upper.append(manufacturer.strip().upper())
    #         sleep(1)
    #         break
    #
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
