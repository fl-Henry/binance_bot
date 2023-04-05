import os
import time
import unittest
import sqlite3

from shutil import rmtree

from db_handler import SQLiteHandler
from tables import create_all_tables

db_dir = f"{str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]}/for_tests"
db_name = f"test"
db_path = f"{db_dir}/{db_name}.db"

if not os.path.exists(db_dir):
    os.mkdir(db_dir)
    print(f"Created: {db_dir}")


class TestSum(unittest.TestCase):

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

    def test_insert(self):
        print('\ntest_insert')
        current_db_name = 'test_insert'
        sqlh = SQLiteHandler(db_name=current_db_name, db_dir=db_dir)

        try:
            sqlh.create_all_tables(create_all_tables)

            data = self.data
            columns = self.columns

            for row_data in data:
                sqlh.insert('orders', columns, row_data)

            # print(f"\nSELECT {', '.join([x for x in columns])} FROM orders ORDER BY orderId DESC")
            # res = sqlh.cursor.execute(f"SELECT {', '.join([x for x in columns])} FROM orders ORDER BY orderId DESC")
            res = sqlh.cursor.execute(f"SELECT {columns[1]} FROM orders WHERE {columns[1]} = {data[1][1]}")

            param_01 = str(res.fetchone()[0])
            param_02 = str(data[1][1])
            self.assertEqual(param_01, param_02)

        finally:
            sqlh.close()
            os.remove(f"{db_dir}/{current_db_name}.db")

    def test_insert_from_dict(self):
        print('\ntest_insert_from_dict')
        current_db_name = 'test_insert_from_dict'
        sqlh = SQLiteHandler(db_name=current_db_name, db_dir=db_dir)
        try:
            sqlh.create_all_tables(create_all_tables)

            table = 'current_state'
            data_dict = self.current_state

            sqlh.insert_from_dict(table, data_dict)

            res = sqlh.cursor.execute(f"SELECT {list(data_dict.keys())[5]} FROM {table} WHERE pk = 1")

            param_db = str(res.fetchone()[0])
            param_const = str(data_dict['balance_second_symbol_locked_value'])
            self.assertEqual(param_db, param_const)
            # print('param_db:    ', param_db)
            # print('param_const: ', param_const)
        finally:
            sqlh.close()
            os.remove(f"{db_dir}/{current_db_name}.db")

    def test_check_sec(self):
        print('\ntest_check_sec')
        current_db_name = 'test_check_sec'
        sqlh = SQLiteHandler(db_name=current_db_name, db_dir=db_dir)
        try:
            sqlh.create_all_tables(create_all_tables)

            table = 'current_state'
            bad_table = 'current_state;'
            # print('table:    ', table)
            # print('bad_table:', bad_table)

            column_names = self.columns
            bad_column_names = [x for x in self.columns]
            bad_column_names.append('abadre;sd')
            # print("column_names:    ", column_names)
            # print("bad_column_names:", bad_column_names)

            values = self.data[2]
            bad_values = [x for x in self.data[2]]
            bad_values.append('asfgwc;sdavr')
            # print('values:    ', values)
            # print('bad_values:', bad_values)

            sqlh.check_sec(table)

            with self.assertRaises(sqlite3.OperationalError):
                sqlh.check_sec(bad_table)

            sqlh.check_sec(column_names)

            with self.assertRaises(sqlite3.OperationalError):
                sqlh.check_sec(bad_column_names)

            sqlh.check_sec(values)

            with self.assertRaises(sqlite3.OperationalError):
                sqlh.check_sec(bad_values)

        finally:
            sqlh.close()
            os.remove(f"{db_dir}/{current_db_name}.db")

    def test_insert_from_dict_with_bad_check_sec(self):
        print('\ntest_insert_from_dict_with_bad_check_sec')
        current_db_name = 'test_insert_from_dict_with_bad_check_sec'
        sqlh = SQLiteHandler(db_name=current_db_name, db_dir=db_dir)
        try:
            sqlh.create_all_tables(create_all_tables)

            table = 'current_state'
            bad_table = 'current_state;'
            data_dict = self.current_state

            sqlh.insert_from_dict(bad_table, data_dict)
            res = sqlh.cursor.execute(f"SELECT * FROM {table}")
            self.assertIsNone(res.fetchone())

        finally:
            sqlh.close()
            os.remove(f"{db_dir}/{current_db_name}.db")

    def test_select_from_table(self):
        print('\ntest_select_from_table')
        current_db_name = 'test_select_from_table'
        sqlh = SQLiteHandler(db_name=current_db_name, db_dir=db_dir)
        try:
            sqlh.create_all_tables(create_all_tables)

            table = 'current_state'
            data_dict = self.current_state

            sqlh.insert_from_dict(table, data_dict)

            # res = sqlh.cursor.execute(f"SELECT {list(data_dict.keys())[5]} FROM {table} WHERE pk = 1")
            # print("select_from_table(table, columns, 'pk', 1)")
            res = sqlh.select_from_table(table, list(data_dict.keys()), 'pk', 1)

            param_db = str(res.fetchone()[5])
            param_const = str(data_dict['balance_second_symbol_locked_value'])
            # print('param_db:    ', param_db)
            # print('param_const: ', param_const)
            self.assertEqual(param_db, param_const)

            # print("select_from_table(table, columns, where_condition='pk = 1')")
            res = sqlh.select_from_table(table, list(data_dict.keys()), where_condition='pk = 1')
            param_db = str(res.fetchone()[5])
            param_const = str(data_dict['balance_second_symbol_locked_value'])
            self.assertEqual(param_db, param_const)

        finally:
            sqlh.close()
            os.remove(f"{db_dir}/{current_db_name}.db")

    def test_update(self):
        print('\ntest_update')
        current_db_name = 'test_update'
        sqlh = SQLiteHandler(db_name=current_db_name, db_dir=db_dir)
        try:
            sqlh.create_all_tables(create_all_tables)

            table = 'current_state'
            data_dict = self.current_state

            sqlh.insert_from_dict(table, data_dict)

            res = sqlh.select_from_table(table, list(data_dict.keys()), where_condition='pk = 1')
            param_db = str(res.fetchone()[5])
            param_const = str(data_dict['balance_second_symbol_locked_value'])
            self.assertEqual(param_db, param_const)

            data_dict_to_update = self.current_state_01
            sqlh.update(table, data_dict_to_update, 'pk = 1')

            res = sqlh.select_from_table(table, list(data_dict.keys()), where_condition='pk = 1')
            param_db = str(res.fetchone()[5])
            param_const = str(data_dict_to_update['balance_second_symbol_locked_value'])
            self.assertEqual(param_db, param_const)

        finally:
            sqlh.close()
            os.remove(f"{db_dir}/{current_db_name}.db")

    def test_parse_db_data_to_dict(self):
        print('\ntest_parse_db_data_to_dict')
        current_db_name = 'test_parse_db_data_to_dict'
        sqlh = SQLiteHandler(db_name=current_db_name, db_dir=db_dir)
        try:
            sqlh.create_all_tables(create_all_tables)

            table = 'current_state'
            data_dict = self.current_state

            data_to_save = [self.current_state, self.current_state_01]
            if len(data_to_save) > 0:
                for row in data_to_save:
                    sqlh.insert_from_dict(table, row)

            res = sqlh.select_from_table(table, list(data_dict.keys()))
            param_db = res.fetchall()
            parsed_data = sqlh.parse_db_data_to_dict(list(data_dict.keys()), param_db)

            self.assertEqual(
                data_to_save[0]['balance_first_symbol_locked_value'],
                parsed_data[0]['balance_first_symbol_locked_value']
            )

        finally:
            sqlh.close()
            os.remove(f"{db_dir}/{current_db_name}.db")


if __name__ == '__main__':
    unittest.main()
    