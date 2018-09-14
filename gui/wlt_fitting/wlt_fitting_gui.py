import numpy as np
import os
import pyqtgraph as pg

from core.module import Connector

from gui.guibase import GUIBase
from gui.guiutils import ColorBar
from gui.colordefs import ColorScaleInferno
from gui.colordefs import QudiPalettePale as palette
from qtpy import QtCore
from qtpy import QtWidgets
from qtpy import uic


class WLTMainWindow(QtWidgets.QMainWindow):
    """ The main window for the ODMR measurement GUI.
    """
    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'wlt_fitting.ui')

        # Load it
        super(WLTMainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()



class WLTGui(GUIBase):
    """
    This is the GUI Class for WLT measurements
    """

    _modclass = 'WLTGui'
    _modtype = 'gui'

    # declare connectors
    cavitylogic = Connector(interface='CavityLogic')
    savelogic = Connector(interface='SaveLogic')
    fitlogic = Connector(interface='WLTFitLogic')

    sigStartWLTScan = QtCore.Signal(float, float, float)
    sigStopWLTScan = QtCore.Signal()
    sigContinueWLTScan = QtCore.Signal()
    sigClearData = QtCore.Signal()
    sigSpectrometerParamsChanged = QtCore.Signal(float, float)
    # sigSaveMeasurement = QtCore.Signal(str, list, list)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Definition, configuration and initialisation of the ODMR GUI.

        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        """

        # setting up main window
        self._mw = WLTMainWindow()

        # connect to cavity logic
        self._wlt_logic = self.get_connector('cavitylogic')
        self.fitlogic = self.get_connector('fitlogic')

        # Create a QSettings object for the mainwindow and store the actual GUI layout
        self.mwsettings = QtCore.QSettings("QUDI", "WLT")
        self.mwsettings.setValue("geometry", self._mw.saveGeometry())
        self.mwsettings.setValue("windowState", self._mw.saveState())

        path = r'\\serv309\QUIN\Diamondlab\Microcavity experiment\Room temperature setup\2018'
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(path)
        self.model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllDirs)

        self.filemodel = QtWidgets.QFileSystemModel()
        self.filemodel.setRootPath(path)
        self.filemodel.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files)

        self._mw.treeView_filelocation.setModel(self.model)
        self._mw.treeView_filelocation.setRootIndex(self.model.index(path))
        self._mw.treeView_filelocation.clicked.connect(self.folder_click)

        self._mw.QlistView_filename.setModel(self.filemodel)
        self._mw.QlistView_filename.setRootIndex(self.filemodel.index(path))
        self._mw.QlistView_filename.clicked.connect(self.file_click)

        # Get the image from the logic
        self.WLT_image = pg.ImageItem(self.fitlogic.WLT_image, axisOrder='row-major')
        #self.odmr_matrix_image.setRect(QtCore.QRectF(
        #        self._odmr_logic.mw_start,
        #        0,
        #        self._odmr_logic.mw_stop - self._odmr_logic.mw_start,
        #        self._odmr_logic.number_of_lines
        #    ))

        self.spectrum_image = pg.PlotDataItem(self.fitlogic.wl,
                                          self.fitlogic.counts,
                                          pen=pg.mkPen(palette.c1, style=QtCore.Qt.DotLine),
                                          symbol='o',
                                          symbolPen=palette.c1,
                                          symbolBrush=palette.c1,
                                          symbolSize=7)#

        self.pzt_image = pg.PlotDataItem(self.fitlogic.position_time,
                                          self.fitlogic.position_data,
                                          pen=pg.mkPen(palette.c1, style=QtCore.Qt.DotLine),
                                          symbol='o',
                                          symbolPen=palette.c1,
                                          symbolBrush=palette.c1,
                                          symbolSize=7)#

        # Add the display item to the xy and xz ViewWidget, which was defined in the UI file.
        self._mw.transmission_map_PlotWidget.addItem(self.WLT_image)
        self._mw.transmission_map_PlotWidget.setLabel(axis='bottom', text='Time', units='s')
        self._mw.transmission_map_PlotWidget.setLabel(axis='left', text='Wavelength', units='m')

        proxy = pg.SignalProxy(self._mw.transmission_map_PlotWidget.scene().sigMouseMoved, rateLimit=60,
                               slot=self.mouseMoved)

        self._mw.pzt_PlotWidget.addItem(self.pzt_image)
        self._mw.pzt_PlotWidget.setLabel(axis='left', text='Voltage', units='V')
        self._mw.pzt_PlotWidget.setLabel(axis='bottom', text='time', units='s')
        self._mw.pzt_PlotWidget.showGrid(x=True, y=True, alpha=0.8)


        # Get the colorscales at set LUT
        my_colors = ColorScaleInferno()
        self.WLT_image.setLookupTable(my_colors.lut)

        ########################################################################
        #                  Configuration of the Colorbar                       #
        ########################################################################
        self.transmission_map_cb = ColorBar(my_colors.cmap_normed, 100, 0, 100000)

        # adding colorbar to ViewWidget
        self._mw.transmission_map_cb_PlotWidget.addItem(self.transmission_map_cb)
        self._mw.transmission_map_cb_PlotWidget.hideAxis('bottom')
        self._mw.transmission_map_cb_PlotWidget.hideAxis('left')
        self._mw.transmission_map_cb_PlotWidget.setLabel('right', 'Counts', units='counts/s')

        ########################################################################
        #                       Connect signals                                #
        ########################################################################
        # Internal user input changed signal

        # Internal trigger signals
        self._mw.transmission_map_cb_manual_RadioButton.clicked.connect(self.colorscale_changed)

        self._mw.transmission_map_cb_manual_RadioButton.clicked.connect(self.refresh_WLT_image)
        self._mw.transmission_map_cb_centiles_RadioButton.clicked.connect(self.refresh_WLT_image)
        self._mw.normalize_checkBox.clicked.connect(self.refresh_WLT_image)

        self._mw.transmission_map_cb_min_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_manual)
        self._mw.transmission_map_cb_max_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_manual)
        self._mw.transmission_map_cb_low_percentile_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_centiles)
        self._mw.transmission_map_cb_high_percentile_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_centiles)

        self._mw.load_image_pushButton.clicked.connect(self.load_image_data)
        self._mw.load_pzt_pushButton.clicked.connect(self.load_position_data)

        self._mw.pushButton_crop.clicked.connect(self.crop)

        # Show the Main ODMR GUI:
        self.show()
        # Update parameters
        self.adjust_xy_window()

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

    def show(self):
        """Make window visible and put it above all other windows. """
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()

    def restore_defaultview(self):
        self._mw.restoreGeometry(self.mwsettings.value("geometry", ""))
        self._mw.restoreState(self.mwsettings.value("windowState", ""))

    def colorscale_changed(self):
        """
        Updates the range of the displayed colorscale in both the colorbar and the matrix plot.
        """
        cb_range = self.get_matrix_cb_range()
        self.update_colorbar(cb_range)
        self.WLT_image.setImage(image=self.WLT_image.image.transpose(), levels=(cb_range[0], cb_range[1]))
        return

    def update_colorbar(self, cb_range):
        """
        Update the colorbar to a new range.

        @param list cb_range: List or tuple containing the min and max values for the cb range
        """

        self.transmission_map_cb.refresh_colorbar(cb_range[0], cb_range[1])
        return

    def get_matrix_cb_range(self, data=None):
        """
        Determines the cb_min and cb_max values for the matrix plot
        """
        if data is None:
            matrix_image = self.WLT_image.image
        else:
            matrix_image = data
        # If "Manual" is checked or the image is empty (all zeros), then take manual cb range.
        # Otherwise, calculate cb range from percentiles.
        if self._mw.transmission_map_cb_manual_RadioButton.isChecked() or np.max(matrix_image) < 0.1:
            cb_min = self._mw.transmission_map_cb_min_DoubleSpinBox.value()
            cb_max = self._mw.transmission_map_cb_max_DoubleSpinBox.value()
        else:
            # Exclude any zeros (which are typically due to unfinished scan)
            matrix_image_nonzero = matrix_image[np.nonzero(matrix_image)]

            # Read centile range
            low_centile = self._mw.transmission_map_cb_low_percentile_DoubleSpinBox.value()
            high_centile = self._mw.transmission_map_cb_high_percentile_DoubleSpinBox.value()

            cb_min = np.percentile(matrix_image_nonzero, low_centile)
            cb_max = np.percentile(matrix_image_nonzero, high_centile)

        cb_range = [cb_min, cb_max]
        return cb_range

    def refresh_pzt_plot(self):
        self.pzt_image.setData(x=self.fitlogic.position_time, y=self.fitlogic.position_data)

    def refresh_spectrum_graph(self, wavelengths, counts):
        self.spectrum_image.setData(x=wavelengths, y=counts)

    def refresh_WLT_image(self):
        """ Update the current XY image from the logic.

        Everytime the scanner is scanning a line in xy the
        image is rebuild and updated in the GUI.
        """
        self.WLT_image.getViewBox().updateAutoRange()

        if self._mw.normalize_checkBox.isChecked():
            WLT_image_data = (self.fitlogic.WLT_image.transpose() / self.fitlogic.WLT_image.max(axis=1)).transpose()
        else:
            WLT_image_data = self.fitlogic.WLT_image

        cb_range = self.get_matrix_cb_range(WLT_image_data)

        # Now update image with new color scale, and update colorbar
        self.WLT_image.setImage(image=WLT_image_data.transpose(), levels=(cb_range[0], cb_range[1]))
        self.update_colorbar(cb_range=cb_range)
        self.adjust_xy_window()

    def shortcut_to_xy_cb_manual(self):
        """Someone edited the absolute counts range for the xy colour bar, better update."""
        self._mw.transmission_map_cb_manual_RadioButton.setChecked(True)
        self.refresh_WLT_image()

    def shortcut_to_xy_cb_centiles(self):
        """Someone edited the centiles range for the xy colour bar, better update."""
        self._mw.transmission_map_cb_centiles_RadioButton.setChecked(True)
        self.refresh_WLT_image()

    def adjust_xy_window(self):
        """ Fit the visible window in the xy scan to full view.

        Be careful in using that method, since it uses the input values for
        the ranges to adjust x and y. Make sure that in the process of the depth scan
        no method is calling adjust_depth_window, otherwise it will adjust for you
        a window which does not correspond to the scan!
        """
        # It is extremly crucial that before adjusting the window view and
        # limits, to make an update of the current image. Otherwise the
        # adjustment will just be made for the previous image.

        yMin = self.fitlogic.wl[0]
        yMax = self.fitlogic.wl[-1]
        xMin = self.fitlogic.time[0]
        xMax = self.fitlogic.time[-1]


        #xy_viewbox.setLimits(xMin=xMin - (xMax - xMin) * 0.01,
        #                         xMax=xMax + (xMax - xMin) * 0.01,
        #                         yMin=yMin - (yMax - yMin) * 0.01,
        #                         yMax=yMax + (yMax - yMin) * 0.01)

        self.WLT_image.setRect(QtCore.QRectF(xMin, yMin, xMax - xMin, yMax - yMin))

        #xy_viewbox.updateAutoRange()
        #xy_viewbox.updateViewRange()

    def load_image_data(self):
        """
        Loads the data into plot
        
        :return: 
        """

        file_location = self.file_location

        filename = self.filename

        self.fitlogic.load_image_data(file_location, filename)
        self.refresh_WLT_image()

    def load_position_data(self):
        '''
        Loads the data into plot
        
        :return: 
        '''
        file_location = self.file_location

        filename = self.filename

        self.fitlogic.load_position_data(file_location, filename)
        self.refresh_pzt_plot()

    def folder_click(self, index):
        """
        Sets the folder path to clicked folder
        
        :param index: 
        :return: 
        """
        path = self.model.fileInfo(index).absoluteFilePath()
        self._mw.QlistView_filename.setRootIndex(self.filemodel.setRootPath(path))
        self.file_location = path

    def file_click(self, index):
        """
        Take filename from clikced file
        
        :param index: 
        :return: 
        """

        self.filename = self.filemodel.fileInfo(index).fileName()

    def mouseMoved(self,evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        vb = self._mw.transmission_map_PlotWidget.plotItem.vb
        if self._mw.transmission_map_PlotWidget.sceneBoundingRect().contains(pos):
            mousePoint = vb.mapSceneToView(pos)
            print(mousePoint.x())
            print(mousePoint.y())

    def crop(self):

        xMin = self._mw.doubleSpinBox_xmin.value()
        xMax = self._mw.doubleSpinBox_xmax.value()
        yMin = self._mw.doubleSpinBox_ymin.value()*1e-9
        yMax = self._mw.doubleSpinBox_ymax.value()*1e-9

        self.fitlogic.crop_data(xMin, xMax, yMin, yMax)

        self.refresh_WLT_image()

    def plot_tracking_of_resonance(self, data):

        track = pg.PlotDataItem(pen=pg.mkPen(palette.c1), symbol=None)
        self._mw.transmission_map_PlotWidget.addItem(track)
        track.setData(x=data[0], y=data[1])









