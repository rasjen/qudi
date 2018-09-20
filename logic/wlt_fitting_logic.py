from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
import numpy as np
from os.path import join



class WLTFitLogic(GenericLogic):
    """
    This module is made for fitting 2D scan of a fiber cavity
    
    """
    _modclass = 'fitlogic'
    _modtype = 'logic'


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # locking for thread safety
        self.lock = Mutex()

    def on_activate(self):
        self.wl = np.linspace(100e-9,1e-6,100)
        self.counts = np.zeros_like(self.wl)
        self.position_time = np.linspace(0,1,10)
        self.position_data = np.zeros_like(self.position_time)
        self.time = np.linspace(0,100,100)
        self.WLT_image = np.zeros([len(self.wl), 1600])
        self.start_point = None

    def on_deactivate(self):
        pass

    def load_image_data(self, file_location, filename):
        data = np.loadtxt(join(file_location, filename), comments='#')
        '''
           Load scan parameters
        '''
        parameters = []
        with open(join(file_location, filename), 'r') as f:
            lines = f.readlines()
            for line in lines[5:15]:
                string = line.strip()
                # print(line.strip())
                for elem in string.split():
                    try:
                        parameters.append(float(elem))
                    except ValueError:
                        pass

        self.wl = np.linspace(parameters[0],parameters[1], data.shape[1])
        self.time = np.linspace(parameters[8], parameters[9], data.shape[0])

        self.pos_start = parameters[2]
        self.pos_stop = parameters[3]
        self.scan_frequency = parameters[4]
        self.exposure_time = parameters[5]
        self.number_of_steps = parameters[6]
        self.cycle_time = parameters[7]

        self.WLT_image = data

        return 0

    def load_position_data(self, file_location, filename):
        '''
        Simply loading the data record by the scope from the strain gauge

        :param file_location: ex. r'\\serv309\QUIN\Diamondlab\Microcavity experiment'
        :param filename: ex. 'filename.dat'
        :return:    0
        '''

        pzt_data = np.loadtxt(join(file_location, filename), comments='#')

        pzt_time = pzt_data[0]
        pzt_voltage = pzt_data[1]

        self.position_time = pzt_time
        self.position_data = pzt_voltage

        return 0

    def fit_bare_cavity_resonane(self):
        pass

    def fit_cavity_w_diamond_resosnances(self):
        pass

    def extract_resoanaces_from_image(self):
        """ Gives an array with wavelength and positions of a single resonances
        
        
        """
        self.wl_res = []
        self.pos_res = []

        start_line = 0
        stop_line = 10
        start_pos = 0


        start_guess = (start_line, start_pos)

        fit_range = np.arange(start_line, stop_line, 1)

        for i in fit_range:

            if i == 0:
                """ Find peak near guess"""
                last = start_guess

            else:
                """ From last peak find highest peak """
                last = self.pos_res[i-1]

            span = self.span
            search_interval = [last - span, last + span]

            (peak_wl, peak_pos) = np.argmax(self.WLT_image[i, search_interval[0]:search_interval[1]])
            # Add to lists
            self.wl.append(peak_wl)
            self.pos_res.append(peak_pos)


        # Signal fit updated:



        return 0

    def fit_strain_gauge_data(self):
        self.pzt_voltage_fit = self._polyfit(self.pzt_time, self.pzt_voltage)

    def _polyfit(self, xdata, ydata, order=3):
        p_coefficient = np.polyfit(xdata, ydata, order)
        p_fit_function = np.poly1d(p_coefficient)
        y_fit = p_fit_function(xdata)

        return y_fit

    def crop_data(self, xMin, xMax, yMin, yMax):
        '''
        Crops data
        
        :return: 
        '''

        xmin = np.argmin(np.abs(self.time - xMin))
        xmax = np.argmin(np.abs(self.time - xMax))

        ymin = np.argmin(np.abs(self.wl - yMin))
        ymax = np.argmin(np.abs(self.wl - yMax))

        self.WLT_image = self.WLT_image[xmin:xmax+1, ymin:ymax+1]
        self.wl = self.wl[ymin:ymax+1]
        self.time = self.time[xmin:xmax+1]

    def initial_resonances_position(self, time, wavelength):
        self.point0 = [time, wavelength]

        self.point0_index = self.from_units_to_index(time, wavelength)

    def from_units_to_index(self, time=None, wavelength=None):
        '''
        converts the times and wavelengths that are seen on the sceen to the indicies
        
        :param time: 
        :param wavelength: 
        :return: 
        '''

        return_list = []
        if time is not None:
            index_time = np.argmin(np.abs(self.time - time))
            return_list.append(index_time)

        if wavelength is not None:
            index_wavelength = np.argmin(np.abs(self.wl - wavelength))
            return_list.append(index_wavelength)

        return return_list

    def find_nearest_peak(self, start_point=None):

        start_time = start_point[0]
        start_wl = start_point[1]

        window = 10
        low = np.max([0, start_wl-window])
        high = np.min([len(self.wl)-1, start_wl + window])

        current_time = start_time+1
        current_wl = np.argmax(self.WLT_image[current_time, low:high]) + low
        current_point = [current_time, current_wl]
        return current_point

    def track_resonances(self):
        result_list = [self.point0_index]

        for t in range(100):
            result_list.append(self.find_nearest_peak(result_list[-1]))

        result_array = np.array(result_list).transpose()
        
        return result_array














