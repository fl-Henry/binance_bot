import os
import sqlite3
import argparse
import datetime
# from datetime import datetime
from decimal import Decimal, getcontext, ROUND_CEILING, ROUND_UP, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN
import time

base_path = str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]
print(base_path)

symbol = "CUSTOMUSDT"
print(symbol[:-4])
print(symbol[-4:])

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
