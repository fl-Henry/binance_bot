import time
import os
import configparser
import unittest

from shutil import rmtree

from .log_handler import LogHandler


class LogHandlerTests(unittest.TestCase):
    # TODO: backUP exist logs / now exist logs are deleted

    base_path = str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]
    test_cfg_name = 'test.cfg'
    test_cfg_path = f"{base_path}/{test_cfg_name}"

    def test_no_name(self):
        """
        If name=None in LogHandler() ->  name=(from config).
        """
        print('\ntest_no_name')
        lh = LogHandler(config_name=self.test_cfg_name, name=None)
        name = self.get_from_test_config('LOG', 'NAME')
        self.assertEqual(lh.name, name)

    def test_no_config_file(self):
        """
        If config_name=None in LogHandler() ->  config_name=log_handler.cfg
        """
        print('\ntest_no_config_file')
        lh = LogHandler(name='test_no_config_file')
        config_name = 'log_handler.cfg'
        self.assertEqual(lh.config_name, config_name)

    def test_config_file_doesnt_exist(self):
        """
        If config_name in LogHandler() doesn't exist ->  create config_name
        """
        print('\ntest_config_file_doesnt_exist')
        config_name = 'test_cfg_do_delete.cfg'
        lh = LogHandler(config_name=config_name, name='test_config_file_doesnt_exist')
        self.assertEqual(lh.config_name, config_name)
        os.remove(f'{self.base_path}/{config_name}')

    def test_log_dir_doesnt_exist(self):
        """
        If logs_dir from config.get('LOG', 'LOG_DIR_NAME') doesn't exist ->  create logs_dir
        """
        print('\ntest_log_dir_doesnt_exist')
        logs_dir = self.get_from_test_config('LOG', 'LOG_DIR_NAME')
        log_dir_path = f"{self.base_path}/{logs_dir}/"

        if os.path.exists(log_dir_path):
            rmtree(str(log_dir_path))

        self.assertFalse(os.path.exists(log_dir_path))
        lh = LogHandler(config_name=self.test_cfg_name, name='test_log_dir_doesnt_exist')
        self.assertTrue(os.path.exists(log_dir_path))
        rmtree(str(log_dir_path))
        self.assertFalse(os.path.exists(str(log_dir_path)))

    def test_log_dir_exists(self):
        """
        If logs_dir from config.get('LOG', 'LOG_DIR_NAME') doesn't exist ->  create logs_dir
        """
        print('\ntest_log_dir_exists:')
        logs_dir = self.get_from_test_config('LOG', 'LOG_DIR_NAME')
        log_dir_path = f"{self.base_path}/{logs_dir}/"

        if not os.path.exists(log_dir_path):
            os.mkdir(str(log_dir_path))

        self.assertTrue(os.path.exists(log_dir_path))
        lh = LogHandler(config_name=self.test_cfg_name, name='test_log_dir_exists')
        self.assertTrue(os.path.exists(log_dir_path))
        rmtree(str(log_dir_path))
        self.assertFalse(os.path.exists(str(log_dir_path)))

    def load_test_config(self):
        config = configparser.ConfigParser()
        config.read(self.test_cfg_path)
        return config

    def get_from_test_config(self, section: str, option: str):
        cfg = self.load_test_config()
        return cfg.get(section, option)

