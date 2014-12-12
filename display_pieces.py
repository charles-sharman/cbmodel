#! /usr/bin/python

"""
Description
-----------
piece viewer for sticks_sim.  Mostly used to create the icon list.

Author
------
Charles Sharman

Revision History
----------------
version 0.1 changes to 8/20/11
- Many undocumented changes
- Added render option
- Added partial_pieces
version 0.2 changes to 5/4/12
- changed to gtk (very kluged still)
"""

import sys
import types
import time
import math

import pieces
import base_pieces
import vector_math
import instructions

from OpenGL.GL import *
from OpenGL.GLE import *
from OpenGL.GLU import *

# FPE with Rage 128 card, python-opengl and numnp.array
#from numnp.array import *
#from Numeric import *
import numpy as np

import Image

import pygtk, gtk, gtk.gtkgl, pango

image_scale = 900 # use a larger number for larger images
draw_called = 0
ppu = 7.0/pieces.sf

partial_pieces = ['coupler', 'gear1', 'gear3s', 'gear3l', 'gear_bevel', 'wheelp5', 'wheel1', 'stiffen']

class coupler(base_pieces.piece):
    def shape(self):
        pieces.draw_drawing('coupler')

class gear1(base_pieces.piece):
    icon_extent = 3.0
    def shape(self):
        pieces.draw_drawing('gear1')

#class gear2s(base_pieces.piece):
#    icon_extent = 2.5
#    def shape(self):
#        pieces.draw_drawing('gear2s')

#class gear2l(base_pieces.piece):
#    icon_extent = 4.0
#    def shape(self):
#        pieces.draw_drawing('gear2l')

class gear3s(base_pieces.piece):
    icon_extent = 2.5
    def shape(self):
        pieces.draw_drawing('gear3s')

class gear3l(base_pieces.piece):
    icon_extent = 4.0
    def shape(self):
        pieces.draw_drawing('gear3l')

class gear_bevel(base_pieces.piece):
    icon_extent = 3.0
    def shape(self):
        pieces.draw_drawing('gear_bevel')

#class gear_rack_spur(base_pieces.piece):
#    icon_extent = 3.0
#    def shape(self):
#        pieces.draw_drawing('gear_rack_spur')

class wheelp5(base_pieces.piece):
    icon_extent = 4.0
    def shape(self):
        pieces.draw_drawing('wheelp5')
        pieces.draw_drawing('tirep5', (0.35, 0.35, 0.35))

class wheel1(base_pieces.piece):
    icon_extent = 8.0
    def shape(self):
        pieces.draw_drawing('wheel1')
        pieces.draw_drawing('tire1', (0.35, 0.35, 0.35))

class stiffen(base_pieces.piece):
    icon_center = (0.0, -2.5*pieces.sf, -2.5*pieces.sf)
    icon_extent = 3.5
    def shape(self):
        pieces.draw_drawing('stiffen')

def screen_capture(background = 0):
    global piece_name
    print piece_name
    filename = screen_capture_path + piece_name + screen_capture_type
    #expose()
    x0, y0, width, height = glGetIntegerv(GL_VIEWPORT)
    glReadBuffer(GL_FRONT)
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    if background:
        data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        im = Image.fromstring('RGB', (width, height), data)
    else:
        data = glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        im = Image.fromstring('RGBA', (width, height), data)
    #print im.getbbox()
    #im = im.crop(im.getbbox()) # Shrink as much as possible # fast but no outline
    im = im.crop(instructions.bbox(im))
    #if scale != 1.0:
    #    xsize, ysize = im.size
    #    im = im.resize((xsize*scale, ysize*scale))

    # Shrink if too big
    limit = 100.0
    xsize, ysize = im.size
    max_extent = float(max(xsize, ysize))
    if max_extent > limit:
        scale = (limit + 0.5*(max_extent - limit)) / max_extent
        im = im.resize((scale*xsize, scale*ysize))
    im = instructions.outline(im, 4, (0, 0, 0))
    
    im.transpose(Image.FLIP_TOP_BOTTOM).save(filename)

def generate_icons(widget = None):
    global piece_name, piece_list, screen_capture_path, draw_called

    screen_capture_path = 'icons/'

    store_name = piece_name
    for count in range(len(piece_list)):
        #piece_name = piece_list[count]
        draw_called = 0
        new_part([count])
        while not draw_called:
            gtk.main_iteration()
        screen_capture(0)
    piece_name = store_name
    setview('iso')

