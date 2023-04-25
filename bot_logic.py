import os
import sys
import time
import argparse
import pandas as pd

from binance.error import ClientError
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP, localcontext
from datetime import datetime
from random import randint
from time import sleep

from binance_API.spot_client.spot_client_handler import SpotClient
from binance_API.websocket.websocket_handler import WebsocketClient
from sqlite3_handler.db_handler import SQLiteHandler
from sqlite3_handler import tables
from print_tags import Tags

spot_client: SpotClient
web_socket: WebsocketClient
sqlh: SQLiteHandler
sqlh_dict: dict[str, SQLiteHandler] = {}  # {symbol: SQLiteHandler, "}

buy_div = 0.2  # sell_div = 1 - buy_div
profit_percent = 0.3
symbol_cost_limit = 20
cost_limit = 60

loop_waiting = (0 * 60) + 20

base_path = str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]
base_dir = f"{base_path}/"
db_dir = f"{base_dir}databases/"


def decimal_rounding(decimal_value, value_for_round="0.00000000", int_round=False, rounding=ROUND_HALF_UP):
    if int_round:
        return Decimal(decimal_value) // Decimal(value_for_round) * Decimal(value_for_round)
    else:
        return Decimal(decimal_value).quantize(Decimal(value_for_round), rounding=rounding)


def create_db_name(symbol, test_key=False):
    if test_key:
        db_name = f"test_{symbol}"
    else:
        db_name = f"{symbol}"
    return db_name


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


def new_order_test_from_dict(order):
    """
    order = {
        "symbol": str(symbol),                                                  \n
        "price": str(buy_price),                                                \n
        "origQty": str(quantity),                                               \n
        "cost": str(buy_cost),                                                  \n
        "side": str('BUY'),                                                     \n
        "workingTime": int(time.time() * 1000 // 1),                            \n
    }
    :param order:
    :return:
    """
    try:
        spot_client.new_order_test(
            symbol=str(order['symbol']),
            quantity=str(order['origQty']),
            side=str(order['side']),
            type="LIMIT",
            price=str(order['price']),
            timeInForce="GTC"
        )

        return True
    except Exception as _ex:
        to_print_data = f"\nOrder: Sy:{order['symbol']}; Si:{order['side']} P: {order['price']}; " \
                        f"Q: {order['origQty']}; C: {order['cost']}"
        print(to_print_data)
        print('[ERROR] new_order_test_from_dict > ', str(order['symbol']), _ex)
        return False


