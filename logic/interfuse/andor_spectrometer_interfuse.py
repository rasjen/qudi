from core.module import Base
from logic.generic_logic import GenericLogic
from interface.spectrometer_interface2 import SpectrometerInterface
import platform
from ctypes import *
import sys
import numpy as np
from core.module import Connector
from time import sleep
from qtpy import QtCore

class AndorSpectrometerInterfuse(GenericLogic, SpectrometerInterface):

    _modclass = 'spectrometerinterfuce'
    _modtype = 'interfuse'

    andor = Connector(interface='SpectrometerInterface')
    shamrock = Connector(interface='SpectrometerInterface')

    verbosity = 2
    _max_slit_width = 2500  # maximal width of slit in um
    exp_time = 0.02
    cam = None

    spec = None
    closed = False
    mode = None
    single_track_minimum_vertical_pixels = 0

    sigMeasurementStarted = QtCore.Signal()
    sigMeasurementStarted_0 = QtCore.Signal()

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self._wl = None
        self._hstart = 128 - 5
        self._hstop = 128 + 5
        self.offset = 40


    def on_activate(self):
        self.andor = self.get_connector('andor')
        self.shamrock = self.get_connector('shamrock')

        start_cooler = False
        init_shutter = False

        self.andor.set_temperature(-15)
        if start_cooler:
            self.andor.cooler_on()

        # //Set Read Mode to --FVB --
        self.andor.set_read_mode(0)

        # //Set Acquisition mode to --Single scan--
        self.andor.set_acquisition_mode(1)

        # //Get Detector dimensions
        self._width, self._height = self.andor.get_detector()
        # print((self._width, self._height))
        self.min_width = 1
        self.max_width = self._width

        # Get Size of Pixels
        self._pixelwidth, self._pixelheight = self.andor.get_pixel_size()

        # //Initialize Shutter
        if init_shutter:
            self.andor.set_shutter(1, 0, 30, 30)

        # //Setup Image dimensions
        self.andor.set_image(1, 1, 1, self._width, 1, self._height)

        # shamrock = ShamrockSDK()

        # Used for calibration
        self.shamrock.set_grating_offset(self.offset)

        self.shamrock.set_number_pixels(self._width)

        self.shamrock.set_pixel_width(self._pixelwidth)

        # //Set initial exposure time
        self.andor.set_exposure_time(self.exp_time)

        # Change orientation of image
        self.andor.set_image_flip(horizontal=1, vertical=0)

    def __del__(self):
        pass
        #self.andor.shutdown()
        #self.shamrock.shutdown()

    def on_deactivate(self):
        self.log.info('Spectrometer deactivatecd')
        #self.andor.on_deactivate()
        #self.shamrock.on_deactivate()

    def set_temperature(self, temp):
        self.andor.set_temperature(temp)

    def get_temperature(self):
        return self.andor.get_temperature()

    def get_slit_width(self):
        return self.shamrock.get_auto_slit_width(1)

    def get_grating_info(self):
        num_gratings = self.shamrock.get_number_gratings()
        gratings = {}
        for i in range(num_gratings):
            lines, blaze, home, offset = self.shamrock.get_grating_info(i + 1)
            gratings[i + 1] = lines
        return gratings

    def get_grating(self):
        return self.shamrock.get_grating()

    def set_grating(self, grating):
        status = self.shamrock.set_grating(grating)
        self._wl = self.shamrock.get_calibration(self._width)
        return status

    def abort_acquisition(self):
        self.andor.abort_acquisition()

    def set_number_accumulations(self, number):
        self.andor.set_number_accumulations(number)

    def set_exposure_time(self, seconds):
        self.andor.set_exposure_time(seconds)
        self.exposure_time = seconds

    def set_slit_width(self, slitwidth):
        self.shamrock.SetAutoSlitWidth(1, slitwidth)
        if self.mode is 'Image':
            self.andor.set_image(1, 1, self.min_width, self.max_width, 1, self._height)
        else:
            self.calc_single_track_slit_pixels()
            self.andor.set_image(1, 1, 1, self._width, self._hstart, self._hstop)

    def get_wavelengths(self):
        """
        Get the wavelenghts and converts them to nanometer

        @return:
        """
        self._wl = np.asarray(self.shamrock.get_calibration())*1.0e-9
        return self._wl

    def set_full_image(self):
        self.andor.set_image(1, 1, 1, self._width, 1, self._height)
        self.mode = 'Image'

    def acquisition_data(self, start_sweep=False):
        if start_sweep is True:
            self.sigMeasurementStarted_0.emit()
            sleep(0.5)
        self.andor.start_acquisition()
        if start_sweep is True:
            sleep(0.8)
            self.sigMeasurementStarted.emit()
        acquiring = True
        while acquiring:
            sleep(1.0)
            status = self.andor.get_status()
            self.log.info(status)
            if status == 'DRV_IDLE':
                acquiring = False
                continue
            elif status == 'DRV_ACQUIRING':
                continue
            else: #not status == 'DRV_ACQUIRING':
                return None

        data = self.andor.get_acquired_data()
        return np.asarray(data)

    def set_centre_wavelength(self, wavelength):
        minwl, maxwl = self.shamrock.get_wavelength_limits(self.shamrock.get_grating())
        # if (wavelength < maxwl) and (wavelength > minwl):
        #     self.shamrock.SetWavelength(wavelength)
        #     self._wl = self.shamrock.GetCalibration(self._width)
        # else:
        #     pass
        self.shamrock.set_wavelength(wavelength)
        if (wavelength > maxwl) and (wavelength < minwl):
            self._wl = self.shamrock.get_calibration(self._width)
            print("You set the centre wavelength outside the usable range, wavelengths will be invalid")

    def calc_image_of_slit_dim(self):
        # Calculate which pixels in x direction are acutally illuminated (usually the slit will be much smaller than the ccd)
        visible_xpixels = (self._max_slit_width) / self._pixelwidth
        min_width = round(self._width / 2 - visible_xpixels / 2)
        max_width = self._width - min_width

        # This two values have to be adapted if to fit the image of the slit on your detector !
        min_width -= 25  # 45#25
        max_width -= -25  # 0#5

        if min_width < 1:
            min_width = 1
        if max_width > self._width:
            max_width = self._width

        return min_width, max_width

    def set_image_of_slit(self):
        self.shamrock.set_wavelength(0)

        min_width, max_width = self.calc_image_of_slit_dim()
        self.min_width = min_width
        self.max_width = max_width

        self.andor.set_image(1, 1, self.min_width, self.max_width, 1, self._height)
        self.mode = 'Image'

    def take_image_of_slit(self):
        return self.take_image(self.max_width - self.min_width + 1, self._height)

    def set_single_track_minimum_vertical_pixels(self, pixels):
        self.single_track_minimum_vertical_pixels = pixels

    def calc_single_track_slit_pixels(self):
        slitwidth = self.shamrock.get_auto_slit_width(1)
        pixels = (slitwidth / self._pixelheight)
        if pixels < self.single_track_minimum_vertical_pixels:  # read out a minimum of 7 pixels, this is the smallest height that could be seen on the detector, smaller values will give wrong spectra due to chromatic abberation
            pixels = self.single_track_minimum_vertical_pixels
        middle = round(self._height / 2)
        self._hstart = round(middle - pixels / 2)
        self._hstop = round(middle + pixels / 2) + 3
        print('Detector readout:' + str(self._hstart) + ' - ' + str(self._hstop) + ' pixels, middle at ' + str(
            middle) + ', throwing away ' + str(self._hstop - 3) + '-' + str(self._hstop))
        # the -3 is a workaround as the detector tends to saturate the first two rows, so we take these but disregard them later

    def set_single_track(self, hstart=None, hstop=None):
        if (hstart is None) or (hstop is None):
            self.calc_single_track_slit_pixels()
        else:
            self._hstart = hstart
            self._hstop = hstop
        self.andor.set_image(1, 1, 1, self._width, self._hstart, self._hstop)
        self.mode = 'SingleTrack'

    def take_single_spectrum(self):
        self.andor.set_read_mode(0)
        self.andor.set_acquisition_mode(1)
        data = self.acquisition_data()
        return data

    def get_exposure_time(self):
        return self.andor.get_exposure_time()

    def get_number_accumulations(self):
        return self.andor.get_number_accumulations()

    def kinetic_scan(self, exposure_time=None, cycle_time=None, number_of_cycles=None, sweep_start=False):
        """
        Takes a kinetic scan

        @param exposure_time: This is the time in seconds during which the CCD collects light prior to readout
        @param cycle_time: This is the period in seconds between the start of individual scans
        @param number_of_cycles: This is the number of scans (or ‘accumulated scans’) you specify to be in your series
        @return:
        """

        # Full vertical binning
        self.andor.set_read_mode(0)
        # Set Kinetic scan
        self.andor.set_acquisition_mode(3)
        # Sets exposure time
        if exposure_time is not None:
            self.andor.set_exposure_time(exposure_time)
        else:
            self.log.warning('No exposure time given for kinetic scan')
        # Sets number of accumulations to 1
        self.andor.set_number_accumulations(1)

        if cycle_time is not None:
            self.andor.set_kinetic_cycle_time(cycle_time)
        else:
            self.log.warning('No cycle time givin for the kinetic scan')

        if number_of_cycles is not None:
            self.andor.set_number_kinetics(number_of_cycles)
        else:
            self.log.warning('No number given for then number cycles in kinetic scan')

        #Take the data
        data = self.acquisition_data(start_sweep=sweep_start)

        # Reshape data
        data = data.reshape(number_of_cycles, int(data.size/number_of_cycles)).transpose()

        return data

    def set_cycle_time(self, cycle_time):
        self.andor.set_acquisition_mode(3)
        self.andor.set_kinetic_cycle_time(cycle_time)

    def get_cycle_time(self):
        return self.andor.get_cycle_time()



