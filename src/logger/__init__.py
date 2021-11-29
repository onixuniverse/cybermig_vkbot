from loguru import logger


def info(info_msg):
    logger.info(info_msg)


def error(error_msg):
    logger.error(error_msg)


def debug(debug_msg):
    logger.debug(debug_msg)


def warning(warn_msg):
    logger.warning(warn_msg)