def create_buy_order_from_dict(order):
    symbol = order['symbol']
    try:
        current_state = spot_client.get_current_state(symbol)
        if Decimal(current_state['balance_second_symbol_free_value']) > Decimal(order['cost']):
            spot_client.new_order(
                symbol=symbol,
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
    symbol = order['symbol']
    try:
        current_state = spot_client.get_current_state(symbol)
        if Decimal(current_state['balance_first_symbol_free_value']) > Decimal(order['origQty']):
            spot_client.new_order(
                symbol=symbol,
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


def get_orders_in_process_from_db(symbol_sqlh=None):
    if symbol_sqlh is None:
        symbol_sqlh = sqlh

    pending_orders_from_db = symbol_sqlh.select_from_table('pending_orders', tables.columns__pending_orders)
    pending_orders_fetchall = pending_orders_from_db.fetchall()
    pending_orders_from_db = symbol_sqlh.parse_db_data_to_dict(tables.columns__pending_orders, pending_orders_fetchall)

    orders_from_db = symbol_sqlh.select_from_table('orders', tables.columns__orders)
    orders_fetchall = orders_from_db.fetchall()
    orders_from_db = symbol_sqlh.parse_db_data_to_dict(tables.columns__orders, orders_fetchall)

    orders_in_process = sort_orders_by_status([*pending_orders_from_db, *orders_from_db])
    orders_in_process_buy = sort_orders_by_side(orders_in_process, 'BUY')
    orders_in_process_sell = sort_orders_by_side(orders_in_process, 'SELL')
    orders_in_process_pending = sort_orders_by_status(orders_in_process, ['PENDING'])
    orders_in_process_new = sort_orders_by_status(orders_from_db, ['NEW'])

    orders_in_process_cost = 0
    for order in orders_in_process_new:
        orders_in_process_cost = orders_in_process_cost + float(order['cost'])

    return {
        'orders': orders_in_process,
        'orders_new_cost': orders_in_process_cost,
        'orders_buy': orders_in_process_buy,
        'orders_sell': orders_in_process_sell,
        'orders_pending': orders_in_process_pending,
        'orders_new': orders_in_process_new,
    }


def list_of_orders_to_dataframe(orders, header: str = None, key_to_print=False, columns=None, sort_col='price',
                                ascending=True, reset_index=True):
    """

    :param orders:
    :param header:
    :param key_to_print:
    :param columns:
    :param sort_col:
    :param ascending: bool      | True -> min to max
    :param reset_index:
    :return:
    """
    if columns is None:
        columns = ['symbol', 'orderId', 'price', 'origQty', 'cost', 'side', 'status']

    if len(orders) > 0:
        orders_df = pd.DataFrame(
            orders,
            columns=columns
        )
        orders_df = orders_df.sort_values([sort_col], ascending=ascending).reset_index(drop=reset_index)

        if key_to_print:
            print(f'\n{Tags.LightBlue}{header}{Tags.ResetAll}\n{orders_df}')

        return orders_df


def new_order_from_pending_db(pending_orders):
    sell_orders = sort_orders_by_side(pending_orders, side_list=["SELL"])
    buy_orders = sort_orders_by_side(pending_orders, side_list=["BUY"])

    sell_orders_df = list_of_orders_to_dataframe(
        sell_orders,
        header='--- Pending SELL orders ------------------',
        key_to_print=True,
        sort_col='price',
        reset_index=False
    )
    if len(sell_orders) > 0:
        create_sell_order_from_dict(sell_orders[sell_orders_df['index'][0]])

    buy_orders_df = list_of_orders_to_dataframe(
        buy_orders,
        header='--- Pending BUY orders -------------------',
        key_to_print=True,
        sort_col='price',
        ascending=False,
        reset_index=False
    )
    if len(buy_orders) > 0:
        create_buy_order_from_dict(buy_orders[buy_orders_df['index'][0]])


def trade_process(custom_buy_div=None, custom_cost_limit=None):
    """
        -->> Deprecated <<-- use symbol_trade_process() instead

        :param custom_cost_limit: int
        :param custom_buy_div: float
        0.5 > $more ----s==|==b---- $less ; stable
        0.75 >      -----s=|===b---       ; down
        0.25 >      ---s===|=b-----       ; up
        "--s==|==b--" - offset of buy price
    """
    if custom_cost_limit is None:
        custom_cost_limit = cost_limit

    if custom_buy_div is None:
        buy_profit_percent = 1 - (profit_percent * buy_div) / 100
        sell_profit_percent = 1 + (profit_percent * (1 - buy_div)) / 100
    else:
        buy_profit_percent = 1 - (profit_percent * custom_buy_div) / 100
        sell_profit_percent = 1 + (profit_percent * (1 - custom_buy_div)) / 100

    buy_price = Decimal(
        Decimal(spot_client.current_state_data['order_book_bid_current_price']) *
        Decimal(buy_profit_percent)
    ) // Decimal(spot_client.filters['PRICE_FILTER_tickSize']) * Decimal(spot_client.filters['PRICE_FILTER_tickSize'])

    if Decimal(str(custom_cost_limit)) * Decimal('0.09') < Decimal(spot_client.filters['MIN_NOTIONAL_minNotional']):
        purchase_cost = (Decimal(spot_client.filters['MIN_NOTIONAL_minNotional']) * Decimal('1.01')).quantize(
            Decimal('0.00000000'), rounding=ROUND_HALF_UP
        )
    else:
        purchase_cost = (Decimal(custom_cost_limit) * Decimal('0.11')).quantize(
            Decimal('0.00000000'), rounding=ROUND_HALF_UP
        )

    quantity = (
                       Decimal(purchase_cost) / Decimal(spot_client.current_state_data['order_book_bid_current_price'])
               ) // Decimal(spot_client.filters['LOT_SIZE_stepSize']) * Decimal(spot_client.filters['LOT_SIZE_stepSize']
                                                                                ) + Decimal(
        spot_client.filters['LOT_SIZE_stepSize'])

    buy_cost = (
                       Decimal(buy_price) * Decimal(quantity)
               ) // Decimal(spot_client.filters['PRICE_FILTER_tickSize']) * Decimal(
        spot_client.filters['PRICE_FILTER_tickSize'])

    sell_price = Decimal(
        Decimal(spot_client.current_state_data['order_book_bid_current_price']) *
        Decimal(sell_profit_percent)
    ) // Decimal(spot_client.filters['PRICE_FILTER_tickSize']) * Decimal(spot_client.filters['PRICE_FILTER_tickSize'])

    sell_cost = (
                        Decimal(sell_price) * Decimal(quantity)
                ) // Decimal(spot_client.filters['PRICE_FILTER_tickSize']) * Decimal(
        spot_client.filters['PRICE_FILTER_tickSize'])

    buy_order_to_db = {
        "symbol": str(spot_client.symbol),
        "price": str(buy_price),
        "origQty": str(quantity),
        "cost": str(buy_cost),
        "side": str('BUY'),
        "workingTime": int(time.time() * 1000 // 1),
    }
    sell_order_to_db = {
        "symbol": str(spot_client.symbol),
        "price": str(sell_price),
        "origQty": str(quantity),
        "cost": str(sell_cost),
        "side": str('SELL'),
        "workingTime": int(time.time() * 1000 // 1),
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

    to_print_data = f"\n             Pending orders created (profit_percent: {custom_cost_limit})" \
                    f"\nBuy:      Price: {buy_price}  | Quantity: {quantity}    |    Cost: {buy_cost}" \
                    f"\nSell:     Price: {sell_price}  | Quantity: {quantity}    |    Cost: {sell_cost}"

    print(f'{Tags.BackgroundLightGreen}{Tags.Black}{to_print_data}{Tags.ResetAll}')

    create_buy_order_from_dict(buy_order_to_db)
    create_sell_order_from_dict(sell_order_to_db)


def symbol_trading_process(symbol, symbol_sqlh: SQLiteHandler, custom_buy_div=None, custom_cost_limit=None, custom_profit_percent=None):
    """
        :param symbol: str                      | "BTCUSDT"
        :param symbol_sqlh: SQLiteHandler
        :param custom_cost_limit: int           | 100 -> $100
        :param custom_buy_div: float
            0.5 > $more ----s==|==b---- $less ; stable
            0.75 >      -----s=|===b---       ; down
            0.25 >      ---s===|=b-----       ; up
            "--s==|==b--" - offset of buy price

        :param custom_profit_percent: float     | 0.3 -> 0.3 %  \\  1 -> 1 %
    """
    if custom_cost_limit is None:
        custom_cost_limit = cost_limit

    if custom_profit_percent is None:
        custom_profit_percent = profit_percent

    if custom_buy_div is None:
        buy_profit_percent = 1 - ((custom_profit_percent + 0.15) * buy_div) / 100
        sell_profit_percent = 1 + ((custom_profit_percent + 0.15) * (1 - buy_div)) / 100
    else:
        buy_profit_percent = 1 - ((custom_profit_percent + 0.15) * custom_buy_div) / 100
        sell_profit_percent = 1 + ((custom_profit_percent + 0.15) * (1 - custom_buy_div)) / 100

    current_state = spot_client.get_current_state(symbol)

    if Decimal(str(custom_cost_limit)) * Decimal('0.09') < Decimal(spot_client.filters_list[symbol]['MIN_NOTIONAL_minNotional']):
        purchase_cost = Decimal(spot_client.filters_list[symbol]['MIN_NOTIONAL_minNotional']) * Decimal('2')
        purchase_cost = decimal_rounding(purchase_cost, "0.00000000")
    else:
        purchase_cost = Decimal(custom_cost_limit) * Decimal('0.22')
        purchase_cost = decimal_rounding(purchase_cost, "0.00000000")

    buy_price = Decimal(current_state['order_book_bid_current_price']) * Decimal(buy_profit_percent)
    buy_price = decimal_rounding(buy_price, spot_client.filters_list[symbol]['PRICE_FILTER_tickSize'], int_round=True)

    buy_quantity = Decimal(purchase_cost) / Decimal(current_state['order_book_bid_current_price'])
    buy_quantity = decimal_rounding(buy_quantity, spot_client.filters_list[symbol]['LOT_SIZE_stepSize'], int_round=True)
    buy_quantity += Decimal(spot_client.filters_list[symbol]['LOT_SIZE_stepSize'])

    sell_quantity = Decimal(buy_quantity) * Decimal(0.9985)
    sell_quantity = decimal_rounding(sell_quantity, spot_client.filters_list[symbol]['LOT_SIZE_stepSize'], int_round=True)
    sell_quantity += Decimal(spot_client.filters_list[symbol]['LOT_SIZE_stepSize'])

    buy_cost = Decimal(buy_price) * Decimal(buy_quantity)
    buy_cost = decimal_rounding(buy_cost, spot_client.filters_list[symbol]['PRICE_FILTER_tickSize'], int_round=True)

    sell_price = Decimal(current_state['order_book_bid_current_price']) * Decimal(sell_profit_percent)
    sell_price = decimal_rounding(sell_price, spot_client.filters_list[symbol]['PRICE_FILTER_tickSize'], int_round=True)

    sell_cost = Decimal(sell_price) * Decimal(sell_quantity)
    sell_cost = decimal_rounding(sell_cost, spot_client.filters_list[symbol]['PRICE_FILTER_tickSize'], int_round=True)

    buy_order_to_db = {
        "symbol": str(symbol),
        "price": str(buy_price),
        "origQty": str(buy_quantity),
        "cost": str(buy_cost),
        "side": str('BUY'),
        "workingTime": int(time.time() * 1000 // 1),
    }
    sell_order_to_db = {
        "symbol": str(symbol),
        "price": str(sell_price),
        "origQty": str(sell_quantity),
        "cost": str(sell_cost),
        "side": str('SELL'),
        "workingTime": int(time.time() * 1000 // 1),
    }

    to_print_data = f"\n            Orders info: Symbol: {symbol} (profit_percent: {custom_profit_percent})" \
                    f"\nBuy:      Price: {buy_price}  | Quantity: {buy_quantity}    |    Cost: {buy_cost}" \
                    f"\nSell:     Price: {sell_price}  | Quantity: {sell_quantity}    |    Cost: {sell_cost}"

    # Check filters
    quantity_difference = Decimal(buy_order_to_db["origQty"]) - Decimal(sell_order_to_db["origQty"])
    filters_key = (quantity_difference / Decimal(buy_order_to_db["origQty"])) > Decimal("0.001")
    if filters_key:
        filters_key = (quantity_difference / Decimal(buy_order_to_db["origQty"])) < Decimal("0.0025")
    if filters_key:
        filters_key = new_order_test_from_dict(buy_order_to_db)
    else:
        print(to_print_data)
        print("Quantity difference is less then 0.1% or greater then 0.25%")
    if filters_key:
        filters_key = new_order_test_from_dict(sell_order_to_db)

    if filters_key:
        symbol_sqlh.insert_from_dict('pending_orders', buy_order_to_db)
        symbol_sqlh.insert_from_dict('pending_orders', sell_order_to_db)
        pair_pk = symbol_sqlh.select_from_table('pending_orders', ['pk'])
        last_pair_pk = pair_pk.fetchall()[-2:]

        pair_pk_to_db = {
            'buy_order_pk': last_pair_pk[0][0],
            'sell_order_pk': last_pair_pk[1][0],
        }
        symbol_sqlh.insert_from_dict('orders_pair', pair_pk_to_db)

        to_print_data = f"\n     Pending orders created: Symbol: {symbol} (profit_percent: {custom_profit_percent})" \
                        f"\nBuy:      Price: {buy_price}  | Quantity: {buy_quantity}    |    Cost: {buy_cost}" \
                        f"\nSell:     Price: {sell_price}  | Quantity: {sell_quantity}    |    Cost: {sell_cost}"

        print(f'{Tags.BackgroundLightGreen}{Tags.Black}{to_print_data}{Tags.ResetAll}')

        create_buy_order_from_dict(buy_order_to_db)
        create_sell_order_from_dict(sell_order_to_db)

        # Waiting for responses
        sleep(5)


def if_buy():
    """
    """
    orders_in_process = get_orders_in_process_from_db()

    list_of_orders_to_dataframe(
        orders_in_process['orders_new'],
        header='--- New orders ---------------------------',
        key_to_print=True,
        sort_col='price',
        ascending=True,
        reset_index=True
    )

    if len(orders_in_process['orders_pending']) > 0:
        new_order_from_pending_db(orders_in_process['orders_pending'])
    elif orders_in_process['orders_new_cost'] < cost_limit:
        print("\nOrders in process cost:", orders_in_process['orders_new_cost'])
        print('Cost limit', cost_limit)
        print('Start trade_process:')
        trade_process()
    else:
        print("\nOrders in process cost:", orders_in_process['orders_new_cost'])
        print('Cost limit', cost_limit)
        print('Skip')


def if_buy_kline():
    """
        -->> Deprecated <<-- use symbol_if_buy_kline() instead

    """
    custom_cost_limit = cost_limit * 2

    orders_in_process = get_orders_in_process_from_db()

    list_of_orders_to_dataframe(
        orders_in_process['orders_new'],
        header='--- New orders ---------------------------',
        key_to_print=True,
        sort_col='price',
        ascending=True,
        reset_index=True
    )

    average_all_cost = (Decimal(spot_client.last_kline['sum']['all_cost']
                                ) / Decimal(spot_client.last_kline['sum']['amount'])
                        ) // Decimal('0.00000001') * Decimal('0.00000001')
    all_cost = float(web_socket.kline_last['all_cost'])
    buy_cost = float(web_socket.kline_last['buy_cost'])
    sell_cost = float(web_socket.kline_last['sell_cost'])
    buy_part = Decimal(100 * (buy_cost / all_cost)).quantize(Decimal("0.0"), rounding=ROUND_HALF_UP)
    sell_part = Decimal(100 * (sell_cost / all_cost)).quantize(Decimal("0.0"), rounding=ROUND_HALF_UP)

    print(f"\nAverage volume:      {str(average_all_cost):>24} | {str(average_all_cost // 10 ** 5 / 10):>6}M | "
          f"{str(average_all_cost // 10 ** 2 / 10):>6}K |")
    print(f"All volume:          {str(all_cost):>24} | {str(all_cost // 10 ** 5 / 10):>6}M | "
          f"{str(all_cost // 10 ** 2 / 10):>6}K |  100%")
    print(f"Buy volume:          {str(buy_cost):>24} | {str(buy_cost // 10 ** 5 / 10):>6}M | "
          f"{str(buy_cost // 10 ** 2 / 10):>6}K | {str(buy_part):>4}%")
    print(f"Sell volume:         {str(sell_cost):>24} | {str(sell_cost // 10 ** 5 / 10):>6}M | "
          f"{str(sell_cost // 10 ** 2 / 10):>6}K | {str(sell_part):>4}%")
    print("\nOrders in process cost:", orders_in_process['orders_new_cost'])
    print('Cost limit', cost_limit)

    if len(orders_in_process['orders_pending']) > 0:
        new_order_from_pending_db(orders_in_process['orders_pending'])
    elif (float(web_socket.kline_last['all_cost']) > float(spot_client.last_kline['sum']["all_cost"]
                                                           ) / float(spot_client.last_kline['sum']["amount"])) and (
            float(web_socket.kline_last['buy_cost']) > float(web_socket.kline_last["all_cost"]) * 0.6) and (
            orders_in_process['orders_new_cost'] < cost_limit
    ):
        print("\nUP > custom_buy_div=0.2")
        trade_process(custom_buy_div=0.2, custom_cost_limit=custom_cost_limit)

    elif (float(web_socket.kline_last['all_cost']) > float(spot_client.last_kline['sum']["all_cost"]) / 48 * 0.8) and (
            float(web_socket.kline_last['sell_cost']) > float(web_socket.kline_last["all_cost"]) * 0.6) and (
            orders_in_process['orders_new_cost'] < cost_limit
    ):
        print("\nDOWN > custom_buy_div=0.8")
        trade_process(custom_buy_div=0.8, custom_cost_limit=custom_cost_limit)


def symbol_if_buy_kline(symbol, symbol_sqlh: SQLiteHandler, side, profit=0.3, pending_only=False):
    """
    :param symbol: str                  | "BTCUSDT"
    :param symbol_sqlh: SQLiteHandler
    :param side: str                    | "BUY", "SELL"
    :param profit: float                | 0.3 -> 0.3 %  \\  1 -> 1 %
    :param pending_only: bool
    :return:
    """

    # Getting and sorting all orders
    orders_in_process = get_orders_in_process_from_db(symbol_sqlh=symbol_sqlh)
    list_of_orders_to_dataframe(
        orders_in_process['orders_new'],
        header='--- New orders ---------------------------',
        key_to_print=True,
        sort_col='price',
        ascending=True,
        reset_index=True
    )

    # Parameters for pending_only
    all_new_orders_cost, symbol_new_orders_cost = cost_limit * 2, symbol_cost_limit * 2
    if not pending_only:
        # Calculating parameters
        all_new_orders = spot_client.get_orders_to_db(open_only=True, all_symbols=True)
        all_new_orders_cost = 0
        for order in all_new_orders:
            all_new_orders_cost = float(all_new_orders_cost) + float(order['cost'])
        symbol_new_orders_cost = float(orders_in_process["orders_new_cost"])

        # Output
        output = f"\nAll orders in process cost:        {all_new_orders_cost}" \
                 f"\nSymbol orders in process cost:     {symbol_new_orders_cost}" \
                 f"\nCost limit:    {cost_limit} | Symbol cost limit: {symbol_cost_limit}"
        print(output)

    # Trade process // There are pending orders -> New order from pending orders
    if len(orders_in_process['orders_pending']) > 0:
        new_order_from_pending_db(orders_in_process['orders_pending'])

    # There are no pending orders -> New order
    elif (all_new_orders_cost < cost_limit) and (symbol_new_orders_cost < symbol_cost_limit) and not pending_only:
        if side == "BUY":
            symbol_trading_process(symbol, symbol_sqlh, custom_buy_div=0.05, custom_cost_limit=symbol_cost_limit, custom_profit_percent=profit)
        elif side == "SELL":
            symbol_trading_process(symbol, symbol_sqlh, custom_buy_div=0.95, custom_cost_limit=symbol_cost_limit, custom_profit_percent=profit)


def kline_sum(klines):
    """
    return {
        "symbol"\n
        "start_time",\n
        "start_time_utc",\n
        "close_time",\n
        "close_time_utc",\n
        "interval",\n
        "open_price",\n
        "close_price",\n
        "high_price",\n
        "low_price",\n
        "number_of_trades",\n
        "all_origQty",\n
        "all_cost",\n
        "buy_origQty",\n
        "buy_cost",\n
        "sell_origQty",\n
        "sell_cost",\n
        "amount"
    }

    :param klines:
    :return: dict
    """
    sum_of_klines = {
        "symbol": klines[0]["symbol"],
        "start_time": klines[0]['start_time'],
        "start_time_utc": klines[0]['start_time_utc'],
        "close_time": klines[-1]['close_time'],
        "close_time_utc": klines[-1]['close_time_utc'],
        "interval": klines[0]['interval'],
        "open_price": klines[0]['open_price'],
        "close_price": klines[-1]['close_price'],
        "high_price": klines[0]['high_price'],
        "low_price": klines[0]['low_price'],
        "number_of_trades": '0',
        "all_origQty": '0',
        "all_cost": '0',
        "buy_origQty": '0',
        "buy_cost": '0',
        "sell_origQty": '0',
        "sell_cost": '0',
    }
    for kline in klines:
        if Decimal(kline['high_price']) > Decimal(sum_of_klines['high_price']):
            sum_of_klines.update({"high_price": kline['high_price']})

        if Decimal(kline['low_price']) < Decimal(sum_of_klines['low_price']):
            sum_of_klines.update({"low_price": kline['low_price']})

        sum_of_klines.update(
            {
                "number_of_trades": int(sum_of_klines['number_of_trades']) + int(kline['number_of_trades'])
            }
        )

        sum_of_klines.update(
            {
                "all_origQty": (Decimal(str(sum_of_klines['all_origQty'])) +
                                Decimal(str(kline['all_origQty']))).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ),
            }
        )

        sum_of_klines.update(
            {
                "all_cost": (Decimal(str(sum_of_klines['all_cost'])) +
                             Decimal(str(kline['all_cost']))).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ),
            }
        )

        sum_of_klines.update(
            {
                "buy_origQty": (Decimal(str(sum_of_klines['buy_origQty'])) +
                                Decimal(str(kline['buy_origQty']))).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ),
            }
        )

        sum_of_klines.update(
            {
                "buy_cost": (Decimal(str(sum_of_klines['buy_cost'])) +
                             Decimal(str(kline['buy_cost']))).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ),
            }
        )

        sum_of_klines.update(
            {
                "sell_origQty": (Decimal(str(sum_of_klines['sell_origQty'])) +
                                 Decimal(str(kline['sell_origQty']))).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ),
            }
        )

        sum_of_klines.update(
            {
                "sell_cost": (Decimal(str(sum_of_klines['sell_cost'])) +
                              Decimal(str(kline['sell_cost']))).quantize(
                    Decimal('0.00000000'),
                    rounding=ROUND_HALF_UP
                ),
            }
        )

    sum_of_klines.update({'amount': len(klines)})
    return sum_of_klines


