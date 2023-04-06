import os
import time
import unittest
import sqlite3

from shutil import rmtree

from binance_API.websocket.websocket_handler import WebsocketClient
from sqlite3_handler.db_handler import SQLiteHandler
from sqlite3_handler import tables

db_dir = f"{str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]}/for_tests"
db_name = f"test"
db_path = f"{db_dir}/{db_name}.db"

if not os.path.exists(db_dir):
    os.mkdir(db_dir)
    print(f"Created: {db_dir}")


class TestBot(unittest.TestCase):

    data = [
        ['BTCUSDT', 156, '4.1234', '4.4321', '54.432', 'SELL', 'NEW'],
        ['BTCUSDT', 157, '45.1234', '12.4321', '31.5432', 'BUY', 'NEW'],
        ['BTCUSDT', 158, '46.1234', '13.4321', '32.5432', 'SELL', 'FILLED'],
        ['BTCUSDT', 159, '47.1234', '14.4321', '33.5432', 'BUY', 'FILLED'],
        # ['BTCUSDT', 123450, '12348.1234', '43215.4321', '54324.5432', 'SELL'],
        # ['BTCUSDT', 123451, '12349.1234', '43216.4321', '54325.5432', 'BUY'],
    ]

    columns = ['symbol', 'orderId', 'price', 'origQty', 'cost', 'side', 'status']
    current_state_columns = [
        "balance_first_symbol",
        "balance_first_symbol_free_value",
        "balance_first_symbol_locked_value",
        "balance_second_symbol",
        "balance_second_symbol_free_value",
        "balance_second_symbol_locked_value",
        "time"
    ]

    current_state = {
        'balance_first_symbol': 'BTC',
        'balance_first_symbol_free_value': '1234.5678',
        'balance_first_symbol_locked_value': '321.654',
        'balance_second_symbol': 'USDT',
        'balance_second_symbol_free_value': '5678.1234',
        'balance_second_symbol_locked_value': '789.654',

        'time': int(time.time()*1000 // 1)
    }

    current_state_01 = {
        'balance_first_symbol': 'BTC',
        'balance_first_symbol_free_value': '543.123',
        'balance_first_symbol_locked_value': '854.36',
        'balance_second_symbol': 'USDT',
        'balance_second_symbol_free_value': '56.1234',
        'balance_second_symbol_locked_value': '9.654',

        'time': int(time.time()*1000 // 1)
    }

    buy_order_to_db = {
        "symbol": 'BTCUSDT',
        "price": '27913.27000000',
        "origQty": '0.00100000',
        "cost": '27.91327000',
        "side": str('BUY'),
        "workingTime": int(time.time()*1000 // 1),
    }
    sell_order_to_db = {
        "symbol": 'BTCUSDT',
        "price": '28059.64000000',
        "origQty": '0.00178300',
        "cost": '50.03033812',
        "side": str('SELL'),
        "workingTime": int(time.time()*1000 // 1),
    }

    execution_report_sell = {
              "e": "executionReport",        # Event type
              "E": 1499405658658,            # Event time
              "s": "BTCUSDT",                # Symbol
              "c": "mUvoqJxFIILMdfAW5iGSOW", # Client order ID
              "S": "SELL",                   # Side
              "o": "LIMIT",                  # Order type
              "f": "GTC",                    # Time in force
              "q": "0.00178300",             # Order quantity
              "p": "28059.64000000",         # Order price
              "P": "0.00000000",             # Stop price
              "d": 4,                        # Trailing Delta; This is only visible if the order was a trailing stop order.
              "F": "0.00000000",             # Iceberg quantity
              "g": -1,                       # OrderListId
              "C": "",                       # Original client order ID; This is the ID of the order being canceled
              "x": "NEW",                    # Current execution type
              "X": "NEW",                    # Current order status
              "r": "NONE",                   # Order reject reason; will be an error code.
              "i": 4293153,                  # Order ID
              "l": "0.00000000",             # Last executed quantity
              "z": "0.00000000",             # Cumulative filled quantity
              "L": "0.00000000",             # Last executed price
              "n": "0",                      # Commission amount
              "N": None,                     # Commission asset
              "T": 1499405658657,            # Transaction time
              "t": -1,                       # Trade ID
              "v": 3,                        # Prevented Match Id; This is only visible if the order expire due to STP trigger.
              "I": 8641984,                  # Ignore
              "w": True,                     # Is the order on the book?
              "m": False,                    # Is this trade the maker side?
              "M": False,                    # Ignore
              "O": 1499405658657,            # Order creation time
              "Z": "0.00000000",             # Cumulative quote asset transacted quantity
              "Y": "0.00000000",             # Last quote asset transacted quantity (i.e. lastPrice * lastQty)
              "Q": "0.00000000",             # Quote Order Quantity
              "D": 1668680518494,            # Trailing Time; This is only visible if the trailing stop order has been activated.
              "j": 1,                        # Strategy ID; This is only visible if the strategyId parameter was provided upon order placement
              "J": 1000000,                  # Strategy Type; This is only visible if the strategyType parameter was provided upon order placement
              "W": 1499405658657,            # Working Time; This is only visible if the order has been placed on the book.
              "V": "NONE",                   # selfTradePreventionMode
              "u": 1,                        # TradeGroupId; This is only visible if the account is part of a trade group and the order expired due to STP trigger.
              "U": 37,                       # CounterOrderId; This is only visible if the order expired due to STP trigger.
              "A": "3.000000",               # Prevented Quantity; This is only visible if the order expired due to STP trigger.
              "B": "3.000000"                # Last Prevented Quantity; This is only visible if the order expired due to STP trigger.
            }

    # {
    #     'symbol': 'BTCUSDT',
    #     'orderId': 12345678,
    #     'price': '28059.64000000',
    #     'origQty': '0.00178300',
    #     'cost': '50.03033812',
    #     'side': 'SELL',
    #     'status': 'NEW',
    #     'type': 'LIMIT',
    #     'timeInForce': 'GTC',
    #     'workingTime': int(time.time()*1000 // 1),
    # }

    test_key = True
    force_url = False
    first_symbol = "BTC"
    second_symbol = "USDT"

    def test_report_execution_handler(self):
        print('\ntest_report_execution_handler')
        current_db_name = 'test_report_execution_handler'
        sqlh = SQLiteHandler(db_name=current_db_name, db_dir=db_dir)

        web_socket = WebsocketClient(
            test_key=self.test_key,
            force_url=self.force_url,
            first_symbol=self.first_symbol,
            second_symbol=self.second_symbol,
        )

        try:
            sqlh.create_all_tables(tables.create_all_tables)

            table = 'pending_orders'
            data_dict = self.sell_order_to_db

            data_to_save = [self.sell_order_to_db, self.buy_order_to_db]
            if len(data_to_save) > 0:
                for row in data_to_save:
                    sqlh.insert_from_dict(table, row)

            res = sqlh.select_from_table(table, list(data_dict.keys()))
            param_db = res.fetchall()
            parsed_data = sqlh.parse_db_data_to_dict(list(data_dict.keys()), param_db)

            self.assertEqual(
                data_to_save[0]['price'],
                parsed_data[0]['price']
            )

            exec_rep_resp = self.execution_report_sell
            web_socket._execution_reports(exec_rep_resp, sqlh)

            where_condition = f"price = {repr(str(data_dict['price']))}"
            res = sqlh.select_from_table(table, tables.columns__pending_orders, where_condition=where_condition)
            param_db = res.fetchall()
            parsed_data = sqlh.parse_db_data_to_dict(tables.columns__pending_orders, param_db)

            # print(f"\nstr(parsed_data[0]['orderId']): {str(parsed_data[0]['orderId'])}"
            #       f"\nstr(exec_rep_resp['i']): {str(exec_rep_resp['i'])}")

            self.assertEqual(
                str(parsed_data[0]['orderId']),
                str(exec_rep_resp['i'])
            )

        except KeyboardInterrupt:
            ...
        finally:
            web_socket.stop()
            print('web_socket.stop()')
            sqlh.close()
            print('sqlh.close()')
            os.remove(f"{db_dir}/{current_db_name}.db")
