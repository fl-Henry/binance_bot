import sqlite3

try:
    import tables
except ModuleNotFoundError:
    from . import tables


class SQLiteHandler:

    def __init__(self, db_name='sqlite', db_dir='.', check_same_thread=True, read_only=False):

        self.db_dir = db_dir
        self.db_name = f"{db_name}.db"
        self.db_path = f"{self.db_dir}/{self.db_name}"
        if read_only:
            self.connected_db = sqlite3.connect(
                f"file:{self.db_path}?mode=ro",
                uri=True,
                check_same_thread=check_same_thread
            )
        else:
            self.connected_db = sqlite3.connect(
                self.db_path,
                check_same_thread=check_same_thread
            )
        self.cursor = self.connected_db.cursor()

    def close(self):
        self.connected_db.close()

    @staticmethod
    def check_sec(items):
        if len(items) > 0:
            for item in items:
                if type(item) == str:
                    if ";" in item:
                        print("[ERROR] check_sec > ';' in", items)
                        raise sqlite3.OperationalError

    def create_all_tables(self, create_table_commands: tuple[str]):
        for create_table_command in create_table_commands:
            self.cursor.execute(create_table_command)

    def select_from_table(self, table, column_names: list, where_col: str = None, where_col_val: str = None,
                          where_condition: str = None, conditions: str = None):

        try:
            self.check_sec(table)
            self.check_sec(column_names)
            self.check_sec(str(where_col))
            self.check_sec(str(where_col_val))
            self.check_sec(str(where_condition))
            self.check_sec(str(conditions))
        except sqlite3.OperationalError as _ex:
            print('sqlite3.OperationalError')

        else:
            sql_command = ''
            if (where_col is not None) and (where_col_val is not None) and (where_condition is not None):
                print('[ERROR] select_from_table > too many args')
            else:
                if (where_col is None) and (where_col_val is None) and (where_condition is None)\
                        and (conditions is None):
                    sql_command = f"SELECT {', '.join([str(x) for x in column_names])} FROM {table};"
                elif where_col is not None and where_col_val is not None:
                    sql_command = f"SELECT {', '.join([str(x) for x in column_names])} FROM {table} " \
                                  f"WHERE {where_col} = {where_col_val};"
                elif where_condition is not None:
                    sql_command = f"SELECT {', '.join([str(x) for x in column_names])} FROM {table} " \
                                  f"WHERE {where_condition};"
                elif conditions is not None:
                    sql_command = f"SELECT {', '.join([str(x) for x in column_names])} FROM {table} " \
                                  f"{conditions};"
                if sql_command != '':
                    # print(sql_command)
                    return self.cursor.execute(sql_command)

    @staticmethod
    def parse_db_data_to_dict(column_names: list, db_data):
        result_list = []
        for row_values in db_data:
            data_dict = {}
            for col, value in zip(column_names, row_values):
                data_dict.update({str(col): value})
            result_list.append(data_dict)

        return result_list

    def update(self, table, set_data_dict, where_condition: str = None):
        """
            UPDATE employees                // table = 'employees'
            SET
                city = 'Toronto',           // set_data_dict = {'city': 'Toronto',
                state = 'ON',               //                  'state': 'ON',
                postalcode = 'M5P 2N7'      //                  'postalcode': 'M5P 2N7'}
            WHERE
                employeeid = 4;             // where_condition = 'employeeid = 4'

        :param table: str
        :param set_data_dict: dict
        :param where_condition: str
        """
        try:
            self.check_sec(table)
            self.check_sec(set_data_dict)
            self.check_sec(str(where_condition))
        except sqlite3.OperationalError as _ex:
            print('sqlite3.OperationalError')

        else:
            dict_data_to_list = [f"{col} = {repr(set_data_dict[col])}, " for col in set_data_dict.keys()]

            set_data_str = ""
            for item in dict_data_to_list:
                set_data_str += str(item)
            set_data_str = set_data_str[:-2]

            sql_command = f"""
                UPDATE {table}
                SET {set_data_str}
                WHERE
                    {where_condition};
            """
            # print(sql_command)
            if sql_command != '':
                self.cursor.execute(sql_command)
                self.connected_db.commit()

    def insert(self, table, column_names: list, values: list):
        try:
            self.check_sec(table)
            self.check_sec(column_names)
            self.check_sec(values)
        except sqlite3.OperationalError as _ex:
            print('sqlite3.OperationalError')
        else:
            sql_command = f"INSERT INTO {table} ({', '.join([str(x) for x in column_names])}) " \
                          f"VALUES ({', '.join([repr(x) for x in values])})"
            try:
                self.cursor.execute(sql_command)
                self.connected_db.commit()
            except sqlite3.OperationalError as _ex:
                print('[ERROR] insert >', _ex)
                print(sql_command)

    def insert_from_dict(self, table, data_dict):
        column_names = [key for key in data_dict.keys()]
        values = [data_dict[key] for key in data_dict.keys()]
        self.insert(table, column_names, values)


if __name__ == '__main__':
    sqlh = SQLiteHandler(db_name="test")
    sqlh.create_all_tables(tables.create_all_tables)
    data = [
        # ['BTCUSDT', 123456, '1234.1234', '4321.4321', '5432.5432', 'SELL', 'NEW'],
        # ['BTCUSDT', 123457, '12345.1234', '43212.4321', '54321.5432', 'BUY', 'NEW'],
        # ['BTCUSDT', 123458, '12346.1234', '43213.4321', '54322.5432', 'SELL', 'FILLED'],
        # ['BTCUSDT', 123459, '12347.1234', '43214.4321', '54323.5432', 'BUY', 'FILLED'],
        ['BTCUSDT', 123450, '12348.1234', '43215.4321', '54324.5432', 'SELL'],
        ['BTCUSDT', 123451, '12349.1234', '43216.4321', '54325.5432', 'BUY'],
    ]
    columns = ['symbol', 'orderId', 'price', 'origQty', 'cost', 'side'] # , 'status'

    for row_data in data:
        sqlh.insert('orders', columns, row_data)

    print(f"\nSELECT {', '.join([x for x in columns])} FROM orders ORDER BY orderId DESC")
    res = sqlh.cursor.execute(f"SELECT {', '.join([x for x in columns])} FROM orders ORDER BY orderId DESC")
    print(res.fetchall())
    sqlh.close()
