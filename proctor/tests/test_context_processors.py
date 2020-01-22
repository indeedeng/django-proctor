from unittest import TestCase
from mock import Mock

from proctor import context_processors


class ContextProcessorsTest(TestCase):
    def test_proc_returns_proc(self):
        request = Mock(proc='test')
        proc = context_processors.proc(request)
        self.assertEqual({'proc': 'test'}, proc)

    def test_empty_request_proc_returns_empty_dict(self):
        proc = context_processors.proc(None)
        self.assertEqual({}, proc)
