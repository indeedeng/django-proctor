import sys
from unittest import TestCase
import mock

from proctor.tests import settings


@mock.patch.dict(sys.modules, {"settings": settings})
class PrivateViewsTest(TestCase):
    def test_import(self):
        # FIXME: Add real tests! Import module to ensure that test suite tests top-level code:
        from proctor.views import private  # noqa
