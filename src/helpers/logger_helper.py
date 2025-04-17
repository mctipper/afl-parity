import logging
from logging import Logger
from typing import Any, Optional
from pathlib import Path
from datetime import datetime
from logging import FileHandler, LogRecord
from io import TextIOWrapper


class LazyFileHandler(FileHandler):
    """nifty helper that delays the creation of the log file/dir until the first log command is actually received"""

    def __init__(
        self,
        filename: Any,
        mode: str = "a",
        encoding: Optional[Any] = None,
        delay: bool = True,
    ) -> None:
        self.file_created = False
        super().__init__(filename, mode, encoding, delay)

    def _open(self) -> TextIOWrapper:
        """overrider that first creates the dir before creating the file"""
        if not Path(self.baseFilename).parent.is_dir():
            Path(self.baseFilename).parent.mkdir(parents=True, exist_ok=True)
        return super()._open()

    def emit(self, record: LogRecord) -> None:
        """overrider that awaits a log before creating and opening the logfile"""
        if not self.file_created:
            self._open()
            self.file_created = True
        super().emit(record)


class LoggerHelper:
    @staticmethod
    def setup(
        current_datetime: datetime,
        logname: str = "main",
        output_file_debug: bool = False,
    ) -> Logger:
        """creates and configs out a logger"""
        # determine the root directory of the application (hacky but static so works fine)
        app_root = Path(__file__).resolve().parents[2]

        # create a generic logger
        logger = logging.getLogger(logname)
        logger.setLevel(logging.DEBUG)

        # create stream handler
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)

        # and now the file handler
        logfilepath = (
            app_root
            / f".logs/{current_datetime:%Y%m%d}/{current_datetime:%Y%m%d_%H%M%S}_{logname}.log"
        )
        if not logfilepath.parent.is_dir():
            logfilepath.parent.mkdir(parents=True, exist_ok=True)

        f_handler = LazyFileHandler(logfilepath)

        if output_file_debug:
            f_handler.setLevel(logging.DEBUG)
        else:
            f_handler.setLevel(logging.INFO)

        # create different formatters and add them to each handler
        c_format = logging.Formatter(
            "%(levelname)-8s - [%(filename)s - %(funcName)s() ] - %(message)s"
        )
        f_format = logging.Formatter(
            "%(asctime)s - %(levelname)-8s - [%(filename)s:%(lineno)s - %(funcName)s() ] --- %(message)s"
        )
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        # register them and we are away
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        return logger