def kline_params(kline, sum_kline):
    """
    return {
        "changing",\n
        "direction",\n
        "volume_part",\n
    }
    :param kline: 
    :param sum_kline: 
    :return: 
    """
    kline_params = {}

    with localcontext() as local_context:
        # Setting precision of decimal calculations
        local_context.prec = 8

        # Changing
        changing = (Decimal(kline["close_price"]) - Decimal(kline["open_price"])) / Decimal(kline["close_price"])
        kline_params.update({"changing": changing})

        # Direction
        if changing < 0:
            kline_params.update({"direction": 'DOWN'})
            kline_params.update({"changing": -changing})
        else:
            kline_params.update({"direction": 'UP'})

        # Volume part
        volume_part = Decimal(kline["all_cost"]) * Decimal(sum_kline["amount"]) / Decimal(sum_kline["all_cost"])
        kline_params.update({"volume_part": volume_part})

    return kline_params


def monitoring_symbol(sum_kline, filters, monitoring_time=30):
    """
    :param monitoring_time: int     | sec
    :param filters:
    :param sum_kline: kline_sum(klines)
    :return:
    """
    symbol = sum_kline["symbol"]
    print(f"\n{Tags.LightYellow}Start monitoring {symbol}{Tags.ResetAll}")

    # Getting balance
    current_state = spot_client.get_current_state(symbol, first_symbol=symbol[:-4], second_symbol=symbol[-4:])

    # If I have enough quantity
    with localcontext() as local_context:

        # Setting precision of decimal calculations
        local_context.prec = 8

        min_quantity = Decimal(filters['MIN_NOTIONAL_minNotional']) * Decimal('1.1') / (
            Decimal(current_state['order_book_bid_current_price']))

        if_enough = min_quantity < Decimal(current_state['balance_first_symbol_free_value'])

    counter_limit = monitoring_time // 2
    not_ready = True
    counter = 0
    state_value = 0
    while (counter < counter_limit) and not_ready:
        counter += 1

        # Getting klines with params
        klines = spot_client.get_kline(
            symbol=symbol,
            interval="1m",
            limit=3
        )
        third_kline = {"kline": klines['klines'][-3]}
        third_kline.update(kline_params(third_kline["kline"], sum_kline))
        second_kline = {"kline": klines['klines'][-2]}
        second_kline.update(kline_params(second_kline["kline"], sum_kline))
        last_kline = {"kline": klines['klines'][-1]}
        last_kline.update(kline_params(last_kline["kline"], sum_kline))

        # Conditions for starting operations // Up
        if (last_kline['direction'] == "UP") and (second_kline['direction'] == last_kline['direction']):

            # Small body
            if last_kline["changing"] < 0.001:

                # Probably will change direction or changing will be near zero
                if (second_kline['changing'] > 0.002) and (third_kline['changing'] > 0.002) and (
                        third_kline['direction'] == "UP"):
                    state_value = 0

                # Probably will be growing or changing will be near zero
                elif (second_kline['changing'] > 0.002) and (third_kline['changing'] > 0.002) and (
                        third_kline['direction'] == "DOWN"):
                    state_value = 20

                # Probably changing will be near zero
                elif (second_kline['changing'] < 0.002) or (third_kline['changing'] < 0.002):
                    state_value = 0

                if counter > 4:
                    not_ready = False

            # Still growing and bigger // good condition to buy
            elif last_kline["changing"] > second_kline["changing"]:
                state_value = 100

            # Still growing but smaller // not bad condition to buy
            elif last_kline["changing"] < second_kline["changing"]:
                state_value = 80

        # Down // only if I have some
        elif (last_kline['direction'] == "DOWN") and (
                second_kline['direction'] == last_kline['direction']) and if_enough:

            # Small body
            if last_kline["changing"] < 0.001:

                # Probably will change direction or changing will be near zero
                if (second_kline['changing'] > 0.002) and (third_kline['changing'] > 0.002) and (
                        third_kline['direction'] == "DOWN"):
                    state_value = 0

                # Probably will be falling or changing will be near zero
                elif (second_kline['changing'] > 0.002) and (third_kline['changing'] > 0.002) and (
                        third_kline['direction'] == "UP"):
                    state_value = -20

                # Probably changing will be near zero
                elif (second_kline['changing'] < 0.002) or (third_kline['changing'] < 0.002):
                    state_value = 0

            # Still falling and bigger // good condition to sell
            elif last_kline["changing"] > second_kline["changing"]:
                state_value = -100

            # Still falling but smaller // not bad condition to sell
            elif last_kline["changing"] < second_kline["changing"]:
                state_value = -80

        elif (last_kline['direction'] == "DOWN") and not if_enough:
            state_value = 0
            print(f"Falling and if_enough={if_enough}")
            break

        if (state_value > 70) or (state_value < -70):
            not_ready = False

        # Output
        header = f"--- Monitoring time: {str(counter * 2):>4}s / {str(counter_limit * 2):>4}s | " \
                 f"State value: {state_value} ------------"
        orders_df = pd.DataFrame(
            [last_kline, second_kline, third_kline],
            columns=["changing", "direction", "volume_part"]
        )
        orders_df['changing'] = orders_df['changing'] * 100
        print(f'\n{Tags.LightBlue}{header}{Tags.ResetAll}\n{orders_df}')

        sleep(2.1)

    return state_value

    # END // movement anchor

    # END // movement anchor


