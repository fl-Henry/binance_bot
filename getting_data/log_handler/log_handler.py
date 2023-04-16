import os
import sys
import datetime
import logging
import logging.handlers
import configparser


class LogHandler:

    def __init__(self, config_name=None, name=None):
        self.config = None
        self.name = name

        if config_name is None:
            self.config_name = 'log_handler.cfg'
        else:
            self.config_name = config_name

        # path to log_handler.py dir
        self.base_path = str(__file__)[:len(__file__) - len(os.path.basename(str(__file__))) - 1]
        self.config_path = f"{self.base_path}/{self.config_name}"

        if not os.path.exists(self.config_path):
            self.create_default_config()

        self.load_config()

        self.logger = logging.getLogger(self.name)

        self.init_logger()

    def create_default_config(self):
        with open(f"{self.base_path}/{self.config_name}", 'w') as cfg:
            with open(f"{self.base_path}/default.cfg", 'r') as default_cfg:
                cfg.write(default_cfg.read())

    def load_config(self):
        """
        Initialize ConfigParser() in self.config
        and get some data from .cfg file
        """
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        # check/create log directory
        log_dir = self.config.get('LOG', 'LOG_DIR_NAME')
        log_dir_path = f"{self.base_path}/{log_dir}"
        if not os.path.exists(log_dir_path):
            os.mkdir(log_dir_path)

        if self.name is None:
            self.name = self.config.get('LOG', 'NAME')

    def init_logger(self):
        """
        Initialization of logger
        """
        date_fmt = self.config.get('LOG', 'LOG_DATE_FMT')
        log_level: str = self.config.get('LOG', 'LOG_LEVEL')
        log_dir_name = self.config.get('LOG', 'LOG_DIR_NAME')
        log_dir_path = f"{self.base_path}/{log_dir_name}"
        log_file_prefix = self.config.get('LOG', 'LOG_FILE_PREFIX')
        if log_file_prefix != self.name:
            log_file_prefix = f"{log_file_prefix}_{self.name}"

        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % log_level)

        now = datetime.datetime.now()
        self.logger.setLevel(numeric_level)
        rfh = logging.handlers.TimedRotatingFileHandler(
            filename=f"{log_dir_path}/{log_file_prefix}.log",
            when='H',
            interval=2,
            backupCount=6
        )

        fmtr = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt=str(date_fmt))

        rfh.setFormatter(fmtr)
        self.logger.addHandler(rfh)

        self.logger.info("Logger has been initialized!")

        self.logger.debug("Displaying config values!")
        for section_name in self.config.sections():
            self.logger.debug("[SECTION]: %s", section_name)
            self.logger.debug("  Options: %s", self.config.options(section_name))
            for name, value in self.config.items(section_name):
                self.logger.debug("    %s = %s", name, value)

