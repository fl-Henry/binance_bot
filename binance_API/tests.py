import os
from datetime import datetime

from django.db.models import F
from shutil import rmtree
from django.test import TestCase
from django.db.utils import IntegrityError
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP

from .models import Order, OrdersPair, CurrentState, Filters


base_path = str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]
test_dir_name = 'for_test'
test_dir_path = f"{base_path}/{test_dir_name}"

"""
# Exchange Information response
{
  "timezone": "UTC",
  "serverTime": 1680438211063,
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 1200
    },
    {
      "rateLimitType": "ORDERS",
      "interval": "SECOND",
      "intervalNum": 10,
      "limit": 50
    },
    {
      "rateLimitType": "ORDERS",
      "interval": "DAY",
      "intervalNum": 1,
      "limit": 160000
    }
  ],
  "exchangeFilters": [],
  "symbols": [
    {
      "symbol": "BTCUSDT",
      "status": "TRADING",
      "baseAsset": "BTC",
      "baseAssetPrecision": 8,
      "quoteAsset": "USDT",
      "quotePrecision": 8,
      "quoteAssetPrecision": 8,
      "baseCommissionPrecision": 8,
      "quoteCommissionPrecision": 8,
      "orderTypes": [
        "LIMIT",
        "LIMIT_MAKER",
        "MARKET",
        "STOP_LOSS_LIMIT",
        "TAKE_PROFIT_LIMIT"
      ],
      "icebergAllowed": true,
      "ocoAllowed": true,
      "quoteOrderQtyMarketAllowed": true,
      "allowTrailingStop": true,
      "cancelReplaceAllowed": true,
      "isSpotTradingAllowed": true,
      "isMarginTradingAllowed": false,
      "filters": [
        {
          "filterType": "PRICE_FILTER",
          "minPrice": "0.01000000",
          "maxPrice": "1000000.00000000",
          "tickSize": "0.01000000"
        },
        {
          "filterType": "LOT_SIZE",
          "minQty": "0.00000100",
          "maxQty": "900.00000000",
          "stepSize": "0.00000100"
        },
        {
          "filterType": "MIN_NOTIONAL",
          "minNotional": "10.00000000",
          "applyToMarket": true,
          "avgPriceMins": 1
        },
        {
          "filterType": "ICEBERG_PARTS",
          "limit": 10
        },
        {
          "filterType": "MARKET_LOT_SIZE",
          "minQty": "0.00000000",
          "maxQty": "100.00000000",
          "stepSize": "0.00000000"
        },
        {
          "filterType": "TRAILING_DELTA",
          "minTrailingAboveDelta": 10,
          "maxTrailingAboveDelta": 2000,
          "minTrailingBelowDelta": 10,
          "maxTrailingBelowDelta": 2000
        },
        {
          "filterType": "PERCENT_PRICE_BY_SIDE",
          "bidMultiplierUp": "5",
          "bidMultiplierDown": "0.2",
          "askMultiplierUp": "5",
          "askMultiplierDown": "0.2",
          "avgPriceMins": 1
        },
        {
          "filterType": "MAX_NUM_ORDERS",
          "maxNumOrders": 200
        },
        {
          "filterType": "MAX_NUM_ALGO_ORDERS",
          "maxNumAlgoOrders": 5
        }
      ],
      "permissions": [
        "SPOT"
      ],
      "defaultSelfTradePreventionMode": "NONE",
      "allowedSelfTradePreventionModes": [
        "NONE",
        "EXPIRE_TAKER",
        "EXPIRE_MAKER",
        "EXPIRE_BOTH"
      ]
    }
  ]
}





# Order Book response
{
  "lastUpdateId": 1027024,
  "bids": [
    [
      "4.00000000",     // PRICE
      "431.00000000"    // QTY
    ]
  ],
  "asks": [
    [
      "4.00000200",
      "12.00000000"
    ]
  ]
}
"""




def check_dir_for_tests():
    if not os.path.exists(test_dir_path):
        os.mkdir(test_dir_path)


def remove_dir_for_tests():
    if os.path.exists(test_dir_path):
        rmtree(test_dir_path)