def checking_symbol_history(symbol):
    klines = web_socket.kline_history[symbol]
    sum_kline = kline_sum(klines)

    # Conditions
    with localcontext() as local_context:

        # Counting amount of large volume of 15 last klines
        lv_ratio = "2.5"
        amount_of_large_volumes = 0
        sum_10_last_klines = kline_sum(klines[-10:])

        if (
                (Decimal(sum_kline['amount']) == Decimal("0")) or
                (Decimal(sum_10_last_klines['amount']) == Decimal("0")) or
                (Decimal(sum_10_last_klines['all_origQty']) == Decimal("0"))
        ):
            return -666

        for kline in klines[-10:]:
            if Decimal(kline["all_cost"]) > Decimal(sum_kline['all_cost']) * Decimal(lv_ratio) / Decimal(
                    sum_kline['amount']):
                amount_of_large_volumes += 1

        # Setting precision of decimal calculations
        local_context.prec = 8

        # If amount of large volumes more than 4
        if_large_volume = amount_of_large_volumes > 4

        # If last klines have small amount of trades
        smota_ratio = "0.5"
        average_num_of_trades = Decimal(sum_kline['number_of_trades']) / Decimal(sum_kline['amount'])
        average_last_num_of_trades = Decimal(sum_10_last_klines["number_of_trades"]) / Decimal(
            sum_10_last_klines['amount'])
        if_small_amount_of_trades_number = average_num_of_trades * Decimal(smota_ratio) > average_last_num_of_trades

        # If order book has disbalance of orders' sides
        sd_ratio = "0.65"
        buy_quantity_part = Decimal(sum_10_last_klines['buy_origQty']) / Decimal(sum_10_last_klines['all_origQty'])
        sell_quantity_part = Decimal(sum_10_last_klines['sell_origQty']) / Decimal(sum_10_last_klines['all_origQty'])
        if_sides_disbalance = (1 - buy_quantity_part > Decimal(sd_ratio)) or (
                1 - sell_quantity_part > Decimal(sd_ratio))

        # If 2 last klines have large changing
        changing_ratio = Decimal("0.25") / Decimal("100")
        if_two_last_changing_is_large = False
        for kline in klines[-2:]:
            if (Decimal(kline['open_price']) - Decimal(kline['close_price'])) / Decimal(
                    kline['open_price']) > changing_ratio:
                if_two_last_changing_is_large = True
            elif (Decimal(kline['close_price']) - Decimal(kline['open_price'])) / Decimal(
                    kline['close_price']) > changing_ratio:
                if_two_last_changing_is_large = True

    output = f"Amount of large volumes: " \
             f"{Tags.BackgroundDarkGray}{amount_of_large_volumes} > 4 (x{lv_ratio}){Tags.ResetAll}" \
             f" -> {if_large_volume}" \
             f"\nAverage NoT * {smota_ratio}: " \
             f"{Tags.BackgroundDarkGray}{average_num_of_trades} > {average_last_num_of_trades}{Tags.ResetAll}" \
             f" :Average last NoT -> {if_small_amount_of_trades_number}" \
             f"\nChanging more then: " \
             f"{Tags.BackgroundDarkGray}{changing_ratio * 100}%{Tags.ResetAll}" \
             f" -> {if_two_last_changing_is_large}" \
             f"\nbuy_quantity_part: " \
             f"{Tags.BackgroundDarkGray}{buy_quantity_part} | {sell_quantity_part}{Tags.ResetAll}" \
             f" :sell_quantity_part -> {if_sides_disbalance}"

    # More preferable conditions are located above
    if if_large_volume and if_small_amount_of_trades_number and if_two_last_changing_is_large and if_sides_disbalance:
        print(f"\n{Tags.BackgroundLightYellow}{klines[0]['symbol']}{Tags.ResetAll}")
        print(output)
        return 20

    elif if_two_last_changing_is_large and if_small_amount_of_trades_number and if_sides_disbalance:
        print(f"\n{Tags.BackgroundRed}{klines[0]['symbol']}{Tags.ResetAll}")
        print(output)
        return 10

    elif if_large_volume and if_sides_disbalance:
        print(f"\n{Tags.BackgroundMagenta}{klines[0]['symbol']}{Tags.ResetAll}")
        print(output)
        return 0
    else:
        return -666

    # END // movement anchor

    # END // movement anchor


