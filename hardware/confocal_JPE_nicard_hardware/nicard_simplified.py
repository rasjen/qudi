# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 10:47:01 2017

@author: qpitlab
"""

from PyDAQmx import *
import numpy
import matplotlib.pyplot as plt

# Declaration of variable passed by reference
taskHandle = TaskHandle()
read = int32()
data = numpy.zeros((1000,), dtype=numpy.float64)

try:
    # DAQmx Configure Code
    DAQmxCreateTask("",byref(taskHandle))
    DAQmxCreateAIVoltageChan(taskHandle, "Dev1/ai0", "", DAQmx_Val_Cfg_Default, -10.0, 10.0, DAQmx_Val_Volts, None)
    DAQmxCfgSampClkTiming(taskHandle, "", 1000.0, DAQmx_Val_Rising,DAQmx_Val_FiniteSamps, 1000)

    # DAQmx Start Code
    DAQmxStartTask(taskHandle)

    # DAQmx Read Code
    DAQmxReadAnalogF64(taskHandle, 1000, 10.0, DAQmx_Val_GroupByChannel, data, 1000, byref(read), None)
    plt.plot(data)
    plt.show()
    print("Acquired %d points"%read.value)
except DAQError as err:
    print("DAQmx Error: %s"%err)
finally:
    if taskHandle:
        # DAQmx Stop Code
        DAQmxStopTask(taskHandle)
        DAQmxClearTask(taskHandle)