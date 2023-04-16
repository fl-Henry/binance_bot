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
        self.kline_output_key = True

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

    def _kline(self, response):
        """"""
        """
            {                                                    {
              "e": "kline",     // Event type                      "e": "kline",                                
              "E": 123456789,   // Event time                      "E": 1681596056639,                                
              "s": "BNBBTC",    // Symbol                          "s": "BTCUSDT",                            
              "k": {                                               "k": {        
                "t": 123400000, // Kline start time                  "t": 1681596000000,                                    
                "T": 123460000, // Kline close time                  "T": 1681596899999,                                    
                "s": "BNBBTC",  // Symbol                            "s": "BTCUSDT",                            
                "i": "1m",      // Interval                          "i": "15m",                            
                "f": 100,       // First trade ID                    "f": 3082623730,                                    
                "L": 200,       // Last trade ID                     "L": 3082624211,                                    
                "o": "0.0010",  // Open price                        "o": "30263.77000000",                                
                "c": "0.0020",  // Close price                       "c": "30258.03000000",                                
                "h": "0.0025",  // High price                        "h": "30263.77000000",                                
                "l": "0.0015",  // Low price                         "l": "30258.03000000",                                
                "v": "1000",    // Base asset volume                 "v": "10.19177000",                                        
                "n": 100,       // Number of trades                  "n": 482,                                    
                "x": false,     // Is this kline closed?             "x": false,                                            
                "q": "1.0000",  // Quote asset volume                "q": "308416.96462810",                                        
                "V": "500",     // Taker buy base asset volume       "V": "4.56349000",                                                
                "Q": "0.500",   // Taker buy quote asset volume      "Q": "138095.12143420",                                                
                "B": "123456"   // Ignore                            "B": "0"                            
              }                                                    }
            }                                                    }
        """

        if response.get('e') == 'kline':

            response_data = {
                "symbol": response["s"],
                "time": response["E"],
                "time_utc": str(datetime.datetime.utcfromtimestamp(int(int(response["E"])) // 1000)),
                "start_time": response["k"]["t"],
                "start_time_utc": str(datetime.datetime.utcfromtimestamp(int(int(response["k"]["t"])) // 1000)),
                "close_time": response["k"]["T"],
                "close_time_utc": str(datetime.datetime.utcfromtimestamp(int(int(response["k"]["T"])) // 1000)),
                "interval": response["k"]["i"],
                "first_orderId": response["k"]["f"],
                "last_orderId": response["k"]["L"],
                "open_price": response["k"]["o"],
                "close_price": response["k"]["c"],
                "high_price": response["k"]["h"],
                "low_price": response["k"]["l"],
                "number_of_trades": response["k"]["n"],
                "if_closed": response["k"]["x"],
                "all_origQty": response["k"]["v"],
                "all_cost": response["k"]["q"],
                "buy_origQty": response["k"]["V"],
                "buy_cost": response["k"]["Q"],
                "sell_origQty": (Decimal(str(response["k"]["v"])) - Decimal(str(response["k"]["V"]))).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ),
                "sell_cost": (Decimal(str(response["k"]["q"])) - Decimal(str(response["k"]["Q"]))).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ),
            }
            self.kline_data = response_data

            if self.kline_output_key:
                output = f"[{response_data['symbol']}] " \
                         f"Start: {response_data['start_time_utc']:>20} | Close: {response_data['close_time_utc']:>20}" \
                         f"\nALL : " \
                         f"Cost: {response_data['all_cost']:>20} | " \
                         f"Qty: {response_data['all_origQty']:>20}" \
                         f"\nBUY : " \
                         f"Cost: {response_data['buy_cost']:>20} | " \
                         f"Qty: {response_data['buy_origQty']:>20}" \
                         f"\nSELL: " \
                         f"Cost: {response_data['sell_cost']:>20} | " \
                         f"Qty: {response_data['sell_origQty']:>20}"

                if response_data['close_price'] >= response_data["open_price"]:
                    output += f"\n-- {response_data['high_price']} --:: {response_data['close_price']} ::" \
                              f":: {response_data['open_price']} ::-- {response_data['low_price']} --"
                else:
                    output += f"\n-- {response_data['high_price']} --:: {response_data['open_price']} ::" \
                              f":: {response_data['close_price']} ::-- {response_data['low_price']} --"

                resp_type_pr = f'---- Kline ----------------------------------------- ' \
                               f'{response_data["time_utc"]:<20}' \
                               f' ----'

                print(f'\n{Tags.LightBlue}{resp_type_pr}{Tags.ResetAll}')
                print(output)

        else:
            print(repr(response))

    def _execution_reports(self, response):
        """"""
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

    @staticmethod
    def _trades(response):
        """"""
        """
            {                                                              {
              "e": "trade",            // Event type                          "e": "trade",
              "E": 1681584398049,      // Event time                          "E": 123456789,
              "s": "BTCUSDT",          // Symbol                              "s": "BNBBTC",
              "t": 1896841,            // Trade ID                            "t": 12345,
              "p": "30293.88000000",   // Price                               "p": "0.001",
              "q": "0.05941500",       // Quantity                            "q": "100",
              "b": 5771390,            // Buyer order ID                      "b": 88,
              "a": 5771198,            // Seller order ID                     "a": 50,
              "T": 1681584398048,      // Trade time                          "T": 123456785,
              "m": false,              // Is the buyer the market maker?      "m": true,
              "M": true                // Ignore                              "M": true
            }                                                              }
        """
        if response.get('e') == 'trade':
            response_data = {
                'symbol': str(response.get('s')),
                'orderId': int(response.get('t')),
                'price': str(response.get('p')),
                'origQty': str(response.get('q')),
                'cost': (Decimal(response.get('p')) * Decimal(response.get('q'))).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ),
                'buyer': str(response.get('b')),
                'seller': str(response.get('a')),
                # 'side': str(response.get('S')),
                # 'status': str(response.get('X')),
                # 'type': str(response.get('o')),
                # 'timeInForce': str(response.get('f')),
                # 'workingTime': int(response.get('W')),
            }

            output = f"[{response_data['symbol']}] Id: {response_data['orderId']} | P: {response_data['price']} | " \
                     f"Q: {response_data['origQty']} | C: {response_data['cost']}" \
                     f"\nBuyer ID: {response_data['buyer']} | Seller ID: {response_data['seller']}"

            resp_type_pr = f'---- Trade ----------------------------------------- ' \
                           f'{str(datetime.datetime.utcfromtimestamp(int(int(response.get("E"))) // 1000)):<20}' \
                           f' ----'
            print(f'\n{Tags.LightBlue}{resp_type_pr}{Tags.ResetAll}')
            print(output)

        else:
            print(repr(response))

    @staticmethod
    def _agg_trades(response):
        """"""
        """
            {
                "e": "aggTrade",  // Event type
                "E": 123456789,   // Event time
                "s": "BNBBTC",    // Symbol
                "a": 12345,       // Aggregate trade ID
                "p": "0.001",     // Price
                "q": "100",       // Quantity
                "f": 100,         // First trade ID
                "l": 105,         // Last trade ID
                "T": 123456785,   // Trade time
                "m": true,        // Is the buyer the market maker?
                "M": true         // Ignore
            }
        """
        if response.get('e') == 'aggTrade':
            response_data = {
                'symbol': str(response.get('s')),
                'orderId': int(response.get('a')),
                'price': str(response.get('p')),
                'origQty': str(response.get('q')),
                'cost': (Decimal(response.get('p')) * Decimal(response.get('q'))).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ),
                'first': str(response.get('f')),
                'last': str(response.get('l')),
                # 'side': str(response.get('S')),
                # 'status': str(response.get('X')),
                # 'type': str(response.get('o')),
                # 'timeInForce': str(response.get('f')),
                # 'workingTime': int(response.get('W')),
            }

            if float(response_data['cost']) > 100000:
                output = f"[{response_data['symbol']}] Id: {response_data['orderId']} | P: {response_data['price']} | " \
                         f"Q: {response_data['origQty']} | C: {response_data['cost']}" \
                         f"\nFirst ID: {response_data['first']} | Last ID: {response_data['last']}"

                resp_type_pr = f'---- Aggregate Trade ------------------------------- ' \
                               f'{str(datetime.datetime.utcfromtimestamp(int(int(response.get("E"))) // 1000)):<20}' \
                               f' ----'
                print(f'\n{Tags.LightBlue}{resp_type_pr}{Tags.ResetAll}')
                print(output)
            else:
                print('.', end='')

        else:
            print(repr(response))

    def stream_book_ticker(self):

        self.book_ticker(
                    id=1,
                    symbol=self.symbol,
                    callback=self._book_ticker
                )

    def stream_kline(self, interval='15m'):

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

    def stream_trades(self):
        self.trade(
            id=5,
            symbol=self.symbol,
            callback=self._trades
        )

    def stream_agg_trades(self):
        self.agg_trade(
            id=6,
            symbol=self.symbol,
            callback=self._agg_trades
        )

