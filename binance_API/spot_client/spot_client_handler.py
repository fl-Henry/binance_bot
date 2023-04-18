import time
import pandas as pd

from decimal import Decimal, ROUND_HALF_UP
from binance.spot import Spot
from datetime import datetime, timedelta

try:
    from .. import Kiss
except ImportError:
    import binance_API.Kiss as Kiss


class SpotClient(Spot):
    # TODO: DB cancel orders

    def __init__(self, test_key=False, force_url=False, low_permissions=False, first_symbol='BTC', second_symbol='USDT'):
        """
        Spot client init
        :param test_key: bool       | False
        :param force_url: bool      | False
        :param first_symbol: str    | 'BTC'
        :param second_symbol: str   | 'USDT'
        :return: Spot               | client
        """
        self.minNotional = None
        self.minPrice = None
        self.maxPrice = None
        self.tickSize = None
        self.minQty = None
        self.maxQty = None
        self.stepSize = None
        self.filters = None
        self.current_state_data = None
        self.first_symbol = first_symbol
        self.second_symbol = second_symbol
        self.symbol = f"{self.first_symbol}{self.second_symbol}"
        self.test_key = test_key
        self.last_kline = None

        api_key, api_secret, base_url, stream_url = Kiss.get_api_credentials(test_key, low_permissions)

        if test_key:
            print("Spot URL:", base_url)
            super().__init__(
                api_key=api_key,
                api_secret=api_secret,
                base_url=base_url
            )
        elif force_url:
            print("Spot URL:", base_url)
            super().__init__(
                api_key=api_key,
                api_secret=api_secret,
                base_url=base_url
            )
        else:
            print("Spot URL:", 'Default URL')
            super().__init__(
                api_key=api_key,
                api_secret=api_secret
            )

        self.listen_key = self.new_listen_key().get('listenKey')

    def get_kline(self, symbol=None, interval='1d', limit=1, start_time=None, end_time=None, if_sum=False,
                  output_key=False):
        """"""
        """
            [                                                          [
              [                                                          [
                1499040000000,      // Kline open time                     1681603200000,
                "0.01634790",       // Open price                          "30295.08000000",
                "0.80000000",       // High price                          "30319.04000000",
                "0.01575800",       // Low price                           "30064.73000000",
                "0.01577100",       // Close price                         "30249.35000000",
                "148976.11427815",  // Volume                              "353.08085300",
                1499644799999,      // Kline Close time                    1681689599999,
                "2434.19055334",    // Quote asset volume                  "10681639.59001725",
                308,                // Number of trades                    10768,
                "1756.87402397",    // Taker buy base asset volume         "201.13368700",
                "28.46694368",      // Taker buy quote asset volume        "6084200.47457115",
                "0"                 // Unused field, ignore.               "0"
              ]                                                          ]
            ]                                                          ]
            
            
        """
        if symbol is None:
            symbol = self.symbol
        result = None

        # Getting klines
        if start_time is not None:
            response = self.klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                startTime=start_time
            )
        elif end_time is not None:
            response = self.klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                endTime=end_time
            )
        else:
            response = self.klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )

        # if limit > 1:
        if True:
            response_list = []
            response_data = {
                "symbol": symbol,
                "start_time": response[0][0],
                "start_time_utc": str(datetime.utcfromtimestamp(int(int(response[0][0])) // 1000)),
                "close_time": response[-1][6],
                "close_time_utc": str(datetime.utcfromtimestamp(int(int(response[-1][6])) // 1000)),
                "interval": interval,
                "open_price": response[0][1],
                "close_price": response[-1][4],
                "high_price": response[0][2],
                "low_price": response[0][3],
                "number_of_trades": '0',
                "all_origQty": '0',
                "all_cost": '0',
                "buy_origQty": '0',
                "buy_cost": '0',
                "sell_origQty": '0',
                "sell_cost": '0',
            }
            for response_item in response:
                item = {
                    "symbol": symbol,
                    "start_time": response_item[0],
                    "start_time_utc": str(datetime.utcfromtimestamp(int(int(response_item[0])) // 1000)),
                    "close_time": response_item[6],
                    "close_time_utc": str(datetime.utcfromtimestamp(int(int(response_item[6])) // 1000)),
                    "interval": interval,
                    "open_price": response_item[1],
                    "close_price": response_item[4],
                    "high_price": response_item[2],
                    "low_price": response_item[3],
                    "number_of_trades": response_item[8],
                    "all_origQty": response_item[5],
                    "all_cost": response_item[7],
                    "buy_origQty": response_item[9],
                    "buy_cost": response_item[10],
                    "sell_origQty": (Decimal(str(response_item[5])) - Decimal(str(response_item[9]))).quantize(
                        Decimal('0.00000000'),
                        rounding=ROUND_HALF_UP
                    ),
                    "sell_cost": (Decimal(str(response_item[7])) - Decimal(str(response_item[10]))).quantize(
                        Decimal('0.00000000'),
                        rounding=ROUND_HALF_UP
                    ),
                }
                response_list.append(item)

                if if_sum:
                    if Decimal(item['high_price']) > Decimal(response_data['high_price']):
                        response_data.update({"high_price": item['high_price']})

                    if Decimal(item['low_price']) < Decimal(response_data['low_price']):
                        response_data.update({"low_price": item['low_price']})

                    response_data.update(
                        {
                            "number_of_trades": int(response_data['number_of_trades']) + int(item['number_of_trades'])
                        }
                    )

                    response_data.update(
                        {
                            "all_origQty": (Decimal(str(response_data['all_origQty'])) +
                                            Decimal(str(item['all_origQty']))).quantize(
                                Decimal('0.00000000'),
                                rounding=ROUND_HALF_UP
                            ),
                        }
                    )

                    response_data.update(
                        {
                            "all_cost": (Decimal(str(response_data['all_cost'])) +
                                         Decimal(str(item['all_cost']))).quantize(
                                Decimal('0.00000000'),
                                rounding=ROUND_HALF_UP
                            ),
                        }
                    )

                    response_data.update(
                        {
                            "buy_origQty": (Decimal(str(response_data['buy_origQty'])) +
                                            Decimal(str(item['buy_origQty']))).quantize(
                                Decimal('0.00000000'),
                                rounding=ROUND_HALF_UP
                            ),
                        }
                    )

                    response_data.update(
                        {
                            "buy_cost": (Decimal(str(response_data['buy_cost'])) +
                                         Decimal(str(item['buy_cost']))).quantize(
                                Decimal('0.00000000'),
                                rounding=ROUND_HALF_UP
                            ),
                        }
                    )

                    response_data.update(
                        {
                            "sell_origQty": (Decimal(str(response_data['sell_origQty'])) +
                                             Decimal(str(item['sell_origQty']))).quantize(
                                Decimal('0.00000000'),
                                rounding=ROUND_HALF_UP
                            ),
                        }
                    )

                    response_data.update(
                        {
                            "sell_cost": (Decimal(str(response_data['sell_cost'])) +
                                          Decimal(str(item['sell_cost']))).quantize(
                                Decimal('0.00000000'),
                                rounding=ROUND_HALF_UP
                            ),
                        }
                    )

            if if_sum:
                result = {'sum': response_data, 'klines': response_list}
            else:
                result = {'sum': None, 'klines': response_list}

        # else:
        #     response_data = {
        #         "symbol": symbol,
        #         "start_time": response[0][0],
        #         "start_time_utc": str(datetime.utcfromtimestamp(int(int(response[0][0])) // 1000)),
        #         "close_time": response[0][6],
        #         "close_time_utc": str(datetime.utcfromtimestamp(int(int(response[0][6])) // 1000)),
        #         "interval": interval,
        #         "open_price": response[0][1],
        #         "close_price": response[0][4],
        #         "high_price": response[0][2],
        #         "low_price": response[0][3],
        #         "number_of_trades": response[0][8],
        #         "all_origQty": response[0][5],
        #         "all_cost": response[0][7],
        #         "buy_origQty": response[0][9],
        #         "buy_cost": response[0][10],
        #         "sell_origQty": (Decimal(str(response[0][5])) - Decimal(str(response[0][9]))).quantize(
        #             Decimal('0.00000000'),
        #             rounding=ROUND_HALF_UP
        #         ),
        #         "sell_cost": (Decimal(str(response[0][7])) - Decimal(str(response[0][10]))).quantize(
        #             Decimal('0.00000000'),
        #             rounding=ROUND_HALF_UP
        #         ),
        #     }
        #     result = response_data

        if output_key:
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
                output += f"\nUP" \
                          f"\n-- {response_data['high_price']} --:: {response_data['close_price']} ::" \
                          f":: {response_data['open_price']} ::-- {response_data['low_price']} --"
            else:
                output += f"\nDOWN" \
                          f"\n-- {response_data['high_price']} --:: {response_data['open_price']} ::" \
                          f":: {response_data['close_price']} ::-- {response_data['low_price']} --"

            resp_type_pr = f'---- Kline ------------- SUM ----------------- ' \
                           f'{str(datetime.utcnow()):<20}' \
                           f' ----'

            print(f'\n{resp_type_pr}')
            print(output)

        self.last_kline = result
        return result

    def get_exchange_info(self, symbol=None):
        """
        """
        if symbol is None:
            symbol = self.symbol

        symbol_exchange_info = self.exchange_info(symbol=symbol)

        try:
            if self.test_key:
                symbol_exchange_info['symbols'][0]['filters'][2]["filterType"] = 'MIN_NOTIONAL'
                symbol_exchange_info['symbols'][0]['filters'][2]["minNotional"] = '10.00000000'
                symbol_exchange_info['symbols'][0]['filters'][2]["applyToMarket"] = '1'
                symbol_exchange_info['symbols'][0]['filters'][2]["avgPriceMins"] = '5'

            self.filters = {
                "serverTime": symbol_exchange_info['serverTime'],
                "symbol": symbol_exchange_info['symbols'][0]['symbol'],
                'PRICE_FILTER_filterType': symbol_exchange_info['symbols'][0]['filters'][0]["filterType"],
                'PRICE_FILTER_minPrice': symbol_exchange_info['symbols'][0]['filters'][0]["minPrice"],
                'PRICE_FILTER_maxPrice': symbol_exchange_info['symbols'][0]['filters'][0]["maxPrice"],
                'PRICE_FILTER_tickSize': symbol_exchange_info['symbols'][0]['filters'][0]["tickSize"],
                'LOT_SIZE_filterType': symbol_exchange_info['symbols'][0]['filters'][1]["filterType"],
                'LOT_SIZE_minQty': symbol_exchange_info['symbols'][0]['filters'][1]["minQty"],
                'LOT_SIZE_maxQty': symbol_exchange_info['symbols'][0]['filters'][1]["maxQty"],
                'LOT_SIZE_stepSize': symbol_exchange_info['symbols'][0]['filters'][1]["stepSize"],
                'MIN_NOTIONAL_filterType': symbol_exchange_info['symbols'][0]['filters'][2]["filterType"],
                'MIN_NOTIONAL_minNotional': symbol_exchange_info['symbols'][0]['filters'][2]["minNotional"],
                'MIN_NOTIONAL_applyToMarket': symbol_exchange_info['symbols'][0]['filters'][2]["applyToMarket"],
                'MIN_NOTIONAL_avgPriceMins': symbol_exchange_info['symbols'][0]['filters'][2]["avgPriceMins"],
            }
        except Exception as _ex:
            print(_ex)
            print(f"symbol_exchange_info: {symbol_exchange_info}")
            raise _ex

        self.minNotional = Decimal(str(float(self.filters['MIN_NOTIONAL_minNotional'])))
        self.minPrice = Decimal(str(float(self.filters['PRICE_FILTER_minPrice'])))
        self.maxPrice = Decimal(str(float(self.filters['PRICE_FILTER_maxPrice'])))
        self.tickSize = Decimal(str(float(self.filters['PRICE_FILTER_tickSize'])))
        self.minQty = Decimal(str(float(self.filters['LOT_SIZE_minQty'])))
        self.maxQty = Decimal(str(float(self.filters['LOT_SIZE_maxQty'])))
        self.stepSize = Decimal(str(float(self.filters['LOT_SIZE_stepSize'])))

        return self.filters

    def depth_limit(self, limit, side='bids'):
        """
        :param self: Spot
        :param limit: int       | limit
        :param side: str        | "bids", "asks"
        :return: price: float
        """

        depth = self.depth(symbol=self.symbol, limit=limit)
        price = depth.get(side)[-1][0]
        return price

    def get_current_state(self):

        # getting the first bid and the first ask
        current_depth = self.depth(symbol=self.symbol, limit=1)
        symbol_bid_price = current_depth['bids'][-1][0]
        symbol_bid_quantity = current_depth['bids'][-1][1]
        symbol_ask_price = current_depth['asks'][-1][0]
        symbol_ask_quantity = current_depth['asks'][-1][1]

        # getting the account balance
        balance = self.account().get('balances')

        # parsing values of symbols
        second_symbol_free_value, first_symbol_free_value = 0, 0
        second_symbol_locked_value, first_symbol_locked_value = 0, 0
        for item in balance:
            if item['asset'] == self.first_symbol:
                first_symbol_free_value = str(Decimal(item['free']))
                first_symbol_locked_value = str(Decimal(item['locked']))
            if item['asset'] == self.second_symbol:
                second_symbol_free_value = item['free']
                second_symbol_locked_value = item['locked']

        free = str((Decimal(first_symbol_free_value) * Decimal(symbol_bid_price)).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ) + Decimal(second_symbol_free_value))
        locked = str((Decimal(first_symbol_locked_value) * Decimal(symbol_bid_price)).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ) + Decimal(second_symbol_locked_value))

        # saving the result data
        self.current_state_data = {
            'order_book_bid_current_price': symbol_bid_price,
            'order_book_bid_current_quantity': symbol_bid_quantity,
            'order_book_ask_current_price': symbol_ask_price,
            'order_book_ask_current_quantity': symbol_ask_quantity,
            'balance_free': free,
            'balance_locked': locked,
            'balance_sum': str(Decimal(free) + Decimal(locked)),
            'balance_first_symbol': self.first_symbol,
            'balance_first_symbol_free_value': first_symbol_free_value,
            'balance_first_symbol_locked_value': first_symbol_locked_value,
            'balance_second_symbol': self.second_symbol,
            'balance_second_symbol_free_value': second_symbol_free_value,
            'balance_second_symbol_locked_value': second_symbol_locked_value,
            'time': int(time.time()*1000 // 1)
        }

        return self.current_state_data

    def str_current_state(self):
        wallet = pd.DataFrame(
            [
                [
                    self.current_state_data['balance_first_symbol'],
                    self.current_state_data['balance_first_symbol_free_value'],
                    self.current_state_data['balance_first_symbol_locked_value']
                ],
                [
                    self.current_state_data['balance_second_symbol'],
                    self.current_state_data['balance_second_symbol_free_value'],
                    self.current_state_data['balance_second_symbol_locked_value']
                ]
            ],
            columns=['symbol', 'free', 'locked']
        )
        output = f"" \
                 f"\nCurrent 1st bid:   {self.current_state_data['order_book_bid_current_price']} " \
                 f"USDT/{self.first_symbol} | Quantity: {self.current_state_data['order_book_bid_current_quantity']}" \
                 f"\nCurrent 1st ask:   {self.current_state_data['order_book_ask_current_price']} " \
                 f"USDT/{self.first_symbol} | Quantity: {self.current_state_data['order_book_ask_current_quantity']}" \
                 f"\nLocked:            {self.current_state_data['balance_locked']} USDT" \
                 f"\nFree:              {self.current_state_data['balance_free']} USDT" \
                 f"\nSum:               {self.current_state_data['balance_sum']} USDT" \
                 f"\n" \
                 f"\nWallet:" \
                 f"\n{wallet}"
        print(output)

    def get_orders_to_db(self, get_limit=200, orders_to_sort=None):
        """
        :param self: Spot
        :param get_limit: int           | 200
        :param orders_to_sort: dict     | None
        """
        orders = self.get_orders(symbol=self.symbol, limit=get_limit)

        orders_list = []
        for order in orders:
            order_to_append = {
                "symbol": str(order['symbol']),
                "orderId": int(order['orderId']),
                "price": str(order['price']),
                "origQty": str(order['origQty']),
                "cost": str((Decimal(order['price']) * Decimal(order['origQty'])).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                )),
                "side": str(order['side']),
                "status": str(order['status']),
                "type": str(order['type']),
                "timeInForce": str(order['timeInForce']),
                "workingTime": int(order['workingTime']),
            }
            orders_list.append(order_to_append)

        if orders_to_sort is None:
            return orders_list
        else:
            id_list = []
            for order in orders_to_sort:
                id_list.append(int(order['orderId']))

            sorted_orders_list = []
            for order in orders_list:
                if int(order['orderId']) not in id_list:
                    sorted_orders_list.append(order)

            return sorted_orders_list

    def cancel_all_new_orders(self):
        orders = self.get_orders(symbol=self.symbol, limit=200)
        if len(orders) > 0:
            for order in orders:
                try:
                    if order['status'] == 'NEW':
                        self.cancel_order(symbol=self.symbol, orderId=order['orderId'])
                except Exception as _ex:
                    print(_ex)


if __name__ == '__main__':
    spot_client = SpotClient(
        first_symbol='JOE',
        # test_key=True
    )

    _id = 7

    if _id == 1:
        r = spot_client.new_order(
            symbol=spot_client.symbol,
            quantity=0.00108,
            side='BUY',
            type="LIMIT",
            price=spot_client.depth_limit(26),
            timeInForce="GTC"
        )
        print(r)
        buy_order_to_db = {
            "symbol": str(r['symbol']),
            "price": str(r['price']),
            "origQty": str(r['origQty']),
            "cost": str((Decimal(r['origQty']) * Decimal(r['price'])).quantize(
                Decimal('0.000000'), rounding=ROUND_HALF_UP
            )),
            "side": str(r['side']),
            "type": str(r['type']),
            "timeInForce": str(r['timeInForce']),
            "workingTime": str(r['workingTime'])
        }

        orders_df = pd.DataFrame(
            [buy_order_to_db],
            columns=['symbol', 'orderId', 'price', 'origQty', 'cost', 'side', 'status']
        )

        print(f'\n{orders_df}')

    elif _id == 2:
        r = spot_client.cancel_order(
            symbol=spot_client.symbol,
            orderId=20743405370
        )
        print(r)
    elif _id == 3:
        spot_client.cancel_all_new_orders()
    elif _id == 4:
        pd.set_option('display.max_columns', None)
        orders = spot_client.get_orders_to_db()

        columns = ['symbol', 'orderId', 'price', 'origQty', 'cost', 'side', 'status']

        if len(orders) > 0:
            orders_df = pd.DataFrame(
                orders,
                columns=columns
            )
            orders_df = orders_df.sort_values(['price'], ascending=True).reset_index(drop=True)

            print(f'\n---- Orders ------------------------------'
                  f'\n{orders_df}')
    elif _id == 5:
        spot_client.get_current_state()
        spot_client.str_current_state()
    elif _id == 6:
        spot_client.get_exchange_info()

        print('minNotional:', spot_client.minNotional)
        print('minPrice:', spot_client.minPrice)
        print('maxPrice:', spot_client.maxPrice)
        print('tickSize:', spot_client.tickSize)
        print('minQty:', spot_client.minQty)
        print('maxQty:', spot_client.maxQty)
        print('stepSize:', spot_client.stepSize)
    elif _id == 7:

        # now = int(time.time() // 1)
        # delta_sec = timedelta(days=1).total_seconds()
        # start_time = int((now - delta_sec) * 1000)
        # now = int(now * 1000)
        # print(now)
        # print(datetime.utcfromtimestamp(start_time / 1000))
        # print(start_time)
        r = spot_client.get_kline(interval='1h', limit=24, output_key=True)
        # print(r)
