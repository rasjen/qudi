"""TIScam

View image from a The Imaging Source USB camera with overlaid coordinates and crosshair.

Usage:
  tiscam.py
  tiscam.py -z <zf>
  
Options:
  -z <zf>  Microscope zoom setting [default: 0.58].
  
"""
#from __future__ import division

import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
from matplotlib.text import Text
from matplotlib.widgets import RadioButtons
from datetime import datetime
from scipy.special import erf
from scipy.misc import imsave
import time
import os
import numpy as np
import cv2
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from docopt import docopt

if __name__ == '__main__':
    arguments = docopt(__doc__, version='TIScam 0.2')
    
snapshot_dir = 'C:/tmp/snapshots/'
signal_dir = 'C:/tmp/snapshots/signal/'
signal_fname = 'do_snapshot.txt'

# zoom setting of the Varitar microscope - to be handled by commandline or GUI
try:
    zoomfactor = float(arguments['-z'])
except ValueError:
    print('invalid zoom factor; setting to 0.58')
    zoomfactor = .58

real_size = np.array([5952, 4464]) / (9.52 * zoomfactor)  # object size in um
real_size *= 1.05  # calibration is off by 12% for some reason

crosshair_opacity_scale = [1, .5, 0]
cop_ix = 0
edge_opacity_scale = [1, .3, 0]
ed_ix = 0


cam = cv2.VideoCapture(0)  # device 0 might be the laptop's webcam

plt.rcParams['toolbar'] = 'None'

img_ini = cam.getImage().transpose(3)
size = np.array(img_ini.size)
cs = 20
px, py = size[0]/2., size[1]/2.

fig = plt.figure(figsize=size/plt.rcParams['figure.dpi']/1)
ax = plt.axes([0.0, 0.0, 1, 1], frameon=False)

axzoom = plt.axes([.95, .9, .07, .1], frameon=False, axisbg=(0,0,0,.5))
radio = RadioButtons(axzoom, activecolor='w',
                     labels=('.58x', '1x', '2x', '3x', '4x', '5x', '6x', '7x'))
for label in radio.labels:
    label.set_color('w')
    

def change_zoom(label):
    global zoomfactor, real_size
    old_zoomfactor = zoomfactor
    zoomfactor = float(label[:-1])
    real_size = np.array([5952, 4464]) / (9.52 * zoomfactor)
    curr_xlim = np.array(ax.get_xlim())
    curr_ylim = np.array(ax.get_ylim())
    ax.set_xlim(curr_xlim * old_zoomfactor/zoomfactor)
    ax.set_ylim(curr_ylim * old_zoomfactor/zoomfactor)
    img.set_extent(ax.get_xlim() + ax.get_ylim())

radio.on_clicked(change_zoom)


img = ax.imshow(img_ini, origin='lower', 
                extent=[-real_size[0]/2., real_size[0]/2.,
                        -real_size[1]/2., real_size[1]/2.])
                
ax.grid(color=(.5, 1, .5), alpha=.3, linewidth=2, linestyle='--')
ax.tick_params(direction='in', labelcolor=(.5, 1, .5))
for tick in ax.yaxis.get_major_ticks():
    tick.set_pad(-15)
    tick.label1.set_horizontalalignment('left')
for tick in ax.xaxis.get_major_ticks():
    tick.set_pad(-15)

#cross = [Line2D([px, px], [py-cs/2., py+cs/2.], transform=ax.transData, color='red'),
#         Line2D([px-cs/2., px+cs/2.], [py, py], transform=ax.transData, color='red')]



recordvideo = False
videoframes = np.zeros((100,) + img.get_array().shape, dtype='uint8')
frametimes = []
axesframes = []
framecount = 0
no_frames = 20
snapshot_path = ''


class Crosshairs():
    def __init__(self, px=0, py=0):
        self.px = px
        self.py = py
        self.cs = 20
        self.update(self.px, self.py, crosshair_opacity_scale[cop_ix])
        
    def update(self, px, py, cop=1):
        self.artists = [Line2D([], [], transform=ax.transData, color=(1,0,0,cop)),
                        Line2D([], [], transform=ax.transData, color=(1,0,0,cop)),
                        Circle([px, py], 25, transform=ax.transData, linewidth=2, linestyle='dashed',
                               facecolor=(1,0,0,0), edgecolor=(1,0,0,.5*cop)),
                        Circle([px, py], 67.5, transform=ax.transData, linewidth=2, linestyle='dotted',
                               facecolor=(1,0,0,.1*cop), edgecolor=(1,0,0,.5*cop)),
                        Circle([px, py], 120, transform=ax.transData, linewidth=2, linestyle='dotted',
                               facecolor=(1,0,0,.1*cop), edgecolor=(1,0,0,.5*cop))]
                               
        self.artists[0].set_data([px, px], [py-cs/2., py+cs/2.])
        self.artists[1].set_data([px-cs/2., px+cs/2.], [py, py])


def process_image(im, show_edges=True):
    r, g, b = cv2.split(np.asarray(im))
    edges = cv2.Canny(cv2.GaussianBlur(r, (9,9), 0), 10, 20)
    edges_op = edge_opacity_scale[ed_ix]
    if edges_op != 0:
        with_edges = cv2.addWeighted(r, 1, edges, edges_op, 0)
        im = cv2.merge((with_edges, with_edges, b))
    if increase_contrast:
        im = np.take(LUT, im)
        
    info = dict(contrast=edges.sum())
    
    return im, info