# ===== Base logic modes =============================================================== Base logic modes ======
...
# ===== Base logic modes =============================================================== Base logic modes ======


def id_arg_1():
    pass


def id_arg_2(db_name, db_dir):
    web_socket.stream_execution_reports(db_name=db_name, db_dir=db_dir)
    web_socket.kline_output_key = False
    web_socket.stream_kline()

    spot_client.get_current_state()
    spot_client.str_current_state()
    if len(spot_client.current_state_data) > 0:
        sqlh.insert_from_dict('current_state', spot_client.current_state_data)

    spot_client.get_exchange_info()
    if len(spot_client.filters) > 0:
        sqlh.insert_from_dict('filters', spot_client.filters)
    else:
        print("[ERROR] Can't get filters")
        sys.exit(1)

    # Getting 24h kline
    spot_client.get_kline(interval='1h', limit=24, output_key=True, if_sum=True)

    update_orders_db()

    # Waiting for first kline
    if web_socket.kline_last is None:
        print("Waiting for first kline:")
        while web_socket.kline_last is not None:
            sleep(1)
            print(".", end='')

    # Mode base logic
    renew_listen_key_counter = 0
    while True:
        print(f'{Tags.BackgroundLightYellow}{Tags.Black}'
              f'\n      Scheduled if_buy_kline'
              f'{Tags.ResetAll}')
        if_buy_kline()

        # Updating listen_key
        if renew_listen_key_counter >= 15:
            spot_client.renew_listen_key(spot_client.listen_key)
            renew_listen_key_counter = 0
            print("listen_key is updated!")

        # Printing header before sleeping
        resp_type_pr = f'---- UTC time -------------------------------------- ' \
                       f'{str(datetime.utcfromtimestamp(int(time.time()))):<20}' \
                       f' ----'
        print(f'\n{Tags.LightBlue}{resp_type_pr}{Tags.ResetAll}')
        print(f'Waiting {loop_waiting} sec')
        sleep(loop_waiting)

        # Updating current_state
        while_counter = 0
        while while_counter < 6:
            try:
                spot_client.get_current_state()
                spot_client.str_current_state()
                if len(spot_client.current_state_data) > 0:
                    sqlh.insert_from_dict('current_state', spot_client.current_state_data)

                update_orders_db()
                while_counter = 20

            except Exception as _ex:
                print("[ERROR] start_bot_logic > id_arg == 2 > ", _ex)
                while_counter += 1
                time.sleep(randint(1, 10))

        renew_listen_key_counter += 1
        print("renew_listen_key_counter: ", renew_listen_key_counter)