def opengl_init(widget):
    global glarea, ppu

    glcontext = gtk.gtkgl.widget_get_gl_context(glarea)
    gldrawable = gtk.gtkgl.widget_get_gl_drawable(glarea)
    if not gldrawable.gl_begin(glcontext):
        return

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glViewport(0, 0, image_scale, image_scale)
    glOrtho(-14.0, 14.0, -14.0, 14.0, -1000.0, 1000.0) # The screen's limits
    base_pieces.depth_scale = 1.0/800.0 # determined by glOrtho
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glDrawBuffer(GL_FRONT)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)

    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.5, 0.5, 0.5, 1.0))
    glMaterialfv(GL_FRONT, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
    glMaterialfv(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
    glMaterialfv(GL_FRONT, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))
    glMaterialfv(GL_FRONT, GL_SHININESS, 0.0)

    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHTING)
    glColorMaterial(GL_FRONT, GL_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)

    gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)

    glClearColor(0.0, 0.0, 0.0, 0.0) # Must be black for Image.getbbox to work

    gldrawable.gl_end()

def opengl_expose(widget = None, event = None):
    global views, glarea, draw_called, to_draw

    glcontext = gtk.gtkgl.widget_get_gl_context(glarea)
    gldrawable = gtk.gtkgl.widget_get_gl_drawable(glarea)
    if not gldrawable.gl_begin(glcontext):
        return

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Determine the center
    if hasattr(part, 'icon_center'):
        vcenter = np.array(part.icon_center)
    else:
        vcenter = np.array([0.0, 0.0, 0.0])
        if len(part.unaligned_ends) > 0:
            for end in part.unaligned_ends:
                vcenter = vcenter + end[0]
            vcenter = vcenter/len(part.unaligned_ends)
    print 'vcenter', vcenter

    if hasattr(part, 'icon_view'):
        view = part.icon_view
    else:
        view = current_view
    print view

    glLoadIdentity()
    for rots in views[view][2]:
        glRotatef(rots[0], rots[1], rots[2], rots[3])
    glTranslatef(-vcenter[0], -vcenter[1], -vcenter[2])
    vout = views[view][0]
    vup = views[view][1]

    glColor3f(1.0, 1.0, 1.0)
    part.shape()
    if pieces.detail == 1:
        for end, end_type in zip(part.unaligned_ends, part.ends_types):
            pieces.draw_end(end, end_type)

    glFlush()
    gldrawable.gl_end()
    draw_called = 1

def expose(widget = None, event = None):
    global part, views, o, module, glarea, draw_called

    glcontext = gtk.gtkgl.widget_get_gl_context(glarea)
    gldrawable = gtk.gtkgl.widget_get_gl_drawable(glarea)
    if not gldrawable.gl_begin(glcontext):
        return

    ppu = 7.0/pieces.sf # pixels per unit
    #border = 2.5

    # Determine the center
    if hasattr(part, 'icon_center'):
        vcenter = np.array(part.icon_center)
    else:
        vcenter = np.array([0.0, 0.0, 0.0])
        if len(part.unaligned_ends) > 0:
            for end in part.unaligned_ends:
                vcenter = vcenter + end[0]
            vcenter = vcenter/len(part.unaligned_ends)
    print 'vcenter', vcenter

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    #size = int(2*max_extent*ppu*image_scale) # 1.0 scale
    #size = int((3.0+0.5*(max_extent-3.0))*2*ppu*image_scale) # 0.5 scale
    #size = int(2*3.0*ppu*image_scale) # 0.0 scale
    glViewport(0, 0, image_scale, image_scale)
    #glOrtho(-max_extent, max_extent, -max_extent, max_extent, -1000.0, 1000.0)
    glOrtho(-14.0, 14.0, -14.0, 14.0, -1000.0, 1000.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glDrawBuffer(GL_FRONT)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)

    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHTING)
    glColorMaterial(GL_FRONT, GL_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)

    gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)

    glClearColor(0.0, 0.0, 0.0, 0.0) # Must be black for Image.getbbox to work
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    if hasattr(part, 'icon_view'):
        view = part.icon_view
    else:
        view = current_view
    print view
    
    for rots in views[view][2]:
        glRotatef(rots[0], rots[1], rots[2], rots[3])
    glTranslatef(-vcenter[0], -vcenter[1], -vcenter[2])
    vout = views[view][0]
    vup = views[view][1]

    glColor3f(1.0, 1.0, 1.0)
    part.shape()
    if pieces.detail == 1:
        for end, end_type in zip(part.unaligned_ends, part.ends_types):
            pieces.draw_end(end, end_type)

    #viewport = glGetIntegerv(GL_VIEWPORT)
    #module.total_bmd = glReadPixelsf(viewport[0], viewport[1], viewport[2], viewport[3], GL_DEPTH_COMPONENT)
    #module.draw_part_outlines()

    glFlush()
    gldrawable.gl_end()
    draw_called = 1

