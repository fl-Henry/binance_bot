import os
import argparse
import time
from random import randint
from time import sleep
import pandas as pd

from decimal import Decimal, ROUND_HALF_UP
from binance_API.spot_client.spot_client_handler import SpotClient
from binance_API.websocket.websocket_handler import WebsocketClient
from sqlite3_handler.db_handler import SQLiteHandler
from sqlite3_handler import tables
from print_tags import Tags

spot_client: SpotClient
sqlh: SQLiteHandler

cost_limit = 500
profit_percent = 0.3


def create_buy_order():
    spot_client.new_order(
        symbol=spot_client.symbol,
        quantity=0.001,
        side='BUY',
        type="LIMIT",
        price=spot_client.depth_limit(20),
        timeInForce="GTC"
    )


def create_sell_order():
    spot_client.new_order(
        symbol=spot_client.symbol,
        quantity=0.001,
        side='SELL',
        type="LIMIT",
        price=spot_client.depth_limit(20, side='asks'),
        timeInForce="GTC"
    )


def create_buy_order_from_dict(order):
    try:
        if Decimal(spot_client.current_state_data['balance_second_symbol_free_value']) > Decimal(order['cost']):
            spot_client.new_order(
                symbol=spot_client.symbol,
                quantity=str(order['origQty']),
                side='BUY',
                type="LIMIT",
                price=str(order['price']),
                timeInForce="GTC"
            )
            order_created_print = f"\n{Tags.LightBlue}---- Order created --------------------------------------------" \
                                  f"\n[{order['symbol']}] P:{order['price']}; Q:{order['origQty']}; " \
                                  f"C:{order['cost']}; Si:{order['side']};" \
                                  f"{Tags.ResetAll}"
            print(order_created_print)

    except Exception as _ex:
        print('[ERROR] create_buy_order_from_dict > ', _ex)


def create_sell_order_from_dict(order):
    try:
        if Decimal(spot_client.current_state_data['balance_first_symbol_free_value']) > Decimal(order['origQty']):
            spot_client.new_order(
                symbol=spot_client.symbol,
                quantity=str(order['origQty']),
                side='SELL',
                type="LIMIT",
                price=str(order['price']),
                timeInForce="GTC"
            )

            order_created_print = f"\n{Tags.LightBlue}---- Order created --------------------------------------------" \
                                  f"\n[{order['symbol']}] P:{order['price']}; Q:{order['origQty']}; " \
                                  f"C:{order['cost']}; Si:{order['side']};" \
                                  f"{Tags.ResetAll}"
            print(order_created_print)

    except Exception as _ex:
        print('[ERROR] create_sell_order_from_dict > ', _ex)


def update_orders_db():
    sqlh.cursor.execute(tables.drop_table__orders)
    sqlh.cursor.execute(tables.create_table__orders)

    orders_to_save = spot_client.get_orders_to_db()
    if len(orders_to_save) > 0:
        for order in orders_to_save:
            sqlh.insert_from_dict('orders', order)


def sort_orders_by_status(list_of_orders_dict, status_list=None):
    if status_list is None:
        status_list = ['NEW', 'PENDING']

    sorted_orders_list = []
    for order in list_of_orders_dict:
        if str(order['status']) in status_list:
            sorted_orders_list.append(order)
    return sorted_orders_list


def sort_orders_by_side(list_of_orders_dict, side_list=None):
    if side_list is None:
        side_list = ['SELL']

    sorted_orders_list = []
    for order in list_of_orders_dict:
        if str(order['side']) in side_list:
            sorted_orders_list.append(order)
    return sorted_orders_list


def get_orders_in_process_from_db():
    pending_orders_from_db = sqlh.select_from_table('pending_orders', tables.columns__pending_orders)
    pending_orders_fetchall = pending_orders_from_db.fetchall()
    pending_orders_from_db = sqlh.parse_db_data_to_dict(tables.columns__pending_orders, pending_orders_fetchall)

    orders_from_db = sqlh.select_from_table('orders', tables.columns__orders)
    orders_fetchall = orders_from_db.fetchall()
    orders_from_db = sqlh.parse_db_data_to_dict(tables.columns__orders, orders_fetchall)

    orders_in_process = sort_orders_by_status([*pending_orders_from_db, *orders_from_db])
    orders_in_process_buy = sort_orders_by_side(orders_in_process, 'BUY')
    orders_in_process_sell = sort_orders_by_side(orders_in_process, 'SELL')
    orders_in_process_pending = sort_orders_by_status(orders_in_process, ['PENDING'])

    orders_in_process_cost = 0
    for order in orders_in_process:
        orders_in_process_cost = orders_in_process_cost + float(order['cost'])

    return {
        'orders': orders_in_process,
        'orders_cost': orders_in_process_cost,
        'orders_buy': orders_in_process_buy,
        'orders_sell': orders_in_process_sell,
        'orders_pending': orders_in_process_pending,
    }


