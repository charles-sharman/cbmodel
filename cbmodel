#!/usr/bin/python

"""
Description
-----------
cbmodel simulates building a Crossbeams model.

Author
------
Charles Sharman

License
-------
Distributed under the GNU GENERAL PUBLIC LICENSE Version 3.  View
LICENSE for details.

Revision History
----------------
 10/25/05: Began
 10/25/05 - 11/19/09: Many undocumented modifications
version 0.1 changes to 5/31/10
- Added detail option
- Added some Blender-compatible keys
- Made edit a RMB event
- Allowed multiple selections (and deletions)
- Added more Blender-compatible keys
- Removed 'total'/'part' distinction
- Converted from tk to gtk
- Added manual.pdf and called this version 0.1
- Added MMB pan/orbit
version 0.2 changes to 6/1/10
- Made project_directory relative
- Allowed for missing icons
- Fixed resize
version 0.3 changes to 6/24/10
- Added border select
- Fixed no more valid ports code
- Added Options->Add Pieces
version 0.4 changes to 7/22/10
- Added grab, duplicate, rotate mode
- Updated to new (v0.4) save format
- Added Mass feature
- Spruced up menus
- Made rotate work around mouse origin
version 0.5 changes to 12/18/10
- Fixed overlapping ports error
- Changed redraw to a gtk-expose event
- Added ends_visible option
- Added render ability (detail == 2) (caused selection display change)
- Added status line
- Made 1-ended icons more viewable
- Added mirror mode
version 0.6 changes to 7/11/11
- fixed Ends Visible redisplay bug
- added registry with .sticksrc
- Made individual detail==1 pieces be a CallList
- Removed ends_visible option
- Moved color setting to module level
- Put more keyboard options in menu
- Diverted most key calls to menu accelerators
- Made installation more official with distutils
- Minor bug fixes
version 0.7 changes to 7/18/11
- Added configure option to gears and wheels
- Fixed gllist memory leak for detail1
- Improved .png output
- Fixed line draw errors after/in Detail - Line mode
version 0.8 changes to 9/12/11
- Added Window menu to size/color for modelling or instructions
- Added part_outline in base_pieces (for white on white)
- Switched from numarray to numpy
- removed join2s from pieces.
- Made registery update project_dir on save
- Added -p option to print_keys
- Added instruction mode
- Sped-up render with .raw format
- Fixed move straight1m2 port bug
- Made render mode an option to setup.py (use --render)
- Made share directory lookup automated according to setup.py
- Used mailcap for pdf viewer
- Fixed rotate/mirror center bug
version 0.9 changes to 5/5/12
- Changed len1 to 43.2
- Added -gear option
- Scaled grab/duplicate moves to 0.25*len1
- Added stiffen option to joinrots
- Added import option
- Redid base_pieces.write_move to avoid hanging nodes
- Changed file extension to .cbm, name to cbmodel, .sticksrc to .cbmodelrc
- Many instruction appearance changes
- Shuffled the menu items
version 0.91 changes to 5/21/13
- Made redraw the default (rather than draw) to avoid blurring on expose
- Changed len1 to 44.8 and subsequent dimensions
- Altered colors
- Added name aliases
- Fixed a bug in instruction mode submodel
- Fixed labelling of joinrot and wheels
- Added combination parameter to base_pieces to allow combinations of pieces
- Added indirect rendering option for off-screen PS_SCALE
- Added more piece color options
- Sped-up base_pieces.write_move
- Added pose option
- Looked at storing connectivity as the model goes, but it made the
  code more complex in many places, and didn't speed up anything but
  pose.  remove_piece is clever and simply takes the inverted ends
  removed.  Skipped.
version 1.00 changes to 07/09/14
- Made ps_scale an option to allow faster instruction rendering
- Simplified instruction piece names
- Added piece center option
- Added undo/redo
- Added tooltips and removed menu descriptions from the manual
- Replaced the Select menu with the Edit menu
- Removed detail=0 from pieces
- Reintroduced self.redisplay for faster drawing on expose
- Added chirality to detail==1 joints to reflect actual pieces
- Added instruction helps
- Changed instruction color scheme
- Moved document images into doc_images
- Added non-NumPad run-time option
- Improved documentation
- Improved comments
- Migrated from double- to single-buffered opengl.  Screen redraws
  were so slow, the user needed visual feedback about the refresh
  rate.  Additionally, OSX had trouble with ReadPixels from the BACK
  buffer.
- Added the Navigation with Numpad or Alphas options
- Added OSX compatibility
version 1.01 changes to 12/29/14
- Connection added to helps, front page
- Fixed load bug on models with no instructions
- Fixed TypeError in fuzzy_frame call for later PIL versions

Conventions
-----------
A part is a piece in a module. *
A piece is anything that can be added to a module. *
* Unfortunately, this wasn't followed too strictly

Helps
-----
- The python-gtkglext documentation is terrible.  Use the c-code
  documentation: /usr/share/doc/libgtkglext1-doc/html/index.html.
- check /usr/share/doc/python-gtkglext1/examples for examples.
- check /var/lib/python-support/python2.5/gtk-2.0/gtk/gtkgl for
  specific gtkglext code.
- check /usr/share/doc/python-gtk2-doc/examples for pygtk examples.
- reportlab drawImage had bugs (required import PIL.Image instead of
  import Image, required reportab.lib.utils.ImageReader, and im.fp).
  Used drawInlineImage instead; shouldn't harm instructions.

To Do
-----
- Consider making the detail==1 pieces .raw also and remove GLE
- Consider transparency instead of grey for unplaced instruction pieces
"""

import sys

if '-h' in sys.argv or '--help' in sys.argv:
    print """
Usage: cbmodel
Run the Crossbeams Modeller

Optional arguments
  -h, --help       display this help and exit
  -i, --indirect   force indirect (software-driven, not graphics-card driven)
                   drawing
  -p, --printkeys  print the key code as a key is pressed
  -a, --alpha      use alpha-numeric (non-numpad) keys for navigation
"""
    sys.exit()

import os
import time
import math
import copy
import ConfigParser

from OpenGL.GL import *
from OpenGL.GLE import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import pygtk, gtk, gtk.gtkgl, pango, cairo, pangocairo

import numpy as np

import PIL.Image as Image

# Global Variables
try:
    bundled_directory = sys._MEIPASS # Needed for OSX bundles
except:
    bundled_directory = './'

share_directory = os.path.normpath(os.path.join(os.path.dirname(__file__), '../share/cbmodel/'))
if not os.path.exists(share_directory):
    if os.path.exists(bundled_directory):
        share_directory = bundled_directory
    else:
        share_directory = './'

doc_directory = os.path.normpath(os.path.join(share_directory, '../doc/cbmodel/'))
if not os.path.exists(doc_directory):
    if os.path.exists(bundled_directory):
        doc_directory = bundled_directory
    else:
        doc_directory = './'

os.chdir(bundled_directory)
if os.path.exists(os.path.join(share_directory, 'ogl_drawings/')):
    max_detail = 2
else:
    max_detail = 1
sys.path.append(share_directory)

# Now that the path is right, we can import the rest

import base_pieces
import pieces
import vector_math
import instructions

version = '1.01' # Change also in setup.py, cbmodel.tex

piece_aliases = [('anglep5xp5', 'angle1x1', '1x1'),
                 ('angle1xp5', 'angle2x1', '2x1'),
                 ('angle1x1', 'angle2x2', '2x2'),
                 ('angle1p5x1p5', 'angle3x3', '3x3'),
                 ('angle2x1', 'angle4x2', '4x2'),
                 ('angle2x2', 'angle4x4', '4x4'),
                 ('arc1x1', 'arc2x2', '2x2'),
                 ('arc1p5x1p5', 'arc3x3', '3x3'),
                 ('arc2x1', 'arc4x2', '4x2'),
                 ('arc2x2', 'arc4x4', '4x4'),
                 ('gear_axle1s', 'axle_g1', 'g1'),
                 ('gear_axle2s', 'axle_g2', 'g2'),
                 ('gear1', 'gear1', '1'),
                 ('gear3s', 'gear3s', '3s'),
                 ('gear3l', 'gear3l', '3l'),
                 ('gear_bevel', 'gear_b', 'b'),
                 ('gear_rack', 'rack', 'rack'),
                 ('gear_rack_spur', 'gear_r', 'r'),
                 ('join1', 'join1', '1'),
                 ('join2', 'join2', '2'),
                 ('join2flat', 'join2f', '2f'),
                 ('join3', 'join3', '3'),
                 ('join3flat', 'join3f', '3f'),
                 ('join4', 'join4', '4'),
                 ('join4flat', 'join4f', '4f'),
                 ('join5', 'join5', '5'),
                 ('join6', 'join6', '6'),
                 #('joinrot11', 'rotate1s', '1s'),
                 #('joinrot12', 'rotate1d', '1d'),
                 #('joinrot21', 'rotate2s', '2s'),
                 #('joinrot22', 'rotate2d', '2d'),
                 #('joinrot2flat1', 'rotate2fs', '2fs'),
                 #('joinrot2flat2', 'rotate2fd', '2fd'),
                 #('joinrot3flat1', 'rotate3fs', '3fs'),
                 #('joinrot3flat2', 'rotate3fd', '3fd'),
                 #('joinrot4flat1', 'rotate4fs', '4fs'),
                 #('joinrot4flat2', 'rotate4fd', '4fd'),
                 ('joinrot11', 'rotate2s', '2s'),
                 ('joinrot12', 'rotate3fd', '3fd'),
                 ('joinrot21', 'rotate3s', '3s'),
                 ('joinrot22', 'rotate4d', '4d'),
                 ('joinrot2flat1', 'rotate3fs', '3fs'),
                 ('joinrot2flat2', 'rotate4fd', '4fd'),
                 ('joinrot3flat1', 'rotate4s', '4s'),
                 ('joinrot3flat2', 'rotate5d', '5d'),
                 ('joinrot4flat1', 'rotate5s', '5s'),
                 ('joinrot4flat2', 'rotate6d', '6d'),
                 ('pivotm1', 'couple2s', '2s'),
                 ('pivot', 'couple22', '22'),
                 ('pivot00', 'couple11', '11'), 
                 ('pivot01', 'couple12', '12'),
                 ('pivot0m1', 'couple1s', '1s'),
                 ('pivotm1m1', 'coupless', 'ss'),
                 ('pivot0', 'couple211', '211'),
                 ('straightp5', 'straight1', '1'),
                 ('straight1m1', 'axle_s', 's'),
                 ('straight1', 'straight2', '2'),
                 ('straight1p5', 'straight3', '3'),
                 ('straight2', 'straight4', '4'),
                 ('wheel_axle1s1w', 'axle_w1', 'w1'),
                 ('wheel_axle2s2w', 'axle_w2', 'w2'),
                 ('wheel_axle1s3w', 'axle_w3', 'w3'),
                 ('wheelp5', 'wheel1', '1'),
                 ('wheel1', 'wheel2', '2'),
                 ('coupler', 'couple', 'couple'),
                 ('stiffen', 'stiff', 'stiff')]

