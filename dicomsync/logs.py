import logging

import coloredlogs

ROOT_LOGGER_NAME = "dicomsync"


def get_module_logger(name):
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


def install_colouredlogs(level):
    """Use coloured logs"""
    coloredlogs.install(level=level)
