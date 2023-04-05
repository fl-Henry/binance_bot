import sqlite3
import argparse
from datetime import datetime
from decimal import Decimal, getcontext, ROUND_CEILING, ROUND_UP, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN
import time

print(int(time.time()*1000 // 1))
print('1564034571105')
print('1680625921677')

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