def record(im, record_axes=False):
    global recordvideo, videoframes, frametimes, framecount, no_frames
    global snapshot_path
    
    if not recordvideo:
        return

    if framecount == 0:
        with open(signal_dir + signal_fname, 'r') as f:
            path = (snapshot_dir + f.readline()).strip()
            if path == snapshot_path:
                recordvideo = False
                return
            else:
                snapshot_path = path
        if not os.path.exists(snapshot_path):
            os.makedirs(snapshot_path)

    videoframes[framecount] = im
    frametimes.append(datetime.now())
    framecount += 1

    if record_axes:
        fig.savefig(snapshot_path + 's%04d.jpg' % framecount)
        
    if framecount >= no_frames:
        fig.savefig(snapshot_path + 'final_' + 
                    datetime.now().strftime('%H%M%S-%f')[:-3] + '.jpg')
        for i in range(no_frames):
            if no_frames < 100:
                snapnum = 's{:02d}-'.format(i)
            else:
                snapnum = 's{:04d}-'.format(i)
            imsave(snapshot_path + snapnum + 
                   frametimes[i].strftime('%H%M%S-%f')[:-3] + '.jpg', 
                   videoframes[i])
            
        framecount = 0
        frametimes = []
        recordvideo = False
        print('wrote {} frames to {}'.format(no_frames, snapshot_path))
        


cross = Crosshairs()
fps = [0, 0, 0]
LUT = erf(3 * (np.arange(256)/255. - .5))
show_edges = True
increase_contrast = False


def init():
    img.set_data(img_ini)
    ax.artists = cross.artists
    
    return ax.artists


def update(*args):
    global fps, LUT, show_edges, increase_contrast
    im = cam.getImage().transpose(3)
    im, info = process_image(im)
    img.set_data(im)
    
    ax.artists = cross.artists
    
    infotext = ''
    now = datetime.now()
    
    if now.second == fps[1]:
        fps[0] += 1
    else:
        #print fps[0], info['contrast']      
        fps = [0, now.second, fps[0]]
    
    
    infotext += now.strftime('%H:%M:%S.%f')[:-3] + '\n'
#    infotext += 'contrast:  %.2e\n' % info['contrast']
    infotext += 'contrast:  {:>010.0f}\n'.format(info['contrast'])
    infotext += 'fps:  %d' % fps[2]  

    
    ax.texts = []
    ax.text(.01, .99, infotext, 
            color='white', alpha=0.8, fontsize=24,
            verticalalignment='top', transform=ax.transAxes)
#            bbox=dict(facecolor='k', linewidth=0, alpha=.4))        
    
    record(im, record_axes=False)
        
    return [ax, img] + ax.artists


def onclick(event):
    if event.key == 'shift' and event.inaxes == ax:
        print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
            event.button, event.x, event.y, event.xdata, event.ydata))
        
        ex, ey = event.xdata, event.ydata
        curr_xlim = ax.get_xlim()
        curr_ylim = ax.get_ylim()
        
        #cross.update(event.xdata, event.ydata)
        
        print(ax.get_xlim())
        ax.set_xlim((curr_xlim[0] - ex, curr_xlim[1] - ex))
        print(ax.get_xlim())
        ax.set_ylim((curr_ylim[0] - ey, curr_ylim[1] - ey))
        img.set_extent([curr_xlim[0] - ex, curr_xlim[1] - ex,
                        curr_ylim[0] - ey, curr_ylim[1] - ey])
                        
        #cross.update(0, 0)
        
def onkey(event):
    global cop_ix, ed_ix, recordvideo
    if event.key == 'h':
        cop_ix = (cop_ix + 1) % len(crosshair_opacity_scale)
        cross.update(0, 0, crosshair_opacity_scale[cop_ix])
    elif event.key == 'e':
        ed_ix = (ed_ix + 1) % len(edge_opacity_scale)
    elif event.key == 'c':
        cam.displayCaptureFilterProperties()
    elif event.key == 'p':
        now = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
        #cam.saveSnapshot('d:/tmp/snap_' + now + '.jpg')
        img_bbox = ax.get_window_extent().transformed(
                                                fig.dpi_scale_trans.inverted())
        img_width = img_bbox.width * fig.dpi
        save_scaling = size[0]/img_width
        
#        fig2 = fig
#        fig2.axes.pop()
#        fig2.canvas.draw()
        snapshot_fname = 'snap_' + now + '.jpg'
        fig.savefig(snapshot_dir + snapshot_fname, dpi=80*save_scaling)
    elif event.key == 'r':
        recordvideo = True
    

def onclose(event):
    global cam
    del cam

cid = fig.canvas.mpl_connect('button_press_event', onclick)
cid = fig.canvas.mpl_connect('key_press_event', onkey)
cid = fig.canvas.mpl_connect('close_event', onclose)

ani = animation.FuncAnimation(fig, update, init_func=init, interval=1, blit=False)


class RecordHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == signal_dir + signal_fname:
            global recordvideo
            recordvideo = True
        
event_handler = RecordHandler()
observer = Observer()
observer.schedule(event_handler, path=signal_dir, recursive=False)
observer.start()


plt.show()

#try:
#    while True:
#        time.sleep(1)
#except KeyboardInterrupt:
#        observer.stop()
#observer.join()


    
    