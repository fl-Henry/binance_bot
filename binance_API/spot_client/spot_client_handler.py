import pandas as pd
import time

from binance.spot import Spot
from decimal import Decimal, ROUND_HALF_UP

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

    def get_exchange_info(self):
        """
        """
        symbol_exchange_info = self.exchange_info(symbol=self.symbol)

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
        # first_symbol='DASH'
        first_symbol='BTC'
        # first_symbol='JOE'
    )

    _id = 6

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
