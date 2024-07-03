"""Shared objects for CLI and basic CLI commands"""
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dicomsync.logs import get_module_logger, install_colouredlogs
from dicomsync.persistence import DicomSyncSettings, DicomSyncSettingsFromFile

logger = get_module_logger("dicomsync")


def configure_logging(verbose):
    loglevel = logging.INFO
    if verbose == 0:
        loglevel = logging.INFO
    if verbose >= 1:
        loglevel = logging.DEBUG

    install_colouredlogs(level=loglevel)
    logging.debug(
        f"Set loglevel "
        f"to {logging.getLevelName(logging.getLogger().getEffectiveLevel())}"
    )


@dataclass
class DicomSyncContext:
    settings: DicomSyncSettings
    current_dir: Path


def get_context() -> DicomSyncContext:
    current_dir = Path(os.getcwd())
    return DicomSyncContext(
        settings=DicomSyncSettingsFromFile.init_from_default_file(current_dir),
        current_dir=current_dir,
    )
