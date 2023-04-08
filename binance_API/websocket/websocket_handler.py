import datetime
import time
from random import randint

import pandas as pd

from binance.websocket.spot.websocket_client import SpotWebsocketClient
from decimal import Decimal, ROUND_HALF_UP

from sqlite3_handler.db_handler import SQLiteHandler
from .. import Kiss
from ..print_tags import Tags


class WebsocketClient(SpotWebsocketClient):

    def __init__(self, test_key=False, force_url=False, low_permissions=False, first_symbol='BTC',
                 second_symbol='USDT', listen_key=None):

        self.db_name = None
        self.db_dir = None
        self.sqlh = None
        self.first_symbol = first_symbol
        self.second_symbol = second_symbol
        self.symbol = f"{self.first_symbol}{self.second_symbol}"

        api_key, api_secret, base_url, stream_url = Kiss.get_api_credentials(test_key, low_permissions)

        if test_key:
            print("Websocket URL:", stream_url)
            super().__init__(stream_url=stream_url)
            self.start()
        elif force_url:
            print("Websocket URL:", stream_url)
            super().__init__(stream_url=stream_url)
            self.start()
        else:
            print("Websocket URL:", 'Base URL')
            super().__init__()
            self.start()

        self.listen_key = listen_key

    @staticmethod
    def _book_ticker(response):

        print("\033[31m\n\n\n Isn't realized \n\n\n\033[0m")
        print(response)
        # if 'k' in r:
        #     print(r.get('k').get('c'), r.get('k').get('V'))
        # else:
        #     print("book_ticker stream")

    @staticmethod
    def _kline(response):
        """
           kline stream
           :param response:
           :return:
       """
        # TODO: rewrite output to db

        if 'k' in response:
            response_open = response.get('k').get('o')
            response_close = response.get('k').get('c')
            response_high = response.get('k').get('h')
            response_low = response.get('k').get('l')
            response_symbol = response.get('k').get('s')
            response_dif = Decimal(response_close) - Decimal(response_open)
            # print(f'                                        kline stream                                          ')
            # print(f'[SYMBOL]  --------- HIGH -------:::::::: UP ::::::::::::::: DOWN :::::::-------- LOW ---------')
            # print(f'[BTCUSDT] ---- 26856.97000000 --:: 26856.97000000 :::: 26826.03000000 ::-- 26817.85000000 ----')

            if response_close >= response_open:
                print(f"[{response_symbol}] ---- {response_high} --:: {response_close} ::"
                      f":: {response_open} ::-- {response_low} ----  || {response_close} || {response_dif}")
            else:
                print(f"[{response_symbol}] ---- {response_high} --:: {response_open} ::"
                      f":: {response_close} ::-- {response_low} ----  || {response_close} || {response_dif}")

        else:
            print(f"                                        kline stream "
                  f"                                         ")
            print(f'[SYMBOL]  --------- HIGH -------:::::::: UP '
                  f'::::::::::::::: DOWN :::::::-------- LOW ---------')

    def _execution_reports(self, response):
        self.sqlh = SQLiteHandler(db_name=self.db_name, db_dir=self.db_dir, check_same_thread=False)
        table = 'pending_orders'
        if response.get('e') == 'executionReport':
            if str(response.get('s')) != self.symbol:
                print('\n[WARNING] report_execution_handler > execution report was not handled')
                print(f"[WARNING] {str(response.get('s'))} != {self.symbol}")
            else:
                response_data = {
                    'symbol': str(response.get('s')),
                    'orderId': int(response.get('i')),
                    'price': str(response.get('p')),
                    'origQty': str(response.get('q')),
                    'cost': (Decimal(response.get('p')) * Decimal(response.get('q'))).quantize(
                        Decimal('0.00000000'),
                        rounding=ROUND_HALF_UP
                    ),
                    'side': str(response.get('S')),
                    'status': str(response.get('X')),
                    'type': str(response.get('o')),
                    'timeInForce': str(response.get('f')),
                    'workingTime': int(response.get('W')),
                }

                while_counter = 0
                while while_counter < 6:
                    try:
                        if response_data['status'] == 'NEW':
                            where_condition = f"price = {repr(str(response_data['price']))} AND orderId IS NULL"
                            order_pk = self.sqlh.select_from_table(table, ['pk'], where_condition=where_condition)

                            pk = order_pk.fetchall()[0][0]
                            set_data_dict = {
                                'orderId': int(response.get('i')),
                                'status': str(response.get('X')),
                            }
                            where_condition = f'pk = {pk}'

                            self.sqlh.update(table, set_data_dict, where_condition=where_condition)

                        elif response_data['status'] in ['FILLED', 'CANCELED']:

                            try:
                                where_condition = f"orderId = {repr(str(response_data['orderId']))}"
                                order_pk = self.sqlh.select_from_table(table, ['pk'], where_condition=where_condition)
                                pk = order_pk.fetchall()[0][0]
                            except IndexError as _ex:
                                print("[ERROR] _execution_reports > IndexError >", _ex)
                                print("response_data['status']:", response_data['status'])
                                print("where_condition:", where_condition)
                                print(
                                    'order_pk:',
                                    self.sqlh.select_from_table(table, ['pk'], where_condition=where_condition)
                                )
                            else:
                                set_data_dict = {'status': str(response.get('X'))}
                                where_condition = f'pk = {pk}'
                                self.sqlh.update(table, set_data_dict, where_condition=where_condition)

                        else:
                            print('[WARNING] report_execution_handler > execution report was not handled')
                        while_counter = 20

                    except Exception as _ex:
                        print("[ERROR] _execution_reports > ", _ex)
                        while_counter += 1
                        time.sleep(randint(1, 10))

        self.sqlh.close()

    def _user_data(self, response):
        """
            :param response: Payload       'executionReport', 'balanceUpdate', 'outboundAccountPosition'
        """

        # pd.set_option('display.max_columns', None)

        if response.get('e') == 'executionReport':

            # first event ----------------------/-----------------------/-----------------------/----------------------/
            # first event ----------------------/                executionReport                /----------------------/
            # first event ----------------------/-----------------------/-----------------------/----------------------/

            '''
            {
              "e": "executionReport",        // Event type
              "E": 1499405658658,            // Event time
              "s": "ETHBTC",                 // Symbol
              "c": "mUvoqJxFIILMdfAW5iGSOW", // Client order ID
              "S": "BUY",                    // Side
              "o": "LIMIT",                  // Order type
              "f": "GTC",                    // Time in force
              "q": "1.00000000",             // Order quantity
              "p": "0.10264410",             // Order price
              "P": "0.00000000",             // Stop price
              "d": 4,                        // Trailing Delta; This is only visible if the order was a trailing stop order.
              "F": "0.00000000",             // Iceberg quantity
              "g": -1,                       // OrderListId
              "C": "",                       // Original client order ID; This is the ID of the order being canceled
              "x": "NEW",                    // Current execution type
              "X": "NEW",                    // Current order status
              "r": "NONE",                   // Order reject reason; will be an error code.
              "i": 4293153,                  // Order ID
              "l": "0.00000000",             // Last executed quantity
              "z": "0.00000000",             // Cumulative filled quantity
              "L": "0.00000000",             // Last executed price
              "n": "0",                      // Commission amount
              "N": null,                     // Commission asset
              "T": 1499405658657,            // Transaction time
              "t": -1,                       // Trade ID
              "v": 3,                        // Prevented Match Id; This is only visible if the order expire due to STP trigger.
              "I": 8641984,                  // Ignore
              "w": true,                     // Is the order on the book?
              "m": false,                    // Is this trade the maker side?
              "M": false,                    // Ignore
              "O": 1499405658657,            // Order creation time
              "Z": "0.00000000",             // Cumulative quote asset transacted quantity
              "Y": "0.00000000",             // Last quote asset transacted quantity (i.e. lastPrice * lastQty)
              "Q": "0.00000000",             // Quote Order Quantity
              "D": 1668680518494,            // Trailing Time; This is only visible if the trailing stop order has been activated.
              "j": 1,                        // Strategy ID; This is only visible if the strategyId parameter was provided upon order placement
              "J": 1000000,                  // Strategy Type; This is only visible if the strategyType parameter was provided upon order placement
              "W": 1499405658657,            // Working Time; This is only visible if the order has been placed on the book.
              "V": "NONE",                   // selfTradePreventionMode
              "u":1,                         // TradeGroupId; This is only visible if the account is part of a trade group and the order expired due to STP trigger.
              "U":37,                        // CounterOrderId; This is only visible if the order expired due to STP trigger.
              "A":"3.000000",                // Prevented Quantity; This is only visible if the order expired due to STP trigger.
              "B":"3.000000"                 // Last Prevented Quantity; This is only visible if the order expired due to STP trigger.
            }
            '''

            response_data = {
                'symbol': str(response.get('s')),
                'orderId': int(response.get('i')),
                'price': Decimal(response.get('p')).quantize(
                    Decimal('0.0000'),
                    rounding=ROUND_HALF_UP
                ),
                'origQty': str(response.get('q')),
                'cost': (Decimal(response.get('p')) * Decimal(response.get('q'))).quantize(
                    Decimal('0.0000'),
                    rounding=ROUND_HALF_UP
                ),
                'side': str(response.get('S')),
                'status': str(response.get('X')),
                'type': str(response.get('o')),
                'timeInForce': str(response.get('f')),
                'workingTime': int(response.get('W')),
            }

            output_df = pd.DataFrame(
                [response_data],
                columns=['symbol', 'orderId', 'price', 'origQty', 'cost', 'side', 'status']
            )
            resp_type_pr = f'---- Execution Report ------------------------------ ' \
                           f'{str(datetime.datetime.utcfromtimestamp(int(int(response.get("E"))) // 1000)):<20}' \
                           f' ----'
            print(f'\n{Tags.LightBlue}{resp_type_pr}{Tags.ResetAll}')

            if response_data['status'] == 'FILLED':
                stat_pr = f"---- FILLED ----------------------------- {response_data['side']:<4} " \
                          f"-------------------------------"
                print(f'{Tags.BackgroundLightYellow}{Tags.Black}{Tags.Bold}{stat_pr}{Tags.ResetAll}')
            elif response_data['status'] == 'NEW':
                stat_pr = f"---- NEW -------------------------------- {response_data['side']:<4} " \
                          f"-------------------------------"
                print(f"{Tags.BackgroundDarkGray}{Tags.Bold}{stat_pr}{Tags.ResetAll}")
            else:
                stat_pr = f"---- ??? -------------------------------- {response_data['side']:<4} " \
                          f"-------------------------------"
                print(f'{Tags.Red}{Tags.Bold}{Tags.BackgroundCyan}{stat_pr}{Tags.ResetAll}')

            print(output_df)

            # return response_data

        elif response.get('e') == 'balanceUpdate':

            # next event ----------------------/-----------------------/-----------------------/----------------------/
            # next event ----------------------/                 balanceUpdate                 /----------------------/
            # next event ----------------------/-----------------------/-----------------------/----------------------/

            '''
            {
              "e": "balanceUpdate",         //Event Type
              "E": 1573200697110,           //Event Time
              "a": "BTC",                   //Asset
              "d": "100.00000000",          //Balance Delta
              "T": 1573200697068            //Clear Time
            }
            '''

            response_data = {
                'Event Type': response.get('e'),
                'Event Time': response.get('E'),
                'Asset': response.get('a'),
                'Balance Delta': response.get('d'),
                'Clear Time': response.get('T')
            }

            output_df = pd.DataFrame(
                [response_data]
            )
            resp_type_pr = f'---- Balance Update -------------------------------- ' \
                           f'{str(datetime.datetime.utcfromtimestamp(int(int(response.get("E"))) // 1000)):<20}' \
                           f' ----'

            print(f'\n{Tags.LightBlue}{resp_type_pr}{Tags.ResetAll}')
            print(output_df)

            # return response_data

        elif response.get('e') == 'outboundAccountPosition':

            # next event ----------------------/-----------------------/-----------------------/----------------------/
            # next event ----------------------/          outboundAccountPosition              /----------------------/
            # next event ----------------------/-----------------------/-----------------------/----------------------/

            '''
            {
              "e": "outboundAccountPosition", //Event type
              "E": 1564034571105,             //Event Time
              "u": 1564034571073,             //Time of last account update
              "B": [                          //Balances Array
                {
                  "a": "ETH",                 //Asset
                  "f": "10000.000000",        //Free
                  "l": "0.000000"             //Locked
                }
              ]
            }
            '''

            # parsing values of symbols
            second_symbol_free_value, first_symbol_free_value = 0, 0
            second_symbol_locked_value, first_symbol_locked_value = 0, 0
            for item in response['B']:
                if item['a'] == self.first_symbol:
                    first_symbol_free_value = Decimal(item['f'])
                    first_symbol_locked_value = Decimal(item['l'])
                if item['a'] == self.second_symbol:
                    second_symbol_free_value = Decimal(item['f'])
                    second_symbol_locked_value = Decimal(item['l'])

            response_data = [
                {
                    'symbol': self.first_symbol,
                    'free_value': first_symbol_free_value,
                    'locked_value': first_symbol_locked_value,
                },
                {
                    'symbol': self.second_symbol,
                    'free_value': second_symbol_free_value,
                    'locked_value': second_symbol_locked_value,
                }
            ]

            wallet = pd.DataFrame(
                response_data
            )

            output = f"\nWallet:" \
                     f"\n{wallet}"

            resp_type_pr = f'---- Outbound Account Position --------------------- ' \
                           f'{str(datetime.datetime.utcfromtimestamp(int(int(response.get("E"))) // 1000)):<20}' \
                           f' ----'
            print(f'\n{Tags.LightBlue}{resp_type_pr}{Tags.ResetAll}')
            print(output)

            # return current_state
        else:
            print(repr(response))

    def stream_book_ticker(self):

        self.book_ticker(
                    id=1,
                    symbol=self.symbol,
                    callback=self._book_ticker
                )

    def stream_kline(self, interval='1s'):

        self.kline(
                id=2,
                symbol=self.symbol,
                interval=interval,
                callback=self._kline
            )

    def stream_user_data(self):
        if self.listen_key is not None:
            self.user_data(
                self.listen_key,
                id=3,
                callback=self._user_data
            )
        else:
            raise KeyError('listen_key is None')

    def stream_execution_reports(self, db_name, db_dir):
        """
        """
        self.db_name = db_name
        self.db_dir = db_dir

        if self.listen_key is not None:
            self.user_data(
                self.listen_key,
                id=4,
                callback=self._execution_reports
            )
        else:
            raise KeyError('listen_key is None')

