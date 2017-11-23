# -*- coding: utf-8 -*-

"""
This file contains the Qudi Hardware module NICard class.

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

from core.module import Base
from interface.JPE_stage_interface import JPEStageInterface
import subprocess


class JPEStageHardware(Base, JPEStageInterface):
    _modtype = 'hardware'
    _modclass = 'JPEStageHardware'

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self.cacli_path = r'C:\Users\qpitlab\Desktop\JPE software installation\CPS_v5.2b_2017-03-13_134000\cacli.exe '

    def on_deactivate(self, e=None):
        """ Shut down the device.

        @param object e: Event class object from Fysom. A more detailed
                         explanation can be found in method activation.
        """
        pass

    # ================ ConfocalScannerInterface Commands =======================
    def reset_hardware(self):
        """ Resets the NI hardware, so the connection is lost and other
            programs can access it.

        @return int: error code (0:OK, -1:error)
        """
        pass

    def do_command(self, COMMAND, ADDR = '', CH = '', TYPE = '', TEMP = '', DIR = '', FREQ = '', REL = '', STEPS = '', TRQFR = ''):
        proc = subprocess.Popen(self.cacli_path + COMMAND + ADDR + CH + TYPE + TEMP + DIR + FREQ + REL + STEPS + TRQFR,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = proc.stdout.read().decode('utf-8')  # .strip().split()
        print(output)
        return 0


# do_command('MOV 1 1 CA1801 293 0 200 100 20')
# do_command('/type')
# do_command('/ver')
# do_command('modlist')
# do_command('DESC 1')
# do_command('INFO 1 1')
