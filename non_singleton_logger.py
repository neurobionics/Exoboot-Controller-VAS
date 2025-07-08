import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Any, Callable
import csv
import threading
from collections import deque
from datetime import datetime

class NonSingletonLogger:
    """
    A logger class that does NOT use the singleton pattern.
    Each instance is independent and can be used for per-thread logging.
    This logger can produce the following types of logs:
    - Debug
    - Info
    - Warning
    - Error
    - Critical

    The logs are saved to a file and can also be printed to the console.

    It takes in the following arguments:
    - log_path: Directory where the log file will be saved.
    - log_format: Format of the log messages.
    - file_level: Logging level for the file handler.
    - stream_level: Logging level for the stream handler.
    - file_max_bytes: Maximum size of the log file before it gets rotated.
    - file_backup_count: Number of backup files to keep.
    - file_name: Name of the log file. If not provided, a timestamped name will be used.
    """

    def __init__(
        self,
        log_path: str = "./",
        log_format: str = "[%(asctime)s] %(levelname)s: %(message)s",
        file_level: int = logging.DEBUG,
        stream_level: int = logging.INFO,
        file_max_bytes: int = 0,
        file_backup_count: int = 5,
        file_name: Optional[str] = None,
        buffer_size: int = 1000,
        enable_csv_logging: bool = True
    ):
        # Ensure log directory exists
        os.makedirs(log_path, exist_ok=True)

        # if no filename is provided, create one using the current timestamp
        if file_name is None:
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            file_name = f"log_{timestamp}"
        elif "." in file_name:  # otherwise, if the filename contains a dot (e.g. ".log"), then remove it
            file_name = file_name.split(".")[0]

        # assemble a filepath using the filename and log path
        self._file_path = os.path.join(log_path, f"{file_name}.log")

        # create a unique logger instance using the id of the current instance
        self._logger = logging.getLogger(f"NonSingletonLogger_{id(self)}")

        # set the logging level & prevent logs from being recorded by root logger
        self._logger.setLevel(file_level)
        self._logger.propagate = False

        # remove any existing handlers (to prevent duplicate logs)
        if self._logger.hasHandlers():
            self._logger.handlers.clear()

        formatter = logging.Formatter(log_format)

        # set-up a file handler that writes to the log file
        # the handler rotates the file if it gets too big
        file_handler = RotatingFileHandler(
            filename=self._file_path,
            mode="w",
            maxBytes=file_max_bytes,
            backupCount=file_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler) # add the file handler to the logger

        # stream handler prints logs to the console
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(stream_level)
        stream_handler.setFormatter(formatter)
        self._logger.addHandler(stream_handler) # add the stream handler to the logger

        self._tracked_vars = {}
        self._var_names = {}
        self._buffer = deque(maxlen=buffer_size)
        self._buffer_size = buffer_size
        self._header_written = False
        self._enable_csv_logging = enable_csv_logging
        self._csv_path = os.path.join(log_path, f"{file_name}.csv")
        self._file = None
        self._writer = None
        self._lock = threading.RLock()

    def track_variable(self, var_func: Callable[[], Any], name: str) -> None:
        self._tracked_vars[id(var_func)] = var_func
        self._var_names[id(var_func)] = name
        self.debug(f"Started tracking variable: {name}")

    def update(self) -> None:
        if not self._tracked_vars or not self._enable_csv_logging:
            return
        with self._lock:
            data = []
            for var_id, get_value in self._tracked_vars.items():
                try:
                    value = get_value()
                except Exception as e:
                    value = "ERROR"
                data.append(str(value))
            if data:
                self._buffer.append(data)
            if len(self._buffer) >= self._buffer_size:
                self.flush_buffer()

    def flush_buffer(self) -> None:
        if not self._buffer or not self._enable_csv_logging:
            return
        with self._lock:
            if self._file is None:
                self._file = open(self._csv_path, "a", encoding="utf-8", newline="")
                self._writer = csv.writer(self._file)
            if not self._header_written:
                self._write_header()
            self._writer.writerows(self._buffer)
            self._buffer.clear()
            self._file.flush()

    def _write_header(self) -> None:
        header = list(self._var_names.values())
        if header:
            self._writer.writerow(header)
            self._header_written = True

    def close(self):
        self.flush_buffer()
        if self._file:
            self._file.close()
            self._file = None

    # logging methods at different levels:
    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)

    @property
    def file_path(self):
        return self._file_path

class test():
    def __init__(self):
        self.x = 25

if __name__ == "__main__":

    logger = NonSingletonLogger(log_path="./src/logs/",
                                file_name="test_logger",
                                file_level=logging.DEBUG,
                                stream_level=logging.INFO,
                                buffer_size=100)

    # instantiate test class
    obj = test()
    logger.track_variable(lambda: obj.x, "test")

    for i in range(10):
        logger.update()

        logger.debug(f"Debug message {i}")
        logger.info(f"Info message {i}")
        logger.warning(f"Warning message {i}")
        logger.error(f"Error message {i}")
        logger.critical(f"Critical message {i}")

    print(f"Log file created at: {logger.file_path}")
    logger.flush_buffer()
    logger.close()



