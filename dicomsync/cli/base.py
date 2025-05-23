"""Shared objects for CLI and basic CLI commands"""
import logging
import os
from functools import wraps
from pathlib import Path
from typing import Any

import click
from click import UsageError

from dicomsync.core import Domain
from dicomsync.exceptions import (
    DICOMSyncError,
    NoSettingsFoundError,
    PasswordNotFoundError,
)
from dicomsync.logs import get_module_logger, install_colouredlogs
from dicomsync.persistence import DicomSyncSettingsFromFile

logger = get_module_logger("dicomsync")


def configure_logging(verbose):
    """Set logging options based on how many v's were passed to cli. More -vvv is
    more verbose then -vv
    """

    if verbose == 0:
        logger.info("Set loglevel INFO")
        install_colouredlogs(level=logging.INFO)
    if verbose == 1:
        logger.info("Set loglevel to DEBUG but keeping hyper-verbose urllib3 at INFO")
        install_colouredlogs(level=logging.DEBUG)
        # urllib is *very* verbose. tone it down urllib.
        logging.getLogger("urllib3").setLevel(logging.INFO)
    if verbose >= 2:
        logger.info("Set loglevel to DEBUG. Max verbosity.")
        install_colouredlogs(level=logging.DEBUG)


class DicomSyncContext:
    """Essential information automatically passed to any dicomsync CLI function"""

    def __init__(self, domain: Domain):
        self._domain = domain

    def get_domain(self) -> Domain:
        """Initialize domain. Delayed init to facility lazy loading in CLI functions.
        Some functions can be run without settings.
        """
        return self._domain

    def save_settings(self) -> Any:
        """Dummy save settings method here to provide a consistent interface for CLI
        methods, even if they are called in-memory only during tests
        """
        logger.debug(
            "Save settings called on in-memory base DicomSyncContext. "
            "Cannot save anything"
        )
        return None


class LazyDicomSyncContext(DicomSyncContext):
    """Context that only reads settings when they are actually needed.

    Useful to be able to run simple cli functions that do not require settings.
    """

    def __init__(self, settings_path):
        super().__init__(domain=None)
        self.settings_path = settings_path

    def get_domain(self) -> Domain:
        if not self._domain:
            settings = load_settings(settings_path=self.settings_path)
            self._domain = Domain(places=settings.places)
        return self._domain

    def save_settings(self) -> Path:
        """Write current domain places and other settings to disk"""
        settings = DicomSyncSettingsFromFile(
            places=self.get_domain().places, path=self.settings_path
        )
        settings.save()
        return settings.path


def init_context() -> DicomSyncContext:
    settings_path = DicomSyncSettingsFromFile.get_default_file(Path(os.getcwd()))
    return LazyDicomSyncContext(settings_path=settings_path)


def load_settings(settings_path):
    """Load settings from given path.

    Returns
    -------
    DicomSyncSettingsFromFile

    Raises
    ------
    click.UsageError
    """
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
        except (PasswordNotFoundError, DICOMSyncError) as e:
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
