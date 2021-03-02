# -*- coding: utf-8 -*-
"""
PY-MMD-TOOLS : Package Config Class
==============================

Copyright 2020–2021 MET Norway

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
import logging

from os import path

logger = logging.getLogger(__name__)

class Config():
    """Main config object for the package.
    """

    def __init__(self):

        self.pkgPath = None

        return

    def initConfig(self):
        """Initialise the config variables.
        """
        self.pkgPath = getattr(sys, "_MEIPASS", path.abspath(path.dirname(__file__)))

        logger.debug("Package path is %s" % self.pkgPath)

        return

# END Class Config
