
from datetime import datetime
from binance.websocket.spot.websocket_client import SpotWebsocketClient
from decimal import Decimal, ROUND_HALF_UP

from .. import Kiss


class WebsocketClient(SpotWebsocketClient):

    def __init__(self, test_key=False, force_url=False, first_symbol='BTC', second_symbol='USDT', listen_key=None):

        self.first_symbol = first_symbol
        self.second_symbol = second_symbol
        self.symbol = f"{self.first_symbol}{self.second_symbol}"

        if test_key:
            print("Websocket URL:", Kiss.STREAM_URL_TEST)
            super().__init__(stream_url=Kiss.STREAM_URL_TEST)
            self.start()
        else:
            if force_url:
                print("Websocket URL:", Kiss.STREAM_URL_REAL)
                super().__init__(stream_url=Kiss.STREAM_URL_REAL)
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

    def _user_data(self, response):
        """
            :param response: Payload       'executionReport', 'balanceUpdate', 'outboundAccountPosition'
        """

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
                'transactTime': int(response.get('T')),
                'workingTime': int(response.get('W')),
            }
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
                    first_symbol_free_value = Decimal(item['free'])
                    first_symbol_locked_value = Decimal(item['locked'])
                if item['a'] == self.second_symbol:
                    second_symbol_free_value = Decimal(item['free'])
                    second_symbol_locked_value = Decimal(item['locked'])

            current_state = {
                'balance_first_symbol': self.first_symbol,
                'balance_first_symbol_free_value': first_symbol_free_value,
                'balance_first_symbol_locked_value': first_symbol_locked_value,
                'balance_second_symbol': self.second_symbol,
                'balance_second_symbol_free_value': second_symbol_free_value,
                'balance_second_symbol_locked_value': second_symbol_locked_value,

                'time': int(response.get('E'))
            }
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