class ModelsTests(TestCase):

    ORDER = {
        'symbol': 'BTCUSDT',
        'orderId': 123456,
        'price': '1234.1234',
        'origQty': '0.003456',
        'cost': '12.123456',
        'side': 'SELL',
        'status': 'NEW',
        'type': 'MARKET',
        'timeInForce': '12345678',
        'transactTime': '12345678',
        'workingTime': '12345678',
    }

    current_state_data = {
        'order book': {
            'bid': {
                'current price': Decimal('1234.1234'),
                'current quantity': Decimal('5678.1234'),
            },
            'ask': {
                'current price': Decimal('5678.1234'),
                'current quantity': Decimal('1234.1234'),
            }
        },
        'balance': {
            'free': Decimal('1357.1234'),
            'locked': Decimal('246.1234'),
            'sum': Decimal('5319.1234'),
            'first symbol': {
                'symbol': 'BTC',
                'free value': Decimal('1245.1234'),
                'locked value': Decimal('4325.1234')
            },
            'second symbol': {
                'symbol': 'USDT',
                'free value': Decimal('7612.1234'),
                'locked value': Decimal('3481.1234')
            }
        },
        'time': datetime.utcnow()
    }

    def test_adding_order_to_db(self):
        """
        adding Order to db
        """
        print('\ntest_adding_order_to_db')
        order_to_add = Order(
            symbol=self.ORDER['symbol'],
            price=self.ORDER['price'],
            origQty=self.ORDER['origQty'],
            cost=self.ORDER['cost'],
            side=self.ORDER['side'],
            status=self.ORDER['status'],
        )
        order_to_add.save()
        order_from_db = Order.objects.get(pk=1)

        self.assertEqual(self.ORDER['cost'], order_from_db.cost)

    def test_adding_bad_order_to_db(self):
        """
        adding bad Orders to db
        """
        print('\ntest_adding_bad_order_to_db')

        with transaction.atomic():
            with self.assertRaises(Order.DoesNotExist):
                not_existed_order_from_db = Order.objects.get(pk=1)

        order_with_bad_symbol_to_add = Order(
            # symbol=self.ORDER['symbol'],
            price=self.ORDER['price'],
            origQty=self.ORDER['origQty'],
            cost=self.ORDER['cost'],
            side=self.ORDER['side'],
            status=self.ORDER['status'],
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                order_with_bad_symbol_to_add.save()

        order_with_bad_price_to_add = Order(
            symbol=self.ORDER['symbol'],
            # price=self.ORDER['price'],
            origQty=self.ORDER['origQty'],
            cost=self.ORDER['cost'],
            side=self.ORDER['side'],
            status=self.ORDER['status'],
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                order_with_bad_price_to_add.save()

        order_with_bad_quantity_to_add = Order(
            symbol=self.ORDER['symbol'],
            price=self.ORDER['price'],
            # origQty=self.ORDER['origQty'],
            cost=self.ORDER['cost'],
            side=self.ORDER['side'],
            status=self.ORDER['status'],
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                order_with_bad_quantity_to_add.save()

        order_with_bad_cost_to_add = Order(
            symbol=self.ORDER['symbol'],
            price=self.ORDER['price'],
            origQty=self.ORDER['origQty'],
            # cost=self.ORDER['cost'],
            side=self.ORDER['side'],
            status=self.ORDER['status'],
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                order_with_bad_cost_to_add.save()

        order_with_bad_side_force_none_to_add = Order(
            symbol=self.ORDER['symbol'],
            price=self.ORDER['price'],
            origQty=self.ORDER['origQty'],
            cost=self.ORDER['cost'],
            side=None,
            status=self.ORDER['status'],
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                order_with_bad_side_force_none_to_add.save()

    def test_adding_orders_pair_to_db(self):
        """
        adding OrdersPair to db
        """
        print('\ntest_adding_orders_pair_to_db')

        # sell_order = {k: self.ORDER[k] for k in self.ORDER.keys()}
        sell_order = {}
        sell_order.update(self.ORDER)
        sell_order.update({
            'side': 'SELL',
            'price': '1234.5678'
        })

        order_to_add = Order(
            symbol=sell_order['symbol'],
            price=sell_order['price'],
            origQty=sell_order['origQty'],
            cost=sell_order['cost'],
            side=sell_order['side'],
            status=sell_order['status'],
        )
        order_to_add.save()

        # buy_order = {k: self.ORDER[k] for k in self.ORDER.keys()}
        buy_order = {}
        buy_order.update(self.ORDER)
        buy_order.update({
            'side': 'BUY',
            'price': '8765.4321'
        })
        order_to_add = Order(
            symbol=buy_order['symbol'],
            price=buy_order['price'],
            origQty=buy_order['origQty'],
            cost=buy_order['cost'],
            side=buy_order['side'],
            status=buy_order['status'],
        )
        order_to_add.save()
        sell_order_from_db = Order.objects.get(side='SELL')
        buy_order_from_db = Order.objects.get(side='BUY')

        self.assertEqual(sell_order['price'], sell_order_from_db.price)
        self.assertEqual(buy_order['price'], buy_order_from_db.price)

        orders_pair_to_save = OrdersPair(
            buy_order=buy_order_from_db,
            sell_order=sell_order_from_db
        )
        orders_pair_to_save.save()

        orders_pair_from_db = OrdersPair.objects.get(pk=1)

        self.assertEqual(buy_order['price'], orders_pair_from_db.buy_order.price)
        self.assertEqual(sell_order['price'], orders_pair_from_db.sell_order.price)

    def test_adding_current_state(self):
        """
        adding CurentState to db
        """
        print('\ntest_adding_current_state')

        current_state_to_save = CurrentState(
            order_book_bid_current_price=self.current_state_data['order book']['bid']['current price'],
            order_book_bid_current_quantity=self.current_state_data['order book']['bid']['current quantity'],
            order_book_ask_current_price=self.current_state_data['order book']['ask']['current price'],
            order_book_ask_current_quantity=self.current_state_data['order book']['ask']['current quantity'],
            balance_free=self.current_state_data['balance']['free'],
            balance_locked=self.current_state_data['balance']['locked'],
            balance_sum=self.current_state_data['balance']['sum'],
            balance_first_symbol=self.current_state_data['balance']['first symbol']['symbol'],
            balance_first_symbol_free_value=self.current_state_data['balance']['first symbol']['free value'],
            balance_first_symbol_locked_value=self.current_state_data['balance']['first symbol']['locked value'],
            balance_second_symbol=self.current_state_data['balance']['second symbol']['symbol'],
            balance_second_symbol_free_value=self.current_state_data['balance']['second symbol']['free value'],
            balance_second_symbol_locked_value=self.current_state_data['balance']['second symbol']['locked value'],
            time=self.current_state_data['time'],
        )
        current_state_to_save.save()
        current_state_from_db = CurrentState.objects.get(pk=1)

        self.assertEqual(
            str(self.current_state_data['balance']['first symbol']['free value']),
            str(current_state_from_db.balance_first_symbol_free_value)
        )
        self.assertEqual(
            str(self.current_state_data['balance']['second symbol']['free value']),
            str(current_state_from_db.balance_second_symbol_free_value)
        )
        self.assertEqual(
            str(self.current_state_data['order book']['ask']['current price']),
            str(current_state_from_db.order_book_ask_current_price)
        )
        self.assertEqual(
            str(self.current_state_data['order book']['bid']['current quantity']),
            str(current_state_from_db.order_book_bid_current_quantity)
        )

# daphne binance_bot.asgi:application
    def test_adding_filters(self):
        """
         adding Filters to db
         """
        print('\ntest_adding_filters')
        filters = {
            "serverTime": 1680438211063,
            "symbol": 'BTCUSDT',
            "filters": {
                'PRICE_FILTER': {
                  "filterType": "PRICE_FILTER",
                  "minPrice": "0.01000000",
                  "maxPrice": "1000000.00000000",
                  "tickSize": "0.01000000"
                },
                'LOT_SIZE': {
                  "filterType": "LOT_SIZE",
                  "minQty": "0.00000100",
                  "maxQty": "900.00000000",
                  "stepSize": "0.00000100"
                },
                'MIN_NOTIONAL': {
                  "filterType": "MIN_NOTIONAL",
                  "minNotional": "10.00000000",
                  "applyToMarket": True,
                  "avgPriceMins": 1
                },
                'ICEBERG_PARTS': {
                  "filterType": "ICEBERG_PARTS",
                  "limit": 10
                },
                'MARKET_LOT_SIZE': {
                  "filterType": "MARKET_LOT_SIZE",
                  "minQty": "0.00000000",
                  "maxQty": "100.00000000",
                  "stepSize": "0.00000000"
                },
                'TRAILING_DELTA': {
                  "filterType": "TRAILING_DELTA",
                  "minTrailingAboveDelta": 10,
                  "maxTrailingAboveDelta": 2000,
                  "minTrailingBelowDelta": 10,
                  "maxTrailingBelowDelta": 2000
                },
                'PERCENT_PRICE_BY_SIDE': {
                  "filterType": "PERCENT_PRICE_BY_SIDE",
                  "bidMultiplierUp": "5",
                  "bidMultiplierDown": "0.2",
                  "askMultiplierUp": "5",
                  "askMultiplierDown": "0.2",
                  "avgPriceMins": 1
                },
                'MAX_NUM_ORDERS': {
                  "filterType": "MAX_NUM_ORDERS",
                  "maxNumOrders": 200
                },
                'MAX_NUM_ALGO_ORDERS': {
                  "filterType": "MAX_NUM_ALGO_ORDERS",
                  "maxNumAlgoOrders": 5
                }
            }
        }

        filters_to_save = Filters(
            symbol=filters['symbol'],
            serverTime=datetime.utcfromtimestamp(float(filters['serverTime'])/1000),
            filters=filters['filters']
        )
        filters_to_save.save()

        filters_from_db = Filters.objects.get(pk=1)

        self.assertEqual(
            str(filters['symbol']),
            str(filters_from_db.symbol)
        )
        self.assertEqual(
            datetime.utcfromtimestamp(float(filters['serverTime'])/1000),
            filters_from_db.serverTime
        )
        self.assertEqual(
            str(filters['filters']),
            str(filters_from_db.filters)
        )






