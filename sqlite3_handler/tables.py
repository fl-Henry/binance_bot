
create_table__orders = """
    CREATE TABLE IF NOT EXISTS orders (
        pk INTEGER PRIMARY KEY,
        symbol TEXT NOT NULL DEFAULT NULL,
        orderId INTEGER,
        price TEXT NOT NULL DEFAULT NULL,
        origQty TEXT NOT NULL DEFAULT NULL,
        cost TEXT NOT NULL DEFAULT NULL,
        side TEXT NOT NULL DEFAULT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        type TEXT ,
        timeInForce TEXT ,
        workingTime INTEGER
    );
"""

drop_table__orders = """
    DROP TABLE orders ;
"""

columns__orders = [
            'symbol',
            'orderId',
            'price',
            'origQty',
            'cost',
            'side',
            'status',
            'type',
            'timeInForce',
            'workingTime'
        ]


def str__orders(data):
    return f"[{data.symbol}] P:{data.price}; Q:{data.origQty}; C:{data.cost}; Si:{data.side}; St:{data.status};"


create_table__pending_orders = """
    CREATE TABLE IF NOT EXISTS pending_orders (
        pk INTEGER PRIMARY KEY,
        symbol TEXT NOT NULL DEFAULT NULL,
        orderId INTEGER,
        price TEXT NOT NULL DEFAULT NULL,
        origQty TEXT NOT NULL DEFAULT NULL,
        cost TEXT NOT NULL DEFAULT NULL,
        side TEXT NOT NULL DEFAULT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        type TEXT ,
        timeInForce TEXT ,
        workingTime INTEGER
    );
"""

columns__pending_orders = [
            'symbol',
            'orderId',
            'price',
            'origQty',
            'cost',
            'side',
            'status',
            'type',
            'timeInForce',
            'workingTime'
        ]


def str__pending_orders(data):
    return f"[{data.symbol}] P:{data.price}; Q:{data.origQty}; C:{data.cost}; Si:{data.side}; St:{data.status};"


create_table__orders_pair = """
    CREATE TABLE IF NOT EXISTS orders_pair (
        buy_order_pk INTEGER,
        sell_order_pk INTEGER,
        FOREIGN KEY (buy_order_pk) REFERENCES pending_orders (pk), 
        FOREIGN KEY (sell_order_pk) REFERENCES pending_orders (pk) 
        PRIMARY KEY (buy_order_pk, sell_order_pk)
    );
"""

columns__orders_pair = [
            'buy_order_pk',
            'sell_order_pk'
        ]


def str__orders_pair(data):
    return f"\n{data.buy_order}" \
           f"\n{data.sell_order}"


create_table__current_state = """
    CREATE TABLE IF NOT EXISTS current_state (
        pk INTEGER PRIMARY KEY,
        time INTEGER NOT NULL DEFAULT NULL,    

        order_book_bid_current_price TEXT DEFAULT NULL,        
        order_book_bid_current_quantity TEXT DEFAULT NULL,     
        order_book_ask_current_price TEXT DEFAULT NULL,        
        order_book_ask_current_quantity TEXT DEFAULT NULL,     

        balance_free TEXT DEFAULT NULL,                        
        balance_locked TEXT DEFAULT NULL,                      
        balance_sum TEXT DEFAULT NULL,                         
        balance_first_symbol TEXT NOT NULL DEFAULT NULL,                
        balance_first_symbol_free_value TEXT NOT NULL DEFAULT NULL,     
        balance_first_symbol_locked_value TEXT NOT NULL DEFAULT NULL,   
        balance_second_symbol TEXT NOT NULL DEFAULT NULL,               
        balance_second_symbol_free_value TEXT NOT NULL DEFAULT NULL,    
        balance_second_symbol_locked_value TEXT NOT NULL DEFAULT NULL   
    );
"""

columns__current_state = [
            "time",
            "order_book_bid_current_price",
            "order_book_bid_current_quantity",
            "order_book_ask_current_price",
            "order_book_ask_current_quantity",
            "balance_free",
            "balance_locked",
            "balance_sum",
            "balance_first_symbol",
            "balance_first_symbol_free_value",
            "balance_first_symbol_locked_value",
            "balance_second_symbol",
            "balance_second_symbol_free_value",
            "balance_second_symbol_locked_value"
        ]


def str__current_state(data):
    return f"\nTIME: {data.time}" \
           f"\nSMB: {data.balance_first_symbol};" \
           f" FREE: {data.balance_first_symbol_free_value};" \
           f" LOCKED: {data.balance_first_symbol_locked_value}" \
           f"\nSMB: {data.balance_second_symbol};" \
           f" FREE: {data.balance_second_symbol_free_value};" \
           f" LOCKED: {data.balance_second_symbol_locked_value}"


create_table__filters = """
    CREATE TABLE IF NOT EXISTS filters (
        pk INTEGER PRIMARY KEY,
        serverTime INTEGER NOT NULL DEFAULT NULL,
        symbol TEXT DEFAULT NULL,
        PRICE_FILTER_filterType TEXT NOT NULL DEFAULT NULL,
        PRICE_FILTER_minPrice TEXT NOT NULL DEFAULT NULL,
        PRICE_FILTER_maxPrice TEXT NOT NULL DEFAULT NULL,
        PRICE_FILTER_tickSize TEXT NOT NULL DEFAULT NULL,
        LOT_SIZE_filterType TEXT NOT NULL DEFAULT NULL,
        LOT_SIZE_minQty TEXT NOT NULL DEFAULT NULL,
        LOT_SIZE_maxQty TEXT NOT NULL DEFAULT NULL,
        LOT_SIZE_stepSize TEXT NOT NULL DEFAULT NULL,
        MIN_NOTIONAL_filterType TEXT NOT NULL DEFAULT NULL,
        MIN_NOTIONAL_minNotional TEXT NOT NULL DEFAULT NULL,
        MIN_NOTIONAL_applyToMarket TEXT NOT NULL DEFAULT NULL,
        MIN_NOTIONAL_avgPriceMins TEXT NOT NULL DEFAULT NULL
    );
"""

columns__filters = [
            "serverTime",
            "symbol",
            "PRICE_FILTER_filterType",
            "PRICE_FILTER_minPrice",
            "PRICE_FILTER_maxPrice",
            "PRICE_FILTER_tickSize",
            "LOT_SIZE_filterType",
            "LOT_SIZE_minQty",
            "LOT_SIZE_maxQty",
            "LOT_SIZE_stepSize",
            "MIN_NOTIONAL_filterType",
            "MIN_NOTIONAL_minNotional",
            "MIN_NOTIONAL_applyToMarket",
            "MIN_NOTIONAL_avgPriceMins"
        ]


def str__filters(data):
    return f"\nTIME: {data.serverTime}" \
           f"\nSMB: {data.symbol};" \
           f"\nFILTERS_JSON: {data.filters};\n"


create_all_tables = [
    create_table__orders,
    create_table__pending_orders,
    create_table__orders_pair,
    create_table__current_state,
    create_table__filters,
]
