from core.module import Base
from interface.spectrometer_interface2 import SpectrometerInterface
import platform
from ctypes import *
import sys
from time import time

ERROR_CODE = {
    20201: "SHAMROCK_COMMUNICATION_ERROR",
    20202: "SHAMROCK_SUCCESS",
    20266: "SHAMROCK_P1INVALID",
    20267: "SHAMROCK_P2INVALID",
    20268: "SHAMROCK_P3INVALID",
    20269: "SHAMROCK_P4INVALID",
    20270: "SHAMROCK_P5INVALID",
    20275: "SHAMROCK_NOT_INITIALIZED"
}

class Shamrock(Base, SpectrometerInterface):
    """
    This the module for controlling the shamrock spectrometer
    
    """
    _modtype = 'Shamrock'
    _modclass = 'hardware'

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def __del__(self):
        """
        Deleting the instance

        :return: 
        """
        self.shutdown()

    def on_activate(self):
        if platform.system() == "Windows":
            self.dll2 = windll.LoadLibrary(r"C:\Program Files\Andor SDK\Shamrock64\atshamrock.dll")
            self.dll = windll.LoadLibrary(r"C:\Program Files\Andor SDK\Shamrock64\ShamrockCIF.dll")
        else:
            self.log.error("Cannot detect operating system, wil now stop")


        self.verbosity = True
        Error_init = self.initialize()

        self.shamrocks = None
        self.current_shamrock = 0  # for more than one Shamrock this has to be varied, see ShamrockGetNumberDevices
        self.grating = None
        self.current_grating = None
        self.motor_present = None
        self.current_wavelength = None
        self.wavelength_is_zero = None
        self.current_slit = 2
        self.slit_present = None
        self.out_slit_width = None
        self.slit_width = None
        self.pixel_width = None
        self.pixel_number = None
        self.status = Error_init
        self.current_grating = None

    def on_deactivate(self):
        self.close()

    def set_verbose(self, state=True):
        self.verbosity = state

    def verbose(self, error, function=''):
        """
        Print error messeages

        :param error: 
        :param function: 
        :return: 
        """
        if self.verbosity is True:
            self.log.info('{}:{}'.format(function, error))

    # basic Shamrock features
    def initialize(self):
        error = self.dll.ShamrockInitialize("")
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def close(self):
        error = self.dll.ShamrockClose()
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_number_devices(self):
        no_shamrocks = c_int()
        error = self.dll.ShamrockGetNumberDevices(byref(no_shamrocks))
        self.shamrocks = no_shamrocks.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    # Calibration functions
    def set_pixel_width(self, width):
        error = self.dll.ShamrockSetPixelWidth(self.current_shamrock, width)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_pixel_width(self):
        pixelw = c_float()
        error = self.dll.ShamrockGetPixelWidth(self.current_shamrock, byref(pixelw))
        self.pixel_width = pixelw.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_number_pixels(self):
        numpix = c_int()
        error = self.dll.ShamrockGetNumberPixels(self.current_shamrock, byref(numpix))
        self.pixel_number = numpix.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_number_pixels(self, pixels):
        error = self.dll.ShamrockSetNumberPixels(self.current_shamrock, pixels)
        self.pixel_number = pixels
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    # Wavelength features
    def wavelength_is_present(self):
        ispresent = c_int()
        error = self.dll.ShamrockWavelengthIsPresent(self.current_shamrock, byref(ispresent))
        self.motor_present = ispresent.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_wavelength(self):
        curr_wave = c_float()
        error = self.dll.ShamrockGetWavelength(self.current_shamrock, byref(curr_wave))
        self.current_wavelength = curr_wave.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return self.current_wavelength

    def at_zero_order(self):
        is_at_zero = c_int()
        error = self.dll.ShamrockAtZeroOrder(self.current_shamrock, byref(is_at_zero))
        self.wavelength_is_zero = is_at_zero.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_wavelength_limits(self):
        min_wl = c_float()
        max_wl = c_float()
        error = self.dll.ShamrockGetWavelengthLimits(self.current_shamrock, self.current_grating, byref(min_wl),
                                                     byref(max_wl))
        self.wl_limits = [min_wl.value, max_wl.value]
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_wavelength(self, centre_wl):
        error = self.dll.ShamrockSetWavelength(self.current_shamrock, c_float(centre_wl))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def go_to_zero_order(self):
        error = self.dll.ShamrockGotoZeroOrder(self.current_shamrock)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    # basic Grating features
    def grating_is_present(self):
        is_present = c_int()
        error = self.dll.ShamrockGratingIsPresent(self.current_shamrock, is_present)
        self.grating = is_present.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return self.grating

    def get_turret(self):
        self.Turret = c_int()
        error = self.dll.ShamrockGetTurret(self.current_shamrock, byref(self.Turret))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return self.Turret

    def get_number_gratings(self):
        self.noGratings = c_int()
        error = self.dll.ShamrockGetNumberGratings(self.current_shamrock, byref(self.noGratings))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return self.noGratings

    def get_grating(self):
        grating = c_int()
        error = self.dll.ShamrockGetGrating(self.current_shamrock, byref(grating))
        self.current_grating = grating.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_grating(self,grating):
        error = self.dll.ShamrockSetGrating(self.current_shamrock, grating)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_grating_info(self):
        if self.current_grating == None:
            self.get_grating()
        lines = c_float()
        blaze = c_char()
        home = c_int()
        offset = c_int()
        error = self.dll.ShamrockGetGratingInfo(self.current_shamrock, self.current_grating, byref(lines), byref(blaze),
                                                byref(home), byref(offset))
        self.CurrGratingInfo = [lines.value, blaze.value, home.value, offset.value]
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return self.CurrGratingInfo

    def get_grating_offset(self):
        if self.current_grating == None:
            self.getGrating()
        self.GratingOffset = c_int()  # not this is in steps, so int
        error = self.dll.ShamrockGetGratingOffset(self.current_shamrock, self.current_grating,
                                                  byref(self.GratingOffset))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return self.GratingOffset

    def set_grating_offset(self, offset):
        error = self.dll.ShamrockSetGratingOffset(self.current_shamrock, self.current_grating, c_int(offset))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def get_detector_offset(self):
        self.DetectorOffset = c_int()  # not this is in steps, so int
        error = self.dll.ShamrockGetDetectorOffset(self.current_shamrock, byref(self.DetectorOffset))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return self.DetectorOffset

    def set_detector_offset(self, offset):
        error = self.dll.ShamrockSetDetectorOffset(self.current_shamrock, self.current_grating, c_int(offset))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_turret(self, turret):
        error = self.dll.ShamrockSetTurret(self.current_shamrock, c_int(turret))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def eeprom_get_optical_params(self):
        self.FocalLength = c_float()
        self.AngularDeviation = c_float()
        self.FocalTilt = c_float()
        error = self.dll.ShamrockEepromGetOpticalParams(self.current_shamrock, byref(self.FocalLength),
                                                        byref(self.AngularDeviation), byref(self.FocalTilt))
        return ERROR_CODE[error]

    def get_calibration(self):
        self.get_number_pixels()
        ccalib = c_float * self.pixel_number
        ccalib_array = ccalib()
        error = self.dll.ShamrockGetCalibration(self.current_shamrock, pointer(ccalib_array), self.pixel_number)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        calib = []

        for i in range(len(ccalib_array)):
            calib.append(ccalib_array[i])

        self.wl_calibration = calib[:]

        return calib

    # Output Slits
    def get_auto_slit_width(self, slit):
        slitw = c_float()
        error = self.dll.ShamrockGetAutoSlitWidth(self.current_shamrock, slit, byref(slitw))
        self.out_slit_width = slitw.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def set_auto_slit_width(self, slit, width):
        slit_w = c_float(width)
        error = self.dll.ShamrockSetAutoSlitWidth(self.current_shamrock, slit, slit_w)
        self.out_slit_width = width
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    # Input Slits
    def get_slit(self):
        slitw = c_float()
        error = self.dll.ShamrockGetSlit(self.current_shamrock, byref(slitw))
        self.slit_width = slitw.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return self.slit_width

    def set_slit(self, width):
        slit_w = c_float(width)
        error = self.dll.ShamrockSetSlit(self.current_shamrock, slit_w)
        time.sleep(1)
        self.ShamrockGetSlit()
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def slit_reset(self):
        error = self.dll.ShamrockSlitReset(self.current_shamrock)
        time.sleep(1)
        self.ShamrockGetSlit()
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]