def new_order_from_pending_db(pending_orders):
    sell_orders = sort_orders_by_side(pending_orders, side_list=["SELL"])
    buy_orders = sort_orders_by_side(pending_orders, side_list={"BUY"})

    if len(sell_orders) > 0:
        sell_orders_df = pd.DataFrame(
            sell_orders,
            columns=['symbol', 'price', 'origQty', 'cost', 'side', 'status']
        )
        sell_orders_df = sell_orders_df.sort_values(['price']).reset_index(drop=False)

        print(f'\n{Tags.LightBlue}pending_sell_orders_df{Tags.ResetAll}\n{sell_orders_df}')

        create_sell_order_from_dict(sell_orders[sell_orders_df['index'][0]])

    if len(buy_orders) > 0:
        buy_orders_df = pd.DataFrame(
                buy_orders,
                columns=['symbol', 'price', 'origQty', 'cost', 'side', 'status']
            )
        buy_orders_df = buy_orders_df.sort_values(['price'], ascending=False).reset_index(drop=False)

        print(f'\n{Tags.LightBlue}pending_buy_orders_df{Tags.ResetAll}\n{buy_orders_df}')

        create_buy_order_from_dict(buy_orders[buy_orders_df['index'][0]])


def trade_process():
    """
    """
    buy_profit_percent = 1 - (profit_percent * 2 / 3) / 100
    sell_profit_percent = 1 + (profit_percent * 1 / 3) / 100

    buy_price = Decimal(
        Decimal(spot_client.current_state_data['order_book_bid_current_price']) *
        Decimal(buy_profit_percent)
    ) // Decimal(spot_client.filters['PRICE_FILTER_tickSize']) * Decimal(spot_client.filters['PRICE_FILTER_tickSize'])

    if cost_limit * 0.1 < float(spot_client.filters['MIN_NOTIONAL_minNotional']):
        purchase_cost = (Decimal(spot_client.filters['MIN_NOTIONAL_minNotional']) * Decimal('1.01')).quantize(
            Decimal('0.00000000'), rounding=ROUND_HALF_UP
        )
    else:
        purchase_cost = (Decimal(cost_limit) * Decimal('0.1')).quantize(
            Decimal('0.00000000'), rounding=ROUND_HALF_UP
        )

    quantity = (
            Decimal(purchase_cost) / Decimal(spot_client.current_state_data['order_book_bid_current_price'])
    ) // Decimal(spot_client.filters['LOT_SIZE_stepSize']) * Decimal(spot_client.filters['LOT_SIZE_stepSize'])

    buy_cost = (
            Decimal(buy_price) * Decimal(quantity)
    ) // Decimal(spot_client.filters['PRICE_FILTER_tickSize']) * Decimal(spot_client.filters['PRICE_FILTER_tickSize'])

    sell_price = Decimal(
        Decimal(spot_client.current_state_data['order_book_bid_current_price']) *
        Decimal(sell_profit_percent)
    ) // Decimal(spot_client.filters['PRICE_FILTER_tickSize']) * Decimal(spot_client.filters['PRICE_FILTER_tickSize'])

    sell_cost = (
            Decimal(sell_price) * Decimal(quantity)
    ) // Decimal(spot_client.filters['PRICE_FILTER_tickSize']) * Decimal(spot_client.filters['PRICE_FILTER_tickSize'])

    buy_order_to_db = {
        "symbol": str(spot_client.symbol),
        "price": str(buy_price),
        "origQty": str(quantity),
        "cost": str(buy_cost),
        "side": str('BUY'),
        "workingTime": int(time.time()*1000 // 1),
    }
    sell_order_to_db = {
        "symbol": str(spot_client.symbol),
        "price": str(sell_price),
        "origQty": str(quantity),
        "cost": str(sell_cost),
        "side": str('SELL'),
        "workingTime": int(time.time()*1000 // 1),
    }

    sqlh.insert_from_dict('pending_orders', buy_order_to_db)
    sqlh.insert_from_dict('pending_orders', sell_order_to_db)
    pair_pk = sqlh.select_from_table('pending_orders', ['pk'])
    last_pair_pk = pair_pk.fetchall()[-2:]

    pair_pk_to_db = {
        'buy_order_pk': last_pair_pk[0][0],
        'sell_order_pk': last_pair_pk[1][0],
    }
    sqlh.insert_from_dict('orders_pair', pair_pk_to_db)

    to_print_data = f"\n             Pending orders created (profit_percent: {profit_percent})" \
                    f"\nBuy:      Price: {buy_price}  | Quantity: {quantity}    |    Cost: {buy_cost}" \
                    f"\nSell:     Price: {sell_price}  | Quantity: {quantity}    |    Cost: {sell_cost}"

    print(f'{Tags.BackgroundLightGreen}{Tags.Black}{to_print_data}{Tags.ResetAll}')

    create_buy_order_from_dict(buy_order_to_db)
    create_sell_order_from_dict(sell_order_to_db)


def if_buy():
    """
    """
    # TODO: table "pending orders" > order pairs > when callback with execution report - check table "pending orders"
    # if pending match orders quantity and price then append orderId and update status
    # when both of orders are filled > OK

    # TODO: when the balance is not enough to sell then create only buy order and make sell order still pending

    key_to_trade_process = True
    orders_in_process = get_orders_in_process_from_db()

    if len(orders_in_process['orders_pending']) > 0:
        new_order_from_pending_db(orders_in_process['orders_pending'])
    elif (orders_in_process['orders_cost'] < cost_limit) and key_to_trade_process:
        trade_process()
    else:
        print('[WARNING] if_buy > orders creation failed')


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
    parser.add_argument('--id', dest='id', default=4,
                        help='Id of callback Ex: 4')
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

    global spot_client
    spot_client = SpotClient(
        test_key=test_key,
        force_url=force_url,
        first_symbol=first_symbol,
        second_symbol=second_symbol
    )

    web_socket = WebsocketClient(
        test_key=test_key,
        force_url=force_url,
        first_symbol=first_symbol,
        second_symbol=second_symbol,
        listen_key=spot_client.listen_key
    )

    if id_arg == 4:

        base_path = str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]
        if test_key:
            db_name = f"test_{first_symbol}{second_symbol}"
        else:
            db_name = f"{first_symbol}{second_symbol}"

        global sqlh
        sqlh = SQLiteHandler(db_name=db_name, db_dir=base_path)
        sqlh.create_all_tables(tables.create_all_tables)

        try:
            spot_client.get_current_state()
            spot_client.str_current_state()
            if len(spot_client.current_state_data) > 0:
                sqlh.insert_from_dict('current_state', spot_client.current_state_data)

            spot_client.get_exchange_info()
            if len(spot_client.filters) > 0:
                sqlh.insert_from_dict('filters', spot_client.filters)

            # create_buy_order()
            #
            # create_sell_order()

            spot_client.cancel_all_new_orders()
            update_orders_db()

            renew_listen_key_counter = 0
            while True:
                print(f'{Tags.BackgroundLightYellow}{Tags.Black}'
                      f'\n      Scheduled if_buy\n'
                      f'{Tags.ResetAll}')
                if_buy()

                # if (renew_listen_key_counter % 4) == 0:
                #     print(f'{Tags.BackgroundLightRed}'
                #           f'\n      Scheduled if_cancel\n'
                #           f'{Tags.ResetAll}')
                #     if_cancel(f'{symbol}USDT')

                if renew_listen_key_counter >= 120:
                    spot_client.renew_listen_key(spot_client.listen_key)
                    renew_listen_key_counter = 0
                    print("listen_key is updated:", repr(spot_client.listen_key))

                key_to_exit_from_update_loop = True
                while key_to_exit_from_update_loop:
                    try:
                        spot_client.get_current_state()
                        spot_client.str_current_state()
                        if len(spot_client.current_state_data) > 0:
                            sqlh.insert_from_dict('current_state', spot_client.current_state_data)

                        update_orders_db()
                        key_to_exit_from_update_loop = False
                    except Exception as _ex:
                        print("[ERROR] start_bot_logic > id_arg == 4 > ", _ex)
                        key_to_exit_from_update_loop = True
                        time.sleep(randint(1, 10))

                renew_listen_key_counter += 1
                print("renew_listen_key_counter: ", renew_listen_key_counter)
                sleep(15)

        except KeyboardInterrupt:
            ...
        finally:
            web_socket.stop()
            print('web_socket.stop()')
            sqlh.close()
            print('sqlh.close()')

    elif id_arg == 3:
        try:
            web_socket.stream_user_data()

            while True:
                sleep(60)

        except KeyboardInterrupt:
            ...
        finally:
            web_socket.stop()
            print('web_socket.stop()')
    else:
        print("[ERROR] start_bot_logic > id_arg is out of range | expected 3 or 4")
        print("id_arg = 3 > web_socket.stream_user_data()")
        print("id_arg = 4 > web_socket.stream_execution_reports()")


if __name__ == '__main__':
    start_bot_logic()


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

