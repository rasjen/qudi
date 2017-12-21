from qtpy import QtCore
from collections import OrderedDict
import datetime
import numpy as np
import os
from itertools import product
from time import sleep, time
import matplotlib.pyplot as plt
import matplotlib as mpl

from scipy.optimize import curve_fit
from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
from core.module import Connector, ConfigOption, StatusVar



class WLTLogic(GenericLogic):
    """
    This is the Logic class for cavity white light transmission measurement.
    """
    _modclass = 'WLTlogoc'
    _modtype = 'logic'

    # declare connectors
    nicard = Connector(interface='ConfocalScannerInterface')
    spectrometer = Connector(interface='spectrometerInterface')
    savelogic = Connector(interface='SaveLogic')

    # signals for WLT
    sigNextLine = QtCore.Signal()

    # Update signals, e.g. for GUI module
    sigParameterUpdated = QtCore.Signal(int, float, int)
    sigOutputStateUpdated = QtCore.Signal(str, bool)
    sigSpectrumPlotUpdated = QtCore.Signal(np.ndarray, np.ndarray)
    sigWLTimageUpdated = QtCore.Signal()
    signal_xy_data_saved = QtCore.Signal()

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        # locking for thread safet
        self.threadlock = Mutex()

        self.number_of_steps = 10
        self.spectrometer_resolution = 100

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._scanning_devices = self.get_connector('nicard')
        self._save_logic = self.get_connector('savelogic')
        self._spectrometer = self.get_connector('spectrometer')

        self.target_temperature = -999
        self.current_temperature = -999
        self.number_accumulations = 50
        self.exposure_time = 0.003 # sec
        self.scan_frequency = 1.0 # Hz
        self.pos_start = self._scanning_devices._cavity_position_range[0]
        self.pos_stop = self._scanning_devices._cavity_position_range[1]

        self.get_number_accumulations()
        self.get_exposure_time()
        self.get_temperature()

        self.initialize_image()
        self.initialize_spectrum_plot()


    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._spectrometer.on_deactivate()
        self._scanning_device.on_deactivate()


    def start_wlt_measurement(self, frequency, pos_start, pos_stop):
        '''
        Start the white light transmission measurement

        :return: 
        '''
        self.scan_frequency = frequency
        self._sweep(frequency, pos_start, pos_stop)

        sleep(0.5)
        self._scanning_devices.start_sweep()
        self._start_spectrometer_measurements()

        sleep(10.0)
        self._scanning_devices.close_sweep()

        pass

    def stop_wlt_measurement(self):
        '''
        Stops the white light transmission measurement
        :return: 
        '''
        pass

    def continue_wlt_measurement(self):
        '''
        Continues the white light transmission measurement

        :return: 
        '''
        pass

    def setup_wlt_measurement(self, scan_frequency, scan_range, measurement_frequency):
        '''

        :param scan_frequency: How fast is the cavity length swept
        :param scan_range: What is the min and max cavity position during the measurement
        :param exposure_time: Exposure time of the camera
        :param measurement_frequency: How fast are we going to measure
        :return: 
        '''
        pass


    def initialize_image(self):
        '''
        Setup an initial array for the WLT measurement

        :return: 
        '''
        self.wl = self._spectrometer.get_wavelengths()

        self.WLT_image = np.zeros([self.wl.size, self.number_of_steps])
        pass

    def initialize_spectrum_plot(self):
        """
        Initialises single spectrum for gui
        
        :return: 
        """
        self.wl = self._spectrometer.get_wavelengths()
        self.counts = 1e6*np.random.rand(self.wl.size)
        pass

    def get_temperature(self):
        '''
        Gets the temperature for the camera in spectrometer

        :return: the temperature of the camera in spectrometer 
        '''

        try:
            self.current_temperature = self._spectrometer.get_temperature()
        except:
            self.log.error('Could not get temperature from spectrometer')

        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations)

    def set_temperature(self, temperature=None):
        '''
        Sets the temperature for the spectrometer 

        :param temperature: in C [-75, 25]
        :return: 
        '''

        if temperature is None:
            if self.target_temperature is not None:
                temperature = self.target_temperature
            else:
                self.log.error('No target temperature')

        self._spectrometer.set_temperature(temperature)

    def set_exposure_time(self, exposure_time=None):
        '''
        Sets the exposure time for the camera in the spectrometer

        :return: 
        '''
        if exposure_time is None:
            exposure_time = self.exposure_time

        self._spectrometer.set_exposure_time(exposure_time)

        self.get_exposure_time()

    def get_exposure_time(self):
        '''
        Gets the exposure time for the camera in the spectrometer

        :return: 
        '''

        self.exposure_time = self._spectrometer.get_exposure_time()

        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations)

    def set_number_accumulations(self, number_accumulations=None):
        """
        Sets the number of accumulations that the spectrometer 

        :param number_accumulations: number of accumulations (int)
        :return: 
        """
        if number_accumulations is None:
            number_accumulations = self.number_accumulations

        self._spectrometer.set_number_accumulations(number_accumulations)

        self.get_number_accumulations()

    def get_number_accumulations(self):
        '''
        Gets the number of accumulations for the spectrometer

        :return: 
        '''
        self.number_accumulations = self._spectrometer.get_number_accumulations()
        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations)

    def get_hw_constraints(self):
        """ Return the names of all ocnfigured fit functions.
        @return object: Hardware constraints object
        """
        # FIXME: Should be from hardware
        constraints_dict = {'min_position': 0, 'max_position': 20e-6, 'min_speed': 0, 'max_speed':  100,
                            'min_temperature': -100, 'max_temperature': 30, 'min_number_accumulations': 1,
                            'max_number_accumulations': 1000, 'min_exposure': 0, 'max_exposure': 100}

        return constraints_dict

    def take_single_spectrum(self):
        self.counts = self._spectrometer.take_single_spectrum()
        self.wl = self._spectrometer.get_wavelengths()
        self.sigSpectrumPlotUpdated.emit(self.wl, self.counts)

    def _sweep(self, frequency, pos_start, pos_stop):
        """
        
        :param frequency: 
        :param pos_start: 
        :param pos_stop: 
        :return: 
        """

        start_volt = self._scanning_devices._cavity_position_to_volt(np.array(pos_start))
        stop_volt = self._scanning_devices._cavity_position_to_volt(np.array(pos_stop))

        self._scanning_devices.cavity_set_voltage(start_volt)
        sleep(1.0)
        RepOfSweep = 1

        self._scanning_devices.set_up_sweep(start_volt, stop_volt, frequency, RepOfSweep)



    def set_cavity_position(self, position):
        """
        set the position of the cavity 
        
        :param position: 
        :return: 
        """
        self._scanning_devices.cavity_set_position(position)

    def _start_spectrometer_measurements(self):
        """
        Takes data while the cavity is besing scanned
        
        :return: 
        """

        number_of_cycles = self.number_of_steps
        cycle_time = 0.5 * 1/self.scan_frequency / self.number_of_steps
        exposure_time = self.exposure_time

        data = self._spectrometer.kinetic_scan(exposure_time=exposure_time, cycle_time=cycle_time,
                                               number_of_cycles=number_of_cycles)


        self.WLT_image = data
        self.sigWLTimageUpdated.emit()

        pass




    def save_xy_data(self, colorscale_range=None, percentile_range=None):
        """ Save the current confocal xy data to file.

        Two files are created.  The first is the imagedata, which has a text-matrix of count values
        corresponding to the pixel matrix of the image.  Only count-values are saved here.

        The second file saves the full raw data with x, y, z, and counts at every pixel.

        A figure is also saved.

        @param: list colorscale_range (optional) The range [min, max] of the display colour scale (for the figure)

        @param: list percentile_range (optional) The percentile range [min, max] of the color scale
        """
        filepath = self._save_logic.get_path_for_module('WhiteLightTransmission')
        timestamp = datetime.datetime.now()
        # Prepare the metadata parameters (common to both saved files):
        parameters = OrderedDict()


        # Prepare a figure to be saved
        image_extent = [self.wl[0],
                        self.wl[-1],
                        self.pos_start,
                        self.pos_stop]
        axes = ['Wavelength', 'Position']


        fig = self.draw_figure( data=self.WLT_image,
                                image_extent=image_extent,
                                scan_axis=axes,
                                cbar_range=colorscale_range,
                                percentile_range=percentile_range)


        image_data = OrderedDict()
        # FIXME: new text

        image_data['Confocal pure XY scan image data without axis.\n'
            'The upper left entry represents the signal at the upper left pixel position.\n'
            'A pixel-line in the image corresponds to a row '
            'of entries where the Signal is in counts/s:'] = self.WLT_image

        filelabel = 'wlt_image'
        self._save_logic.save_data(image_data,
                                   filepath=filepath,
                                   timestamp=timestamp,
                                   parameters=parameters,
                                   filelabel=filelabel,
                                   fmt='%.6e',
                                   delimiter='\t',
                                   plotfig=fig)


        self.signal_xy_data_saved.emit()
        return


    def draw_figure(self, data, image_extent, scan_axis=None, cbar_range=None, percentile_range=None):
        """ Create a 2-D color map figure of the scan image.

        @param: array data: The NxM array of count values from a scan with NxM pixels.

        @param: list image_extent: The scan range in the form [hor_min, hor_max, ver_min, ver_max]

        @param: list axes: Names of the horizontal and vertical axes in the image

        @param: list cbar_range: (optional) [color_scale_min, color_scale_max].  If not supplied then a default of
                                 data_min to data_max will be used.

        @param: list percentile_range: (optional) Percentile range of the chosen cbar_range.

        @param: list crosshair_pos: (optional) crosshair position as [hor, vert] in the chosen image axes.

        @return: fig fig: a matplotlib figure object to be saved to file.
        """

        # If no colorbar range was given, take full range of data
        if cbar_range is None:
            cbar_range = [np.min(data), np.max(data)]

        # Scale color values using SI prefix
        prefix = ['', 'k', 'M', 'G']
        prefix_count = 0
        image_data = data
        draw_cb_range = np.array(cbar_range)
        image_dimension = image_extent.copy()

        while draw_cb_range[1] > 1000:
            image_data = image_data/1000
            draw_cb_range = draw_cb_range/1000
            prefix_count = prefix_count + 1

        c_prefix = prefix[prefix_count]


        # Scale axes values using SI prefix
        axes_prefix = ['', 'm', r'$\mathrm{\mu}$', 'n']
        x_prefix_count = 0
        y_prefix_count = 0

        while np.abs(image_dimension[1]-image_dimension[0]) < 1:
            image_dimension[0] = image_dimension[0] * 1000.
            image_dimension[1] = image_dimension[1] * 1000.
            x_prefix_count = x_prefix_count + 1

        while np.abs(image_dimension[3] - image_dimension[2]) < 1:
            image_dimension[2] = image_dimension[2] * 1000.
            image_dimension[3] = image_dimension[3] * 1000.
            y_prefix_count = y_prefix_count + 1

        x_prefix = axes_prefix[x_prefix_count]
        y_prefix = axes_prefix[y_prefix_count]

        # Use qudi style
        plt.style.use(self._save_logic.mpl_qd_style)

        # Create figure
        fig, ax = plt.subplots()

        # Create image plot
        cfimage = ax.imshow(image_data.transpose(),
                            cmap=plt.get_cmap('inferno'), # reference the right place in qd
                            origin="lower",
                            vmin=draw_cb_range[0],
                            vmax=draw_cb_range[1],
                            interpolation='none',
                            extent=image_dimension

                         )
        ax.set_aspect('auto')
        ax.set_xlabel(scan_axis[0] + '(' + x_prefix + 'm)')
        ax.set_ylabel(scan_axis[1] + '(' + y_prefix + 'm)')
        ax.spines['bottom'].set_position(('outward', 10))
        ax.spines['left'].set_position(('outward', 10))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

        # Draw the colorbar
        cbar = plt.colorbar(cfimage, shrink=0.8)#, fraction=0.046, pad=0.08, shrink=0.75)
        cbar.set_label('Fluorescence (' + c_prefix + 'c/s)')

        # remove ticks from colorbar for cleaner image
        cbar.ax.tick_params(which=u'both', length=0)

        # If we have percentile information, draw that to the figure
        if percentile_range is not None:
            cbar.ax.annotate(str(percentile_range[0]),
                             xy=(-0.3, 0.0),
                             xycoords='axes fraction',
                             horizontalalignment='right',
                             verticalalignment='center',
                             rotation=90
                             )
            cbar.ax.annotate(str(percentile_range[1]),
                             xy=(-0.3, 1.0),
                             xycoords='axes fraction',
                             horizontalalignment='right',
                             verticalalignment='center',
                             rotation=90
                             )
            cbar.ax.annotate('(percentile)',
                             xy=(-0.3, 0.5),
                             xycoords='axes fraction',
                             horizontalalignment='right',
                             verticalalignment='center',
                             rotation=90
                             )
        return fig