def id_arg_3():
    web_socket.stream_user_data()
    renew_listen_key_counter = 0

    while True:

        if renew_listen_key_counter >= 15:
            spot_client.renew_listen_key(spot_client.listen_key)
            renew_listen_key_counter = 0
            print("listen_key is updated!")

        sleep(loop_waiting)
        renew_listen_key_counter += 1


def id_arg_4(db_name, db_dir):
    web_socket.stream_execution_reports(db_name=db_name, db_dir=db_dir)

    spot_client.get_current_state()
    spot_client.str_current_state()
    if len(spot_client.current_state_data) > 0:
        sqlh.insert_from_dict('current_state', spot_client.current_state_data)

    spot_client.get_exchange_info()
    if len(spot_client.filters) > 0:
        sqlh.insert_from_dict('filters', spot_client.filters)
    else:
        print("[ERROR] Can't get filters")
        sys.exit(1)

    # print("DEBUG")
    # spot_client.cancel_all_new_orders()
    # print("CLOSED")
    # sleep(30)

    update_orders_db()

    renew_listen_key_counter = 0
    while True:

        # Mode base logic
        print(f'{Tags.BackgroundLightYellow}{Tags.Black}'
              f'\n      Scheduled if_buy'
              f'{Tags.ResetAll}')
        if_buy()

        # Updating listen_key
        if renew_listen_key_counter >= 15:
            spot_client.renew_listen_key(spot_client.listen_key)
            renew_listen_key_counter = 0
            print("listen_key is updated!")

        # Printing header before sleeping
        resp_type_pr = f'---- UTC time -------------------------------------- ' \
                       f'{str(datetime.utcfromtimestamp(int(time.time()))):<20}' \
                       f' ----'
        print(f'\n{Tags.LightBlue}{resp_type_pr}{Tags.ResetAll}')
        print(f'Waiting {loop_waiting} sec')
        sleep(loop_waiting)

        # Updating current_state
        while_counter = 0
        while while_counter < 6:
            try:
                spot_client.get_current_state()
                spot_client.str_current_state()
                if len(spot_client.current_state_data) > 0:
                    sqlh.insert_from_dict('current_state', spot_client.current_state_data)

                update_orders_db()
                while_counter = 20

            except Exception as _ex:
                print("[ERROR] start_bot_logic > id_arg == 4 > ", _ex)
                while_counter += 1
                time.sleep(randint(1, 10))

        renew_listen_key_counter += 1
        print("renew_listen_key_counter: ", renew_listen_key_counter)


def id_arg_5():
    web_socket.stream_trades()

    while True:
        sleep(loop_waiting)


def id_arg_6():
    web_socket.stream_agg_trades()

    while True:
        sleep(5)
        print()


