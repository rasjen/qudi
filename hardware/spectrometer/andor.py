from core.module import Base
from interface.spectrometer_interface2 import SpectrometerInterface
import platform
from ctypes import *
import sys
from time import sleep


ERROR_CODE = {
    20001: "DRV_ERROR_CODES",
    20002: "DRV_SUCCESS",
    20003: "DRV_VXNOTINSTALLED",
    20006: "DRV_ERROR_FILELOAD",
    20007: "DRV_ERROR_VXD_INIT",
    20010: "DRV_ERROR_PAGELOCK",
    20011: "DRV_ERROR_PAGE_UNLOCK",
    20013: "DRV_ERROR_ACK",
    20024: "DRV_NO_NEW_DATA",
    20026: "DRV_SPOOLERROR",
    20034: "DRV_TEMP_OFF",
    20035: "DRV_TEMP_NOT_STABILIZED",
    20036: "DRV_TEMP_STABILIZED",
    20037: "DRV_TEMP_NOT_REACHED",
    20038: "DRV_TEMP_OUT_RANGE",
    20039: "DRV_TEMP_NOT_SUPPORTED",
    20040: "DRV_TEMP_DRIFT",
    20050: "DRV_COF_NOTLOADED",
    20053: "DRV_FLEXERROR",
    20066: "DRV_P1INVALID",
    20067: "DRV_P2INVALID",
    20068: "DRV_P3INVALID",
    20069: "DRV_P4INVALID",
    20070: "DRV_INIERROR",
    20071: "DRV_COERROR",
    20072: "DRV_ACQUIRING",
    20073: "DRV_IDLE",
    20074: "DRV_TEMPCYCLE",
    20075: "DRV_NOT_INITIALIZED",
    20076: "DRV_P5INVALID",
    20077: "DRV_P6INVALID",
    20083: "P7_INVALID",
    20089: "DRV_USBERROR",
    20091: "DRV_NOT_SUPPORTED",
    20095: "DRV_INVALID_TRIGGER_MODE",
    20099: "DRV_BINNING_ERROR",
    20990: "DRV_NOCAMERA",
    20991: "DRV_NOT_SUPPORTED",
    20992: "DRV_NOT_AVAILABLE"
}

ReadModes = {
    # Full Vertical Binning
    'FVB': 0,
    # Multi-Track
    'MT': 1,
    # Random-Track
    'RT': 2,
    #Single-Track
    'ST': 3,
    # Image
    'Image': 4

}

AcquisitionModes = {
    'Single Scan':  1,
    'Accumulate': 2,
    'Kinetics': 3,
    'Fast Kinetics': 4,
    'Run till abort': 5
}

