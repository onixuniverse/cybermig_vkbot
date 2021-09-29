from loguru import logger


logger.add("log.log", format="{time} - {level} - {message}", level="INFO", rotation="10 MB", compression="zip")


def info(info_msg):
    logger.info(info_msg)


def error(error_msg):
    logger.error(error_msg)
    print(error_msg)


def debug(debug_msg):
    logger.debug(debug_msg)
    print(debug_msg)