def new_part(part_index):
    global part, piece_list, piece_name

    #print part_index
    try:
        piece_name = piece_list[int(part_index[0])]
    except:
        piece_name = 'join3'
    print piece_name
    if piece_name in partial_pieces:
        part = eval(piece_name + '()')
    else:
        part = eval('pieces.' + piece_name + '()')
    expose()

def setview(view):
    global current_view

    current_view = view

# An np.array of out/up vectors
views = {'front': (np.array([0.0, 0.0, 1.0]), np.array([0.0, 1.0, 0.0]), []),
         'top': (np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, -1.0]), [(90.0, 1.0, 0.0, 0.0)]),
         'right': (np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), [(-90.0, 0.0, 1.0, 0.0)]),
         'left': (np.array([-1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), [(90.0, 0.0, 1.0, 0.0)]),
         'bottom': (np.array([0.0, -1.0, 0.0]), np.array([0.0, 0.0, 1.0]), [(-90.0, 1.0, 0.0, 0.0)]),
         'back': (np.array([0.0, 0.0, -1.0]), np.array([0.0, 1.0, 0.0]), [(180.0, 1.0, 0.0, 0.0), (180.0, 0.0, 0.0, 1.0)]),
         'iso': (np.array([1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)]),
                 np.array([0.0, 1.0, 0.0]), [(45.0, 1.0, 0.0, 0.0), (-45.0, 0.0, 1.0, 0.0)]),
         'iso_back': (np.array([-1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)]),
                 np.array([0.0, 1.0, 0.0]), [(-45.0, 1.0, 0.0, 0.0), (135.0, 0.0, 1.0, 0.0)]),
         'iso_down': (np.array([1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)]),
                 np.array([0.0, 1.0, 0.0]), [(-45.0, 1.0, 0.0, 0.0), (-45.0, 0.0, 1.0, 0.0)])}

def set_detail(detail):
    pieces.detail = detail

current_view = 'iso'
screen_capture_type = '.png'
screen_capture_path = 'icons/'
pieces.detail = 2
module = base_pieces.module()

win = gtk.Window()
win.set_default_size(image_scale, image_scale)
win.connect('destroy', gtk.main_quit)
win.show()

vbox1 = gtk.VBox()
win.add(vbox1)
vbox1.show()

menubar = gtk.MenuBar()
vbox1.pack_start(menubar, False)
menubar.show()

file_container = gtk.Menu()

file_generate = gtk.MenuItem('Generate')
file_generate.connect('activate', generate_icons)
file_generate.show()
file_container.append(file_generate)

file_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
file_quit.connect('activate', gtk.main_quit)
file_quit.show()
file_container.append(file_quit)

file_menu = gtk.MenuItem('_File')
file_menu.set_submenu(file_container)
file_menu.show()

menubar.append(file_menu)

glconfig = gtk.gdkgl.Config(mode=gtk.gdkgl.MODE_RGB | gtk.gdkgl.MODE_DEPTH | gtk.gdkgl.MODE_SINGLE | gtk.gdkgl.MODE_ALPHA)
glarea = gtk.gtkgl.DrawingArea(glconfig)
#glarea.connect('expose-event', expose)
glarea.connect('realize', opengl_init)
glarea.connect('expose-event', opengl_expose)

gtk.gtkgl.widget_set_gl_capability(glarea, glconfig)
glarea.show()
vbox1.pack_start(glarea)

#pieces.init('/usr/local/share/sticks_sim') # after openglstart
pieces.init('.')

piece_list = filter(lambda x: type(eval('pieces.' + x)) == type(pieces.stick) and issubclass(eval('pieces.' + x), pieces.stick), dir(pieces))
piece_list.remove('stick')
piece_list.remove('axle')
for partial_piece in partial_pieces:
    if partial_piece not in piece_list:
        piece_list.append(partial_piece)
piece_list.sort()
print 'total pieces = ' + str(len(piece_list))
piece_name = 'join3'
part = eval('pieces.' + piece_name + '()')

gtk.main()
