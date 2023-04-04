import os
import argparse
from time import sleep
import pandas as pd

from binance_API.spot_client.spot_client_handler import SpotClient
from binance_API.websocket.websocket_handler import WebsocketClient
from sqlite3_handler.db_handler import SQLiteHandler
from log_handler.log_handler import LogHandler
from sqlite3_handler.tables import create_all_tables
from print_tags import Tags

lh: LogHandler
spot_client: SpotClient
sqlh: SQLiteHandler


def if_buy(symbol):
    """
    :param symbol: str      | 'BTCUSTD'
    """
    orders = spot_requests.get_orders(
        client=spot_client,
        symbol=symbol,
        status="NEW",
        get_limit=200,
        log_key=True
    )
    start_state_update(symbol[:len(symbol) - 4])

    sleep(1)
    buy_orders = []
    sell_orders = []
    for item in orders:
        if item['side'] == 'BUY':
            buy_orders.append(item)
        elif item['side'] == 'SELL':
            sell_orders.append(item)

    # percen from wallet sum --------------/--------------/--------------/--------------/--------------/
    # percen from wallet sum --------------/--------------/--------------/--------------/--------------/
    # percen from wallet sum --------------/--------------/--------------/--------------/--------------/
    percent_from_wallet_sum = 0.3
    if (len(sell_orders) < limit_orders_amount) and (len(buy_orders) < limit_orders_amount) and (
            (
                    (start_state['Locked'] + start_state['symbol_free_value']) / start_state['usdt_free_value']
            ) < percent_from_wallet_sum                                                 # ----bad condition----------------
    ):
        trade_process(symbol)


def start_bot_logic():
    """
    # TODO: start websocket user_agent

    # TODO: if_buy
    # TODO: schedule of orders

    logger: errors
            current state
            pair of orders
            executionReport

    """

    parser = argparse.ArgumentParser(description='Binance app')
    parser.add_argument('--first-symbol', dest='first_symbol', required=True,
                        help='Symbol of token to buy Ex: "BTC"')
    parser.add_argument('--second-symbol', dest='second_symbol', default='USDT',
                        help='Symbol of token as money Ex: "USDT"')
    parser.add_argument('--id', dest='id', default=3,
                        help='Id of callback Ex: 3')
    parser.add_argument('--test', dest='test_key', nargs='?', const=True, default=False,
                        help='Enable test mode')
    parser.add_argument('--force-url', dest='force_url', nargs='?', const=True, default=False,
                        help="Enable force url for Spot and Websocket (in the test mode has no effect")
    args = parser.parse_args()

    first_symbol = args.first_symbol
    second_symbol = args.second_symbol
    id_arg = args.id
    test_key = args.test_key
    force_url = args.force_url

    print(
        '\nfirst_symbol:', first_symbol,
        '\nsecond_symbol:', second_symbol,
        '\nid_arg:', id_arg,
        '\ntest_key:', test_key,
        '\nforce_url:', force_url,
    )

    global lh
    lh = LogHandler(name=f'{first_symbol}{second_symbol}')
    lh.logger.info('logger created')

    global spot_client
    spot_client = SpotClient(
        test_key=test_key,
        force_url=force_url,
        first_symbol=first_symbol,
        second_symbol=second_symbol
    )
    lh.logger.info('spot_client created')

    web_socket = WebsocketClient(
        test_key=test_key,
        force_url=force_url,
        first_symbol=first_symbol,
        second_symbol=second_symbol,
        listen_key=spot_client.listen_key
    )
    lh.logger.info('web_socket created')

    base_path = str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]
    if test_key:
        db_name = f"test_{first_symbol}{second_symbol}"
    else:
        db_name = f"{first_symbol}{second_symbol}"

    global sqlh
    sqlh = SQLiteHandler(db_name=db_name, db_dir=base_path)
    sqlh.create_all_tables(create_all_tables)
    lh.logger.info(f'sql_handler created, db_name: {db_name}')

    try:
        spot_client.get_current_state()
        if len(spot_client.current_state_data) > 0:
            sqlh.insert_from_dict('current_state', spot_client.current_state_data)

        spot_client.get_exchange_info()
        if len(spot_client.filters) > 0:
            sqlh.insert_from_dict('filters', spot_client.filters)

        # spot_client.update_orders_to_db()

        renew_listen_key_counter = 0
        while True:
            print(f'{Tags.BackgroundLightYellow}{Tags.Black}'
                  f'\n      Scheduled if_buy\n'
                  f'{Tags.ResetAll}')
            # if_buy(f'{symbol}USDT')

            if (renew_listen_key_counter % 4) == 0:
                print(f'{Tags.BackgroundLightRed}'
                      f'\n      Scheduled if_cancel\n'
                      f'{Tags.ResetAll}')
                # if_cancel(f'{symbol}USDT')

            if renew_listen_key_counter >= 120:
                spot_client.renew_listen_key(spot_client.listen_key)
                renew_listen_key_counter = 0
                print("listen_key is updated:", repr(spot_client.listen_key))

            renew_listen_key_counter += 1
            sleep(15)

    except KeyboardInterrupt:
        ...
    finally:
        web_socket.stop()
        sqlh.close()