class MainScreen(object):
    """
    Does everything for screen display and interaction with the module
    """

    key_table = {'toggle_port()': 'p',
                 'toggle_port(-1)': '<Shift>p', 
                 'flip_port()': 'f',
                 'flip_port(-1)': '<Shift>f', 
                 'connect_part()': 'c',
                 'query_selection()': 'q',
                 'grab()': 'g',
                 'duplicate()': '<Shift>d', 
                 'rotate()': 'r',
                 'mirror()': '<Control>m',
                 'border_select()': 'b',
                 'select_all()': 'a',
                 'delete_part()': 'x',
                 'undo()': '<Control>z',
                 'redo()': '<Control>y',
                 'write_file()': 'F2',
                 'read_file()': 'F1',
                 'solid()': 'z',
                 'render()': 'F12',
                 'redraw_screen()': 'KP_Page_Up',
                 'orbitup()': 'KP_Up',
                 'panup()': 'KP_8', 
                 'orbitdown()': 'KP_Down', 
                 'pandown()': 'KP_2', 
                 'orbitleft()': 'KP_Left', 
                 'panleft()': 'KP_4',
                 'orbitright()': 'KP_Right', 
                 'panright()': 'KP_6', 
                 'rotateccw()': 'KP_Divide', 
                 'rotatecw()': 'KP_Multiply', 
                 'zoomin()': 'KP_Add', 
                 'zoomin(0.25)': '<Control>KP_Add', 
                 'zoomout()': 'KP_Subtract', 
                 'zoomout(0.25)': '<Control>KP_Subtract', 
                 'viewstandard("top")': 'KP_Home', 
                 'viewstandard("bottom")': 'KP_7', 
                 'viewstandard("front")': 'KP_End', 
                 'viewstandard("back")': 'KP_1', 
                 'viewstandard("right")': 'KP_Page_Down', 
                 'viewstandard("left")': 'KP_3', 
                 'toggle_frame()': 'Right',
                 'toggle_frame(None, -1)': 'Left',
                 'quit()': '<Control>q'}

    numpad =    {'redraw_screen()': 'KP_Page_Up',
                 'orbitup()': 'KP_Up',
                 'panup()': 'KP_8', 
                 'orbitdown()': 'KP_Down', 
                 'pandown()': 'KP_2', 
                 'orbitleft()': 'KP_Left', 
                 'panleft()': 'KP_4',
                 'orbitright()': 'KP_Right', 
                 'panright()': 'KP_6', 
                 'rotateccw()': 'KP_Divide', 
                 'rotatecw()': 'KP_Multiply', 
                 'zoomin()': 'KP_Add', 
                 'zoomin(0.25)': '<Control>KP_Add', 
                 'zoomout()': 'KP_Subtract', 
                 'zoomout(0.25)': '<Control>KP_Subtract', 
                 'viewstandard("top")': 'KP_Home', 
                 'viewstandard("bottom")': 'KP_7', 
                 'viewstandard("front")': 'KP_End', 
                 'viewstandard("back")': 'KP_1', 
                 'viewstandard("right")': 'KP_Page_Down', 
                 'viewstandard("left")': 'KP_3'}

    nonumpad =  {'redraw_screen()': 'o',
                 'orbitup()': 'i',
                 'panup()': '<Shift>i',
                 'orbitdown()': 'comma',
                 'pandown()': '<Shift>less',
                 'orbitleft()': 'j',
                 'panleft()': '<Shift>j',
                 'orbitright()': 'l',
                 'panright()': '<Shift>l',
                 'rotateccw()': '8',
                 'rotatecw()': '9',
                 'zoomin()': '<Shift>plus',
                 'zoomin(0.25)': '<Shift><Control>plus',
                 'zoomout()': 'minus',
                 'zoomout(0.25)': '<Control>minus', 
                 'viewstandard("top")': 'u',
                 'viewstandard("bottom")': '<Shift>u',
                 'viewstandard("front")': 'm',
                 'viewstandard("back")': '<Shift>m',
                 'viewstandard("right")': 'period',
                 'viewstandard("left")': '<Shift>greater'}

    # Colors
    #SCREEN_COLOR = ((0.0, 0.0, 0.0), (1.0, 0.25, 0.25)) # BG, FG
    #PRINT_COLOR = ((1.0, 1.0, 1.0), (0.75, 0.0, 0.0)) # BG, FG
    #SCREEN_COLOR = ((0.0, 0.0, 0.0), (0.871, 0.504, 0.055)) # BG, FG
    #PRINT_COLOR = ((1.0, 1.0, 1.0), (0.871, 0.504, 0.055)) # BG, FG
    #SCREEN_COLOR = ((0.0, 0.0, 0.0), (0.875, 0.549, 0.098)) # BG, FG
    #PRINT_COLOR = ((1.0, 1.0, 1.0), (0.875, 0.549, 0.098)) # BG, FG

    SCREEN_COLOR = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (1.0, 0.8, 0.0)) # BG, FG, Highlights
    #PRINT_COVER_COLOR = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (1.0, 0.8, 0.0)) # BG, FG, Highlights
    PRINT_COVER_COLOR = ((1.0, 1.0, 1.0), (0.0, 0.0, 0.0), (1.0, 0.8, 0.0)) # BG, FG, Highlights
    #PRINT_BODY_COLOR = ((0.828, 0.879, 0.938), (0.875, 0.549, 0.098)) # BG, FG
    PRINT_BODY_COLOR = ((1.0, 1.0, 1.0), (0.0, 0.0, 0.0), (1.0, 0.8, 0.0)) # BG, FG, Highlights

    PIECE_COLORS = {'total': (1.0, 1.0, 1.0),
                    'straight': (1.0, 1.0, 1.0),
                    'angle': (1.0, 1.0, 1.0),
                    'arc': (1.0, 1.0, 1.0),
                    'part': (0.0, 1.0, 0.0),
                    'edit': (0.4, 0.6, 0.8),
                    'outline': (0.0, 0.0, 0.0),
                    'newpart': (0.4, 0.6, 0.8),
                    'futurepart': (0.33, 0.33, 0.33),
                    'tire': (0.33, 0.33, 0.33),
                    'wheel': (1.0, 1.0, 1.0),
                    'clip': (1.0, 1.0, 1.0),
                    'gear': (1.0, 1.0, 1.0),
                    'shaft': (0.5, 0.5, 0.5),
                    'region0': (1.0, 0.5, 0.5),
                    'region1': (0.5, 1.0, 0.5),
                    'region2': (0.5, 0.5, 1.0),
                    'region3': (0.8, 0.8, 0.4),
                    'region4': (0.4, 0.8, 0.8),
                    'region5': (0.8, 0.4, 0.4)}

    # Sizes/Scales
    SCREEN_SCALE = 100
    PS_SCALE = 3.0 # Print to Screen Scale DPI = PS_SCALE*SCREEN_SCALE
    IMAGE_SCALE = 300/(PS_SCALE*SCREEN_SCALE) # Image to Print Scale
    PAPER_SIZE = (8.5, 11.0) # inches
    #PAPER_SIZE = (9.06, 11.0) # scaled for 8.5x14 booklet printouts
    MARGIN_SIZE = 0.125 # inches
    SEP_SIZE = 0.05 # Internal separation between frames
    FRAME_MARGIN_SIZE = 0.075 # inches
    COVER_SIZE = (PAPER_SIZE[0]-2*MARGIN_SIZE, PAPER_SIZE[1]-2*MARGIN_SIZE)
    FRAME_SIZE = ((PAPER_SIZE[0]-2*MARGIN_SIZE-SEP_SIZE)/2, (PAPER_SIZE[1]-2*MARGIN_SIZE-SEP_SIZE)/2)

    # Cursors
    REGULAR_CURSOR = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
    WAIT_CURSOR = gtk.gdk.Cursor(gtk.gdk.WATCH)
    
    def __init__(self, print_keys = 0, rendering = 'direct', use_numpad = 1):
        global max_detail

        self.print_keys = print_keys
        self.rendering = rendering
        if not use_numpad:
            for key in self.nonumpad:
                self.key_table[key] = self.nonumpad[key]

        pieces.init(share_directory)
        self.background_color = self.SCREEN_COLOR[0]
        self.annotate_color = self.SCREEN_COLOR[1]
        self.highlight_color = self.SCREEN_COLOR[2]
        base_pieces.colors = self.PIECE_COLORS
        pieces.colors = self.PIECE_COLORS
        self.last_time = 0
        self.mode = 'normal'
        self.redisplay = 'redraw'
        self.current_filename = ''
        self.project_directory = os.path.join(os.getcwd())

        self.morbit = math.pi/12.0
        self.SCR = (900, 900)
        self.start_pixperunit = 10.0
        #self.pixperunit = self.start_pixperunit
        self.set_pixperunit(self.start_pixperunit)
        # self.mpan initialized in opengl_reshape
        # Front view start
        self.start_vcenter = np.array([0.0, 0.0, 0.0])
        self.start_vout = np.array([0.0, 0.0, 1.0])
        self.start_vup = np.array([0.0, 1.0, 0.0])
        
        self.lowerleft = (20.0, 20.0)

        # Do aliases
        self.piece_list = filter(lambda x: type(eval('pieces.' + x)) == type(pieces.stick) and issubclass(eval('pieces.' + x), pieces.stick), dir(pieces))
        self.piece_list.remove('stick')
        self.piece_list.remove('axle')
        self.name2alias = {}
        self.alias2name = {}
        self.name2simple = {}
        for name in self.piece_list:
            self.name2alias[name] = name
            self.alias2name[name] = name
            self.name2simple[name] = name
        for name, alias, simple in piece_aliases:
            self.name2alias[name] = alias
            self.alias2name[alias] = name
            self.name2simple[name] = simple
        pieces.aliases = self.name2alias
        local_alias = map(lambda x: (self.name2alias[x], x), self.piece_list)
        local_alias.sort()
        self.piece_list = map(lambda x: x[1], local_alias)

        self.total = base_pieces.module()
        self.last_joint = 'join2'
        self.last_stick = 'straight1'
        self.current_piece = self.piece_list.index(self.last_stick)
        self.name = self.validate_part(self.piece_list[self.current_piece])

        self.creationmode = 'modelling'
        self.image_type = 'screen'
        self.omit_logo = 0
        self.ps_scale = 1 # start in draft mode
        self.draw_center = 0 # don't show a box at piece centers

        # Main
        config_name = self.config_name()
        if config_name:
            config = ConfigParser.RawConfigParser()
            config.read(self.config_name())
            if config.has_section('Keys'):
                options = dict(config.items('Keys'))
                for key in options:
                    self.key_table[key] = options[key]
            if config.has_option('State', 'project_directory'):
                try_dir = config.get('State', 'project_directory')
                if os.path.exists(try_dir):
                    self.project_directory = try_dir
                else:
                    print 'Warning: Couldn\'t find directory ' + try_dir
        self.vcenter = self.start_vcenter
        self.vout = self.start_vout
        self.vup = self.start_vup

        gtk.window_set_default_icon_from_file(os.path.join(share_directory, 'symbol.png'))
        #print gtk.window_get_default_icon_list()
        self.win = gtk.Window()
        #self.win.set_geometry_hints(None, min_width = 200, min_height = 200)
        self.win.set_default_size(850, 600)
        self.update_title()
        #if not sys.platform.startswith('win'):
        #    self.win.set_resize_mode(gtk.RESIZE_IMMEDIATE)
        self.win.set_reallocate_redraws(True)
        self.win.connect('destroy', self.quit)
        self.win.connect('key_press_event', self.opengl_keypress) # Needed for a few stubborn keycodes that aren't exactly recognized correctly
        self.win.show()
        
        # Vertical Container
        vbox1 = gtk.VBox()
        self.win.add(vbox1)
        vbox1.show()

        # Menu Space
        accel_group = gtk.AccelGroup()
        self.win.add_accel_group(accel_group)
        self.modelling_only_items = []
        self.instructions_only_items = []

        menubar = gtk.MenuBar()
        vbox1.pack_start(menubar, False)
        menubar.show()

        file_container = gtk.Menu()

        file_new = gtk.ImageMenuItem(gtk.STOCK_NEW)
        file_new.set_tooltip_text('Erases the current model and starts a new model')
        file_new.connect('activate', self.clear_all)
        file_container.append(file_new)

        file_open = gtk.ImageMenuItem(gtk.STOCK_OPEN)
        file_open.set_tooltip_text('Erases the current model and opens a previously saved model')
        file_open.connect('activate', self.read_file)
        keyval, keymod = self.key_lookup('read_file()')
        file_open.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        file_container.append(file_open)

        file_save = gtk.ImageMenuItem(gtk.STOCK_SAVE)
        file_save.set_tooltip_text('Save the current model')
        file_save.connect('activate', lambda x: self.write_file(None, False))
        keyval, keymod = self.key_lookup('write_file()')
        file_save.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        file_container.append(file_save)

        file_saveas = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS)
        file_saveas.set_tooltip_text('Save the current model with a different name')
        file_saveas.connect('activate', self.write_file)
        file_container.append(file_saveas)

        file_container.append(gtk.SeparatorMenuItem())

        file_savepng = gtk.ImageMenuItem('Save Snapshot')
        file_savepng.set_tooltip_text('Save a snapshot of the editing window in .png format.')
        file_savepng.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE, gtk.ICON_SIZE_MENU))
        file_savepng.connect('activate', self.write_png)
        file_container.append(file_savepng)

        file_savecsv = gtk.ImageMenuItem('Save Inventory')
        file_savecsv.set_tooltip_text('Save a list of pieces and quantities as a .csv file')
        file_savecsv.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE, gtk.ICON_SIZE_MENU))
        file_savecsv.connect('activate', self.write_csv)
        file_container.append(file_savecsv)

        file_container.append(gtk.SeparatorMenuItem())

        file_merge = gtk.ImageMenuItem('Merge')
        file_merge.set_tooltip_text('Merge a model from another file with the current model')
        file_merge.set_image(gtk.image_new_from_stock(gtk.STOCK_INDENT, gtk.ICON_SIZE_MENU))
        file_merge.connect('activate', self.merge_file)
        self.modelling_only_items.append(file_merge)
        file_container.append(file_merge)

        file_container.append(gtk.SeparatorMenuItem())

        file_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        file_quit.set_tooltip_text('Quit the program')
        file_quit.connect('activate', self.quit)
        keyval, keymod = self.key_lookup('quit()')
        file_quit.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        file_container.append(file_quit)

        file_menu = gtk.MenuItem('_File')
        file_menu.set_submenu(file_container)
        file_menu.show()
        menubar.append(file_menu)

        edit_container = gtk.Menu()

        edit_undo = gtk.ImageMenuItem(gtk.STOCK_UNDO)
        edit_undo.set_tooltip_text('Undo the last model operation')
        edit_undo.connect('activate', self.undo)
        keyval, keymod = self.key_lookup('undo()')
        edit_undo.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        self.modelling_only_items.append(edit_undo)
        edit_container.append(edit_undo)

        edit_redo = gtk.ImageMenuItem(gtk.STOCK_REDO)
        edit_redo.set_tooltip_text('Redo the last model operation')
        edit_redo.connect('activate', self.redo)
        keyval, keymod = self.key_lookup('redo()')
        edit_redo.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        self.modelling_only_items.append(edit_redo)
        edit_container.append(edit_redo)

        edit_container.append(gtk.SeparatorMenuItem())

        edit_select_all = gtk.MenuItem('Select/Deselect All')
        edit_select_all.set_tooltip_text('Select all pieces when none are selected or deselect all pieces when some are selected')
        edit_select_all.connect('activate', self.select_all)
        keyval, keymod = self.key_lookup('select_all()')
        edit_select_all.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        edit_container.append(edit_select_all)
        
        edit_select_border = gtk.MenuItem('Border Select')
        edit_select_border.set_tooltip_text('Select all pieces within a rectangular box')
        edit_select_border.connect('activate', self.border_select)
        keyval, keymod = self.key_lookup('border_select()')
        edit_select_border.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        edit_container.append(edit_select_border)

        edit_select_type = gtk.MenuItem('Select by Type')
        edit_select_type.set_tooltip_text('Select all pieces of the piece type currently being placed')
        edit_select_type.connect('activate', self.type_select)
        self.modelling_only_items.append(edit_select_type)
        edit_container.append(edit_select_type)

        edit_select_set_fixed = gtk.MenuItem('Selected to Fixed')
        edit_select_set_fixed.set_tooltip_text('Make the selected region the fixed region')
        edit_select_set_fixed.connect('activate', self.set_fixed_region)
        self.instructions_only_items.append(edit_select_set_fixed)
        edit_select_set_fixed.set_sensitive(False)
        edit_container.append(edit_select_set_fixed)

        edit_select_hide_selected = gtk.MenuItem('Hide Selected')
        edit_select_hide_selected.set_tooltip_text('Hide the selected parts')
        edit_select_hide_selected.connect('activate', self.hide_selected)
        self.instructions_only_items.append(edit_select_hide_selected)
        edit_select_hide_selected.set_sensitive(False)
        edit_container.append(edit_select_hide_selected)

        edit_select_unhide = gtk.MenuItem('Unhide')
        edit_select_unhide.set_tooltip_text('Unhide all hidden parts')
        edit_select_unhide.connect('activate', self.unhide)
        self.instructions_only_items.append(edit_select_unhide)
        edit_select_unhide.set_sensitive(False)
        edit_container.append(edit_select_unhide)

        edit_container.append(gtk.SeparatorMenuItem())

        edit_query = gtk.MenuItem('Query')
        edit_query.set_tooltip_text('Pop-up a piece query window on the currently selected piece')
        edit_query.connect('activate', self.query_selection)
        keyval, keymod = self.key_lookup('query_selection()')
        edit_query.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        self.modelling_only_items.append(edit_query)
        edit_container.append(edit_query)

        edit_grab = gtk.MenuItem('Grab')
        edit_grab.set_tooltip_text('Move the selected pieces')
        edit_grab.connect('activate', self.grab)
        keyval, keymod = self.key_lookup('grab()')
        edit_grab.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        self.modelling_only_items.append(edit_grab)
        edit_container.append(edit_grab)

        edit_duplicate = gtk.MenuItem('Duplicate')
        edit_duplicate.set_tooltip_text('Duplicate the selected pieces')
        edit_duplicate.connect('activate', self.duplicate)
        keyval, keymod = self.key_lookup('duplicate()')
        edit_duplicate.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        self.modelling_only_items.append(edit_duplicate)
        edit_container.append(edit_duplicate)

        edit_rotate = gtk.MenuItem('Rotate')
        edit_rotate.set_tooltip_text('Rotate the selected pieces')
        edit_rotate.connect('activate', self.rotate)
        keyval, keymod = self.key_lookup('rotate()')
        edit_rotate.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        #self.modelling_only_items.append(edit_rotate)
        edit_container.append(edit_rotate)

        edit_mirror = gtk.MenuItem('Mirror')
        edit_mirror.set_tooltip_text('Mirror the selected pieces')
        edit_mirror.connect('activate', self.mirror)
        keyval, keymod = self.key_lookup('mirror()')
        edit_mirror.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        self.modelling_only_items.append(edit_mirror)
        edit_container.append(edit_mirror)

        edit_delete = gtk.MenuItem('Delete')
        edit_delete.set_tooltip_text('Delete the selected pieces')
        edit_delete.connect('activate', self.delete_part)
        keyval, keymod = self.key_lookup('delete_part()')
        edit_delete.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        self.modelling_only_items.append(edit_delete)
        edit_container.append(edit_delete)

        edit_fix = gtk.MenuItem('Fix')
        edit_fix.set_tooltip_text('Attempts to fix a corrupt model')
        edit_fix.connect('activate', self.fix_model)
        self.modelling_only_items.append(edit_fix)
        edit_container.append(edit_fix)

        edit_menu = gtk.MenuItem('_Edit')
        edit_menu.set_submenu(edit_container)
        edit_menu.show()
        menubar.append(edit_menu)

        view_container = gtk.Menu()

        view_inventory = gtk.MenuItem('Inventory')
        view_inventory.set_tooltip_text('Lists the pieces used in the model')
        view_inventory.connect('activate', self.view_inventory)
        view_container.append(view_inventory)

        view_dimensions = gtk.MenuItem('Dimensions')
        view_dimensions.set_tooltip_text('Bounds the model in a 3D box and reports the box distances')
        view_dimensions.connect('activate', self.view_dimensions)
        view_container.append(view_dimensions)

        view_mass = gtk.MenuItem('Mass')
        view_mass.set_tooltip_text('Reports the model\'s mass')
        view_mass.connect('activate', self.view_mass)
        view_container.append(view_mass)

        view_price = gtk.MenuItem('Price')
        view_price.set_tooltip_text('Reports the model\'s price')
        view_price.connect('activate', self.view_price)
        view_container.append(view_price)

        view_page_count = gtk.MenuItem('Pages')
        view_page_count.set_tooltip_text('Reports the number of instruction set pages including front and back cover')
        view_page_count.connect('activate', self.view_page_count)
        view_container.append(view_page_count)

        view_container.append(gtk.SeparatorMenuItem())

        view_side = gtk.MenuItem('Side')
        view_side_container = gtk.Menu()
        view_side.set_submenu(view_side_container)
        view_container.append(view_side)
        
        view_front = gtk.MenuItem('Front')
        view_front.set_tooltip_text('Views the front of the model')
        view_front.connect('activate', self.viewstandard, 'front')
        keyval, keymod = self.key_lookup('viewstandard("front")')
        view_front.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_side_container.append(view_front)

        view_top = gtk.MenuItem('Top')
        view_top.set_tooltip_text('Views the top of the model')
        view_top.connect('activate', self.viewstandard, 'top')
        keyval, keymod = self.key_lookup('viewstandard("top")')
        view_top.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_side_container.append(view_top)

        view_right = gtk.MenuItem('Right')
        view_right.set_tooltip_text('Views the right side of the model')
        view_right.connect('activate', self.viewstandard, 'right')
        keyval, keymod = self.key_lookup('viewstandard("right")')
        view_right.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_side_container.append(view_right)

        view_back = gtk.MenuItem('Back')
        view_back.set_tooltip_text('Views the back of the model')
        view_back.connect('activate', self.viewstandard, 'back')
        keyval, keymod = self.key_lookup('viewstandard("back")')
        view_back.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_side_container.append(view_back)

        view_bottom = gtk.MenuItem('Bottom')
        view_bottom.set_tooltip_text('Views the bottom of the model')
        view_bottom.connect('activate', self.viewstandard, 'bottom')
        keyval, keymod = self.key_lookup('viewstandard("bottom")')
        view_bottom.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_side_container.append(view_bottom)

        view_left = gtk.MenuItem('Left')
        view_left.set_tooltip_text('Views the left side of the model')
        view_left.connect('activate', self.viewstandard, 'left')
        keyval, keymod = self.key_lookup('viewstandard("left")')
        view_left.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_side_container.append(view_left)

        view_orbit = gtk.MenuItem('Orbit')
        view_orbit_container = gtk.Menu()
        view_orbit.set_submenu(view_orbit_container)
        view_container.append(view_orbit)

        view_orbitup = gtk.MenuItem('Up')
        view_orbitup.set_tooltip_text('Orbits the observer 15 degrees up')
        view_orbitup.connect('activate', self.orbitup)
        keyval, keymod = self.key_lookup('orbitup()')
        view_orbitup.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_orbit_container.append(view_orbitup)

        view_orbitdown = gtk.MenuItem('Down')
        view_orbitdown.set_tooltip_text('Orbits the observer 15 degrees down')
        view_orbitdown.connect('activate', self.orbitdown)
        keyval, keymod = self.key_lookup('orbitdown()')
        view_orbitdown.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_orbit_container.append(view_orbitdown)

        view_orbitleft = gtk.MenuItem('Left')
        view_orbitleft.set_tooltip_text('Orbits the observer 15 degrees to the left')
        view_orbitleft.connect('activate', self.orbitleft)
        keyval, keymod = self.key_lookup('orbitleft()')
        view_orbitleft.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_orbit_container.append(view_orbitleft)

        view_orbitright = gtk.MenuItem('Right')
        view_orbitright.set_tooltip_text('Orbits the observer 15 degrees to the right')
        view_orbitright.connect('activate', self.orbitright)
        keyval, keymod = self.key_lookup('orbitright()')
        view_orbitright.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_orbit_container.append(view_orbitright)

        view_orbitccw = gtk.MenuItem('CCW')
        view_orbitccw.set_tooltip_text('Orbits the observer 15 degrees counter-clockwise')
        view_orbitccw.connect('activate', self.rotateccw)
        keyval, keymod = self.key_lookup('rotateccw()')
        view_orbitccw.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_orbit_container.append(view_orbitccw)

        view_orbitcw = gtk.MenuItem('CW')
        view_orbitcw.set_tooltip_text('Orbits the observer 15 degrees clockwise')
        view_orbitcw.connect('activate', self.rotatecw)
        keyval, keymod = self.key_lookup('rotatecw()')
        view_orbitcw.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_orbit_container.append(view_orbitcw)

        view_pan = gtk.MenuItem('Pan')
        view_pan_container = gtk.Menu()
        view_pan.set_submenu(view_pan_container)
        view_container.append(view_pan)

        view_panup = gtk.MenuItem('Up')
        view_panup.set_tooltip_text('Pans the observer up')
        view_panup.connect('activate', self.panup)
        keyval, keymod = self.key_lookup('panup()')
        view_panup.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_pan_container.append(view_panup)

        view_pandown = gtk.MenuItem('Down')
        view_pandown.set_tooltip_text('Pans the observer down')
        view_pandown.connect('activate', self.pandown)
        keyval, keymod = self.key_lookup('pandown()')
        view_pandown.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_pan_container.append(view_pandown)

        view_panleft = gtk.MenuItem('Left')
        view_panleft.set_tooltip_text('Pans the observer left')
        view_panleft.connect('activate', self.panleft)
        keyval, keymod = self.key_lookup('panleft()')
        view_panleft.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_pan_container.append(view_panleft)

        view_panright = gtk.MenuItem('Right')
        view_panright.set_tooltip_text('Pans the observer right')
        view_panright.connect('activate', self.panright)
        keyval, keymod = self.key_lookup('panright()')
        view_panright.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_pan_container.append(view_panright)

        view_zoom = gtk.MenuItem('Zoom')
        view_zoom_container = gtk.Menu()
        view_zoom.set_submenu(view_zoom_container)
        view_container.append(view_zoom)

        view_zoomin = gtk.MenuItem('In')
        view_zoomin.set_tooltip_text('Zooms in toward the model')
        view_zoomin.connect('activate', self.zoomin)
        keyval, keymod = self.key_lookup('zoomin()')
        view_zoomin.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_zoom_container.append(view_zoomin)

        view_zoomout = gtk.MenuItem('Out')
        view_zoomout.set_tooltip_text('Zooms away from the model')
        view_zoomout.connect('activate', self.zoomout)
        keyval, keymod = self.key_lookup('zoomout()')
        view_zoomout.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        view_zoom_container.append(view_zoomout)

        view_menu = gtk.MenuItem('_View')
        view_menu.set_submenu(view_container)
        view_menu.show()
        menubar.append(view_menu)

        part_container = gtk.Menu()

        self.part_add_pieces = gtk.CheckMenuItem('Add Pieces')
        self.part_add_pieces.set_tooltip_text('Automatically places the next piece in green')
        self.part_add_pieces.set_active(True)
        self.modelling_only_items.append(self.part_add_pieces)
        part_container.append(self.part_add_pieces)

        part_container.append(gtk.SeparatorMenuItem())

        part_next_port = gtk.MenuItem('Next Port')
        part_next_port.set_tooltip_text('Connect the next piece port to the model at the current model port')
        part_next_port.connect('activate', self.toggle_port)
        keyval, keymod = self.key_lookup('toggle_port()')
        part_next_port.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        part_container.append(part_next_port)

        part_previous_port = gtk.MenuItem('Previous Port')
        part_previous_port.set_tooltip_text('Connect the previous piece port to the model at the current model port')
        part_previous_port.connect('activate', self.toggle_port, -1)
        keyval, keymod = self.key_lookup('toggle_port(-1)')
        part_previous_port.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        part_container.append(part_previous_port)

        part_next_flip = gtk.MenuItem('Flip 90')
        part_next_flip.set_tooltip_text('Rotate the piece 90 degrees about the current model port')
        part_next_flip.connect('activate', self.flip_port)
        keyval, keymod = self.key_lookup('flip_port()')
        part_next_flip.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        part_container.append(part_next_flip)

        part_previous_flip = gtk.MenuItem('Flip -90')
        part_previous_flip.set_tooltip_text('Rotate the piece -90 degrees about the current model port')
        part_previous_flip.connect('activate', self.flip_port, -1)
        keyval, keymod = self.key_lookup('flip_port(-1)')
        part_previous_flip.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        part_container.append(part_previous_flip)

        part_connect = gtk.MenuItem('Connect')
        part_connect.set_tooltip_text('Connect the piece to the model')
        part_connect.connect('activate', self.connect_part)
        keyval, keymod = self.key_lookup('connect_part()')
        part_connect.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        part_container.append(part_connect)

        self.part_menu = gtk.MenuItem('_Piece')
        self.part_menu.set_submenu(part_container)
        self.part_menu.show()
        menubar.append(self.part_menu)

        instructions_container = gtk.Menu()

        self.instructions_hide_part_labels = gtk.CheckMenuItem('Hide Part Labels')
        self.instructions_hide_part_labels.set_tooltip_text('Hide labels placed on new pieces added this frame')
        self.instructions_hide_part_labels.set_active(False)
        instructions_container.append(self.instructions_hide_part_labels)

        self.instructions_show_mirror = gtk.CheckMenuItem('Show Mirror')
        self.instructions_show_mirror.set_tooltip_text('Show the mirror icon, showing new pieces are mirrored from old ones')
        self.instructions_show_mirror.set_active(False)
        self.instructions_show_mirror.connect('activate', self.show_mirror)
        instructions_container.append(self.instructions_show_mirror)

        self.instructions_show_magnify = gtk.CheckMenuItem('Show Cross Hair')
        self.instructions_show_magnify.set_tooltip_text('Show the cross hair icon, which shows the piece the next frame will be centered on')
        self.instructions_show_magnify.set_active(False)
        self.instructions_show_magnify.connect('activate', self.show_magnify)
        instructions_container.append(self.instructions_show_magnify)

        instructions_container.append(gtk.SeparatorMenuItem())

        instructions_new = gtk.ImageMenuItem(gtk.STOCK_NEW)
        instructions_new.set_tooltip_text('Erase all instructions and start new instructions')
        instructions_new.connect('activate', self.clear_instructions)
        instructions_container.append(instructions_new)

        self.instructions_hold_pose = gtk.CheckMenuItem('Hold Pose')
        self.instructions_hold_pose.set_tooltip_text('Hold the cover pose through all instruction steps')
        self.instructions_hold_pose.set_active(False)
        self.instructions_hold_pose.connect('toggled', self.hold_pose)
        instructions_container.append(self.instructions_hold_pose)

        instructions_set_title = gtk.MenuItem('Set Title')
        instructions_set_title.set_tooltip_text('Set the title and author of the model')
        instructions_set_title.connect('activate', self.set_instructions_title)
        instructions_container.append(instructions_set_title)

        instructions_container.append(gtk.SeparatorMenuItem())

        instructions_insert_frame_before = gtk.MenuItem('Insert Before')
        instructions_insert_frame_before.set_tooltip_text('Insert a frame before the current frame')
        instructions_insert_frame_before.connect('activate', self.insert_frame, 0)
        instructions_container.append(instructions_insert_frame_before)

        instructions_insert_frame_after = gtk.MenuItem('Insert After')
        instructions_insert_frame_after.set_tooltip_text('Insert a frame after the current frame')
        instructions_insert_frame_after.connect('activate', self.insert_frame, 1)
        instructions_container.append(instructions_insert_frame_after)

        instructions_delete_frame = gtk.ImageMenuItem(gtk.STOCK_DELETE)
        instructions_delete_frame.set_tooltip_text('Delete the current frame')
        instructions_delete_frame.connect('activate', self.delete_frame)
        instructions_container.append(instructions_delete_frame)

        instructions_container.append(gtk.SeparatorMenuItem())

        instructions_next_frame = gtk.ImageMenuItem(gtk.STOCK_GO_FORWARD)
        instructions_next_frame.set_tooltip_text('Store the current frame settings and go to the next frame')
        #instructions_next_frame.set_label('Next')
        instructions_next_frame.connect('activate', self.toggle_frame)
        keyval, keymod = self.key_lookup('toggle_frame()')
        instructions_next_frame.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        instructions_container.append(instructions_next_frame)

        instructions_previous_frame = gtk.ImageMenuItem(gtk.STOCK_GO_BACK)
        instructions_previous_frame.set_tooltip_text('Store the current frame settings and go to the previous frame')
        #instructions_previous_frame.set_label('Previous')
        instructions_previous_frame.connect('activate', self.toggle_frame, -1)
        keyval, keymod = self.key_lookup('toggle_frame(None, -1)')
        instructions_previous_frame.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        instructions_container.append(instructions_previous_frame)

        instructions_goto_frame = gtk.MenuItem('Go To')
        instructions_goto_frame.set_tooltip_text('Store the current frame and advance to a chosen frame')
        instructions_goto_frame.connect('activate', self.goto_frame)
        instructions_container.append(instructions_goto_frame)

        instructions_container.append(gtk.SeparatorMenuItem())

        instructions_start_submodel = gtk.MenuItem('Start Submodel')
        instructions_start_submodel.set_tooltip_text('Starts a submodel sequence where the main model is not drawn')
        instructions_start_submodel.connect('activate', self.start_submodel)
        instructions_container.append(instructions_start_submodel)

        instructions_end_submodel = gtk.MenuItem('End Submodel')
        instructions_end_submodel.set_tooltip_text('End a submodel sequence where the submodel is drawn attached to the main model')
        instructions_end_submodel.connect('activate', self.end_submodel)
        instructions_container.append(instructions_end_submodel)

        instructions_container.append(gtk.SeparatorMenuItem())

        instructions_draft = gtk.CheckMenuItem('Draft')
        instructions_draft.set_tooltip_text('The pdf is set for 100dpi (instead of 300dpi) for faster creation')
        instructions_draft.set_active(True)
        instructions_draft.connect('toggled', self.instructions_draft)
        instructions_container.append(instructions_draft)

        instructions_generate = gtk.MenuItem('Generate')
        instructions_generate.set_tooltip_text('Create a .pdf instruction set, .png cover photo, and .csv inventory')
        instructions_generate.connect('activate', self.generate_instructions)
        instructions_container.append(instructions_generate)
        if not instructions.pdfcanvas:
            instructions_generate.set_sensitive(False)

        self.instructions_menu = gtk.MenuItem('_Instructions')
        self.instructions_menu.set_submenu(instructions_container)
        menubar.append(self.instructions_menu)

        mode_container = gtk.Menu()
        
        self.mode_modelling = gtk.RadioMenuItem(None, 'Modelling')
        self.mode_modelling.set_tooltip_text('Switch to modelling mode')
        self.mode_modelling.set_active(True)
        self.mode_modelling.connect('activate', self.set_mode, 'modelling')
        mode_container.append(self.mode_modelling)

        mode_instructions = gtk.RadioMenuItem(self.mode_modelling, 'Instructions')
        mode_instructions.set_tooltip_text('Switch to instructions mode')
        mode_instructions.connect('activate', self.set_mode, 'instructions')
        mode_container.append(mode_instructions)

        mode_menu = gtk.MenuItem('_Mode')
        mode_menu.set_submenu(mode_container)
        mode_menu.show()
        menubar.append(mode_menu)

        options_container = gtk.Menu()

        options_detail = gtk.MenuItem('Detail')
        options_detail_container = gtk.Menu()
        options_detail.set_submenu(options_detail_container)
        options_container.append(options_detail)

        options_detail_solid = gtk.RadioMenuItem(None, 'Solid')
        options_detail_solid.set_tooltip_text('Solid detail for fast redraw')
        options_detail_solid.set_active(True)
        options_detail_solid.connect('activate', self.set_detail, 1)
        keyval, keymod = self.key_lookup('solid()')
        options_detail_solid.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        options_detail_container.append(options_detail_solid)

        options_detail_render = gtk.RadioMenuItem(options_detail_solid, 'Render')
        options_detail_render.set_tooltip_text('Render detail')
        options_detail_render.connect('activate', self.set_detail, 2)
        if max_detail < 2:
            options_detail_render.set_sensitive(False)
        keyval, keymod = self.key_lookup('render()')
        options_detail_render.add_accelerator('activate', accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
        options_detail_container.append(options_detail_render)
        
        options_size = gtk.MenuItem('Window Size')
        options_size_container = gtk.Menu()
        options_size.set_submenu(options_size_container)
        options_container.append(options_size)

        options_size_any = gtk.MenuItem('Any')
        options_size_any.set_tooltip_text('Size the window so it can be extremely small')
        options_size_any.connect('activate', self.window_size, (1, 1))
        options_size_container.append(options_size_any)

        options_size_full = gtk.MenuItem('Full')
        options_size_full.set_tooltip_text('Size the window so a snapshot fits on a full instruction set page')
        options_size_full.connect('activate', self.window_size_full)
        options_size_container.append(options_size_full)

        options_size_fullr = gtk.MenuItem('FullR')
        options_size_fullr.set_tooltip_text('Size the window so a snapshot fits on a full instruction set page rotate 90 degrees')
        options_size_fullr.connect('activate', self.window_size_fullr)
        options_size_container.append(options_size_fullr)

        options_size_quarter = gtk.MenuItem('Quarter')
        options_size_quarter.set_tooltip_text('Size the window so a snapshot fits on a quarter of a full instruction set page')
        options_size_quarter.connect('activate', self.window_size_quarter)
        options_size_container.append(options_size_quarter)

        options_size_halfh = gtk.MenuItem('Half')
        options_size_halfh.set_tooltip_text('Size the window so a snapshot fits on the top or bottom half of a full instruction set page')
        options_size_halfh.connect('activate', self.window_size_halfh)
        options_size_container.append(options_size_halfh)

        options_color = gtk.MenuItem('Color')
        options_color_container = gtk.Menu()
        options_color.set_submenu(options_color_container)
        options_container.append(options_color)

        options_color_screen = gtk.MenuItem('Screen')
        options_color_screen.set_tooltip_text('Choose the for-screen color scheme (white model on dark background)')
        options_color_screen.connect('activate', self.window_color, self.SCREEN_COLOR)
        options_color_container.append(options_color_screen)

        options_color_print = gtk.MenuItem('Print')
        options_color_print.set_tooltip_text('Choose the for-print color scheme (white model on light background)')
        options_color_print.connect('activate', self.window_color, self.PRINT_BODY_COLOR)
        options_color_container.append(options_color_print)

        options_draw_outlines = gtk.CheckMenuItem('Draw Outlines')
        options_draw_outlines.set_tooltip_text('Outlines pieces in a thick black')
        options_draw_outlines.set_active(False)
        options_draw_outlines.connect('toggled', self.set_draw_outline)
        options_container.append(options_draw_outlines)

        options_draw_centers = gtk.CheckMenuItem('Draw Centers')
        options_draw_centers.set_tooltip_text('Draws the centers of pieces or regions for easier selection')
        options_draw_centers.set_active(False)
        options_draw_centers.connect('toggled', self.set_draw_center)
        options_container.append(options_draw_centers)

        options_keys_numpad = gtk.MenuItem('Navigation with Numpad')
        options_keys_numpad.set_tooltip_text('Overwrites user settings to use Numeric Keypad keys for navigation')
        options_keys_numpad.connect('activate', self.set_keys, 'numpad')
        options_container.append(options_keys_numpad)

        options_keys_nonumpad = gtk.MenuItem('Navigation with Alphas')
        options_keys_nonumpad.set_tooltip_text('Overwrites user settings to use letter keys for navigation')
        options_keys_nonumpad.connect('activate', self.set_keys, 'nonumpad')
        options_container.append(options_keys_nonumpad)

        options_menu = gtk.MenuItem('_Options')
        options_menu.set_submenu(options_container)
        options_menu.show()
        menubar.append(options_menu)

        help_container = gtk.Menu()

        help_manual = gtk.ImageMenuItem('_Manual')
        help_manual.set_tooltip_text('Open the manual in a separate window')
        help_manual.set_image(gtk.image_new_from_stock(gtk.STOCK_HELP, gtk.ICON_SIZE_MENU))
        help_manual.connect('activate', self.display_manual)
        help_container.append(help_manual)

        help_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        help_about.set_tooltip_text('Display the version')
        help_about.connect('activate', self.about)
        help_container.append(help_about)
        
        help_menu = gtk.MenuItem('_Help')
        help_menu.set_submenu(help_container)
        help_menu.show()
        menubar.append(help_menu)
        menubar.show_all()
        self.instructions_menu.hide() # Override the show_all()
        
        # Horizontal Container
        hbox2 = gtk.HBox()
        hbox2.show()
        vbox1.pack_start(hbox2)

        # OpenGL Space
        glconfig = gtk.gdkgl.Config(mode=gtk.gdkgl.MODE_RGB | gtk.gdkgl.MODE_DEPTH | gtk.gdkgl.MODE_DOUBLE | gtk.gdkgl.MODE_ALPHA)
        self.glarea = gtk.gtkgl.DrawingArea(glconfig, direct = (self.rendering == 'direct'))
        self.glarea.connect('realize', self.opengl_init)
        self.glarea.connect('configure-event', self.opengl_reshape)
        self.glarea.connect('expose-event', self.opengl_draw)
        #self.glarea.connect('key_press_event', self.opengl_keypress) # Didn't work here
        self.glarea.connect('button_press_event', self.opengl_mousepress)
        self.glarea.connect('button_release_event', self.opengl_mouserelease)
        self.glarea.connect('motion_notify_event', self.opengl_mousemotion)
        self.glarea.add_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_RELEASE_MASK)

        gtk.gtkgl.widget_set_gl_capability(self.glarea, glconfig)
        self.glarea.show()
        hbox2.pack_start(self.glarea)

        # Pieces Space
        piece_win = gtk.ScrolledWindow()
        piece_win.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        piece_win.set_size_request(250, -1)
        piece_win.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0)) # Didn't work ***
        hbox2.pack_start(piece_win, False)
        plist = gtk.ListStore(gtk.gdk.Pixbuf, str)
        for name in self.piece_list:
            full_name = os.path.join(share_directory, 'icons', name + '.png')
            if os.access(full_name, os.F_OK):
                image = gtk.gdk.pixbuf_new_from_file(full_name)
                image = image.scale_simple(image.get_width()/4, image.get_height()/4, gtk.gdk.INTERP_BILINEAR)
            else:
                image = gtk.gdk.pixbuf_new_from_file(os.path.join(share_directory, 'icons', 'blank.png'))
            #tip = gtk.Tooltips() # Couldn't add to image
            #tip.set_tip(image, name)
            plist.append([image, self.name2alias[name]])
        treeview = gtk.TreeView(plist)
        treeview.set_headers_visible(False) # Turn off column Header
        #treeview.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0)) # Didn't work either ***
        treeview.unset_flags(gtk.CAN_FOCUS) # Disallow keyboard entry
        piece_win.add(treeview)
        column = gtk.TreeViewColumn('Pieces')
        cell_renderer = gtk.CellRendererPixbuf()
        cell_renderer.set_property('cell-background-gdk', gtk.gdk.Color(65536/3, 65536/3, 65536/3))
        column.pack_start(cell_renderer, False)
        column.add_attribute(cell_renderer, 'pixbuf', 0)
        cell_renderer = gtk.CellRendererText()
        cell_renderer.set_property('cell-background-gdk', gtk.gdk.Color(65536/3, 65536/3, 65536/3))
        column.pack_start(cell_renderer)
        column.add_attribute(cell_renderer, 'text', 1) # To view the text
        treeview.append_column(column)
        self.selection = treeview.get_selection()
        self.selection.set_mode(gtk.SELECTION_SINGLE)
        self.selection.connect('changed', self.menu_piece_select)
        piece_win.show_all()

        # Status Line
        hbox_status = gtk.HBox()
        hbox_status.show()
        vbox1.pack_start(hbox_status, False, False)

        # Status Bar
        #self.status_bar = gtk.Statusbar()
        #self.status_bar.push(0, self.mode)
        #self.status_bar.show()
        #vbox1.pack_start(self.status_bar, False, False)
        self.status_bar = gtk.Label()
        self.status_bar.set_tooltip_text('Status bar')
        #self.status_bar.set_justify(gtk.JUSTIFY_LEFT)
        self.status_bar.set_alignment(0.0, 0.5)
        self.status_bar.set_text(self.mode)
        self.status_bar.show()
        hbox_status.pack_start(self.status_bar, True, True)

        self.selected_bar = gtk.Label()
        self.selected_bar.set_tooltip_text('Selected pieces')
        self.selected_bar.set_width_chars(6)
        self.selected_bar.show()
        hbox_status.pack_start(self.selected_bar, False, False)

        self.hidden_bar = gtk.Label()
        self.hidden_bar.set_tooltip_text('Hidden pieces')
        self.hidden_bar.set_width_chars(6)
        self.hidden_bar.set_text('0')
        self.hidden_bar.show()
        hbox_status.pack_start(self.hidden_bar, False, False)

        self.fps_label = gtk.Label()
        self.fps_label.set_tooltip_text('Screen draw time')
        self.fps_label.set_width_chars(6)
        self.fps_label.show()
        hbox_status.pack_start(self.fps_label, False, False)

        # Fonts
        #print map(lambda x: x.get_name(), self.glarea.get_pango_context().list_families()) # Display available fonts
        self.fonts = {}
        self.make_font('Sans 30', 'title')
        self.make_font('Sans Bold 24', 'author')
        self.make_font('Sans Bold 8', 'part')
        self.fonts['framenum'] = self.fonts['author'].copy()

        # Images
        self.images = {}
        self.make_image('logo_white')
        self.make_image('logo_black')
        self.make_image('mirror')
        self.make_image('magnify', 'xhair')

        # Help Sizes
        self.generate_help_sizes()

    def make_font(self, font_str, name):
        """
        Creates an opengl font and puts it into the self.fonts dictionary

        This worked with older versions of gtkglext.  Newer versions
        removed pango support -- yuck!
        """
        font_description = pango.FontDescription(font_str)
        font_base = glGenLists(128)
        font = gtk.gdkgl.font_use_pango_font(font_description, 0, 128, font_base)
        if not font:
            self.make_font_raw(font_description, font_base, font_str, name)
        else:
            font_metrics = font.get_metrics()
            font_width = pango.PIXELS(font_metrics.get_approximate_digit_width())
            font_ascent = pango.PIXELS(font_metrics.get_ascent())
            font_descent = pango.PIXELS(font_metrics.get_descent())
            self.fonts[name] = {'base': font_base, 'width': font_width, 'height': font_ascent + font_descent}

    def make_font_raw(self, font_description, font_base, font_str, name):
        """
        Creates an opengl font and puts it into the self.fonts dictionary

        This slower code works with old and new versions of gtkglext.
        """
        #font_description = pango.FontDescription(font_str)
        size = int(font_str.split()[-1])
        w, h = 3*size, 3*size # assumes 3 pixels per pt ***
        surface = cairo.ImageSurface(cairo.FORMAT_A1, w, h) # B/W, width, height
        cairo_context = cairo.Context(surface)
        context = pangocairo.CairoContext(cairo_context)
        layout = context.create_layout()
        layout.set_font_description(font_description)

        #font_base = glGenLists(128)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1) # One byte alignment
        glPixelStorei(GL_UNPACK_LSB_FIRST, GL_TRUE) # Not sure if endianness dependency is safe over all platforms

        metric_char = ord('F') # basis for width, height
        for c in range(128):
            context.set_operator(cairo.OPERATOR_CLEAR)
            context.rectangle(0, 0, w, h)
            context.fill()
            context.set_operator(cairo.OPERATOR_SOURCE)
            layout.set_text(chr(c))
            context.show_layout(layout)
            pixel_extents, logical_extents = layout.get_pixel_extents()
            if c == metric_char:
                font_width = logical_extents[2]
                font_height = logical_extents[3]

            bytes = np.frombuffer(surface.get_data(), dtype = np.uint8)

            bytes = bytes.reshape((h, 4*int(math.ceil(w/32.0))))
            bytes = bytes[logical_extents[1]:logical_extents[3],
                          int(math.ceil(logical_extents[0]/8.0)):int(math.ceil(logical_extents[2]/8.0))] # extract only the character
            bytes = bytes[::-1] # flip upside down for OpenGL coordinate system

            glNewList(font_base + c, GL_COMPILE)
            glBitmap(logical_extents[2], logical_extents[3], 0, 0, logical_extents[2], 0, bytes)
            glEndList()
        self.fonts[name] = {'base': font_base, 'width': font_width, 'height': font_height}
        glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
        glPixelStorei(GL_UNPACK_LSB_FIRST, GL_FALSE)

    def make_image(self, name, filename = None):
        """
        Creates an image from file and puts it into the self.images dictionary
        """
        if not filename:
            filename = name
        im = Image.open(os.path.join(share_directory, filename + '.png'))
        xsize, ysize = im.size
        im_print = im.resize((int(xsize/self.IMAGE_SCALE), int(ysize/self.IMAGE_SCALE)), Image.BILINEAR)
        im_screen = im.resize((int(xsize/(self.PS_SCALE*self.IMAGE_SCALE)), int(ysize/(self.PS_SCALE*self.IMAGE_SCALE))), Image.BILINEAR)
        self.images[name] = {'im_print': im_print,
                             'im_screen': im_screen,
                             'print': np.frombuffer(im_print.transpose(Image.FLIP_TOP_BOTTOM).tostring(), dtype = np.uint32),
                             'screen': np.frombuffer(im_screen.transpose(Image.FLIP_TOP_BOTTOM).tostring(), dtype = np.uint32)}

    def generate_help_sizes(self):
        """
        Goes through the help images and gets the size of each
        """
        yl = 12.0/72.0*300.0*4 # 12pt, 4 lines
        self.help_sizes = {}
        lefts = []
        rights = []
        help_files = os.listdir(os.path.join(share_directory, 'helps'))
        for help_file in help_files:
            im = Image.open(os.path.join(share_directory, 'helps', help_file))
            base, ext = os.path.splitext(help_file)
            # instructions crops the y, so we do so here, then add
            # room for labels.  It's not perfect in y but closer.
            bbox = im.getbbox()
            self.help_sizes[base] = (im.size[0], bbox[3] - bbox[1] + yl)
            if base.endswith('_left'):
                lefts.append(base)
            elif base.endswith('_right'):
                rights.append(base)
        #print self.help_sizes

        # Handle all the split helps
        for left in lefts:
            for right in rights:
                name = left[:-len('_left')] + right[len('help_gear_axle2s'):-len('_right')]
                name = name.replace('None', '')
                x = self.help_sizes[left][0] + self.help_sizes[right][0]
                y = max(self.help_sizes[left][1], self.help_sizes[right][1])
                self.help_sizes[name] = (x, y)
        for left in lefts:
            del self.help_sizes[left]
        for right in rights:
            del self.help_sizes[right]
        #print self.help_sizes

    def key_lookup(self, func_call):
        """
        Discovers which key is attached to a given function call
        """
        key = self.key_table[func_call]
        retval = gtk.accelerator_parse(key)
        if key not in ['KP_Up', 'KP_Down', 'KP_Left', 'KP_Right', 'Right', 'Left', 'Up', 'Down']: # Avoids pygtk bug that kind of and kind of doesn't recognize these keys
            del self.key_table[func_call]
        return retval
        
    def update_title(self):
        """
        Updates the window title
        """
        if self.current_filename:
            self.win.set_title('cbmodel [' + self.current_filename + ']')
        else:
            self.win.set_title('cbmodel')

    def opengl_init(self, widget):
        """
        Initializes the opengl portion of the window
        """

        if self.image_type == 'print' and self.rendering == 'indirect':
            glcontext = self.print_glarea[0]
            gldrawable = self.print_glarea[1]
        #if 0:
        #    pass
        else:
            glcontext = gtk.gtkgl.widget_get_gl_context(self.glarea)
            gldrawable = gtk.gtkgl.widget_get_gl_drawable(self.glarea)
        if not gldrawable.gl_begin(glcontext):return

        glClearDepth(1.0)
        glEnable(GL_DEPTH_TEST)
        glClearColor(self.background_color[0], self.background_color[1], self.background_color[2], 0.0) 

        glShadeModel(GL_SMOOTH)

        # lighting
        # Default Lighting Good Enough
        glLightfv(GL_LIGHT0, GL_POSITION, (0.0, 0.0, 1.0, 0.0)) # infinite
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        #glLightfv(GL_LIGHT0, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

        # Brighter white
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.5, 0.5, 0.5, 1.0))

        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glColorMaterial(GL_FRONT, GL_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL) # before
        #glDisable(GL_COLOR_MATERIAL) # allows specification of material

        glLoadIdentity()
        gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
        #gleSetNumSides(32)

        glDrawBuffer(GL_FRONT_AND_BACK)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LINE_SMOOTH)
        glLineWidth(2.0)

        gldrawable.gl_end()

    def text_box(self, xl, xr, yb, yt, text, font):
        """
        Draws a box with text centered in it
        """
        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)

        pts = map(lambda x: gluUnProject(x[0], x[1], 0.001, model, projection, viewport), [(xl, yb), (xr, yb), (xr, yt), (xl, yt)])
        glBegin(GL_LINE_LOOP)
        for p in pts:
            glVertex3fv(p)
        glEnd()
        p = gluUnProject((xl + xr)/2 - len(text)*font['width']/2, (yb + yt)/2-font['height'], 0.001, model, projection, viewport) # 0.0 for z component sometimes caused clipping
        glRasterPos3fv(p)
        glListBase(font['base'])
        glCallLists(text)
        
    def opengl_draw(self, widget, event):
        """
        Redraws the opengl portion of the screen
        """
        time1 = time.time()
        if self.image_type == 'print' and self.rendering == 'indirect':
            glcontext = self.print_glarea[0]
            gldrawable = self.print_glarea[1]
        else:
            glcontext = gtk.gtkgl.widget_get_gl_context(self.glarea)
            gldrawable = gtk.gtkgl.widget_get_gl_drawable(self.glarea)
        if not gldrawable.gl_begin(glcontext):return

        glLoadIdentity()
        veye = self.vcenter + self.vout
        gluLookAt(veye[0], veye[1], veye[2], \
        self.vcenter[0], self.vcenter[1], self.vcenter[2], \
        self.vup[0], self.vup[1], self.vup[2]) # reference point currently fixed
        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)

        pieces.default_material()

        if self.redisplay == 'draw':
            # For older python-opengl implementations with
            # glReadPixel/glDrawPixel memory leaks, comment the
            # draw() line and uncomment the redraw() line.
            self.total.draw(self.vout, self.vup, self.creationmode)
            #self.total.redraw(self.vout, self.vup, self.creationmode)
        else:
            self.total.redraw(self.vout, self.vup, self.creationmode)

        if (self.creationmode == 'modelling') and self.part_add_pieces.get_active():
            if len(self.total.ends) > 0:
                self.part.calc_draw(base_pieces.colors['part'])

        elif self.creationmode == 'instructions':

            scale = self.ps_scale
            if scale == 3 and self.image_type == 'print':
                local_image_type = 'print'
            else:
                local_image_type = 'screen'
            FMS = scale*self.FRAME_MARGIN_SIZE*self.SCREEN_SCALE

            if self.total.frame == 0 and not self.omit_logo: # Draw Logo on title
                if self.background_color == self.SCREEN_COLOR[0]:
                    logo = self.images['logo_white']
                else:
                    logo = self.images['logo_black']
                width, height = logo['im_' + local_image_type].size
                p = np.array(gluUnProject(viewport[2]/2-width/2, viewport[3]-height-FMS, 0.001, model, projection, viewport)) # offset by 0.001 to avoid possible rectangle clipping
                glRasterPos3fv(p)
                glDepthMask(GL_FALSE)
                #glAlphaFunc(GL_GREATER, 0.5)
                #glEnable(GL_ALPHA_TEST)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glEnable(GL_BLEND)
                glDrawPixels(width, height, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8_REV, logo[local_image_type])
                #glDisable(GL_ALPHA_TEST)
                glDisable(GL_BLEND)
                glDepthMask(GL_TRUE)

            if len(self.mirror_pos) > 0: # Draw mirror, if need be
                p = np.array(gluUnProject(scale*self.mirror_pos[0], scale*self.mirror_pos[1], 0.001, model, projection, viewport))
                width, height = self.images['mirror']['im_' + local_image_type].size
                glRasterPos3fv(p)
                glDepthMask(GL_FALSE)
                #glAlphaFunc(GL_GREATER, 0.5)
                #glEnable(GL_ALPHA_TEST)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glEnable(GL_BLEND)
                glDrawPixels(width, height, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8_REV, self.images['mirror'][local_image_type])
                #glDisable(GL_ALPHA_TEST)
                glDisable(GL_BLEND)
                glDepthMask(GL_TRUE)

            if len(self.magnify_pos) > 0: # Draw magnify, if need be
                width, height = self.images['magnify']['im_' + local_image_type].size
                if len(self.magnify_pos) == 2: # a coordinate
                    x, y = scale*self.magnify_pos[0], scale*self.magnify_pos[1]
                else: # a part index
                    part_index = self.magnify_pos[-1]
                    center = self.total.netlist[part_index].center
                    snap_pos = gluProject(center[0], center[1], center[2], model, projection, viewport)
                    x = snap_pos[0] - width/2
                    y = snap_pos[1] - height/2
                    x = max(x, 0)
                    x = min(x, viewport[2]-width)
                    y = max(y, 0)
                    y = min(y, viewport[3]-height)
                    self.magnify_pos = (int(x/scale), int(y/scale), part_index)
                p = np.array(gluUnProject(x, y, 0.001, model, projection, viewport))
                glRasterPos3fv(p)
                glDepthMask(GL_FALSE)
                #glAlphaFunc(GL_GREATER, 0.5)
                #glEnable(GL_ALPHA_TEST)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glEnable(GL_BLEND)
                glDrawPixels(width, height, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8_REV, self.images['magnify'][local_image_type])
                #glDisable(GL_ALPHA_TEST)
                glDisable(GL_BLEND)
                glDepthMask(GL_TRUE)

            if self.image_type == 'screen': # Use OpenGL Text Annotation
                glDisable(GL_LIGHTING)

                # Draw submodels
                stack_count = len(self.total.submodel_stack)
                if stack_count > 0:
                    glColor3fv(self.annotate_color)
                    glDepthMask(GL_FALSE)
                    SEP = 10*scale
                    y = viewport[3] - FMS - scale*self.fonts['framenum']['height']
                    width = int(90.0*self.ps_scale/self.PS_SCALE)
                    height = int(20.0*self.ps_scale/self.PS_SCALE)
                    for count in range(1, stack_count + 1):
                        y = y - height - SEP
                        p1 = np.array(gluUnProject(viewport[2] - FMS - width, y, 0.001, model, projection, viewport))
                        p2 = np.array(gluUnProject(viewport[2] - FMS, y, 0.001, model, projection, viewport))
                        glLineWidth(height)
                        glBegin(GL_LINES)
                        glVertex3fv(p1)
                        glVertex3fv(p2)
                        glEnd()
                        glLineWidth(2.0)
                    glDepthMask(GL_TRUE)

                # Draw title
                if self.total.frame == 0:
                    if len(self.total.instructions) > 0:
                        if self.total.instructions[0].has_key('title'):
                            glColor3fv(self.annotate_color)
                            text = self.total.instructions[0]['title'].upper()
                            font = self.fonts['title']
                            p = gluUnProject(scale*self.SCREEN_SCALE*self.MARGIN_SIZE, scale*self.SCREEN_SCALE*self.MARGIN_SIZE, 0.001, model, projection, viewport) # 0.0 for z component sometimes caused clipping
                            glRasterPos3fv(p)
                            glDepthMask(GL_FALSE)
                            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                            glEnable(GL_BLEND)
                            glListBase(font['base'])
                            glCallLists(text)
                            glDisable(GL_BLEND)
                            glDepthMask(GL_TRUE)
                        # Draw Title Block
                        glColor3fv(self.annotate_color)
                        xr = viewport[2] - scale*self.SCREEN_SCALE*self.MARGIN_SIZE
                        xl = xr - scale*self.SCREEN_SCALE*3 # 3x1 inch assumed
                        yb = scale*self.SCREEN_SCALE*self.MARGIN_SIZE
                        yt = yb + scale*self.SCREEN_SCALE*1.0
                        self.text_box(xl, xr, yb, yt, 'Title Block', self.fonts['title'])
                        
                # Poses
                elif self.total.frame < self.total.instruction_start:
                    pass
                            
                # Instruction Steps
                else:
                    glColor3fv(self.annotate_color)
                    # Draw the frame number
                    text = str(self.total.frame - self.total.instruction_start + 1)
                    font = self.fonts['framenum']
                    p = np.array(gluUnProject(viewport[2]-FMS-len(text)*font['width'], viewport[3]-FMS-font['height'], 0.001, model, projection, viewport)) # 0.0 for z component sometimes caused clipping
                    glRasterPos3fv(p)
                    glListBase(font['base'])
                    glCallLists(text)
                    # Draw the part labels
                    if not self.instructions_hide_part_labels.get_active():
                        vleft = -vector_math.cross(self.vup, self.vout)
                        font = self.fonts['part']
                        helper_labels = []
                        glListBase(font['base'])
                        glColor3fv(self.PRINT_BODY_COLOR[2])
                        for part_index in self.total.selected:
                            part = self.total.netlist[part_index]
                            label = part.label()
                            for config_index in range(len(label)):
                                text = self.name2simple[label[config_index]]
                                center = part.center
                                glRasterPos3fv(center + self.vout*pieces.base_rad*20 + vleft*len(text)/2.0*font['width']/self.pixperunit + self.vup*(-0.5 + 1.2*((len(label)-1)/2.0 - config_index))*(font['height'])/self.pixperunit)
                                glCallLists(text)
                            # Check to see if help added before.  Expensive
                            if len(label) > 1: # a help
                                help_add = 1
                                for inst in self.total.instructions[1:self.total.frame]:
                                    for part_index in inst['new_parts']:
                                        if self.total.netlist[part_index].label() == label:
                                            help_add = 0
                                            break
                                    if help_add == 0:
                                        break
                                if help_add and label not in helper_labels:
                                    helper_labels.append(label)
                        yt = viewport[3] - FMS
                        sizes = []
                        for helper_label in helper_labels:
                            key = 'help_' + reduce(lambda x, y: x + y, helper_label)
                            if key in self.help_sizes:
                                text = reduce(lambda x, y: x + ' ' + y, map(lambda z: self.name2alias[z], helper_label))
                                size = self.help_sizes[key]
                                sizes.append((size[0], size[1], text))
                        sizes.sort()
                        sizes.reverse()
                        for size in sizes:
                            x, y, text = size
                            xl = FMS
                            xr = xl + int(scale*x/self.PS_SCALE)
                            yb = yt - int(scale*y/self.PS_SCALE)
                            #print xl, xr, yt, yb
                            self.text_box(xl, xr, yb, yt, text, self.fonts['part'])
                            yt = yb
                    glColor3fv(self.annotate_color)
                glEnable(GL_LIGHTING)

            else: # Drawing the PDF
                self.part_labels = []
                for part_index in self.total.selected:
                    part = self.total.netlist[part_index]
                    p = [gluProject(part.center[0], part.center[1], part.center[2], model, projection, viewport), part.label(), part.help_text(), part.inset_files()]
                    self.part_labels.append(p)

            # Restore the Raster Position
            p = np.array(gluUnProject(0.001, 0.001, 0.001, model, projection, viewport)) # 0.0 for x/y/z sometimes caused clipping
            glRasterPos3fv(p)

        if self.mode == 'border_select' and self.beginx != None:
            glColor3fv(self.highlight_color)
            v0 = gluUnProject(self.beginx, viewport[3]-viewport[1]-self.beginy, 0, model, projection, viewport)
            v1 = gluUnProject(self.beginx, viewport[3]-viewport[1]-self.endy, 0, model, projection, viewport)
            v2 = gluUnProject(self.endx, viewport[3]-viewport[1]-self.endy, 0, model, projection, viewport)
            v3 = gluUnProject(self.endx, viewport[3]-viewport[1]-self.beginy, 0, model, projection, viewport)
            glDisable(GL_LIGHTING)
            glLineStipple(3, 0xAAAA)
            glEnable(GL_LINE_STIPPLE)
            glBegin(GL_LINE_STRIP)
            glVertex3fv(v0)
            glVertex3fv(v1)
            glVertex3fv(v2)
            glVertex3fv(v3)
            glVertex3fv(v0)
            glEnd()
            glDisable(GL_LINE_STIPPLE)
            glEnable(GL_LIGHTING)

        elif self.mode == 'rotate' or self.mode == 'rotate_region':
            glColor3fv(self.highlight_color)
            v0 = gluUnProject(self.beginx, viewport[3]-viewport[1]-self.beginy, 0, model, projection, viewport)
            v1 = gluUnProject(self.endx, viewport[3]-viewport[1]-self.endy, 0, model, projection, viewport)
            glDisable(GL_LIGHTING)
            glLineStipple(3, 0xAAAA)
            glEnable(GL_LINE_STIPPLE)
            glBegin(GL_LINES)
            glVertex3fv(v0)
            glVertex3fv(v1)
            glEnd()
            glDisable(GL_LINE_STIPPLE)
            glEnable(GL_LIGHTING)

        if self.draw_center:
            glColor3fv(self.highlight_color)
            glDisable(GL_LIGHTING)
            glPointSize(5)
            glBegin(GL_POINTS)
            if self.creationmode == 'instructions':
                if self.total.frame < self.total.instruction_start:
                    for center in self.total.region_centers:
                        glVertex3fv(center)
                else:
                    for part_index in range(len(self.total.netlist)):
                        if self.total.part_flags[part_index] != 3:
                            glVertex3fv(self.total.netlist[part_index].center + pieces.base_rad * 2.0 * self.vout)
                            
            else:
                for part in self.total.netlist:
                    glVertex3fv(part.center + pieces.base_rad * 2.0 * self.vout)
            glEnd()
            glEnable(GL_LIGHTING)

        # Shouldn't be part of opengl_draw, but easier to put here
        # than in many other places
        self.selected_bar.set_text(str(len(self.total.selected)))

        glFlush()

        gldrawable.gl_end()
        time2 = time.time()
        self.fps_label.set_text('%.1fs' % (time2-time1))
        self.draw_called = 1
        self.redisplay = 'draw'

    def opengl_reshape(self, widget, event):
        """
        Resizes the opengl screen
        """

        if self.image_type == 'print' and self.rendering == 'indirect':
            glcontext = self.print_glarea[0]
            gldrawable = self.print_glarea[1]
        else:
            glcontext = gtk.gtkgl.widget_get_gl_context(self.glarea)
            gldrawable = gtk.gtkgl.widget_get_gl_drawable(self.glarea)
        if not gldrawable.gl_begin(glcontext):return

        if type(widget) == type(tuple()):
            w, h = widget

        else:
            w = widget.allocation.width
            h = widget.allocation.height

        self.SCR = (w, h)
        #print self.SCR

        aspect = float(w)/float(h)
        glViewport(0, 0, w, h)
        if self.image_type == 'print':
            ppu = self.ps_scale*self.pixperunit
        else:
            ppu = self.pixperunit
        x = 0.5*float(w)/ppu
        y = 0.5*float(h)/ppu
        #print 'New Dimensions: (' + repr(x) + ', ' + repr(y) + ')'
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        #glFrustum(-x, x, -y, y, 50.0, 400.0)
        glOrtho(-x, x, -y, y, -400.0, 400.0)
        base_pieces.depth_scale = 1.0/800.0 # determined by glOrtho
        glMatrixMode(GL_MODELVIEW)
        self.lowerleft = (x, y)
        self.mpan = max(w, h) / 10.0

        gldrawable.gl_end()
        self.redisplay = 'redraw'
        self.glarea.queue_draw() # Needed for gtk
        self.reshape_called = 1
    
    def window_size_full(self, widget = None):
        """
        Sets the opengl screen size to COVER_SIZE
        """
        self.winsize = 'full'
        self.window_size(widget, (int(self.COVER_SIZE[0]*self.SCREEN_SCALE), int(self.COVER_SIZE[1]*self.SCREEN_SCALE)))

    def window_size_fullr(self, widget = None):
        """
        Sets the opengl screen size to COVER_SIZE rotate 90 degrees
        """
        self.winsize = 'fullr'
        self.window_size(widget, (int(self.COVER_SIZE[1]*self.SCREEN_SCALE), int(self.COVER_SIZE[0]*self.SCREEN_SCALE)))

    def window_size_quarter(self, widget = None):
        """
        Sets the opengl screen size to a quarter of COVER_SIZE
        """
        self.winsize = 'quarter'
        self.window_size(widget, (int(self.FRAME_SIZE[0]*self.SCREEN_SCALE), int(self.FRAME_SIZE[1]*self.SCREEN_SCALE)))

    def window_size_halfh(self, widget = None):
        """
        Sets the opengl screen size to half a COVER_SIZE
        """
        self.winsize = 'halfh'
        self.window_size(widget, (int(self.COVER_SIZE[0]*self.SCREEN_SCALE), int(self.FRAME_SIZE[1]*self.SCREEN_SCALE)))

    def window_size(self, widget, size):
        """
        Sets the opengl screen size to size
        """
        if not size:
            size = self.SCR[:]
        #self.reshape_called = 0
        #self.draw_called = 0
        if size[0] < self.SCR[0] or size[1] < self.SCR[1]:
            self.win.resize(200, 200)
        if self.image_type == 'print':
            # Use Pixmap for correct screen-capture of off-screen or
            # obscured-window objects.

            x = int(self.ps_scale*size[0])
            y = int(self.ps_scale*size[1])
            #print 'size', x, y
            if self.rendering == 'indirect':
                self.print_glarea = (None, None, None) # dereference old
                pixmap = gtk.gdk.Pixmap(None, x, y, 24)
                glconfig = gtk.gdkgl.Config(mode=gtk.gdkgl.MODE_RGB | gtk.gdkgl.MODE_DEPTH | gtk.gdkgl.MODE_DOUBLE | gtk.gdkgl.MODE_ALPHA)
                glpixmap = gtk.gdkgl.Pixmap(glconfig, pixmap)
                glcontext = gtk.gdkgl.Context(glpixmap, share_list = self.glarea.get_gl_context(), direct = False) # only works if self.glarea started with direct = False.  The next line works for nvidia cards, but it reportedly fails for others.
                #glcontext = gtk.gdkgl.Context(glpixmap, share_list = self.glarea.get_gl_context())
                self.print_glarea = (glcontext, glpixmap, pixmap)
                self.opengl_init(None)
            else:
                self.glarea.set_size_request(x, y)
        else:
            #print 'size', size[0], size[1]
            self.glarea.set_size_request(size[0], size[1])
        self.reshape_called = 0
        self.draw_called = 0
        self.total.redraw_called = 0
        if self.image_type == 'print' and self.rendering == 'indirect':
            self.opengl_reshape((x, y), None)
        else:
            self.opengl_reshape(self.glarea, None)
        while not self.reshape_called or not self.draw_called or not self.total.redraw_called:
            gtk.main_iteration()

    def window_color(self, widget, color, redraw = 1):
        """
        Sets the opengl screen colors to a given color
        """
        glClearColor(color[0][0], color[0][1], color[0][2], 0.0)
        self.background_color = color[0]
        self.annotate_color = color[1]
        self.highlight_color = color[2]
        if redraw:
            self.redisplay = 'redraw'
            self.glarea.queue_draw()

    def set_pixperunit(self, value):
        self.pixperunit = value
        base_pieces.pixperunit = value

    def set_draw_outline(self, widget = None, value = 0):
        """
        Turns on or off drawing of outlines around the opengl image
        """
        if widget:
            value = int(widget.get_active())
        base_pieces.draw_outline = value

    def set_draw_center(self, widget = None, value = 0):
        """
        Turns on or off center of piece drawing
        """
        if widget:
            value = int(widget.get_active())
        self.draw_center = value

    def set_keys(self, widget = None, value = 'numpad'):
        dialog = gtk.MessageDialog(self.win, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL, 'Your key mappings will permanently change.  You must restart the program to have the key changes take effect.')
        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK or response == gtk.RESPONSE_APPLY:
            config_name = self.config_name()
            if config_name:
                config = ConfigParser.RawConfigParser()
                config.read(config_name)
            if value == 'nonumpad':
                local_keys = self.nonumpad
                if not config.has_section('Keys'):
                    config.add_section('Keys')
                for key in local_keys:
                    value = local_keys[key]
                    config.set('Keys', key, value)
            else:
                if config.has_section('Keys'):
                    config.remove_section('Keys') # Default is numpad
            fp = None
            try:
                fp = open(config_name, 'wb')
            except IOError:
                self.status_bar.set_text('Warning: Can\'t write ' + config_name)
            if fp:
                config.write(fp)
                fp.close()
        dialog.destroy()

    def scrolled_dialog(self, title, msg, xsize = 200, ysize = 200):
        """
        Generates a scrollable dialog box
        """
        dialog = gtk.Dialog(title, self.win, 0, (gtk.STOCK_CLOSE, gtk.RESPONSE_OK))
        dialog.set_default_size(xsize, ysize)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        tv = gtk.TextView()
        tv.set_editable(False)
        tb = tv.get_buffer()
        tb.set_text(msg)
        sw.add(tv)
        dialog.vbox.pack_start(sw)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def alias_inventory(self):
        """
        Converts a piece inventory to the known (alias) names
        """
        inventory = self.total.inventory()
        ainv = []
        for quantity, name in inventory:
            ainv.append((self.name2alias[name], quantity))
        ainv.sort()
        return ainv

    def view_inventory(self, widget):
        """
        Displays a dialog of the inventory in the module
        """
        msg = 'Quantity Piece\n'
        total = 0
        for name, quantity in self.alias_inventory():
            msg = msg + name + ' ' + str(quantity) + '\n'
            total = total + int(quantity)
        msg = msg + 'Total ' + str(total) + '\n'
        #msg = msg + 'Major Total ' + str(len(self.total.netlist)) + '\n'
        self.scrolled_dialog('Inventory', msg)

    def view_mass(self, widget):
        """
        Displays a dialog of the mass of the module
        """
        mass = self.total.mass()
        msg = 'Mass: %.1fg' % mass + \
            '\nWeight: %.1foz' % (mass / 454.0 * 16.0)
        self.scrolled_dialog('Mass', msg)

    def view_price(self, widget):
        """
        Displays a dialog of the price of the module
        """
        self.scrolled_dialog('Price', 'price: $%.2f' % self.total.price())

    def view_dimensions(self, widget):
        """
        Displays a dialog of the dimensions of the module
        """
        dimensions = self.total.dimensions()
        msg = instructions.sizestr(dimensions, 'cm') + '\n' + \
            instructions.sizestr(dimensions, 'm') + '\n' + \
            instructions.sizestr(dimensions, 'in') + '\n' + \
            instructions.sizestr(dimensions, 'ft')
        self.scrolled_dialog('Dimensions', msg)

    def view_page_count(self, widget):
        """
        Displays a dialog of the page count in the module's instructions
        """
        msg = str(self.page_count()) + ' Pages'
        self.scrolled_dialog('Pages', msg)

    def display_manual(self, widget):
        """
        Displays the cbmodel manual
        """
        global doc_directory
        fullname = os.path.join(doc_directory, 'cbmodel.pdf')
        if sys.platform.startswith('linux'):
            os.system('xdg-open ' + fullname + ' &')
        elif sys.platform.startswith('win'):
            os.system('start ' + fullname)
        elif sys.platform.startswith('darwin'):
            os.system('open ' + fullname)
        else:
            self.status_bar.set_text('Warning: PDF viewer not found.')

    def about(self, widget):
        """
        Displays information about the program
        """
        global version
        dialog = gtk.AboutDialog()
        dialog.set_name('Crossbeams Modeller')
        dialog.set_version(str(version))
        dialog.set_copyright('\302\251 Copyright 2014, Seven:Twelve Engineering, LLC')
        dialog.run()
        dialog.destroy()

    def set_mode(self, widget, mode, redraw = 1):
        """
        Changes between creation and instruction mode
        """
        if self.creationmode != mode:
            self.glarea.window.set_cursor(self.WAIT_CURSOR)
            self.total.selected = []
            self.creationmode = mode
            if mode == 'modelling':
                # Hide unused menus
                self.instructions_menu.hide()

                # Show modelling-related menus
                self.part_menu.show()
                for item in self.modelling_only_items:
                    item.set_sensitive(True)
                for item in self.instructions_only_items:
                    item.set_sensitive(False)
                if self.total.hold_pose:
                    self.total.restore_centers()
                if redraw:
                    self.redisplay = 'redraw'
                    self.glarea.queue_draw()
                self.win.set_resizable(True)

            elif mode == 'instructions':
                # Hide unused menus
                self.part_menu.hide()

                # Show instruction-related menus
                self.instructions_menu.show()

                for item in self.modelling_only_items:
                    item.set_sensitive(False)
                for item in self.instructions_only_items:
                    item.set_sensitive(True)

                self.total.find_regions()
                self.toggle_frame(None, 0, 0)
                if self.total.hold_pose: # workaround to avoid menu call
                    if self.instructions_hold_pose.get_active():
                        self.total.hold_pose_matrices()
                        self.total.pose_centers()
                    else:
                        self.instructions_hold_pose.set_active(True)
                self.win.set_resizable(False)

            else:
                print 'Error: Unrecognized mode', mode
            self.glarea.window.set_cursor(self.REGULAR_CURSOR)

    def clear_instructions(self, widget):
        """
        Deletes all instructions, causing a restart
        """
        dialog = gtk.MessageDialog(self.win, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL, 'All current instructions will be removed.')
        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK or response == gtk.RESPONSE_APPLY:
            self.total.instructions = []
            self.total.instruction_start = 1
            self.total.frame = 0
            self.toggle_frame(None, 0, 0)
        dialog.destroy()

    def set_instructions_title(self, widget):
        """
        Displays a dialog to get and set the instruction title and author
        """
        dialog = gtk.Dialog('Instructions Title', self.win, 0, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        entries = []
        table = gtk.Table(2, 2)
        dialog.vbox.pack_start(table, False, False, 0)

        entry_title = gtk.Entry()
        if len(self.total.instructions) > 0 and self.total.instructions[0].has_key('title'):
            entry_title.set_text(self.total.instructions[0]['title'])
        table.attach(gtk.Label('Title'), 0, 1, 0, 1)
        table.attach(entry_title, 1, 2, 0, 1)

        entry_author = gtk.Entry()
        if len(self.total.instructions) > 0 and self.total.instructions[0].has_key('author'):
            entry_author.set_text(self.total.instructions[0]['author'])
        table.attach(gtk.Label('Author'), 0, 1, 1, 2)
        table.attach(entry_author, 1, 2, 1, 2)

        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK or response == gtk.RESPONSE_APPLY:
            if len(self.total.instructions) <= 0:
                self.toggle_frame(None, 0, 1)
            if entry_title.get_text():
                self.total.instructions[0]['title'] = entry_title.get_text()
            if entry_author.get_text():
                self.total.instructions[0]['author'] = entry_author.get_text()
        dialog.destroy()

    def start_submodel(self, widget):
        """
        Starts a submodel in instructions mode
        """
        changed = 0
        if self.total.submodel == -1:
            # Make a continuation if at a pop
            self.total.submodel = 0
            changed = 1
        elif self.total.submodel == 0:
            self.total.submodel = 1
            changed = 1
        if changed:
            self.total.generate_submodel_stack()
            self.redisplay = 'redraw'
            self.glarea.queue_draw()

    def end_submodel(self, widget):
        """
        Ends a submodel in instructions mode
        """
        # Make sure a pop is legal
        changed = 0
        if self.total.submodel == 1:
            # Make a continuation if at a push
            self.total.submodel = 0
            changed = 1
        else:
            if len(self.total.submodel_stack) > 0:
                self.total.submodel = -1
                self.instructions_hide_part_labels.set_active(True)
                changed = 1
        if changed:
            self.total.selected = []
            self.selected_bar.set_text('0')
            self.total.generate_submodel_stack()
            self.redisplay = 'redraw'
            self.glarea.queue_draw()

    def show_mirror(self, widget):
        """
        Show the mirror icon in instructions mode
        """
        if self.total.frame > 0:
            if widget.get_active():
                self.mirror_pos = (self.SCR[0]/2, self.SCR[1]-self.images['mirror']['im_screen'].size[1])
            else:
                self.mirror_pos = ()
        else:
            self.mirror_pos = ()

    def show_magnify(self, widget):
        """
        Show the crosshairs icon in instructions mode
        """
        if self.total.frame > 0:
            if widget.get_active():
                self.magnify_pos = (int(self.SCR[0]/2), int(self.SCR[1]/2))
            else:
                self.magnify_pos = ()
        else:
            self.magnify_pos = ()

    def insert_frame(self, widget, after = 0):
        """
        Insert a frame in instructions mode
        
        Convention: Insert before the current frame and make it
        blank.  If the current frame was a submodel call, make the
        inserted frame the same submodel call.
        """

        self.toggle_frame(None, 0, 1) # Save current
        inst = self.total.instructions[self.total.frame]
        frame = {'vcenter': inst['vcenter'],
                 'vout': inst['vout'],
                 'vup': inst['vup'],
                 'pixperunit': inst['pixperunit'],
                 'new_parts': [],
                 'size': inst['size']}
        if self.total.frame < self.total.instruction_start:
            frame['fixed'] = inst['fixed']
            frame['rotates'] = map(lambda x: 0, self.total.region_rotates)
            self.total.instruction_start = self.total.instruction_start + 1
        if inst.has_key('submodel'):
            del inst['submodel']

        if after:
            self.total.instructions.insert(self.total.frame+1, frame)
        else:
            self.total.instructions.insert(self.total.frame, frame)
            # Only make things blank if it's a before frame
            self.total.selected = []
            self.mirror_pos = ()
            self.magnify_pos = ()
            self.instructions_hide_part_labels.set_active(False)
            self.instructions_show_mirror.set_active(False)
            self.instructions_show_magnify.set_active(False)

        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def delete_frame(self, widget):
        """
        Delete a frame in instructions mode

        Convention: Delete this frame and shift subsequent frames
        down.
        """
        if self.total.frame > 0:

            # Delete Pose
            if self.total.frame < self.total.instruction_start: # a pose frame
                del self.total.instructions[self.total.frame]
                if self.total.instruction_start > 1:
                    self.total.instruction_start = self.total.instruction_start - 1
            # Delete Instruction
            elif self.total.frame < len(self.total.instructions):
                del self.total.instructions[self.total.frame]
                self.total.clean_submodel_stack()

            # Clean Up
            if self.total.frame >= len(self.total.instructions):
                self.total.frame = self.total.frame - 1
            self.toggle_frame(None, 0, 0)

    def goto_frame(self, widget):
        """
        Displays a dialog to move to a specific frame in instructions mode
        """
        dialog = gtk.Dialog('Go To Frame', self.win, 0, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        entries = []
        table = gtk.Table(1, 2)
        dialog.vbox.pack_start(table, False, False, 0)

        entry_frame = gtk.Entry()
        table.attach(gtk.Label('Frame'), 0, 1, 0, 1)
        table.attach(entry_frame, 1, 2, 0, 1)

        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK or response == gtk.RESPONSE_APPLY:
            frame = entry_frame.get_text()
            if frame.isdigit():
                frame = min(max(1, int(frame) + self.total.instruction_start - 1), len(self.total.instructions)-1)
                self.toggle_frame(None, frame - self.total.frame, 1)
        dialog.destroy()
    
    def toggle_frame(self, widget = None, next = 1, save_current = 1):
        """
        Moves to the previous or next frame in instructions mode,
        saving the current frame
        """
        if self.creationmode == 'instructions':
            # If unchanged, don't advance
            if self.total.frame > 0 and self.total.frame < self.total.instruction_start:
                last_frame = self.total.instructions[self.total.frame-1]
                if (np.allclose(last_frame['vcenter'], self.vcenter) and
                    np.allclose(last_frame['vout'], self.vout) and
                    np.allclose(last_frame['vup'], self.vup) and
                    np.allclose(last_frame['pixperunit'], self.pixperunit) and
                    last_frame['fixed'] == self.total.region_fixed and
                    np.allclose(last_frame['rotates'], self.total.region_rotates) and
                    last_frame['size'] == self.winsize):
                    save_current = 0
                    if next > 0 and self.total.frame >= len(self.total.instructions):
                        return

            elif self.total.frame > self.total.instruction_start:
                last_frame = self.total.instructions[self.total.frame-1]
                if (np.allclose(last_frame['vcenter'], self.vcenter) and
                    np.allclose(last_frame['vout'], self.vout) and
                    np.allclose(last_frame['vup'], self.vup) and
                    np.allclose(last_frame['pixperunit'], self.pixperunit) and
                    (last_frame['new_parts'] == self.total.selected or
                     len(self.total.netlist) <= len(self.total.old_parts)) and
                    last_frame['size'] == self.winsize and
                    self.total.submodel == 0):
                    save_current = 0
                    if next > 0 and self.total.frame >= len(self.total.instructions):
                        return

            if save_current:
                # Save Old Frame
                if self.total.frame >= len(self.total.instructions):
                    self.total.instructions.append({})
                self.total.instructions[self.total.frame]['vcenter'] = self.vcenter
                self.total.instructions[self.total.frame]['vout'] = self.vout
                self.total.instructions[self.total.frame]['vup'] = self.vup
                self.total.instructions[self.total.frame]['pixperunit'] = self.pixperunit
                self.total.instructions[self.total.frame]['size'] = self.winsize
                
                if self.total.frame == 0:
                    self.total.restore_centers()
                    if self.total.hold_pose:
                        self.total.instructions[self.total.frame]['hold_pose'] = 1
                        self.total.hold_pose_matrices()
                        self.total.pose_centers()
                    elif self.total.instructions[self.total.frame].has_key('hold_pose'):
                        del self.total.instructions[self.total.frame]['hold_pose']

                if self.total.frame < self.total.instruction_start: # pose
                    self.total.instructions[self.total.frame]['new_parts'] = []
                    self.total.instructions[self.total.frame]['fixed'] = self.total.region_fixed
                    self.total.instructions[self.total.frame]['rotates'] = self.total.region_rotates[:]

                else: # instruction steps
                    self.total.instructions[self.total.frame]['new_parts'] = self.total.selected[:]
                    if self.instructions_hide_part_labels.get_active():
                        self.total.instructions[self.total.frame]['hide_part_labels'] = 1
                    elif self.total.instructions[self.total.frame].has_key('hide_part_labels'):
                        del self.total.instructions[self.total.frame]['hide_part_labels']
                    if len(self.mirror_pos) > 0:
                        self.total.instructions[self.total.frame]['show_mirror'] = self.mirror_pos[:]
                    elif self.total.instructions[self.total.frame].has_key('show_mirror'):
                        del self.total.instructions[self.total.frame]['show_mirror']
                    if len(self.magnify_pos) > 0:
                        self.total.instructions[self.total.frame]['show_magnify'] = self.magnify_pos[:]
                    elif self.total.instructions[self.total.frame].has_key('show_magnify'):
                        del self.total.instructions[self.total.frame]['show_magnify']
                    if self.total.submodel != 0:
                        self.total.instructions[self.total.frame]['submodel'] = self.total.submodel
                        if self.total.submodel == -1: # a pop
                            self.total.clean_submodel_stack()

                    elif self.total.instructions[self.total.frame].has_key('submodel'):
                        del self.total.instructions[self.total.frame]['submodel']

                    # Remove new_parts from all frames after this one (expensive ***)
                    local_frame = self.total.frame + 1
                    while local_frame < len(self.total.instructions):
                        self.total.instructions[local_frame]['new_parts'] = filter(lambda x: x not in self.total.selected, self.total.instructions[local_frame]['new_parts'])
                        local_frame = local_frame + 1

            # Change Frame
            self.total.frame = max(0, self.total.frame + next)

            # Create old_parts
            old_parts = []
            for frame_index in range(self.total.instruction_start, self.total.frame):
                old_parts = old_parts + self.total.instructions[frame_index]['new_parts']
            self.total.old_parts = old_parts

            # Load New Frame
            if self.total.frame < len(self.total.instructions):
                inst = self.total.instructions[self.total.frame]
                self.vcenter = inst['vcenter']
                self.vout = inst['vout']
                self.vup = inst['vup']
                #self.pixperunit = inst['pixperunit']
                self.set_pixperunit(inst['pixperunit'])
                self.total.selected = inst['new_parts']
                winsize = inst['size']
                if inst.has_key('submodel'):
                    self.total.submodel = inst['submodel']
                    if self.total.submodel == -1:
                        self.instructions_hide_part_labels.set_active(True)
                else:
                    self.total.submodel = 0
                if inst.has_key('hide_part_labels'):
                    self.instructions_hide_part_labels.set_active(True)
                else:
                    self.instructions_hide_part_labels.set_active(False)
                if inst.has_key('show_mirror'):
                    self.instructions_show_mirror.set_active(True)
                    self.mirror_pos = inst['show_mirror']
                else:
                    self.instructions_show_mirror.set_active(False)
                    self.mirror_pos = ()
                if inst.has_key('show_magnify'):
                    self.instructions_show_magnify.set_active(True)
                    self.magnify_pos = inst['show_magnify']
                else:
                    self.instructions_show_magnify.set_active(False)
                    self.magnify_pos = ()
                if inst.has_key('fixed'):
                    fixed = min(max(0, inst['fixed']), len(self.total.regions)-1) # Must handle a change from last time
                    self.total.set_region_fixed(fixed)
                if inst.has_key('rotates'):
                    delta = len(self.total.region_rotates) - len(inst['rotates']) # Must handle a change from last time
                    if delta <= 0:
                        self.total.region_rotates = inst['rotates'][:len(self.total.region_rotates)]
                    else:
                        self.total.region_rotates = inst['rotates'] + [0]*delta

            else: # Anything that should be reset per frame goes here
                if self.total.frame == 0:
                    winsize = 'full'
                else:
                    winsize = self.winsize
                self.total.selected = []
                self.total.submodel = 0
                self.mirror_pos = ()
                self.magnify_pos = ()
                self.instructions_hide_part_labels.set_active(False)
                self.instructions_show_mirror.set_active(False)
                self.instructions_show_magnify.set_active(False)

            # Create submodel_stack
            self.total.generate_submodel_stack()

            if winsize == 'full':
                self.window_size_full()
            elif winsize == 'fullr':
                self.window_size_fullr()
            elif winsize == 'quarter':
                self.window_size_quarter()
            elif winsize == 'halfh':
                self.window_size_halfh()
            else:
                self.window_size(None, (1, 1))

            if self.total.frame == 0:
                self.status_bar.set_text('Title Page')
            elif self.total.frame < self.total.instruction_start:
                self.status_bar.set_text('Pose ' + str(self.total.frame))
            else:
                self.status_bar.set_text('Frame ' + str(self.total.frame - self.total.instruction_start + 1))

    def instructions_draft(self, widget = None, value = 1):
        """
        Turns instructions draft mode on or off
        """
        if widget:
            value = int(widget.get_active())
        if value:
            self.ps_scale = 1
        else:
            self.ps_scale = 3

    def page_layouts(self):
        """
        Returns the page layout of each page in the instruction set as
        a list.  Excludes front and back covers.  len(page_layouts())+2
        returns the number of pages.
        """
        sizes = reduce(lambda x, y: x + y,
                       map(lambda z: z['size'][0],
                           self.total.instructions))
        sizes_pose = sizes[:self.total.instruction_start]
        sizes_instruction = sizes[self.total.instruction_start:]
        frame_index = 1
        retval = []
        for sizes in [sizes_pose, sizes_instruction]:
            while frame_index < len(sizes):
                layouts = ['f', 'qqqq', 'qqh', 'hqq', 'hh', 'qh', 'qqq', 'hq',
                           'qq', 'q', 'h']
                for layout in layouts:
                    if sizes[frame_index:frame_index+len(layout)] == layout:
                        frame_index = frame_index + len(layout)
                        retval.append(layout)
                        break
            frame_index = 0

        return retval

    def page_count(self):
        """
        Returns the number of pages in the instruction set including
        front and back cover.
        """
        return len(self.page_layouts()) + 2

    def generate_instructions(self, widget, filename = None, scale = 1.0):
        """
        Generates an instruction set
        """
        save_draw_outline = base_pieces.draw_outline
        base_pieces.draw_outline = 1
        save_draw_center = self.draw_center
        self.draw_center = 0
        save_color_scheme = (self.background_color, self.annotate_color, self.highlight_color)
        base_pieces.draw_future_parts = 0
        self.image_type = 'print'
        base_pieces.generate_pdf = 1
        base_pieces.dim_scale = self.ps_scale

        if not filename and self.current_filename == '':
            self.status_bar.set_text('Choose filename first')
        else:
            if not filename:
                base, ext = os.path.splitext(self.current_filename)
                filename = base + '.pdf'
            instructions.generate_instructions(self, share_directory, filename, scale)
            

        base_pieces.draw_future_parts = 1
        self.image_type = 'screen'
        base_pieces.generate_pdf = 0
        base_pieces.dim_scale = 1.0
        self.total.frame = 0
        self.window_color(None, save_color_scheme)
        self.draw_center = save_draw_center
        base_pieces.draw_outline = save_draw_outline
        self.toggle_frame(None, 0, 0)

    def set_detail(self, widget, detail):
        """
        Sets the detail between solid or rendered
        """
        global max_detail

        if detail > max_detail:
            detail = max_detail

        pieces.detail = detail
        
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def solid(self, widget = None):
        """
        Chooses solid detail
        """
        self.set_detail(None, 1)

    def render(self, widget = None):
        """
        Chooses render detail
        """
        self.set_detail(None, 2)

    def set_fixed_region(self, widget = None):
        """
        Sets the selected region as the fixed region for posing
        """
        if self.total.frame < self.total.instruction_start and len(self.total.selected) > 0:
            self.total.set_region_fixed(self.total.selected[0])
            region_index = self.total.selected[0]
            region_index = (region_index + 1) % len(self.total.regions)
            if region_index == self.total.region_fixed:
                region_index = (region_index + 1) % len(self.total.regions)
            self.total.selected = [region_index]
            self.redisplay = 'redraw'
            self.glarea.queue_draw()

    def hold_pose(self, widget = None, value = 0):
        """
        Holds the current pose through all instruction steps
        """
        if widget:
            value = int(widget.get_active())
            self.total.hold_pose = value
            if len(self.total.instructions) > 0:
                self.total.restore_centers()
                if value:
                    self.total.instructions[0]['hold_pose'] = 1
                    self.total.hold_pose_matrices()
                    self.total.pose_centers()
                elif self.total.instructions[0].has_key('hold_pose'):
                    del self.total.instructions[0]['hold_pose']
            self.redisplay = 'redraw'
            self.glarea.queue_draw()

    def hide_selected(self, widget = None):
        """
        Hides the selected parts
        """
        if len(self.total.selected) > 0:
            self.total.hidden_parts = self.total.hidden_parts + self.total.selected
            self.hidden_bar.set_text(str(len(self.total.hidden_parts)))
            self.total.selected = []
            self.redisplay = 'redraw'
            self.glarea.queue_draw()

    def unhide(self, widget = None):
        """
        Unhides all hidden parts
        """
        self.total.hidden_parts = []
        self.hidden_bar.set_text('0')
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def toggle_port(self, widget = None, next = 1):
        """
        Toggles which port on the piece is attached to the module
        """
        self.part.nextport(next)
        self.redisplay = 'draw'
        self.glarea.queue_draw()

    def flip_port(self, widget = None, dir = 1):
        """
        Rotate the port 90 degrees
        """
        self.part.flipport(dir)
        self.redisplay = 'draw'
        self.glarea.queue_draw()

    def validate_part(self, name):
        """
        Find a valid piece to connect
        """
        if len(self.total.netlist) <= 0:
            if 'j' in eval('pieces.' + name + '.ends_types'):
                self.total.start_ends('j')
            else:
                self.total.start_ends('s')
        if len(self.total.ends) <= 0:
            self.status_bar.set_text('No more valid connections')
            self.part_add_pieces.set_active(False)
            return ''
        else:
            if hasattr(self, 'part_add_pieces'):
                self.part_add_pieces.set_active(True)
            ends_types = eval('pieces.' + name + '.ends_types')
            if 'j' not in ends_types:
                part_type = 's'
                self.last_stick = name
                alt_name = self.last_joint
                alt_type = 'j'
            elif 's' not in ends_types:
                part_type = 'j'
                self.last_joint = name
                alt_name = self.last_stick
                alt_type = 's'
            else:
                part_type = 'b'

            if (len(self.total.ends_types) == 0) or (part_type == 'j' and 's' in self.total.ends_types) or (part_type != 'j' and 'j' in self.total.ends_types) or (part_type == 'b'):
                pass
            else:
                name = alt_name
                part_type = alt_type

            self.current_piece = self.piece_list.index(name)
            self.part = eval('pieces.' + name + '()')
            self.part.name = name
            if part_type == 'b':
                total_end_type = self.total.ends_types[self.total.port]
                if total_end_type == 'j':
                    self.part.port = self.part.ends_types.index('s')
                else:
                    self.part.port = self.part.ends_types.index('j')
            port_type = self.part.ends_types[self.part.port]
            self.part.align(self.total.find_next_port(port_type))
            return name

    def connect_part(self, widget = None):
        """
        Connect the piece to the module
        """
        if len(self.total.ends) > 0 and self.part_add_pieces.get_active():
            bad_angle = self.total.connect(self.part, self.vout, self.vup)
            if not bad_angle:
                self.name = self.validate_part(self.piece_list[self.current_piece])
            self.redisplay = 'draw'
            self.glarea.queue_draw()
    
    def query_selection(self, widget = None):
        """
        Displays a dialog to set the query options of the selected part
        """

        if len(self.total.selected) == 1:
            part = self.total.netlist[self.total.selected[0]]
            if len(part.query_options) > 0:

                config_save = part.configure[:]

                def combo_changed(entry, entry_index, entries, dialog):
                    part.configure[entry_index] = entries[entry_index][1][entry.get_active()]
                    pos = dialog.get_position()
                    dialog.destroy()

                pos = None
                response = gtk.RESPONSE_APPLY
                while response != gtk.RESPONSE_OK and response != gtk.RESPONSE_CANCEL:
                    #print 'configure', part.configure
                    dialog = gtk.Dialog('Piece Query', self.win, 0, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
                    if pos:
                        dialog.move(pos[0], pos[1])
                    entries = []
                    dialog.vbox.pack_start(gtk.Label(part.name))
                    table = gtk.Table(2, len(part.query_options))
                    dialog.vbox.pack_start(table, False, False, 0)
                    for count, option in enumerate(part.query_options):
                        label = gtk.Label(option[0])
                        entry = gtk.combo_box_new_text()
                        entry_options = []
                        for entry_label in option[1]:
                            exclusive = 0
                            entry_options.append(entry_label)
                            if entry_label[0] == '^':
                                for config_index, config in enumerate(part.configure):
                                    if config_index != count and config == entry_label:
                                        exclusive = 1
                                        del entry_options[-1]
                                        break
                                entry_label = entry_label[1:]
                            if not exclusive:
                                entry.append_text(entry_label)
                        entry.set_active(entry_options.index(part.configure[count]))
                        entry.connect('changed', combo_changed, count, entries, dialog)
                        table.attach(label, 0, 1, count, count+1)
                        table.attach(entry, 1, 2, count, count+1)
                        entries.append((entry, entry_options))

                    dialog.show_all()
                    response = dialog.run()

                if response == gtk.RESPONSE_CANCEL:
                    part.configure = config_save

                dialog.destroy()
                self.redisplay = 'redraw'
                self.glarea.queue_draw()

    def border_select(self, widget = None):
        """
        Begin a selection of pieces in a box
        """
        self.mode = 'border_select'
        self.status_bar.set_text(self.mode)
        self.beginx = None

    def cancel(self):
        """
        Cancel a move, copy, rotate, or mirror
        """
        if self.mode == 'grab':
            self.total.move_selected(-self.delta)
        elif self.mode == 'duplicate':
            self.total.netlist = self.total.netlist[:self.dup_parts_index]
            self.total.selected = []
        elif self.mode == 'rotate':
            self.total.rotate_selected(-self.delta[0], self.delta[1], self.delta[2]) # Rotate Back
        elif self.mode == 'rotate_region':
            self.total.region_rotates[self.total.selected[0]] = self.delta
        elif self.mode == 'mirror':
            if self.delta[0] >= 0: # Mirror Back
                self.total.mirror_selected(self.delta[0], self.delta[2])
        self.mode = 'normal'
        self.redisplay = 'redraw'
        self.glarea.queue_draw()
        self.status_bar.set_text(self.mode)

    def select_all(self, widget = None):
        """
        Select all pieces or deselect all pieces
        """
        if len(self.total.selected) > 0:
            self.total.selected = []
        else:
            if self.creationmode == 'modelling':
                self.total.selected = range(len(self.total.netlist))
            elif self.creationmode == 'instructions': # Select remainder
                if self.total.frame >= self.total.instruction_start: # in frames
                    select_flag = np.ones(len(self.total.netlist), np.uint8)
                    select_flag[self.total.old_parts] = 0
                    select_flag[self.total.hidden_parts] = 0
                    self.total.selected = np.nonzero(select_flag)[0].tolist()
        self.redisplay = 'draw'
        self.glarea.queue_draw()

    def type_select(self, widget = None):
        """
        Select all pieces of the type specificed in the piece selector
        """
        model, iter = self.selection.get_selected()
        name = self.alias2name[model.get_value(iter, 1)]
        num_parts = 0
        for count, part in enumerate(self.total.netlist):
            if part.name == name:
                num_parts = num_parts + 1
                if count not in self.total.selected:
                    self.total.selected.append(count)
        msg = str(num_parts) + ' ' + self.name2alias[name]
        self.status_bar.set_text(msg)
        self.redisplay = 'draw'
        self.glarea.queue_draw()

    def delete_part(self, widget = None):
        """
        Remove the selected pieces
        """
        if len(self.total.selected) > 0:
            self.total.remove_parts()
            self.status_bar.set_text(str(len(self.total.selected)))
            self.part_add_pieces.set_active(True)
            self.name = self.validate_part(self.piece_list[self.current_piece])
            self.redisplay = 'redraw'
            self.glarea.queue_draw()

    def grab(self, widget = None):
        """
        Move the selected pieces
        """
        if len(self.total.selected) == 0:
            self.status_bar.set_text('No grab.  Nothing selected.')
        else:
            self.mode = 'grab'
            self.status_bar.set_text(self.mode)
            self.beginx, self.beginy = self.glarea.get_pointer()
            self.last_time = 0
            self.delta = np.array([0.0, 0.0, 0.0])

    def duplicate(self, widget = None):
        """
        Copy the selected pieces and move them
        """
        if len(self.total.selected) == 0:
            self.status_bar.set_text('No duplicate.  Nothing selected.')
        else:
            self.mode = 'duplicate'
            self.status_bar.set_text(self.mode)
            self.dup_parts_index = len(self.total.netlist)
            for index in self.total.selected:
                self.total.netlist.append(copy.deepcopy(self.total.netlist[index]))
            self.total.selected = range(self.dup_parts_index, self.dup_parts_index + len(self.total.selected))
            self.beginx, self.beginy = self.glarea.get_pointer()
            self.last_time = 0
            self.delta = np.array([0.0, 0.0, 0.0])

    def find_center_port(self, x, y, about):
        """
        Find the port nearest the passed x, y
        """
        # Set up line from pt_near to pt_far
        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        winy = viewport[3] - viewport[1] - y
        pt_near = np.array(gluUnProject(x, winy, 0.0, model, projection, viewport))
        pt_far = np.array(gluUnProject(x, winy, 1.0, model, projection, viewport))            
        nearest_part_index = np.argmin(self.distance3d(np.array(map(lambda x: x.center, self.total.netlist)), pt_near, pt_far))
        nearest_part = self.total.netlist[nearest_part_index]

        nearest_end_index = np.argmin(self.distance3d(np.array(map(lambda x: x[0], nearest_part.ends)), pt_near, pt_far))

        # Derive center_port from nearest end
        center_end = nearest_part.ends[nearest_end_index]
        center_end_type = nearest_part.ends_types[nearest_end_index]
        center_end_dir = center_end[0] - center_end[1]
        if center_end_type == 'j':
            dir = 1
        else:
            dir = -1
        center_port = center_end[0] - dir*pieces.join_len*center_end_dir
        return center_port

    def rotate(self, widget = None):
        """
        Rotate the selected pieces
        """
        if len(self.total.selected) == 0:
            self.status_bar.set_text('No rotate.  Nothing selected.')
        else:
            if self.creationmode == 'instructions':
                if self.total.frame < self.total.instruction_start:
                    self.mode = 'rotate_region'
                    self.status_bar.set_text('rotate region')
                    self.beginx, self.beginy = self.glarea.get_pointer() # more correct than self.win.get_pointer()
                    self.last_time = 0
                    self.delta = self.total.region_rotates[self.total.selected[0]] # stores old angle
            else: # Modelling
                self.mode = 'rotate'
                self.status_bar.set_text(self.mode)
                self.beginx, self.beginy = self.glarea.get_pointer() # more correct than self.win.get_pointer()
                self.last_time = 0
                # Create about vector
                about = np.array([0.0, 0.0, 0.0])
                max_dim = np.argmax(np.abs(self.vout))
                if self.vout[max_dim] < 0.0:
                    about[max_dim] = -1.0
                else:
                    about[max_dim] = 1.0
                self.delta = [0, about, self.find_center_port(self.beginx, self.beginy, about)]

    def mirror(self, widget = None):
        """
        Mirror the selected pieces
        """
        if len(self.total.selected) == 0:
            print 'No mirror.  Nothing selected.'
        else:
            self.mode = 'mirror'
            self.status_bar.set_text(self.mode)
            self.beginx, self.beginy = self.glarea.get_pointer() # more correct than self.win.get_pointer()
            self.last_time = 0
            # Create about vector
            about = np.array([0.0, 0.0, 0.0])
            max_dim = np.argmax(np.abs(self.vout))
            if self.vout[max_dim] < 0.0:
                about[max_dim] = -1.0
            else:
                about[max_dim] = 1.0
            self.delta = [-1, np.array(gluUnProject(self.beginx, self.SCR[1]-self.beginy, 0.0)), self.find_center_port(self.beginx, self.beginy, about)]

    def undo(self, widget = None):
        """
        Undo the last module change
        """
        self.status_bar.set_text('Undo')
        self.total.history_undo()
        self.name = self.validate_part(self.piece_list[self.current_piece])

        self.redisplay = 'redraw'
        self.glarea.queue_draw()
    
    def redo(self, widget = None):
        """
        Redo the last module change
        """
        self.status_bar.set_text('Redo')
        self.total.history_redo()
        self.name = self.validate_part(self.piece_list[self.current_piece])

        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def fix_model(self, widget = None):
        """
        Fix broken parts of the module
        """
        self.total.fix()

    def clear_all(self, widget = None):
        """
        Clear the module and start over
        """
        #self.set_mode(None, 'modelling')
        self.vcenter = self.start_vcenter
        self.vout = self.start_vout
        self.vup = self.start_vup
        #self.pixperunit = self.start_pixperunit
        self.set_pixperunit(self.start_pixperunit)
        self.total = base_pieces.module()
        self.name = self.validate_part(self.piece_list[self.current_piece])
        self.current_filename = ''
        self.update_title()
        self.mode_modelling.set_active(True)
        self.instructions_hold_pose.set_active(False)
        self.opengl_reshape(self.glarea, None)

    def screen_capture(self):
        """
        Capture the screen for image storage
        """
        #while gtk.events_pending(): # didn't help on graphics acceleration redraw
        #    gtk.main_iteration()
        rawdata = self.total.screen_capture()
        xlen, ylen = rawdata.shape
        im = Image.fromstring('RGBA', (xlen, ylen), rawdata.tostring(), 'raw', 'RGBA', 0, -1)
        return im

    def write_file(self, widget = None, saveas = True):
        """
        Write the module to a file
        """
        if self.creationmode == 'instructions':
            self.toggle_frame(None, 0, 1) # Save current
        if self.current_filename == '':
            saveas = True
        dialog = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        if saveas:
            dialog.set_current_folder(self.project_directory)
            dialog.set_current_name(self.current_filename)

            filter = gtk.FileFilter()
            filter.set_name('Crossbeams Model')
            filter.add_pattern('*.cbm')
            dialog.add_filter(filter)

            response = dialog.run()
        else:
            response = gtk.RESPONSE_OK

        if response == gtk.RESPONSE_OK:
            if saveas:
                self.current_filename = dialog.get_filename()
                self.project_directory = dialog.get_current_folder()
                dialog.destroy()
            base, ext = os.path.splitext(self.current_filename)
            if (ext != '.jst') or (ext != '.cbm'):
                ext = '.cbm'
            self.current_filename = base + ext
            self.update_title()
            fp = None
            try:
                fp = open(self.current_filename, 'w')
            except IOError:
                self.status_bar.set_text('Warning: Can\'t write ' + self.current_filename)
            if fp:
                fp.write(self.total.write_netlist())
                fp.close()
                self.status_bar.set_text('Write complete.  ' + str(self.total.total_inventory()) + ' pieces.')

        else:
            dialog.destroy()

    def write_png(self, widget = None):
        """
        Write the screen capture to a file
        """
        dialog = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        base, ext = os.path.splitext(self.current_filename)
        filename = base + '.png'
        dialog.set_current_folder(self.project_directory)
        dialog.set_current_name(filename)
        filter = gtk.FileFilter()
        filter.set_name('png')
        filter.add_pattern('*.png')
        dialog.add_filter(filter)
        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            base, ext = os.path.splitext(dialog.get_filename())
            dialog.destroy()
            filename = base + '.png'
            self.image_type = 'print'
            self.omit_logo = 1
            base_pieces.generate_pdf = 1
            base_pieces.dim_scale = self.ps_scale
            save_size = self.SCR[:]
            self.window_size(None, None)
            im = self.screen_capture()
            im.save(filename)
            base_pieces.dim_scale = 1.0
            base_pieces.generate_pdf = 0
            self.omit_logo = 0
            self.image_type = 'screen'
            self.window_size(None, save_size)
            self.status_bar.set_text('Wrote ' + filename)
        else:
            dialog.destroy()
            self.status_bar.set_text('Not Saving (filename not set)')

    def write_csv(self, widget = None):
        """
        Write the inventory to a file
        """
        if self.current_filename:
            base, ext = os.path.splitext(self.current_filename)
            filename = base + '.csv'
            labels = self.alias_inventory()
            fp = None
            try:
                fp = open(base + '.csv', 'w')
            except IOError:
                self.status_bar.set_text('Warning: Can\'t write ' + base + '.csv')
            if fp:
                for label in labels:
                    fp.write(label[0] + ',' + str(label[1]) + '\n')
                fp.close()
                if widget:
                    self.status_bar.set_text('Wrote ' + filename)
        else:
            self.status_bar.set_text('Not Saving (filename not set)')

    def merge_file(self, widget = None):
        """
        Merge the module with another module from file
        """
        if self.image_type == 'print' and self.rendering == 'indirect':
            glcontext = self.print_glarea[0]
            gldrawable = self.print_glarea[1]
        else:
            glcontext = gtk.gtkgl.widget_get_gl_context(self.glarea)
            gldrawable = gtk.gtkgl.widget_get_gl_drawable(self.glarea)
        if not gldrawable.gl_begin(glcontext): return

        if len(self.total.netlist) == 0: # Nothing to merge with
            self.read_file(widget)
        
        else:
            dialog = gtk.FileChooserDialog(title='Import',action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
            dialog.set_current_folder(self.project_directory)

            filter = gtk.FileFilter()
            filter.set_name('Crossbeams Model')
            filter.add_pattern('*.cbm')
            dialog.add_filter(filter)

            filter = gtk.FileFilter()
            filter.set_name('all_files')
            filter.set_name('*')
            dialog.add_filter(filter)

            response = dialog.run()

            if response == gtk.RESPONSE_OK:
                name = dialog.get_filename()
                dir = dialog.get_current_folder()
                dialog.destroy()
                fp = None
                try:
                    fp = open(name, 'r')
                except IOError:
                    self.status_bar.set_text('Warning: Can\'t read ' + name)

                if fp:
                    self.total.selected = []
                    select_start = len(self.total.netlist)
                    module_add = base_pieces.module()
                    module_add.read_netlist(fp.readlines())
                    fp.close()
                    self.total.netlist = self.total.netlist + module_add.netlist
                    self.total.ends = self.total.ends + module_add.ends
                    self.total.ends_types = self.total.ends_types + module_add.ends_types
                    self.total.merge_common()

                    self.total.selected = range(select_start, select_start+len(module_add.netlist))

            else:
                dialog.destroy()

        gldrawable.gl_end()

    def read_file(self, widget = None):
        """
        Read a new module from file
        """

        dialog = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))

        dialog.set_current_folder(self.project_directory)

        filter = gtk.FileFilter()
        filter.set_name('Crossbeams Model')
        filter.add_pattern('*.cbm')
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name('all_files')
        filter.set_name('*')
        dialog.add_filter(filter)

        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            name = dialog.get_filename()
            dir = dialog.get_current_folder()
            dialog.destroy()
            fp = None
            try:
                fp = open(name, 'r')
            except IOError:
                self.status_bar.set_text('Warning: Can\'t read ' + name)

            if fp:
                self.reshape_called = 0
                self.draw_called = 0
                self.clear_all(None)
                while not self.reshape_called or not self.draw_called:
                    gtk.main_iteration()
                self.current_filename = name
                self.project_directory = dir
                self.update_title()
                self.total.read_netlist(fp.readlines())
                fp.close()
                if len(self.total.ends) > 0:
                    self.name = self.validate_part(self.piece_list[self.current_piece])
                self.status_bar.set_text('Read complete.  ' + str(self.total.total_inventory()) + ' pieces.')
                self.glarea.queue_draw()

        else:
            dialog.destroy()

    def redraw_screen(self, widget = None):
        """
        Redraw the screen
        """
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def viewstandard(self, widget = None, viewtype = 'front'):
        """
        View a standard view
        """
        views = {'front': (np.array([0.0, 0.0, 1.0]), np.array([0.0, 1.0, 0.0])),
                 'top': (np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, -1.0])),
                 'right': (np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])),
                 'left': (np.array([-1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])),
                 'bottom': (np.array([0.0, -1.0, 0.0]), np.array([0.0, 0.0, 1.0])),
                 'back': (np.array([0.0, 0.0, -1.0]), np.array([0.0, 1.0, 0.0])),
                 'iso': (np.array([1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)]), np.array([0.0, 1.0, 0.0])),
                 'iso_back': (np.array([-1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)]), np.array([0.0, 1.0, 0.0]))}
        if viewtype not in views.keys():
            print 'Unknown view', viewtype
        else:
            self.vout = views[viewtype][0]
            self.vup = views[viewtype][1]
            self.redisplay = 'redraw'
            self.glarea.queue_draw()

    def orbitup(self, widget = None):
        """
        Orbit the viewer up
        """
        cos_rot = math.cos(self.morbit)
        sin_rot = math.sin(self.morbit)
        vright = vector_math.cross(self.vup, self.vout)
        self.vout = vector_math.normalize(cos_rot * self.vout + sin_rot * self.vup)
        self.vup = vector_math.normalize(vector_math.cross(self.vout, vright))
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def panup(self, widget = None, rapid = 0):
        """
        Pan the viewer up
        """
        self.vcenter = self.vcenter + self.mpan / self.pixperunit * self.vup * (1.0 + 4.0 * rapid)
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def orbitdown(self, widget = None):
        """
        Orbit the viewer down
        """
        cos_rot = math.cos(self.morbit)
        sin_rot = math.sin(self.morbit)
        vright = vector_math.cross(self.vup, self.vout)
        self.vout = vector_math.normalize(cos_rot * self.vout - sin_rot * self.vup)
        self.vup = vector_math.normalize(vector_math.cross(self.vout, vright))
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def pandown(self, widget = None, rapid = 0):
        """
        Pan the viewer down
        """
        self.vcenter = self.vcenter - self.mpan / self.pixperunit * self.vup * (1.0 + 4.0 * rapid)
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def orbitright(self, widget = None):
        """
        Orbit the viewer right
        """
        cos_rot = math.cos(self.morbit)
        sin_rot = math.sin(self.morbit)
        vright = vector_math.cross(self.vup, self.vout)
        self.vout = vector_math.normalize(cos_rot * self.vout + sin_rot * vright)
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def panright(self, widget = None, rapid = 0):
        """
        Pan the viewer right
        """
        vright = vector_math.cross(self.vup, self.vout)
        self.vcenter = self.vcenter + self.mpan / self.pixperunit * vright * (1.0 + 4.0 * rapid)
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def orbitleft(self, widget = None):
        """
        Orbit the viewer left
        """
        cos_rot = math.cos(self.morbit)
        sin_rot = math.sin(self.morbit)
        vright = vector_math.cross(self.vup, self.vout)
        self.vout = vector_math.normalize(cos_rot * self.vout - sin_rot * vright)
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def panleft(self, widget = None, rapid = 0):
        """
        Pan the viewer left
        """
        vright = vector_math.cross(self.vup, self.vout)
        self.vcenter = self.vcenter - self.mpan / self.pixperunit * vright * (1.0 + 4.0 * rapid)
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def zoomin(self, widget = None):
        """
        Zoom in
        """
        size = 1.0
        if type(widget) == type(0.0):
            size = widget
        #self.pixperunit = self.pixperunit * (2.0**(0.5*size))
        self.set_pixperunit(self.pixperunit * (2.0**(0.5*size)))
        self.opengl_reshape(self.glarea, None)

    def zoomout(self, widget = None):
        """
        Zoom out
        """
        size = 1.0
        if type(widget) == type(0.0):
            size = widget
        #self.pixperunit = self.pixperunit / (2.0**(0.5*size))
        self.set_pixperunit(self.pixperunit / (2.0**(0.5*size)))
        self.opengl_reshape(self.glarea, None)

    def rotateccw(self, widget = None):
        """
        Rotate the viewer counter-clockwise
        """
        cos_rot = math.cos(self.morbit)
        sin_rot = math.sin(self.morbit)
        vright = vector_math.cross(self.vup, self.vout)
        self.vup = vector_math.normalize(cos_rot * self.vup - sin_rot * vright)
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def rotatecw(self, widget = None):
        """
        Rotate the viewer clockwise
        """
        cos_rot = math.cos(self.morbit)
        sin_rot = math.sin(self.morbit)
        vright = vector_math.cross(self.vup, self.vout)
        self.vup = vector_math.normalize(cos_rot * self.vup + sin_rot * vright)
        self.redisplay = 'redraw'
        self.glarea.queue_draw()

    def config_name(self):
        """
        Returns the name of the configuration file for various platforms
        """
        retval = ''
        if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            if os.environ.has_key('HOME'):
                retval = os.path.join(os.environ['HOME'], '.cbmodelrc')

        elif sys.platform.startswith('win'):
            if os.environ.has_key('USERPROFILE'):
                retval = os.path.join(os.environ['USERPROFILE'], 'AppData', 'cbmodel.ini')
            else:
                print 'Define USERPROFILE environment variable for cbmodel.ini'
        else:
            print 'Warning: Unknown platform', sys.platform

        if retval:
            path = os.path.dirname(retval)
            if not os.path.exists(path):
                try:
                    os.mkdir(path)
                except:
                    print 'Warning: Couldn\'t create', path
                    retval = ''

        return retval
    
    def quit(self, widget = None):
        """
        Saves any state variables then quits the program
        """

        # Save any state variables
        state_saves = ['project_directory'] # list of state variables
        config_name = self.config_name()
        if config_name:
            config = ConfigParser.RawConfigParser()
            config.read(config_name)
            if not config.has_section('State'):
                config.add_section('State')
            for state_save in state_saves:
                value = eval('self.' + state_save)
                config.set('State', state_save, str(value))
            fp = None
            try:
                fp = open(config_name, 'wb')
            except IOError:
                print 'Warning: Can\'t write', config_name
            if fp:
                config.write(fp)
                fp.close()

        # quit
        gtk.main_quit()

    def distance3d(self, pts, pt_near, pt_far):
        """
        Calculates the minimum distance from pt in pts to the line
        from pt_near to pt_far.
        """

        return vector_math.mag(np.cross(pt_near - pt_far, pts - pt_near))

    def opengl_keypress(self, widget, event):
        """
        Responds to a keypress
        """
        key = gtk.accelerator_name(event.keyval, event.state & gtk.gdk.MODIFIER_MASK)
        if self.mode != 'normal': # Any key cancels, currently
            if key == '0' and self.mode == 'rotate_region':
                self.delta = 0.0
            self.cancel()
        if self.print_keys:
            #print key
            self.status_bar.set_text('Key: ' + key)
        if key in self.key_table.values():
            try:
                cmd = self.key_table.keys()[self.key_table.values().index(key)]
                eval('self.' + cmd)
            except:
                pass

    def opengl_mousepress(self, widget, event):
        """
        Responds to a mousepress
        """

        x = event.x
        y = event.y
        if self.mode == 'border_select': # Works with all mouse buttons?
            #print 'Begin Drag'
            self.beginx = x
            self.beginy = y
            self.endx = x
            self.endy = y
            self.last_time = event.time
        elif self.mode == 'grab':
            #print 'End Grab'
            if event.button == 1 and vector_math.mag(self.delta) > 0.1:
                time1 = time.time()
                self.total.write_move()
                time2 = time.time()
                self.name = self.validate_part(self.piece_list[self.current_piece])
                self.mode = 'grab complete %.1fs' % (time2-time1)
                self.status_bar.set_text(self.mode)
                self.redisplay = 'redraw'
                self.glarea.queue_draw()
                self.mode = 'normal'
            else:
                self.cancel()

        elif self.mode == 'duplicate':
            #print 'End Duplicate'
            if event.button == 1 and vector_math.mag(self.delta) > 0.1:
                dup_parts = self.total.netlist[self.dup_parts_index:]
                self.total.netlist = self.total.netlist[:self.dup_parts_index]
                for dup_part in dup_parts:
                    dup_part.calc_ends()
                    self.total.connect(dup_part, self.vout, self.vup, capture = 0)
                self.name = self.validate_part(self.piece_list[self.current_piece])
                self.mode = 'duplicate complete'
                self.status_bar.set_text(self.mode)
                self.redisplay = 'redraw'
                self.glarea.queue_draw()
                self.mode = 'normal'
            else:
                self.cancel()

        elif self.mode == 'rotate':
            #print 'End Rotate'
            if event.button == 1 and self.delta != 0:
                time1 = time.time()
                self.total.write_move()
                time2 = time.time()
                self.name = self.validate_part(self.piece_list[self.current_piece])
                self.mode = 'rotate done %.1fs' % (time2-time1)
                self.status_bar.set_text(self.mode)
                self.redisplay = 'redraw'
                self.glarea.queue_draw()
                self.mode = 'normal'
            else:
                self.cancel()

        elif self.mode == 'rotate_region':
            if event.button == 1:
                self.mode = 'normal'
                self.redisplay = 'redraw'
                self.glarea.queue_draw()
            else:
                self.cancel()

        elif self.mode == 'mirror':
            #print 'End Mirror'
            if event.button == 1 and self.delta[0] >= 0:
                time1 = time.time()
                self.total.write_move()
                time2 = time.time()
                self.name = self.validate_part(self.piece_list[self.current_piece])
                self.mode = 'mirror complete %.1fs' % (time2 - time1)
                self.status_bar.set_text(self.mode)
                self.redisplay = 'redraw'
                self.glarea.queue_draw()
                self.mode = 'normal'
            else:
                self.cancel()

        else:
            model = glGetDoublev(GL_MODELVIEW_MATRIX)
            projection = glGetDoublev(GL_PROJECTION_MATRIX)
            viewport = glGetIntegerv(GL_VIEWPORT)
            winy = viewport[3] - viewport[1] - y

            pt_near = np.array(gluUnProject(x, winy, 0.0, model, projection, viewport))
            pt_far = np.array(gluUnProject(x, winy, 1.0, model, projection, viewport))

            if event.button == 1 and not (event.state & gtk.gdk.CONTROL_MASK): # Left or Primary Button
                if self.creationmode == 'modelling':
                    if len(self.total.ends) > 0:
                        nearest_end_index = np.argmin(self.distance3d(np.array(map(lambda x: x[0], self.total.ends)), pt_near, pt_far))
                        self.total.port = nearest_end_index
                        msg = 'port at (' + reduce(lambda y, z: y + ', ' + z, map(lambda x: '%.1f' % x, (self.total.ends[self.total.port][0]/pieces.sf).tolist())) + ')'
                        self.status_bar.set_text(msg)
                        #print msg
                        if len(self.total.ends_types) > 0:
                            if self.total.ends_types[self.total.port] == 'j':
                                other_port = 's'
                                alt_name = self.last_stick
                            else:
                                other_port = 'j'
                                alt_name = self.last_joint
                            if other_port not in self.part.ends_types:
                                self.current_piece = self.piece_list.index(alt_name)
                                self.part = eval('pieces.' + alt_name + '()')
                                self.part.name = alt_name
                                self.name = alt_name
                            self.part.port = self.part.ends_types.index(other_port)
                        else:
                            self.part.port = 0
                        self.part.align(self.total.ends[self.total.port])

                    self.redisplay = 'draw'
                    self.glarea.queue_draw()
                    
                elif self.creationmode == 'instructions':
                    dmirror = 200.0
                    dmagnify = 200.0
                    max_dist = 100.0
                    if len(self.mirror_pos) > 0:
                        dmirror = math.sqrt((x-self.mirror_pos[0])**2 + (winy-self.mirror_pos[1])**2)
                    if len(self.magnify_pos) > 0:
                        dmagnify = math.sqrt((x-self.magnify_pos[0])**2 + (winy-self.magnify_pos[1])**2)
                    if dmirror < dmagnify and dmirror < max_dist:
                        self.mode = 'mirror_drag'
                        self.beginx = int(x)-self.mirror_pos[0]
                        self.beginy = int(winy)-self.mirror_pos[1]
                        self.status_bar.set_text(self.mode)
                    elif dmagnify < max_dist:
                        self.mode = 'magnify_drag'
                        self.beginx = int(x)-self.magnify_pos[0]
                        self.beginy = int(winy)-self.magnify_pos[1]
                        self.status_bar.set_text(self.mode)

            elif event.button == 2 or (event.button == 1 and (event.state & gtk.gdk.CONTROL_MASK)): # Middle or Tertiary Button
                self.beginx = x
                self.beginy = y
                self.last_time = event.time

            elif event.button == 3: # Right or Secondary Button
                if event.state & gtk.gdk.SHIFT_MASK:
                    multiple = 1
                else:
                    multiple = 0

                creation_selection_allowed = 0
                if self.creationmode == 'instructions':
                    unselectable = self.total.old_parts + self.total.hidden_parts
                    creation_selection_allowed = (self.total.frame >= self.total.instruction_start) and (self.total.submodel != -1) and (len(self.total.netlist) > len(unselectable))

                if (len(self.total.netlist) > 0) and (self.creationmode == 'modelling' or creation_selection_allowed):
                    nearest_part_indices = np.argsort(self.distance3d(np.array(map(lambda x: x.center, self.total.netlist)), pt_near, pt_far))
                    count = 0
                    if self.creationmode == 'instructions':
                        while nearest_part_indices[count] in unselectable:
                            count = count + 1
                    netlist_index = nearest_part_indices[count]
                    if multiple == 0:
                        self.total.selected = [netlist_index]
                    else:
                        if netlist_index in self.total.selected:
                            self.total.selected.remove(netlist_index)
                        else:
                            self.total.selected.append(netlist_index)
                    msg = self.name2alias[self.total.netlist[netlist_index].name] + ' part ' + repr(netlist_index)
                    self.status_bar.set_text(msg)
                    self.redisplay = 'draw'
                    self.glarea.queue_draw()

                elif self.creationmode == 'instructions' and self.total.frame < self.total.instruction_start and len(self.total.regions) > 1:
                    moving_region = np.argsort(self.distance3d(self.total.region_centers, pt_near, pt_far))
                    if moving_region[0] == self.total.region_fixed:
                        moving_region = moving_region[1]
                    else:
                        moving_region = moving_region[0]
                    if len(self.total.selected) > 0 and moving_region == self.total.selected[0]:
                        pass # Don't do anything if it's already selected
                    else:
                        self.total.selected = [moving_region]
                        msg = 'region ' + str(moving_region)
                        self.status_bar.set_text(msg)
                        self.redisplay = 'redraw'
                        self.glarea.queue_draw()

    def opengl_mouserelease(self, widget, event):
        """
        Responds to a mouserelease
        """

        if self.mode == 'border_select':
            #print 'End Drag'
            x = event.x
            y = event.y
            model = glGetDoublev(GL_MODELVIEW_MATRIX)
            projection = glGetDoublev(GL_PROJECTION_MATRIX)
            viewport = glGetIntegerv(GL_VIEWPORT)
            winy = viewport[3] - viewport[1] - y
            winbeginy = viewport[3] - viewport[1] - self.beginy

            start_selection = self.total.selected[:]
            for count, piece_index in enumerate(self.total.netlist):
                px, py, pz = gluProject(piece_index.center[0], piece_index.center[1], piece_index.center[2], model, projection, viewport)
                if self.beginx <= px <= x and winy <= py <= winbeginy:
                    if count not in start_selection:
                        unselectable = self.total.old_parts + self.total.hidden_parts
                        if (self.creationmode == 'modelling') or (count not in unselectable):
                            self.total.selected.append(count)

            self.mode = 'normal'
            self.status_bar.set_text(self.mode)
            self.redisplay = 'draw'
            self.glarea.queue_draw()

        elif self.mode == 'mirror_drag':
            self.mode = 'normal'
            self.status_bar.set_text(self.mode)

        elif self.mode == 'magnify_drag':
            # Make it snap to the nearest part
            x = event.x
            y = event.y
            model = glGetDoublev(GL_MODELVIEW_MATRIX)
            projection = glGetDoublev(GL_PROJECTION_MATRIX)
            viewport = glGetIntegerv(GL_VIEWPORT)
            winy = viewport[3] - viewport[1] - y

            pt_near = np.array(gluUnProject(x, winy, 0.0, model, projection, viewport))
            pt_far = np.array(gluUnProject(x, winy, 1.0, model, projection, viewport))
            nearest_part_index = np.argmin(self.distance3d(np.array(map(lambda x: x.center, self.total.netlist)), pt_near, pt_far))
            self.magnify_pos = [nearest_part_index] # Stays as len 1 until draw
            #center = self.total.netlist[nearest_part_index].center
            #snap_pos = gluProject(center[0], center[1], center[2], model, projection, viewport)
            #xsize, ysize = self.images['magnify']['im_screen'].size
            #self.magnify_pos = (int(snap_pos[0] - xsize/2), int(snap_pos[1] - ysize/2))
            self.mode = 'normal'
            self.status_bar.set_text(self.mode)
            self.redisplay = 'draw'
            self.glarea.queue_draw()

    def opengl_mousemotion(self, widget, event):
        """
        Responds to mouse motion while a mouse button is pressed
        """
        UPDATE_PERIOD = 100 # Number of milliseconds between each mousemotion
        if abs(event.time - self.last_time) > UPDATE_PERIOD:
            if (event.state & gtk.gdk.BUTTON2_MASK) or ((event.state & gtk.gdk.BUTTON1_MASK) and (event.state & gtk.gdk.CONTROL_MASK)):
                x = event.x
                y = event.y
                vright = vector_math.cross(self.vup, self.vout)

                if event.state & gtk.gdk.SHIFT_MASK: # Pan
                    self.vcenter = self.vcenter - vright * ((x - self.beginx) / self.pixperunit) + self.vup * ((y - self.beginy) / self.pixperunit)
                else: # Orbit
                    ax = (x - self.beginx) / self.SCR[0] * 2 * math.pi
                    cos_rot = math.cos(ax)
                    sin_rot = math.sin(ax)
                    self.vout = vector_math.normalize(cos_rot*self.vout - sin_rot*vright)
                    vright = vector_math.cross(self.vup, self.vout)
                    ay = -(y - self.beginy) / self.SCR[1] * 2 * math.pi
                    cos_rot = math.cos(ay)
                    sin_rot = math.sin(ay)
                    self.vout = vector_math.normalize(cos_rot*self.vout - sin_rot*self.vup)
                    self.vup = vector_math.normalize(vector_math.cross(self.vout, vright))
                self.beginx = x
                self.beginy = y
                self.last_time = event.time
                self.redisplay = 'redraw'
                self.glarea.queue_draw()

            elif self.mode == 'border_select':
                self.endx = event.x
                self.endy = event.y
                self.last_time = event.time
                self.redisplay = 'draw'
                self.glarea.queue_draw()

            elif self.mode == 'grab' or self.mode == 'duplicate':
                numx = (event.x - self.beginx) / (0.5*pieces.lenp5*self.pixperunit) # possible with new scales
                numy = (event.y - self.beginy) / (0.5*pieces.lenp5*self.pixperunit) # possible with new scales
                vright = vector_math.cross(self.vup, self.vout)
                newd = np.around(numx*vright - numy*self.vup)
                if vector_math.mag(newd - self.delta) > 0.1:
                    #print 'newd', newd
                    self.total.move_selected(newd - self.delta)
                    self.delta = newd
                    self.last_time = event.time
                    self.redisplay = 'redraw'
                    self.glarea.queue_draw()

            elif self.mode == 'rotate':
                dx = event.x - self.beginx
                dy = self.beginy - event.y
                if abs(dy) >= abs(dx): # y
                    if dy * np.sum(self.delta[1]) >= 0.0:
                        angle = 90
                    else:
                        angle = 270
                    self.endx = self.beginx
                    self.endy = event.y
                else: # x
                    if dx >= 0.0:
                        angle = 0
                    else:
                        angle = 180
                    self.endx = event.x
                    self.endy = self.beginy
                if angle != self.delta[0]:
                    self.total.rotate_selected(angle - self.delta[0], self.delta[1], self.delta[2])
                    self.delta[0] = angle
                    self.last_time = event.time
                    self.redisplay = 'redraw'
                    self.glarea.queue_draw()

            elif self.mode == 'rotate_region':
                dx = event.x - self.beginx
                dy = self.beginy - event.y
                self.endx = event.x
                self.endy = event.y
                if dx == 0.0 and dy == 0.0:
                    return
                angle = int(round(math.degrees(vector_math.angle_normal(vector_math.normalize(np.array((dx, dy)))))))
                if angle != self.total.region_rotates[self.total.selected[0]]:
                    self.total.region_rotates[self.total.selected[0]] = angle
                    self.last_time = event.time
                    self.redisplay = 'redraw'
                    self.glarea.queue_draw()

            elif self.mode == 'mirror':
                dp = np.abs(np.array(gluUnProject(event.x, self.SCR[1]-event.y, 0.0)) - self.delta[1])
                max_dim = np.argmax(dp)
                if (dp[max_dim]*self.pixperunit <= 5):
                    if self.delta[0] >= 0: # Mirror Back
                        self.total.mirror_selected(self.delta[0], self.delta[2])
                        self.last_time = event.time
                        self.redisplay = 'redraw'
                        self.glarea.queue_draw()
                    self.delta[0] = -1
                elif max_dim != self.delta[0]:
                    if self.delta[0] >= 0: # Mirror Back
                        self.total.mirror_selected(self.delta[0], self.delta[2])
                    self.total.mirror_selected(max_dim, self.delta[2])
                    self.delta[0] = max_dim
                    self.last_time = event.time
                    self.redisplay = 'redraw'
                    self.glarea.queue_draw()

            elif self.mode == 'mirror_drag':
                viewport = glGetIntegerv(GL_VIEWPORT)
                winy = viewport[3] - viewport[1] - int(event.y)
                self.mirror_pos = (int(event.x) - self.beginx, winy - self.beginy)
                self.last_time = event.time
                self.redisplay = 'draw'
                self.glarea.queue_draw()

            elif self.mode == 'magnify_drag':
                viewport = glGetIntegerv(GL_VIEWPORT)
                winy = viewport[3] - viewport[1] - int(event.y)
                self.magnify_pos = (int(event.x) - self.beginx, winy - self.beginy)
                self.last_time = event.time
                self.redisplay = 'draw'
                self.glarea.queue_draw()

    def menu_piece_select(self, selection):
        """
        Respond to a new piece selection in the piece selector
        """
        model, iter = selection.get_selected()
        name = model.get_value(iter, 1)
        name = self.alias2name[name]
        part_index = self.piece_list.index(name)

        if len(self.total.ends) > 0:
            self.name = self.validate_part(name)
            self.current_piece = part_index

        self.redisplay = 'draw'
        self.glarea.queue_draw()

if __name__ == '__main__':
    # Parse the input parameters (so simple don't need optparse yet)
    if '-p' in sys.argv or '--printkeys' in sys.argv:
        print_keys = 1
    else:
        print_keys = 0
    if '-i' in sys.argv or '--indirect' in sys.argv:
        rendering = 'indirect'
    else:
        rendering = 'direct'
    if '-a' in sys.argv or '--alpha' in sys.argv:
        use_numpad = 0
    else:
        use_numpad = 1
    if '-h' in sys.argv or '--help' in sys.argv:
        print """
Usage: cbmodel [OPTION]
  -a, --alpha        use alphanumerics instead of numpad for navigation
  -h, --help         this help screen
  -i, --indirect     force indirect (non-graphics-accelerated) rendering
  -p, --printkeys    print the gtk key code of key presses in the status bar
"""
    MainScreen(print_keys = print_keys, rendering = rendering, use_numpad = use_numpad)
    gtk.main()
