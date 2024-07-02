"""Shared objects for CLI and basic CLI commands"""
import logging
from dataclasses import dataclass

from dicomsync.logs import get_module_logger, install_colouredlogs
from dicomsync.persistence import DicomSyncSettings

logger = get_module_logger("dicomsync")


def configure_logging(verbose):
    loglevel = logging.INFO
    if verbose == 0:
        loglevel = logging.INFO
    if verbose >= 1:
        loglevel = logging.DEBUG

    logging.info(f"Set loglevel to {loglevel}")
    logging.basicConfig(level=loglevel)
    install_colouredlogs(level=loglevel)


@dataclass
class DicomSyncContext:
    settings: DicomSyncSettings


def get_context() -> DicomSyncContext:
    return DicomSyncContext(settings=DicomSyncSettings())
