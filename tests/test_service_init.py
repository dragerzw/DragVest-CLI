import importlib
import sys
import pathlib
import pytest

import app.service as svc


def test_import_service_init():
    # simple import test to cover app.service __init__ lines
    assert hasattr(svc, "exceptions")


def test_service_init_handles_login_import_failure():
    pkg_dir = pathlib.Path(svc.__file__).parent
    target = pkg_dir / 'login_service.py'
    backup = pkg_dir / 'login_service.py.bak'
    if not target.exists():
        pytest.skip("login_service.py not present; skipping")

    try:
        target.rename(backup)
        sys.modules.pop('app.service.login_service', None)
        importlib.reload(svc)
        assert getattr(svc, 'LoginService', None) is None
    finally:
        if backup.exists():
            backup.rename(target)
        sys.modules.pop('app.service.login_service', None)
        importlib.reload(svc)


def test_service_init_handles_exceptions_import_failure():
    pkg_dir = pathlib.Path(svc.__file__).parent
    target = pkg_dir / 'exceptions.py'
    backup = pkg_dir / 'exceptions.py.bak'
    if not target.exists():
        pytest.skip("exceptions.py not present; skipping")

    try:
        target.rename(backup)
        sys.modules.pop('app.service.exceptions', None)
        importlib.reload(svc)
        assert svc.NotFoundError is Exception or issubclass(svc.NotFoundError, Exception)
    finally:
        if backup.exists():
            backup.rename(target)
        sys.modules.pop('app.service.exceptions', None)
        importlib.reload(svc)
