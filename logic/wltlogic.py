from qtpy import QtCore
from collections import OrderedDict
import datetime
import numpy as np
import os
from itertools import product
import matplotlib.pyplot as plt
import matplotlib as mpl
from time import sleep
from scipy.optimize import curve_fit
from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
from core.module import Connector, ConfigOption, StatusVar



class WLTLogic(GenericLogic):
    """
    This is the Logic class for cavity white light transmission measurement.
    """
    _modclass = 'WLTlogic'
    _modtype = 'logic'

    # declare connectors
    scanner = Connector(interface='confocallogic')
    spectrometer = Connector(interface='spectrometerInterface')
    savelogic = Connector(interface='SaveLogic')
    #scopelogic = Connector(interface='ScopeLogic')

    # signals for WLT
    sigNextLine = QtCore.Signal()

    # Update signals, e.g. for GUI module
    sigParameterUpdated = QtCore.Signal(int, float, int, float)
    sigOutputStateUpdated = QtCore.Signal(str, bool)
    sigSpectrumPlotUpdated = QtCore.Signal(np.ndarray, np.ndarray)
    sigWLTimageUpdated = QtCore.Signal()
    sigPztimageUpdated = QtCore.Signal()
    signal_xy_data_saved = QtCore.Signal()
    sigMeasurementStarted = QtCore.Signal()
    sigMeasurementFinished = QtCore.Signal()

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        # locking for thread safet
        self.threadlock = Mutex()

        self.number_of_steps = int(10)
        self.spectrometer_resolution = int(100)

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._scanner_device = self.scanner()
        self._save_logic = self.savelogic()
        self._spectrometer = self.spectrometer()
        #self._scope = self.get_connector('scopelogic')

        self.clock_frequency = 100 # Hz
        self.target_temperature = -999
        self.current_temperature = -999
        self.number_accumulations = 1
        self.exposure_time = 0.02 # sec
        self.scan_frequency = 1.0 # Hz
        self.cycle_time = 0.02
        self.pos_start = self._scanner_device.z_range[0]
        self.pos_stop = self._scanner_device.z_range[1]
        self.time_start = self.number_accumulations * self.cycle_time
        self.time_stop = self.number_accumulations
        self.position_time = np.linspace(0, 1/self.scan_frequency, 100)
        self.position_data = np.ones_like(self.position_time)

        self.get_number_accumulations()
        self.get_exposure_time()
        self.get_temperature()

        self.initialize_image()
        self.initialize_spectrum_plot()

        self.sigMeasurementStarted.connect(self._scanner_device.start_sweep)
        self.sigMeasurementFinished.connect(self.stop_wlt_measurement)
        self._spectrometer.sigSpectrumDataAcquired.connect(self.update_spectrum_data)
        self._spectrometer.sigImageDataAcquired.connect(self.update_image_data)

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        #self._spectrometer.on_deactivate()
        #self._scanner_device.on_deactivate()

    def start_wlt_measurement(self, frequency, pos_start, pos_stop):
        '''
        Start the white light transmission measurement

        :return: 
        '''

        with self.threadlock:
            # set parameters
            self.pos_start = pos_start
            self.pos_stop = pos_stop
            self.scan_frequency = frequency

            self.set_cavity_position(pos_start)

            # Set up master clock
            self.log.info('Measurement started')
            self._scanner_device.set_up_sweep(pos_start, pos_stop, frequency, self.number_of_steps)

            # Starts triggered measurement for spectrometer
            self.log.info('Starting spectrometer')
            self._set_up_kinetic_scan()


            # Starts the Nicard
            self.log.info('Starting scanning')
            self._spectrometer.sigStartAcquiring.emit()
            sleep(1)
            self.sigMeasurementStarted.emit()
        return 0

    def set_positions_parameters(self, pos_start, pos_stop, number_of_steps, frequency):
        self.pos_start = pos_start
        self.pos_stop = pos_stop
        self.number_of_steps = number_of_steps
        self.scan_frequency = frequency

    def stop_wlt_measurement(self):
        '''
        Stops the white light transmission measurement
        :return:
        '''
        # Set back internal trigger
        self._spectrometer.set_trigger_mode(0)

        # Save data
        self.save_xy_data()
        self.save_position_data()
        self.log.info('Data saved')

        self._scanner_device.stop_sweep()
        self.set_cavity_position(self.pos_start)
        self.log.info('Stopped the ni sweep')


    def continue_wlt_measurement(self):
        '''
        Continues the white light transmission measurement

        :return:
        '''
        pass

    def initialize_image(self):
        '''
        Setup an initial array for the WLT measurement

        :return: 
        '''

        self.wl = self._spectrometer.get_wavelengths()
        if len(self.wl) == 0:
            # did not load wl from spectrometer
            self.wl = np.arange(0,100, 11)

        self.WLT_image = np.random.random([self.number_of_steps, self.wl.size])
        return 0

    def initialize_spectrum_plot(self):
        """
        Initialises single spectrum for gui
        
        :return: 
        """
        self.wl = self._spectrometer.get_wavelengths()
        if len(self.wl) == 0:
            # did not lead wl from spectrometer
            self.wl = np.arange(0,100,11)

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

        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations, self.cycle_time)

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

    def set_cycle_time(self, cycle_time):
        self._spectrometer.set_cycle_time(cycle_time)

        self.get_cycle_time()

    def get_cycle_time(self):


        self.cycle_time = self._spectrometer.get_cycle_time()

        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations, self.cycle_time)

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

        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations, self.cycle_time)

    def get_cycle_time(self):
        '''
        Gets the exposure time for the camera in the spectrometer

        :return:
        '''

        self.cycle_time = self._spectrometer.get_cycle_time()

        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations, self.cycle_time)

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
        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations, self.cycle_time)

    def get_hw_constraints(self):
        """ Return the names of all ocnfigured fit functions.
        @return object: Hardware constraints object
        """
        # FIXME: Should be from hardware
        constraints_dict = {'min_position': 0, 'max_position': 20e-6, 'min_speed': 0, 'max_speed':  100,
                            'min_temperature': -100, 'max_temperature': 30, 'min_number_accumulations': 1,
                            'max_number_accumulations': 10000, 'min_exposure': 0, 'max_exposure': 10000}

        return constraints_dict

    def take_single_spectrum(self):
        self._spectrometer.take_single_spectrum()

    def update_spectrum_data(self):
        self.counts = np.array(self._spectrometer.data)
        self.wl = self._spectrometer.wl
        self.sigSpectrumPlotUpdated.emit(self.wl, self.counts)

    def update_image_data(self):

        # Gets data from spectrometer
        with self.threadlock:
            data = np.array(self._spectrometer.data)
            self.data = data.reshape(int(self.number_of_steps), int(data.size/self.number_of_steps)).transpose()

            # Get the strain gauge data from the NI card
            line_position_data = self._scanner_device.read_position()
            self.log.info('Measurement finished')

            # Used for making the plot
            self.time_stop = 1/self.scan_frequency * self.number_of_steps
            self.position_data = line_position_data[1:]
            self.position_time = np.linspace(0, self.time_stop, len(self.position_data))
            self.WLT_image = self.data.transpose()


            # Update image
            self.sigPztimageUpdated.emit()
            self.sigWLTimageUpdated.emit()
            self.log.info('Images updates')

            self.sigMeasurementFinished.emit()


    def set_cavity_position(self, position):
        """
        set the position of the cavity 
        
        :param position: 
        :return: 
        """
        self._scanner_device.set_position(tag='wltlogic', z=position)

    def _set_up_kinetic_scan(self):
        """
        Takes data while the cavity is besing scanned
        
        :return: 
        """
        self.wl = self._spectrometer.get_wavelengths()
        number_of_cycles = int(self.number_of_steps)
        cycle_time = self.cycle_time
        exposure_time = self.exposure_time

        if exposure_time > cycle_time:
            self.log.warning('Exposure is larger than the cycle time. Setting cycle time equal to exposure time')
            cycle_time = exposure_time

        self.log.info('set up spectrometer')
        self._spectrometer.kinetic_scan(exposure_time=exposure_time, cycle_time=cycle_time,
                                               number_of_cycles=number_of_cycles, trigger=1)


        return 0

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

        parameters['wavelength min (m)'] = self.wl[0]
        parameters['wavelength max (m)'] = self.wl[-1]
        parameters['pos min (m)'] = self.pos_start
        parameters['pos max (m)'] = self.pos_stop
        parameters['scan_frequency (Hz)'] = self.scan_frequency
        parameters['exposure time (s)'] = self.exposure_time
        parameters['number of steps'] = self.number_of_steps
        parameters['cycle_time (s)'] = self.cycle_time
        parameters['Time start (m)'] = self.time_start
        parameters['Time stop (m)'] = self.time_stop


        # Prepare a figure to be saved
        image_extent = [self.time_start,
                        self.time_stop,
                        self.wl[0],
                        self.wl[-1]]
        axes = ['Time', 'Wavelength']


        fig = self.draw_figure( data=self.WLT_image,
                                image_extent=image_extent,
                                scan_axis=axes,
                                cbar_range=colorscale_range,
                                percentile_range=percentile_range)


        image_data = OrderedDict()
        # FIXME: new text

        image_data['White light transmission measurement scan.\n'
            'The upper left entry represents the signal at the upper left pixel position.\n'
            'A pixel-line in the image corresponds to a row '
            'of entries where the Signal is in counts/s:'] = self.WLT_image

        filelabel = 'wlt_image'
        self._save_logic.save_data(image_data,
                                   filepath=filepath,
                                   timestamp=timestamp,
                                   parameters=parameters,
                                   filelabel=filelabel,
                                   fmt='%.8e',
                                   delimiter='\t',
                                   plotfig=fig)


        self.signal_xy_data_saved.emit()
        return 0


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

    def save_position_data(self):

        filepath = self._save_logic.get_path_for_module('WhiteLightTransmission')
        timestamp = datetime.datetime.now()
        # Prepare the metadata parameters (common to both saved files):
        parameters = OrderedDict()

        #parameters['wavelength min (m)'] = self.wl[0]

        position_data = OrderedDict()
        # FIXME: new text

        position_data_save = np.vstack((self.position_time, self.position_data))

        position_data['save in voltage * 2 to get position in micron'] = position_data_save

        filelabel = 'position_data'
        self._save_logic.save_data(position_data,
                                   filepath=filepath,
                                   timestamp=timestamp,
                                   parameters=parameters,
                                   filelabel=filelabel,
                                   fmt='%.8e',
                                   delimiter='\t')


        return 0

    def start_ramp(self, amplitude, freq):
        self._scanner_device.start_ramp(amplitude, freq)

    def stop_ramp(self):
        self._scanner_device.stop_ramp()

    def cooler_on(self):
        self._spectrometer.cooler_on()

    def cooler_off(self):
        self._spectrometer.cooler_off()
