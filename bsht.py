import os
import sqlite3
import argparse
import datetime
from random import randint
# from datetime import datetime
from decimal import Decimal, getcontext, ROUND_CEILING, ROUND_UP, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN
import time


def decimal_rounding(decimal_value, value_for_round="0.00000000", int_round=False, rounding=ROUND_HALF_UP):
    if int_round:
        return Decimal(decimal_value) // Decimal(value_for_round) * Decimal(value_for_round)
    else:
        return Decimal(decimal_value).quantize(Decimal(value_for_round), rounding=rounding)

"""
             Pending orders created (profit_percent: 0.6)                                  
Buy:      Price: 12.68700000  | Quantity: 0.80000000    |    Cost: 10.14900000             
Sell:     Price: 12.76300000  | Quantity: 0.80000000    |    Cost: 10.21000000
                
                Orders info (profit_percent: 0.75)
Buy:      Price: 75.70000000  | Quantity: 0.14700000    |    Cost: 11.10000000
Sell:     Price: 76.30000000  | Quantity: 0.14700000    |    Cost: 11.20000000

                Orders info (profit_percent: 0.55)
Buy:      Price: 0.23500000  | Quantity: 47.20000000    |    Cost: 11.09200000
Sell:     Price: 0.23630000  | Quantity: 47.20000000    |    Cost: 11.15330000
"""
custom_buy_div = 0.1
custom_profit_percent = 0.6
custom_profit_percent = custom_profit_percent + 0.15
buy_profit_percent = 1 - (custom_profit_percent * custom_buy_div) / 100
sell_profit_percent = 1 + (custom_profit_percent * (1 - custom_buy_div)) / 100

current_state = {
    "order_book_bid_current_price": "0.2355"
}

filters = {
    "PRICE_FILTER_tickSize": "0.0001",
    "LOT_SIZE_stepSize": "0.1"
}
purchase_cost = "20.1"

buy_price = Decimal(current_state['order_book_bid_current_price']) * Decimal(buy_profit_percent)
buy_price = decimal_rounding(buy_price, filters['PRICE_FILTER_tickSize'], int_round=True)

buy_quantity = Decimal(purchase_cost) / Decimal(current_state['order_book_bid_current_price'])
buy_quantity = decimal_rounding(buy_quantity, filters['LOT_SIZE_stepSize'], int_round=True)
buy_quantity += Decimal(filters['LOT_SIZE_stepSize'])

sell_quantity = Decimal(buy_quantity) * Decimal(0.9985)
sell_quantity = decimal_rounding(sell_quantity, filters['LOT_SIZE_stepSize'], int_round=True)
sell_quantity += Decimal(filters['LOT_SIZE_stepSize'])


buy_cost = Decimal(buy_price) * Decimal(buy_quantity)
buy_cost = decimal_rounding(buy_cost, filters['PRICE_FILTER_tickSize'], int_round=True)

sell_price = Decimal(current_state['order_book_bid_current_price']) * Decimal(sell_profit_percent)
sell_price = decimal_rounding(sell_price, filters['PRICE_FILTER_tickSize'], int_round=True)

sell_cost = Decimal(sell_price) * Decimal(sell_quantity)
sell_cost = decimal_rounding(sell_cost, filters['PRICE_FILTER_tickSize'], int_round=True)

