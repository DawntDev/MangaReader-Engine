import logging


class Logger:
    loggers = {}

    def __init__(self, name: str, filename: str) -> None:
        if not name in self.loggers:
            self.logger = logging.getLogger(name)
            self.logger.setLevel(logging.DEBUG)
            handler = logging.FileHandler(
                filename=f"./logs/{filename}.log", encoding="utf-8"
            )
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
                )
            )

            self.logger.addHandler(handler)
            self.loggers[name] = self.logger
        else:
            self.logger = self.loggers[name]

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs, logger=self.logger)
            return result

        return wrapper
