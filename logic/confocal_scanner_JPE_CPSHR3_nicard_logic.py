"""
Interfuse to do confocal scans with attocube stages.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import time
import numpy as np

from core.module import Base
from interface.confocal_scanner_JPE_CPSHR3_nicard_interface import confocal_scanner_JPE_CPSHR3_nicard_interface


class confocal_scanner_JPE_CPSHR3_nicard_interfuse(Base, confocal_scanner_JPE_CPSHR3_nicard_interface):

    """This is the Interface class to define the controls for the simple
    microwave hardware.
    """
    _modclass = 'confocal_scanner_JPE_CPSHR3_micard_interfuse'
    _modtype = 'interfuse'
    # connectors
    _connectors = {
        'scanner': 'confocal_scanner_JPE_CPSHR3_nicard_interface',
        'counter': 'SlowCounterInterface'
    }

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._scanner_logic = self.get_connector('scanner')
        self._counter_logic = self.get_connector('counter')

    def on_deactivate(self):
        self.reset_hardware()

    def reset_hardware(self):
        """ Resets the hardware, so the connection is lost and other programs can access it.
        """
        self._counter_logic.reset_hardware()
        return 0