def id_arg_7(test_key=False):

    if test_key:
        if os.path.exists("getting_data/test_symbols.txt"):
            with open('getting_data/test_symbols.txt', 'r') as f:
                symbols_list_form_file = f.read()
                symbols_list_form_file = [x.strip("[',]").strip() for x in symbols_list_form_file.split(' ')]
        else:
            exchange_info = spot_client.exchange_info()
            symbols_list_form_file = []
            for item in exchange_info["symbols"]:
                if item["symbol"][:-4] not in symbols_list_form_file:
                    symbols_list_form_file.append(item["symbol"][:-4])
            if len(symbols_list_form_file) > 0:
                with open('getting_data/test_symbols.txt', 'w') as f:
                    f.write(str(symbols_list_form_file))
    else:
        with open('getting_data/symbols.txt', 'r') as f:
            symbols_list_form_file = f.read()
            symbols_list_form_file = [x.strip("[',]").strip() for x in symbols_list_form_file.split(' ')]

    # Creating symbol pairs list
    symbols_list = []
    for symbol in symbols_list_form_file:
        symbol += "USDT"
        symbols_list.append(symbol)

    # Getting filters
    print(f"\n{Tags.LightYellow}Getting filters{Tags.ResetAll}")
    filters_list = {}
    symbols_list_to_delete = []
    for symbol in symbols_list:
        try:
            filters = spot_client.get_exchange_info(symbol)
            filters_list.update({symbol: filters})
            print(f"Filters for {symbol} are got")
        except ClientError as _ex:
            print(f"\n{Tags.LightYellow}[WARNING] Getting filters > {_ex.error_message} > "
                  f"{symbol} is removed from the symbol_list{Tags.ResetAll}")
            symbols_list_to_delete.append(symbol)
            continue
    symbols_list = [item for item in symbols_list if item not in symbols_list_to_delete]
    spot_client.filters_list = filters_list

    # Creating SQLiteHandler for all symbols
    for symbol in symbols_list:
        db_name = create_db_name(symbol, test_key=test_key)
        sqlh_symbol = SQLiteHandler(db_name=db_name, db_dir=db_dir, check_same_thread=False)
        sqlh_dict.update({symbol: sqlh_symbol})
        sqlh_dict[symbol].create_all_tables(tables.create_all_tables)

    # Creating streams
    print(f"\n{Tags.LightYellow}Creating streams{Tags.ResetAll}")

    # Creating stream _execution_reports
    stream_id = randint(1, 99999)
    print(f"Stream: _execution_reports; ID: {stream_id}")
    web_socket.kline_output_key = False
    web_socket.stream_execution_reports(sqlh_dict=sqlh_dict)
    sleep(0.3)

    # Creating streams _kline_history
    for symbol in symbols_list:
        try:
            stream_id = randint(1, 99999)
            print(f"Stream: {symbol}; ID: {stream_id}")
            web_socket.kline_output_key = False
            web_socket.stream_kline_history(symbol=symbol, stream_id=stream_id)
            sleep(0.3)
        except ClientError as _ex:
            print(f"\n{Tags.LightYellow}[WARNING] Creating streams > {_ex.error_message} > "
                  f"{symbol} is removed from the symbol_list{Tags.ResetAll}")
            symbols_list_to_delete.append(symbol)
    symbols_list = [item for item in symbols_list if item not in symbols_list_to_delete]

    # Getting 1h klines
    sleep(3)
    print(f"\n{Tags.LightYellow}Getting 1h klines{Tags.ResetAll}")
    kline_1h_list = {}
    for symbol in symbols_list:
        try:
            kline_1h = spot_client.get_kline(
                symbol=symbol,
                interval='1m',
                limit=60,
                output_key=True,
                if_sum=True
            )
            kline_1h_list.update({symbol: kline_1h})
            web_socket.kline_history[symbol] = kline_1h['klines']
            sleep(0.3)
        except ClientError as _ex:
            print(f"\n{Tags.LightYellow}[WARNING] Getting 24h klines > {_ex.error_message} > "
                  f"{symbol} is removed from the symbol_list{Tags.ResetAll}")
            symbols_list_to_delete.append(symbol)
    symbols_list = [item for item in symbols_list if item not in symbols_list_to_delete]

    # The base mode logic
    sleep(3)
    # The cycle is for the base logic repeating every {loop_waiting} time
    print(f"\n{Tags.LightYellow}Starting the base mode logic{Tags.ResetAll}")
    symbols_to_skip = []
    while True:

        # Checking if symbol is ready to trade process
        checked_symbols = {}
        for symbol in symbols_list:
            checked_symbols.update({symbol: checking_symbol_history(symbol)})

        # # Symbol state // monitoring
        # symbol_state = 0
        # symbol_to_trade = None
        # if 20 in checked_symbols.values():
        #     for symbol in checked_symbols.keys():
        #         if checked_symbols[symbol] == 20:
        #             symbol_state = monitoring_symbol(kline_1h_list[symbol]["sum"], filters_list[symbol])
        #             if (symbol_state > 70) or (symbol_state < -70):
        #                 print(f"\n{Tags.BackgroundBlue}{Tags.Reverse}Symbol state: {symbol_state}{Tags.ResetAll}")
        #                 symbol_to_trade = symbol
        #             else:
        #                 print(f"\n{Tags.BackgroundDarkGray}{Tags.Reverse}Symbol state: {symbol_state}{Tags.ResetAll}")
        #             break
        #
        # elif 10 in checked_symbols.values():
        #     for symbol in checked_symbols.keys():
        #         if checked_symbols[symbol] == 10:
        #             symbol_state = monitoring_symbol(kline_1h_list[symbol]["sum"], filters_list[symbol])
        #             if (symbol_state > 70) or (symbol_state < -70):
        #                 print(f"\n{Tags.BackgroundBlue}{Tags.Reverse}Symbol state: {symbol_state}{Tags.ResetAll}")
        #                 symbol_to_trade = symbol
        #             else:
        #                 print(f"\n{Tags.BackgroundDarkGray}{Tags.Reverse}Symbol state: {symbol_state}{Tags.ResetAll}")
        #             break
        #
        # elif 0 in checked_symbols.values():
        #     for symbol in checked_symbols.keys():
        #         if (checked_symbols[symbol] == 0) and (symbol not in symbols_to_skip):
        #             symbol_state = monitoring_symbol(
        #                 kline_1h_list[symbol]["sum"],
        #                 filters_list[symbol],
        #                 monitoring_time=16
        #             )
        #             if (symbol_state > 70) or (symbol_state < -70):
        #                 print(f"\n{Tags.BackgroundBlue}{Tags.Reverse}Symbol state: {symbol_state}{Tags.ResetAll}")
        #                 symbol_to_trade = symbol
        #             else:
        #                 print(f"\n{Tags.BackgroundDarkGray}{Tags.Reverse}Symbol state: {symbol_state}{Tags.ResetAll}")
        #             if symbol_state != 0:
        #                 break
        #
        # # Trade process // symbol = [100, 80, 20, 0, -20, -80, -100]
        # if symbol_state == 100:
        #     symbol_if_buy_kline(symbol_to_trade, sqlh_dict[symbol_to_trade], side="BUY", profit=0.5)
        # elif symbol_state == 80:
        #     symbol_if_buy_kline(symbol_to_trade, sqlh_dict[symbol_to_trade], side="BUY", profit=0.4)
        # elif symbol_state == -80:
        #     # TODO: if_buy
        #     pass
        # elif symbol_state == -100:
        #     # TODO: if_buy
        #     pass
        # elif test_key:
        #     side_test_list = ["BUY", "SELL"]
        #     side_test = side_test_list[randint(0, len(side_test_list) - 1)]
        #     symbol_to_trade = symbols_list[randint(0, len(symbols_list) - 1)]
        #     symbol_if_buy_kline(symbol_to_trade, sqlh_dict[symbol_to_trade], side=side_test, profit=0.4)

        # Checking pending orders for all symbols
        for symbol in symbols_list:
            symbol_if_buy_kline(symbol, sqlh_dict[symbol], side="PENDING", pending_only=True)

        # TODO: if there is pending pair > check how long > cancel pair ???

        # Printing header before sleeping
        resp_type_pr = f'---- UTC time -------------------------------------- ' \
                       f'{str(datetime.utcfromtimestamp(int(time.time()))):<20}' \
                       f' ----'
        print(f'\n{Tags.LightBlue}{resp_type_pr}{Tags.ResetAll}')
        print(f'Waiting {loop_waiting} sec')
        sleep(loop_waiting)

    # END // movement anchor

    # END // movement anchor