if __name__ == '__main__':
    start_bot_logic()


#
# def trade_process(symbol, profit_percent=0.3):
#     """
#     :param symbol: str      | 'BTCUSDT'
#     :param profit_percent: float   | % of earning Ex: 3 or 0.3 for 3% or 0.3%
#     """
#     buy_profit_percent = 1 - (profit_percent / 2) / 100
#     quantity_precision = 2
#     price_precision = 4
#     min_notional = 10 + 0.1
#
#     current_cost = float(spot_requests.depth_limit(spot_client, symbol, 1))
#     buy_price = round(current_cost * buy_profit_percent, price_precision)
#
#     if (start_state['usdt_locked_value'] + start_state['usdt_free_value']) * 0.02 < min_notional:
#         buy_cost = min_notional
#     else:
#         buy_cost = (start_state['usdt_locked_value'] + start_state['usdt_free_value']) * 0.02
#
#     quantity = buy_cost / current_cost
#     quantity = f'{quantity:.{quantity_precision}f}'
#
#     print(buy_cost)
#     print(quantity)
#
#     buy_key = False
#     try:
#         buy_data = spot_requests.buy_order(
#             client=spot_client,
#             quantity=quantity,
#             symbol=symbol,
#             price=buy_price
#         )
#         buy_key = True
#     except Exception as _ex:
#         print(_ex)
#
#     sleep(1)
#
#     if buy_key:
#         sell_profit_percent = 1 + profit_percent / 100
#         sell_price = round((current_cost * sell_profit_percent), price_precision)
#         to_print_data = f"\n             Trade process completed (profit_percent: {profit_percent})" \
#                         f"\nBuy:      Price: {buy_price}  | Quantity: {quantity}    |" \
#                         f" Cost: {buy_price * float(quantity)}" \
#                         f"\nSell:     Price: {sell_price}  | Quantity: {quantity}    |" \
#                         f" Cost: {sell_price * float(quantity)}"
#         print(f'{Tags.BackgroundLightGreen}{Tags.Black}{to_print_data}{Tags.ResetAll}')
#
#         buy_data.update({'sum': (float(buy_data["price"]) * float(buy_data['quantity']))})
#         sell_data = buy_data
#         sell_data.update({'price': sell_price})
#         sell_data.update({'quantity': quantity})
#         sell_data.update({'sum': (float(sell_data["price"]) * float(sell_data['quantity']))})
#         state_history.add_orders_pair(pd.DataFrame([buy_data, sell_data]))
#
#         try:
#             spot_requests.sell_order(
#                 client=spot_client,
#                 quantity=quantity,
#                 symbol=symbol,
#                 price=sell_price
#             )
#
#         except Exception as _ex:
#             state_history.add_cannot_sell(sell_price, quantity, symbol)
#             print(_ex)
#
#
# def rebuild_orders(orders_df, side):
#     """
#     :param orders_df: pd.DataFrame
#     :param side: str        | 'SELL', 'BUY'
#     :return: json           | json to overwrite log
#     """
#     print('\norders_df\n', orders_df)
#     sort_limit = limit_orders_amount + 10
#
#     for order_counter in range(orders_df.__len__()):
#         if (str(orders_df['orderId'][order_counter]) in ['NaN', 'nan']) and (order_counter < sort_limit):
#             if side == 'SELL':
#                 try:
#                     spot_requests.sell_order(
#                         client=spot_client,
#                         quantity=float(orders_df['origQty'][order_counter]),
#                         symbol=str(orders_df['symbol'][order_counter]),
#                         price=float(orders_df['price'][order_counter])
#                     )
#                     orders_df[order_counter]['orderId'] = 'opened'
#                 except Exception as _ex:
#                     print(_ex)
#
#             elif side == 'BUY':
#                 try:
#                     spot_requests.buy_order(
#                         client=spot_client,
#                         quantity=float(orders_df['origQty'][order_counter]),
#                         symbol=str(orders_df['symbol'][order_counter]),
#                         price=float(orders_df['price'][order_counter])
#                     )
#                     orders_df[order_counter]['orderId'] = 'opened'
#                 except Exception as _ex:
#                     print(_ex)
#             else:
#                 raise KeyError
#
#         elif (str(orders_df['orderId'][order_counter]) not in ['NaN', 'nan']) and \
#                 (order_counter >= sort_limit):
#             spot_requests.cancel_order(
#                 client=spot_client,
#                 symbol=str(orders_df['symbol'][order_counter]),
#                 order_id=int(orders_df['orderId'][order_counter])
#             )
#             orders_df[order_counter]['orderId'] = 'closed'
#
#     print('\norders_df after operations\n', orders_df)
#
#     for order_counter in range(orders_df.__len__()):
#         if (str(orders_df['orderId'][order_counter]) not in ['NaN', 'nan', 'closed']) and (order_counter < sort_limit):
#             print('droped')
#             orders_df.drop(order_counter)
#
#     # if orders_df.__len__() > sort_limit:
#     #     orders_df = orders_df.drop([*range(sort_limit)])
#     # else:
#     #     orders_df = orders_df.drop([*range(orders_df.__len__())])
#
#     for column_name in orders_df.columns.values.tolist():
#         if column_name not in ['price', 'origQty', 'symbol']:
#             orders_df = orders_df.drop(columns=column_name)
#
#     print(f'{Tags.BackgroundMagenta}\nLast orders{Tags.ResetAll}\n', orders_df)
#     orders_df_json = json.loads(orders_df.to_json(orient="records"))
#
#     return orders_df_json
#
#
# def if_cancel(symbol):
#     """
#     :param symbol: str      | 'BTCUSDT'
#     """
#     current_orders_update(symbol)
#
#     buy_failed_orders = state_history.read_cannot_buy()
#     buy_failed_orders = pd.json_normalize(buy_failed_orders)
#
#     sell_failed_orders = state_history.read_cannot_sell()
#     sell_failed_orders = pd.json_normalize(sell_failed_orders)
#
#     current_orders_df = pd.json_normalize(current_orders)
#     if current_orders_df.__len__() > 0:
#         current_sell_orders_df = current_orders_df[current_orders_df['side'] == 'SELL']
#         current_buy_orders_df = current_orders_df[current_orders_df['side'] == 'BUY']
#     else:
#         current_sell_orders_df = current_orders_df
#         current_buy_orders_df = current_orders_df
#
#     sell_orders_df = pd.concat([sell_failed_orders, current_sell_orders_df])
#     buy_orders_df = pd.concat([buy_failed_orders, current_buy_orders_df])
#     all_orders_df = pd.concat([sell_orders_df, buy_orders_df])
#
#     if sell_orders_df.__len__() > 0:
#         print(f'\nRebuild SELL orders:')
#         sell_orders_df = sell_orders_df.sort_values(['price']).reset_index(drop=True)
#         sell_orders_df_json = rebuild_orders(sell_orders_df, 'SELL')
#         state_history.rewrite_cannot_sell(sell_orders_df_json)
#
#     if buy_orders_df.__len__() > 0:
#         print(f'\nRebuild BUY orders:')
#         buy_orders_df = buy_orders_df.sort_values(['price'], ascending=False).reset_index(drop=True)
#         buy_orders_df_json = rebuild_orders(buy_orders_df, 'BUY')
#         state_history.rewrite_cannot_buy(buy_orders_df_json)
#
#     # if (current_orders_df.__len__() >= limit_orders_amount) and (sell_orders_df.__len__() < limit_orders_amount + 2) \
#     #         and (all_orders_df.__len__() < limit_orders_amount + 4):
#     #     print(f'current_orders_df.__len__() >= {limit_orders_amount}  | ', current_orders_df.__len__())
#     #     print(f'sell_orders_df.__len__() < {limit_orders_amount + 2}     | ', sell_orders_df.__len__())
#     #     print(f'all_orders_df.__len__() < {limit_orders_amount + 4}      | ', all_orders_df.__len__())
#     #     trade_process(symbol, profit_percent=0.6)
#
#

