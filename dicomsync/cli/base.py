"""Shared objects for CLI and basic CLI commands"""
import logging
import os
from dataclasses import dataclass
from functools import wraps
from pathlib import Path

import click
from click import UsageError

from dicomsync.exceptions import NoSettingsFoundError, PasswordNotFoundError
from dicomsync.logs import get_module_logger, install_colouredlogs
from dicomsync.persistence import DicomSyncSettingsFromFile

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
    current_dir: Path

    def load_settings(self):
        """Load settings from current dir

        Raises
        ------
        click.UsageError
        """
        return load_settings(folder=self.current_dir)


def get_context() -> DicomSyncContext:
    return DicomSyncContext(current_dir=Path(os.getcwd()))


def load_settings(folder):
    """Load settings from given folder

    Raises
    ------
    click.UsageError
    """
    settings_path = DicomSyncSettingsFromFile.get_default_file(folder)
    logger.debug(f"Reading settings from {settings_path}")
    try:
        return DicomSyncSettingsFromFile.init_from_file(settings_path)
    except NoSettingsFoundError as e:
        logger.warning(str(e))
        raise UsageError(str(e)) from e


def handle_dicomsync_exceptions(func):
    """Decorator for handling dicomsync exceptions more usefully than just raising"""

    @wraps(func)
    def with_handling(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except PasswordNotFoundError as e:
            logger.error(e)
            raise click.UsageError(e) from e

    return with_handling


def dicom_sync_command(**kwargs):
    """Combines decorators used for all click functions inside a ClickCommandGroup
    Identical to

    @click.command(**kwargs)
    @click.pass_obj
    @handle_dicomsync_exceptions

    Just to prevent duplicated code
    """

    def decorated(func):
        return click.command(**kwargs)(
            click.pass_obj(handle_dicomsync_exceptions(func))
        )

    return decorated