buy_order_to_db = {
    "symbol": str("symbol"),
    "price": str(buy_price),
    "origQty": str(buy_quantity),
    "cost": str(buy_cost),
    "side": str('BUY'),
    "workingTime": int(time.time() * 1000 // 1),
}
sell_order_to_db = {
    "symbol": str("symbol"),
    "price": str(sell_price),
    "origQty": str(sell_quantity),
    "cost": str(sell_cost),
    "side": str('SELL'),
    "workingTime": int(time.time() * 1000 // 1),
}
print(buy_order_to_db)
print(sell_order_to_db)
print(((Decimal(buy_order_to_db["origQty"]) - Decimal(sell_order_to_db["origQty"])) / Decimal(buy_order_to_db["origQty"])) > Decimal("0.001"))
print((Decimal(buy_order_to_db["origQty"]) - Decimal(sell_order_to_db["origQty"])) / Decimal(buy_order_to_db["origQty"]))
print((Decimal(buy_order_to_db["price"]) - Decimal(current_state['order_book_bid_current_price'])) / Decimal(buy_order_to_db["price"]))
print((Decimal(sell_order_to_db["price"]) - Decimal(current_state['order_book_bid_current_price'])) / Decimal(buy_order_to_db["price"]))
print((Decimal(buy_order_to_db["cost"]) - Decimal(sell_order_to_db["cost"])) / Decimal(buy_order_to_db["cost"]))
# side_test_list = ["BUY", "SELL"]
# side_test = side_test_list[randint(0, len(side_test_list) - 1)]
# print(side_test)
#
# base_path = str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]
# print(base_path)
#
# symbol = "CUSTOMUSDT"
# print(symbol[:-4])
# print(symbol[-4:])

# blank_dict = {"klines": None}
# if blank_dict["klines"] is None:
#     print("blank")
# else:
#     print(blank_dict)

# with open('getting_data/symbols.txt', 'r') as f:
#     symbols_list = f.read()
#     symbols_list = [x.strip("[',]").strip() for x in symbols_list.split(' ')]
#     print(symbols_list)
#     print(symbols_list[-10:])
#     print(symbols_list[-1])
#     print(symbols_list[-2])
    # for symbol in symbols_list:
    #     print(symbol)


# def shift(data_list):
#     to_app = "smthng"
#     if len(data_list) > 10:
#         data_list = [
#             x for x in data_list[1:]
#         ]
#     data_list.append(to_app)
#     print(data_list)
#     return data_list
#
#
# symbols_list = shift(symbols_list)
# symbols_list = shift(symbols_list)

# print(1_000_000 // 10 ** 6)

# first_state = 1680873169207
# print(int(time.time()*1000 // 1))
# print(datetime.datetime.utcfromtimestamp(int(time.time())))
# print(datetime.datetime.utcfromtimestamp(first_state/1000))
# print(datetime.timedelta(days=1))
# secs = datetime.timedelta(days=1).total_seconds()
# print("secs:", secs)
# delta = datetime.datetime.utcfromtimestamp(first_state/1000) - datetime.timedelta(1)
# print('delta:', delta)
# print(type(delta))
# res_state = first_state - secs * 1000
# print(datetime.datetime.utcfromtimestamp(res_state/1000))

# print('1564034571105')
# print('1680625921677')

# set_data_dict = {
#         'balance_first_symbol': 'BTC',
#         'balance_first_symbol_free_value': '1234.5678',
#         'balance_first_symbol_locked_value': '321.654',
#         'balance_second_symbol': 'USDT',
#         'balance_second_symbol_free_value': '5678.1234',
#         'balance_second_symbol_locked_value': '789.654',
#
#         'time': int(time.time()*1000 // 1)
#     }
#
# print(repr(str(set_data_dict)))


# set_data_str = [f"{col} = {repr(set_data_dict[col])}, " for col in set_data_dict.keys()]
# print(set_data_str)
# print(*set_data_str)
# str_for_sql = ""
# for item in set_data_str:
#     str_for_sql += str(item)
#
# print(str_for_sql)
# print(str_for_sql[:len(str_for_sql) - 2])
# print(str_for_sql[:-2])

# string_of_param = f"--first-symbol BTC --test"
#
# parser = argparse.ArgumentParser(description='Binance app')
# parser.add_argument('--first-symbol', dest='first_symbol', required=True,
#                     help='Symbol of token to buy Ex: "BTC"')
# parser.add_argument('--second-symbol', dest='second_symbol', default='USDT',
#                     help='Symbol of token as money Ex: "USDT"')
# parser.add_argument('--id', dest='id', default=3,
#                     help='Id of callback Ex: 3')
# parser.add_argument('--test', dest='test_key', nargs='?', const=True, default=False,
#                     help='Enable test mode')
# parser.add_argument('--force-url', dest='force_url', nargs='?', const=True, default=False,
#                     help="Enable force url for Spot and Websocket (in the test mode has no effect")
# args = parser.parse_args(string_of_param.split())
#
# first_symbol = args.first_symbol
# second_symbol = args.second_symbol
# id_arg = args.id
# test_key = args.test_key
# force_url = args.force_url
#
# print(
#     '\nfirst_symbol:', first_symbol,
#     '\nsecond_symbol:', second_symbol,
#     '\nid_arg:', id_arg,
#     '\ntest_key:', test_key,
#     '\nforce_url:', force_url,
# )

# print(datetime.fromtimestamp(1680438211063/1000))
# print(datetime.utcfromtimestamp(1680711384376/1000))
# print(datetime.utcnow())

# print('0000.000001')
# print((27631.66 * 0.3 * 2 / 3) // 0.000001 * 0.000001)
# print(27631.66 * 0.3 * 2 / 3)
#
# print(
#     Decimal(
#         Decimal('27631.66000000') *
#         Decimal(0.3 * 2 / 3)
#     )
# )
#
# print(
#     Decimal(
#         Decimal('27631.66000000') *
#         Decimal(0.3 * 2 / 3)
#     ) // Decimal('0.000001') * Decimal('0.000001')
# )
#
#
# print(
#     Decimal(
#         Decimal('27631.66000000') *
#         Decimal(0.3 * 2 / 3)
#     ) // Decimal('0.000002') * Decimal('0.000002')
# )

# price = getcontext().prec = 20
# precis = '0.000'
# print(Decimal('123.123456789012345678901234567890'))
# print(Decimal('123.123456789012345678901234567890').quantize(Decimal(precis), rounding=ROUND_HALF_DOWN))
# print(Decimal('123.123456789012345678901234567890').quantize(Decimal(precis), rounding=ROUND_HALF_EVEN))
# print(Decimal('123.123456789012345678901234567890').quantize(Decimal(precis), rounding=ROUND_HALF_UP))
# print()
# print(Decimal(str(float('0.01000'))))
# print(Decimal('123.1255'))
# print(Decimal('123.1255').quantize(Decimal(precis), rounding=ROUND_HALF_DOWN))
# print(Decimal('123.1255').quantize(Decimal(precis), rounding=ROUND_HALF_EVEN))
# print(Decimal('123.1255').quantize(Decimal(precis), rounding=ROUND_HALF_UP)) # my choice
# print()
# print((Decimal(10) / Decimal(7)))
# print((Decimal(10) / Decimal(7)).quantize(Decimal('0.000'), rounding=ROUND_HALF_UP))


# getcontext().prec = 8
# print(Decimal('3.123456789012345678901234567890'))
# print(Decimal('3.123456789012345678901234567890') / Decimal(1))
