from __future__ import absolute_import, unicode_literals

import sys

globals().update(vars(sys.modules["settings"]))

if "PROCTOR_BASE_TEMPLATE" not in globals():
    PROCTOR_BASE_TEMPLATE = "proctor_default_base.html"