class Andor(Base, SpectrometerInterface):
    """
    This module is controling the Andor spectrometer
        
    
    """

    _modtype = 'AndorSpectrometer'
    _modclass = 'hardware'


    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)


    def on_activate(self):
        """
        Activates the module
        
        :return: 
        """

        if platform.system() == "Windows":
            if platform.architecture()[0] == "32bit":
                self.dll = cdll.LoadLibrary(r"C:\Program Files\Andor SDK\atmcd32d.dll")
            else:
                self.dll = windll.LoadLibrary(r"C:\Program Files\Andor SDK\atmcd64d.dll")
        else:
            self.log.error("Cannot detect operating system, wil now stop")
        self.verbosity = True

        error = self.initialize()

        cw = c_int()
        ch = c_int()
        self.dll.GetDetector(byref(cw), byref(ch))


        self.width = cw.value
        self.height = ch.value
        self.temperature = None
        self.set_T = None
        self.gain = None
        self.gainRange = None
        self.status = ERROR_CODE[error]
        self.verbosity = True
        self.preampgain = None
        self.channel = None
        self.outamp = None
        self.hsspeed = None
        self.vsspeed = None
        self.serial = None
        self.exposure = None
        self.accumulate = None
        self.kinetic = None
        self.ReadMode = None
        self.AcquisitionMode = None
        self.scans = 1
        self.hbin = 1
        self.vbin = 1
        self.hstart = 1
        self.hend = cw
        self.vstart = 1
        self.vend = ch
        self.cooler = None

    def __del__(self):
        """
        Deleting the instance
        
        :return: 
        """
        self.shutdown()

    def on_deactivate(self):
        """
        
        
        :return: 
        """
        self.shutdown()

    def verbose(self, error, function=''):
        """
        Print error messeages
        
        :param error: 
        :param function: 
        :return: 
        """
        if self.verbosity is True:
            self.log.info('{}:{}'.format(function, error))

    def set_verbose(self, state=True):
        self.verbosity = state

    def initialize(self):
        tekst = c_char()
        error = self.dll.Initialize(byref(tekst))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return error

    def shutdown(self, force=False):
        if force:
            self.dll.AbortAcquisition()
            self.cooler_off()
            error = self.dll.ShutDown()
        else:
            self.dll.AbortAcquisition()
            self.set_temperature(0)
            self.cooler_on()
            if self.get_temperature() <= -20:
                self.log.info("Detector warming up, please wait.")
                warm = False
                while not warm:
                    sleep(1)
                    self.log.info(self.get_temperature())
                    if self.get_temperature() > -20:
                        warm = True
                self.log.info("Warmup finished.")

            self.cooler_off()
            error = self.dll.ShutDown()
            #verbose(error, sys._getframe().f_code.co_name)

    def get_camera_serial_number(self):
        serial = c_int()
        error = self.dll.GetCameraSerialNumber(byref(serial))
        self.serial = serial.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_read_mode(self, mode):
        """
        Sets how the data from the CDD should be read
        
        :param mode:  0: Full vertical binning, 1: multi track, 2: random track, 3: single track, 4: image
        :return: 
        """
        error = self.dll.SetReadMode(mode)
        self.ReadMode = mode
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_acquisition_mode(self, mode):
        """
        Set the acquisitions mode for the CDD
        
        :param mode: 1: Single scan, 2: Accumualte, 3: Kinetic scan 
        :return: 
        """
        error = self.dll.SetAcquisitionMode(mode)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        self.AcquisitionMode = mode
        return ERROR_CODE[error]

    def set_number_kinetics(self, numKin):
        cnumKin = c_int(int(numKin))
        error = self.dll.SetNumberKinetics(cnumKin)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        self.scans = numKin
        return ERROR_CODE[error]

    def set_number_accumulations(self, number):
        error = self.dll.SetNumberAccumulations(c_int(int(number)))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_accumulation_cycle_time(self, time):
        error = self.dll.SetAccumulationCycleTime(c_float(time))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_kinetic_cycle_time(self, time):
        error = self.dll.SetKineticCycleTime(c_float(time))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_shutter(self, typ, mode, closingtime, openingtime):
        error = self.dll.SetShutter(typ, mode, closingtime, openingtime)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_image(self, hbin, vbin, hstart, hend, vstart, vend):
        self.hbin = hbin
        self.vbin = vbin
        self.hstart = hstart
        self.hend = hend
        self.vstart = vstart
        self.vend = vend

        error = self.dll.SetImage(hbin, vbin, hstart, hend, vstart, vend)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def start_acquisition(self):
        error = self.dll.StartAcquisition()
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_acquired_data(self):
        if (self.ReadMode == ReadModes['Image']):
            if (self.AcquisitionMode == AcquisitionModes['Single Scan']):
                dim = self.width * self.height / self.hbin / self.vbin
            elif (self.AcquisitionMode == AcquisitionModes['Kinetics']):
                dim = self.width * self.height / self.hbin / self.vbin * self.scans
        elif (self.ReadMode == ReadModes['ST'] or self.ReadMode == ReadModes['FVB']):
            if (self.AcquisitionMode == AcquisitionModes['Single Scan']):
                dim = self.width
            elif (self.AcquisitionMode == AcquisitionModes['Kinetics']):
                dim = self.width * self.scans

        cimageArray = c_int * dim
        cimage = cimageArray()
        error = self.dll.GetAcquiredData(pointer(cimage), dim)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)


        imageArray = []
        for i in range(len(cimage)):
            imageArray.append(cimage[i])

        self.imageArray = imageArray[:]
        # self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return imageArray[:]

    def set_exposure_time(self, time):
        error = self.dll.SetExposureTime(c_float(time))
        self.exposure = time
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_exposure_time(self):
        self.get_acquisition_timings()
        return self.exposure

    def get_number_accumulations(self):
        self.get_acquisition_timings()
        return self.accumulate

    def get_cycle_time(self):
        self.get_acquisition_timings()
        return self.kinetic

    def get_acquisition_timings(self):
        exposure = c_float()
        accumulate = c_float()
        kinetic = c_float()
        error = self.dll.GetAcquisitionTimings(byref(exposure), byref(accumulate), byref(kinetic))
        self.exposure = exposure.value
        self.accumulate = accumulate.value
        self.kinetic = kinetic.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_single_scan(self):
        self.set_read_mode(ReadModes['FVB'])
        self.set_acquisition_mode(AcquisitionModes['Single Scan'])
        self.set_image(1, 1, 1, self.width, 1, self.height)

    def set_cooler_mode(self, mode):
        error = self.dll.SetCoolerMode(mode)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_fan_mode(self, mode):
        # 0: fan on full
        # 1: fan on low
        # 2: fna off
        error = self.dll.SetFanMode(mode)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def abort_acquisition(self):
        error = self.dll.AbortAcquisition()
        self.verbose(error, "AbortAcquisition")

    def cooler_on(self):
        error = self.dll.CoolerON()
        self.cooler = 1
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def cooler_off(self):
        error = self.dll.CoolerOFF()
        self.cooler = 0
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def is_cooler_on(self):
        iCoolerStatus = c_int()
        self.cooler = iCoolerStatus
        error = self.dll.IsCoolerOn(byref(iCoolerStatus))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return iCoolerStatus.value

    def get_temperature(self):
        ctemperature = c_int()
        error = self.dll.GetTemperature(byref(ctemperature))
        self.temperature = ctemperature.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ctemperature.value

    def set_temperature(self,temperature):
        ctemperature = c_int(int(temperature))
        error = self.dll.SetTemperature(ctemperature)
        self.set_T = temperature
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_status(self):
        status = c_int()
        error = self.dll.GetStatus(byref(status))
        self.status = ERROR_CODE[status.value]
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return self.status

    def set_trigger_mode(self, mode):
        """
        This function will set the trigger mode that the camera will operate in.

        @param mode: trigger mode
            Valid values:
            0. Internal
            1. External
            6. External Start
            7. External Exposure (Bulb)
            9. External FVB EM (only valid for EM Newton models in FVB mode)
            10. Software Trigger
            12. External Charge Shifting

        @return:

        """
        mode = c_int(mode)
        error = self.dll.SetTriggerMode(mode)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_pixel_size(self):
        xSize = c_float()
        ySize = c_float()
        error = self.dll.GetPixelSize(byref(xSize), byref(ySize))
        self.verbose(ERROR_CODE[error], "GetPixelSize")
        return xSize, ySize

    def get_detector(self):
        width = c_int(0)
        height = c_int(0)
        error = self.dll.GetDetector(byref(width), byref(height))
        self.verbose(ERROR_CODE[error], "GetDetector")
        return width, height

    def set_image_flip(self, horizontal=1, vertical=0):
        """
        Flips the image of spectrometer. For some reason it seems that the horizontal need to be flipped

        @param horizontal:
        @param vertical:
        @return:
        """
        chorizontal = c_int(horizontal)
        cvertical = c_int(vertical)
        error = self.dll.SetImageFlip(chorizontal,cvertical)
        self.verbose(ERROR_CODE[error], "SetImageFlip")
        return ERROR_CODE[error]

    def get_baseline_clamp(self):
        '''
        This function returns the status of the baseline clamp functionality.
        With this feature enabled the baseline level of each scan in a kinetic series will be
        more consistent across the sequence.

        int * state: Baseline clamp functionality Enabled/Disabled
        1 – Baseline Clamp Enabled
        0 – Baseline Clamp Disabled

        @return: state
        '''
        state = c_int(2)
        error = self.dll.GetBaselineClamp(byref(state))
        self.verbose(ERROR_CODE[error], 'GetBaselineClamp')
        return state

    def set_baseline_clamp(self, state):
        """
        This function turns on and off the baseline clamp functionality. With this feature enabled the baseline level of
        each scan in a kinetic series will be more consistent across the sequence.

        @param state: Enables/Disables Baseline clamp functionality
                      1 – Enable Baseline Clamp
                      0 – Disable Baseline Clamp
        @return: Error code
        """
        state = c_int(state)
        error = self.dll.SetBaselineClamp(state)
        self.verbose(ERROR_CODE[error], 'SetBaselineClamp')
        return ERROR_CODE[error]