def start_bot_logic():
    """TODO cancel all orders with db updating"""
    """
        id_arg = 1 > web_socket.stream_ticker() > TODO ERROR
        id_arg = 2 > web_socket.stream_kline() based
        id_arg = 3 > web_socket.stream_user_data()
        id_arg = 4 > web_socket.stream_execution_reports() based
        id_arg = 5 > web_socket.stream_trades()
        id_arg = 6 > web_socket.stream_agg_trades()
    """

    # Parsing arguments
    try:
        parser = argparse.ArgumentParser(description='Binance app')
        parser.add_argument('--first-symbol', dest='first_symbol', default='BTC',
                            help='Symbol of token to buy Ex: "BTC"')
        parser.add_argument('--second-symbol', dest='second_symbol', default='USDT',
                            help='Symbol of token as money Ex: "USDT"')
        parser.add_argument('--id', dest='id', default=5,
                            help='Id of callback Ex: 5')
        parser.add_argument('--test', dest='test_key', nargs='?', const=True, default=False,
                            help='Enable test mode')
        parser.add_argument('--force-url', dest='force_url', nargs='?', const=True, default=False,
                            help="Enable force url for Spot and Websocket (in the test mode has no effect")
        args = parser.parse_args()

        first_symbol = args.first_symbol
        second_symbol = args.second_symbol
        id_arg = int(args.id)
        test_key = args.test_key
        force_url = args.force_url

        print(
            '\nfirst_symbol:', first_symbol,
            '\nsecond_symbol:', second_symbol,
            '\nid_arg:', id_arg,
            '\ntest_key:', test_key,
            '\nforce_url:', force_url,
        )

        if not os.path.exists(f"{db_dir}"):
            os.mkdir(db_dir)
        db_name = create_db_name(symbol=f"{first_symbol}{second_symbol}", test_key=test_key)

        global spot_client
        global web_socket
        global sqlh

    except Exception as _ex:
        print("[ERROR] Parsing arguments >", _ex)
        sys.exit(1)

    # launching the mode logic
    if id_arg == 1:
        # TODO ???
        print('[ERROR] TODO')
        sys.exit(1)

        # web_socket = WebsocketClient(
        #     test_key=test_key,
        #     force_url=force_url,
        #     low_permissions=True,
        #     first_symbol=first_symbol,
        #     second_symbol=second_symbol
        # )
        #
        # try:
        #     web_socket.stream_trades()
        #
        #     while True:
        #
        #         sleep(loop_waiting)
        #
        # except KeyboardInterrupt:
        #     ...
        # finally:
        #     web_socket.stop()
        #     print(f'\n{Tags.LightYellow}WebSocket is stopped{Tags.ResetAll}')
        #     print("Sleep 5 sec:")
        #     for counter in range(1, 6):
        #         print('Sleep progress: ', end='')
        #         print("." * counter)
        #         sleep(1)

    elif id_arg == 2:

        spot_client = SpotClient(
            test_key=test_key,
            force_url=force_url,
            first_symbol=first_symbol,
            second_symbol=second_symbol
        )

        web_socket = WebsocketClient(
            test_key=test_key,
            force_url=force_url,
            low_permissions=True,
            listen_key=spot_client.listen_key,
            first_symbol=first_symbol,
            second_symbol=second_symbol
        )

        sqlh = SQLiteHandler(db_name=db_name, db_dir=base_path)
        sqlh.create_all_tables(tables.create_all_tables)

        try:
            id_arg_2(db_name=db_name, db_dir=base_path)
        except KeyboardInterrupt:
            ...
        finally:
            web_socket.stop()
            print(f'\n{Tags.LightYellow}WebSocket is stopped{Tags.ResetAll}')
            print("Sleep 5 sec:")
            for counter in range(1, 6):
                print('Sleep progress: ', end='')
                print("." * counter)
                sleep(1)

    elif id_arg == 3:

        spot_client = SpotClient(
            test_key=test_key,
            force_url=force_url,
            low_permissions=True,
            first_symbol=first_symbol,
            second_symbol=second_symbol
        )

        web_socket = WebsocketClient(
            test_key=test_key,
            force_url=force_url,
            low_permissions=True,
            first_symbol=first_symbol,
            second_symbol=second_symbol,
            listen_key=spot_client.listen_key
        )

        try:
            id_arg_3()
        except KeyboardInterrupt:
            ...
        finally:
            web_socket.stop()
            print(f'\n{Tags.LightYellow}WebSocket is stopped{Tags.ResetAll}')
            print("Sleep 5 sec:")
            for counter in range(1, 6):
                print('Sleep progress: ', end='')
                print("." * counter)
                sleep(1)

    elif id_arg == 4:

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

        sqlh = SQLiteHandler(db_name=db_name, db_dir=base_path)
        sqlh.create_all_tables(tables.create_all_tables)

        try:
            id_arg_4(db_name=db_name, db_dir=base_path)
        except KeyboardInterrupt:
            ...
        finally:
            web_socket.stop()
            print(f'\n{Tags.LightYellow}WebSocket is stopped{Tags.ResetAll}')
            sqlh.close()
            print(f'\n{Tags.LightYellow}SQL handler closed{Tags.ResetAll}')
            print("Sleep 5 sec:")
            for counter in range(1, 6):
                print('Sleep progress: ', end='')
                print("." * counter)
                sleep(1)

    elif id_arg == 5:

        web_socket = WebsocketClient(
            test_key=test_key,
            force_url=force_url,
            low_permissions=True,
            first_symbol=first_symbol,
            second_symbol=second_symbol
        )

        try:
            id_arg_5()
        except KeyboardInterrupt:
            ...
        finally:
            web_socket.stop()
            print(f'\n{Tags.LightYellow}WebSocket is stopped{Tags.ResetAll}')
            print("Sleep 5 sec:")
            for counter in range(1, 6):
                print('Sleep progress: ', end='')
                print("." * counter)
                sleep(1)

    elif id_arg == 6:

        web_socket = WebsocketClient(
            test_key=test_key,
            force_url=force_url,
            low_permissions=True,
            first_symbol=first_symbol,
            second_symbol=second_symbol
        )

        try:
            id_arg_6()
        except KeyboardInterrupt:
            ...
        finally:
            web_socket.stop()
            print(f'\n{Tags.LightYellow}WebSocket is stopped{Tags.ResetAll}')
            print("Sleep 5 sec:")
            for counter in range(1, 6):
                print('Sleep progress: ', end='')
                print("." * counter)
                sleep(1)

    elif id_arg == 7:
        # TODO: update list of symbols
        # TODO: check db when bot is starting

        spot_client = SpotClient(
            test_key=test_key,
            force_url=force_url,
        )

        web_socket = WebsocketClient(
            test_key=test_key,
            force_url=force_url,
            listen_key=spot_client.listen_key
        )

        try:
            id_arg_7(test_key=test_key)
        except KeyboardInterrupt:
            ...
        finally:
            print(f'\n{Tags.LightYellow}WebSocket stopping{Tags.ResetAll}')
            web_socket.stop()
            print("Sleep 5 sec:")
            for counter in range(1, 6):
                print('Sleep progress: ', end='')
                print("." * counter)
                sleep(1)

    else:
        print("[ERROR] start_bot_logic > id_arg is out of range | expected 2 or 6")
        print("id_arg = 1 > web_socket.stream_ticker() > [ERROR] TODO")
        print("id_arg = 2 > web_socket.stream_kline()")
        print("id_arg = 3 > web_socket.stream_user_data() > just for inform")
        print("id_arg = 4 > web_socket.stream_execution_reports() > sell/buy")
        print("id_arg = 5 > web_socket.stream_trades()")
        print("id_arg = 6 > web_socket.stream_agg_trades()")
        print("id_arg = 7 > web_socket.stream_agg_trades() > symbols from file ")


if __name__ == '__main__':
    start_bot_logic()
