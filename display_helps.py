#! /usr/bin/python

"""
Description
-----------
helps creator for sticks_sim.  Used to create the help list.

Author
------
Charles Sharman

Revision History
----------------
Began 2/22/14
"""

import os, sys
import types
import time
import math

import pieces
import base_pieces
import vector_math

from OpenGL.GL import *
from OpenGL.GLE import *
from OpenGL.GLU import *

# FPE with Rage 128 card, python-opengl and numnp.array
#from numnp.array import *
#from Numeric import *
import numpy as np

import Image

import pygtk, gtk, gtk.gtkgl, pango
from instructions import outline as instructions_outline

to_draw = 'pass'
draw_called = 0
captured = 0
image_size = (1200, 800) # pixels
image_center = (0.0, 0.0) # mm
crops = [(0, 0, 1200, 800)]
ppu = 10.0 # pixels per unit

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
        glColor3f(1.0, 1.0, 1.0)

class wheel1(base_pieces.piece):
    icon_extent = 8.0
    def shape(self):
        pieces.draw_drawing('wheel1')
        pieces.draw_drawing('tire1', (0.35, 0.35, 0.35))
        glColor3f(1.0, 1.0, 1.0)

class stiffen(base_pieces.piece):
    icon_center = (0.0, -2.5*pieces.sf, -2.5*pieces.sf)
    icon_extent = 3.5
    def shape(self):
        pieces.draw_drawing('stiffen')

def draw_part_outlines(outline_color):
    """
    Borrowed from base_pieces.  Didn't work because drew dark band
    across top.  Cause unknown.
    """
    dim_scale = 1.0

    model = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)

    # reshape needed to circumvent pyopengl bug ***
    #glPixelStorei(GL_PACK_ALIGNMENT, 4)
    #glPixelStorei(GL_PACK_IMAGE_HEIGHT, 800)
    total_bmd = glReadPixelsf(viewport[0], viewport[1], viewport[2], viewport[3], GL_DEPTH_COMPONENT)
    print total_bmd.dtype, total_bmd.shape, viewport
    #print total_bmd[:,0].tolist()
    total_bmd = np.reshape(total_bmd, (viewport[3], viewport[2]))
    #fp = open('tmp.txt', 'w')
    #total_bmd.tofile(fp, sep=" ", format="%s")
    #fp.close()

    binary_depth = (total_bmd < 1.0).astype(np.uint8)
    iterations = 2*dim_scale # Increase for thicker outlines
    outline = binary_depth.copy()
    shadow_bmd = total_bmd.copy()+2*pieces.base_rad*base_pieces.depth_scale # The second term defines the shadow offset.
    while iterations >= 1:
        outline[:,:-1] = outline[:,:-1] | outline[:,1:] # left
        outline[:,1:] = outline[:,1:] | outline[:,:-1] # right
        outline[:-1] = outline[:-1] | outline[1:] # up
        outline[1:] = outline[1:] | outline[:-1] # down
        shadow_bmd[:,:-1] = np.minimum(shadow_bmd[:,:-1], shadow_bmd[:,1:]) # left
        shadow_bmd[:,1:] = np.minimum(shadow_bmd[:,1:], shadow_bmd[:,:-1]) # right
        shadow_bmd[:-1] = np.minimum(shadow_bmd[:-1], shadow_bmd[1:]) # up
        shadow_bmd[1:] = np.minimum(shadow_bmd[1:], shadow_bmd[:-1]) # down
        iterations = iterations - 1
    outline = outline & (shadow_bmd < total_bmd) # Remove this check and all shadow_bmd lines if I only want background highlighted
    column_adds = viewport[2] % 8
    if column_adds > 0:
        column_adds = 8 - column_adds
        full_outline = np.zeros((viewport[3], viewport[2] + column_adds), np.uint8)
        full_outline[:,:viewport[2]] = outline
        outline = full_outline
    outline = np.reshape(outline, (-1, 8)) * np.array([128, 64, 32, 16, 8, 4, 2, 1], np.uint8)
    outline = np.sum(outline, 1).astype(np.uint8)
    glColor3fv(outline_color)
    #glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    p = gluUnProject(0.001, 0.001, 0.001, model, projection, viewport) # Set z to 0.999 (almost back) if I only want background highlighted
    glRasterPos3fv(p)
    glPixelStoref(GL_UNPACK_ALIGNMENT, 1)
    glBitmap(viewport[2], viewport[3], 0, 0, 0, 0, outline)
    glEnable(GL_LIGHTING)
    #glEnable(GL_DEPTH_TEST)
    glPixelStoref(GL_UNPACK_ALIGNMENT, 4)
    p = gluUnProject(0.001, 0.001, 0.001, model, projection, viewport)
    glRasterPos3fv(p)
    # Put outlines at the proper depth (can skip if I only want background highlighted)
    glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
    #glClear(GL_DEPTH_BUFFER_BIT)
    glDrawPixelsf(GL_DEPTH_COMPONENT, total_bmd)
    glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
    glColor3fv((1.0, 1.0, 1.0))

def draw_help(widget = None, name = 'pass'):
    global to_draw
    to_draw = name

def left_arrow(xtip, ytip, tail = 4.0):
    """
    Creates a left-pointing arrow
    """
    """
    global ppu

    dx = 1.0
    dy = 0.5
    sf = pieces.sf

    glDisable(GL_LIGHTING)
    glLineWidth(6.0*ppu/10.0)
    glColor3f(1.0, 0.8, 0.0) # construction yellow
    glBegin(GL_LINES)
    glVertex3f(xtip*sf, ytip*sf, 0.0)
    glVertex3f((xtip + dx)*sf, (ytip + dy)*sf, 0.0)
    glVertex3f(xtip*sf, ytip*sf, 0.0)
    glVertex3f((xtip + dx)*sf, (ytip - dy)*sf, 0.0)
    glVertex3f(xtip*sf, ytip*sf, 0.0)
    glVertex3f((xtip + tail)*sf, ytip*sf, 0.0)
    glEnd()
    glEnable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    """

    arrow3d([((xtip+tail)*pieces.sf, ytip*pieces.sf, 0.0),
             (xtip*pieces.sf, ytip*pieces.sf, 0.0)])

def arrow3d(tail, rad = 0.4, dx = 2.0, dy = 1.0):
    """
    Creates a 3d arrow.  tail is a poly.  The last point in the poly
    is the arrow tip.

    dx is length of tip
    dy is width of tip
    """
    
    np_tail = np.array(tail)
    dt = -vector_math.normalize(np_tail[1] - np_tail[0])
    dh = vector_math.normalize(np_tail[-1] - np_tail[-2])
    cylpts = np.concatenate(([dt + tail[0]], tail[:-1], [-pieces.sf*dx*dh+tail[-1], tail[-1]]))
    #print cylpts

    conepts = np.array((tail[-1]-dh-dx*dh, tail[-1]-dx*pieces.sf*dh, tail[-1], tail[-1] + dh))
    #print conepts

    glColor3f(1.0, 0.8, 0.0) # construction yellow
    glePolyCylinder(cylpts, None, rad*pieces.sf)
    glePolyCone(conepts, None, (dy*pieces.sf, dy*pieces.sf, dy/10*pieces.sf, dy/10*pieces.sf))
    glColor3f(1.0, 1.0, 1.0)

def set_size(x, y):
    pass

def help_bad_connection(widget = None):
    global crops

    sep = pieces.len1/4

    view_good_bad([pieces.len1/2 + sep/2, -pieces.len1/2-sep/2, 0.0])

    j = pieces.join2()
    s = pieces.straight1()

    # Structure 1
    glPushMatrix()
    glRotatef(180.0, 1.0, 0.0, 0.0)
    j.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(pieces.join_len, 0.0, 0.0)
    s.shape()
    glPopMatrix()

    glPushMatrix()
    glRotatef(-90.0, 0.0, 0.0, 1.0)
    glTranslatef(pieces.join_len, 0.0, 0.0)
    s.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.0, -pieces.len1, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    glRotatef(180.0, 1.0, 0.0, 0.0)
    j.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(pieces.len1, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 0.0, 1.0)
    glRotatef(180.0, 1.0, 0.0, 0.0)
    j.shape()
    glPopMatrix()

    # Structure 2
    glPushMatrix()
    glTranslatef(pieces.len1 + sep, -sep, 0.0)
    glRotatef(-90.0, 0.0, 0.0, 1.0)
    glTranslatef(pieces.join_len, 0.0, 0.0)
    s.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(pieces.len1 + sep, -pieces.len1-sep, 0.0)
    glRotatef(180.0, 0.0, 0.0, 1.0)
    glRotatef(180.0, 1.0, 0.0, 0.0)
    j.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(pieces.join_len + sep, -pieces.len1-sep, 0.0)
    s.shape()
    glPopMatrix()

    # Arrows
    arrow_sep = 4.0*pieces.sf
    arrow3d([(pieces.len1 - pieces.base_rad + sep - arrow_sep, -pieces.base_rad-pieces.join_len-arrow_sep-sep, 0.0), (pieces.len1 - pieces.base_rad + sep - arrow_sep, -pieces.base_rad-pieces.join_len-arrow_sep, 0.0)])
    arrow3d([(pieces.join_len+2*sep, -pieces.len1 + pieces.base_rad+arrow_sep - sep, 0.0), (pieces.join_len+sep, -pieces.len1+pieces.base_rad+arrow_sep - sep, 0.0)])

    crops = [(0, 0, image_size[0], image_size[1])]

def help_good_connection(widget = None):
    global crops

    sep = pieces.len1/4

    view_good_bad([pieces.len1/2 + sep/2, -pieces.len1/2, 0.0])

    j = pieces.join2()
    s = pieces.straight1()

    # Structure 1
    glPushMatrix()
    glRotatef(180.0, 1.0, 0.0, 0.0)
    j.shape()
    glPopMatrix()

    glPushMatrix()
    glRotatef(-90.0, 0.0, 0.0, 1.0)
    glTranslatef(pieces.join_len, 0.0, 0.0)
    s.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.0, -pieces.len1, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    glRotatef(180.0, 1.0, 0.0, 0.0)
    j.shape()
    glPopMatrix()

    # Structure 2
    glPushMatrix()
    glTranslatef(pieces.join_len + sep, 0.0, 0.0)
    s.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(pieces.len1 + sep, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 0.0, 1.0)
    glRotatef(180.0, 1.0, 0.0, 0.0)
    j.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(pieces.len1 + sep, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 0.0, 1.0)
    glTranslatef(pieces.join_len, 0.0, 0.0)
    s.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(pieces.len1 + sep, -pieces.len1, 0.0)
    glRotatef(180.0, 0.0, 0.0, 1.0)
    glRotatef(180.0, 1.0, 0.0, 0.0)
    j.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(pieces.join_len + sep, -pieces.len1, 0.0)
    s.shape()
    glPopMatrix()

    # Arrows
    arrow_sep = 4.0*pieces.sf
    arrow3d([(pieces.join_len+sep, -pieces.base_rad-arrow_sep, 0.0), (pieces.join_len, -pieces.base_rad-arrow_sep, 0.0)])
    arrow3d([(pieces.join_len+sep, -pieces.len1 + pieces.base_rad+arrow_sep, 0.0), (pieces.join_len, -pieces.len1+pieces.base_rad+arrow_sep, 0.0)])
    
    crops = [(0, 0, image_size[0], image_size[1])]

def help_couplergear_axle1sgear_axle1s(widget = None):
    global crops

    view_standard()

    join2f = pieces.join2flat()
    c = coupler()
    gear_axle1s = pieces.gear_axle1s()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    c.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, 5.6*pieces.sf, 0.0)
    gear_axle1s.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, -5.6*pieces.sf, 0.0)
    gear_axle1s.shape()
    glPopMatrix()

    left_arrow(-48.0, 0.0)
    left_arrow(-33.0, 0.0)

    crops = [(0, 0, int(50.0*ppu), image_size[1])]

def help_couplerstraight1m1gear_axle1s(widget = None):
    global crops

    view_standard()

    join2f = pieces.join2flat()
    c = coupler()
    gear_axle1s = pieces.gear_axle1s()
    straight1m1 = pieces.straight1m1()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(2.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    c.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, -5.6*pieces.sf, 0.0)
    glRotatef(-90.0, 1.0, 0.0, 0.0)
    straight1m1.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, 5.6*pieces.sf, 0.0)
    gear_axle1s.shape()
    glPopMatrix()

    left_arrow(-48.0, 0.0)
    left_arrow(-33.0, 0.0)
    left_arrow(-14.0, 0.0)

    crops = [(0, 0, int(62.0*ppu), image_size[1])]

def help_couplerstraight1m1straight1m1(widget = None):
    global crops

    view_standard()

    join2f = pieces.join2flat()
    c = coupler()
    straight1m1 = pieces.straight1m1()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(2.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(2.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    c.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, 5.6*pieces.sf, 0.0)
    glRotatef(-90.0, 1.0, 0.0, 0.0)
    straight1m1.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, -5.6*pieces.sf, 0.0)
    glRotatef(-90.0, 1.0, 0.0, 0.0)
    straight1m1.shape()
    glPopMatrix()

    left_arrow(-48.0, 0.0)
    left_arrow(-33.0, 0.0)
    left_arrow(-14.0, 0.0)

    crops = [(0, 0, int(62.0*ppu), image_size[1])]

def help_couplergear_axle2sgear_axle1s(widget = None):
    global crops

    view_standard()

    join2f = pieces.join2flat()
    c = coupler()
    gear_axle2s = pieces.gear_axle2s()
    gear_axle1s = pieces.gear_axle1s()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(13.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    c.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, 5.6*pieces.sf, 0.0)
    gear_axle1s.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, -5.6*pieces.sf, 0.0)
    gear_axle2s.shape()
    glPopMatrix()

    left_arrow(-48.0, 0.0)
    left_arrow(-33.0, 0.0)
    left_arrow(-2.0, 0.0)

    crops = [(0, 0, int(73.0*ppu), image_size[1])]

def help_couplergear_axle2sstraight1m1(widget = None):
    global crops

    view_standard()

    join2f = pieces.join2flat()
    c = coupler()
    gear_axle2s = pieces.gear_axle2s()
    straight1m1 = pieces.straight1m1()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(13.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(13.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    c.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, 5.6*pieces.sf, 0.0)
    glRotatef(90.0, 1.0, 0.0, 0.0)
    straight1m1.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, -5.6*pieces.sf, 0.0)
    gear_axle2s.shape()
    glPopMatrix()

    left_arrow(-48.0, 0.0)
    left_arrow(-33.0, 0.0)
    left_arrow(-2.0, 0.0)

    crops = [(0, 0, int(73.0*ppu), image_size[1])]

def help_couplergear_axle2sgear_axle2s(widget = None):
    global crops

    view_standard()

    join2f = pieces.join2flat()
    c = coupler()
    gear_axle2s = pieces.gear_axle2s()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(30.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(30.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    c.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(8.0*pieces.sf, 0.0, 0.0)
    glRotatef(90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    c.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, 5.6*pieces.sf, 0.0)
    gear_axle2s.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, -5.6*pieces.sf, 0.0)
    gear_axle2s.shape()
    glPopMatrix()

    left_arrow(-48.0, 0.0)
    left_arrow(-33.0, 0.0)
    left_arrow(-2.0, 0.0)
    left_arrow(14.0, 0.0)

    crops = [(0, 0, int(90.0*ppu), image_size[1])]

def help_couplergear_axle2sgear_axle1sgear_axle1s(widget = None):
    global crops

    view_standard()

    join2f = pieces.join2flat()
    c = coupler()
    gear_axle2s = pieces.gear_axle2s()
    gear_axle1s = pieces.gear_axle1s()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(30.0*pieces.sf, 5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(30.0*pieces.sf, -5.6*pieces.sf, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    c.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(8.0*pieces.sf, 0.0, 0.0)
    glRotatef(90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    c.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, 5.6*pieces.sf, 0.0)
    gear_axle1s.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-2.0*pieces.sf, 5.6*pieces.sf, 0.0)
    glRotatef(180.0, 0.0, 1.0, 0.0)
    gear_axle1s.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, -5.6*pieces.sf, 0.0)
    gear_axle2s.shape()
    glPopMatrix()

    left_arrow(-48.0, 0.0)
    left_arrow(-33.0, 0.0)
    left_arrow(-2.0, 0.0)

    crops = [(0, 0, int(90.0*ppu), image_size[1])]

def help_wheel_axle1s1w(widget = None, variant = 0):
    global crops

    view_standard()

    join2f = pieces.join2flat()
    if variant == 0:
        w = wheelp5()
    else:
        w = wheel1()
    wheel_axle1s1w = pieces.wheel_axle1s1w()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 0.0, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-36.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    w.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-20.0*pieces.sf, 0.0, 0.0)
    wheel_axle1s1w.shape()
    glPopMatrix()

    left_arrow(-49.0, 6.0)
    left_arrow(-26.0, 6.0)

    crops = [(0, 0, int(60.0*ppu), image_size[1])]

def help_wheel_axle1s1wwheelp5(widget = None):
    help_wheel_axle1s1w(widget, 0)

def help_wheel_axle1s1wwheel1(widget = None):
    help_wheel_axle1s1w(widget, 1)

def help_wheel_axle2s2w(widget = None, variant = 0):
    global crops

    view_standard()

    join2f = pieces.join2flat()
    if variant == 0:
        w = wheelp5()
    else:
        w = wheel1()
    wheel_axle2s2w = pieces.wheel_axle2s2w()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 0.0, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(20.0*pieces.sf, 0.0, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-36.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    w.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-8.0*pieces.sf, 0.0, 0.0)
    glRotatef(90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    w.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-22.0*pieces.sf, 0.0, 0.0)
    wheel_axle2s2w.shape()
    glPopMatrix()

    left_arrow(-49.0, 6.0)
    left_arrow(-24.0, 6.0)
    left_arrow(3.0, 6.0)

    crops = [(0, 0, int(80.0*ppu), image_size[1])]

def help_wheel_axle2s2wwheelp5(widget = None):
    help_wheel_axle2s2w(widget, 0)

def help_wheel_axle2s2wwheel1(widget = None):
    help_wheel_axle2s2w(widget, 1)

def help_wheel_axle1s3w(widget = None, variant = 0):
    global crops

    view_standard()

    join2f = pieces.join2flat()
    if variant == 0:
        w = wheelp5()
    else:
        w = wheel1()
    wheel_axle1s3w = pieces.wheel_axle1s3w()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 0.0, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-36.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    w.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-12.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 0.0, 1.0, 0.0)
    w.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(5.0*pieces.sf, 0.0, 0.0)
    glRotatef(90.0, 0.0, 1.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    w.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-22.0*pieces.sf, 0.0, 0.0)
    wheel_axle1s3w.shape()
    glPopMatrix()

    left_arrow(-49.0, 6.0)
    left_arrow(-26.0, 6.0)
    #left_arrow(-8.0, 15.0)
    left_arrow(14.0, 6.0)

    crops = [(0, 0, int(80.0*ppu), image_size[1])]

def help_wheel_axle1s3wwheelp5(widget = None):
    help_wheel_axle1s3w(widget, 0)

def help_wheel_axle1s3wwheel1(widget = None):
    help_wheel_axle1s3w(widget, 1)

def help_gear_axle1s(widget = None, gear = 'None'):
    global crops
    
    view_standard()

    join2f = pieces.join2flat()
    if gear != 'None':
        g = eval(gear + '()')
    gear_axle1s = pieces.gear_axle1s()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 0.0, 0.0)
    join2f.shape()
    glPopMatrix()

    if gear != 'None':
        glPushMatrix()
        glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
        glRotatef(90.0, 0.0, 1.0, 0.0)
        g.shape()
        glPopMatrix()

    glPushMatrix()
    if gear != 'None':
        glTranslatef(-21.0*pieces.sf, 0.0, 0.0)
    else:
        glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
    gear_axle1s.shape()
    glPopMatrix()

    left_arrow(-48.0, 6.0)
    if gear != 'None':
        left_arrow(-32.0, 6.0)

    crops = [(0, 0, int(48.0*ppu), image_size[1])]

def help_gear_axle1sgear1(widget = None):
    help_gear_axle1s(widget, 'gear1')

def help_gear_axle1sgear_bevel(widget = None):
    help_gear_axle1s(widget, 'gear_bevel')

def help_gear_axle1sgear3s(widget = None):
    help_gear_axle1s(widget, 'gear3s')

def help_gear_axle1sgear3l(widget = None):
    help_gear_axle1s(widget, 'gear3l')

def help_straight1m1(widget = None, gear = 'None'):
    global crops
    
    view_standard()

    join2f = pieces.join2flat()
    if gear != 'None':
        g = eval(gear + '()')
    straight1m1 = pieces.straight1m1()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 0.0, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
    glRotatef(90.0, 0.0, 1.0, 0.0)
    g.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, 0.0, 0.0)
    glRotatef(-90.0, 1.0, 0.0, 0.0)
    straight1m1.shape()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(2.0*pieces.sf, 0.0, 0.0)
    join2f.shape()
    glPopMatrix()

    left_arrow(-48.0, 6.0)
    left_arrow(-33.0, 6.0)
    left_arrow(-14.0, 6.0)

    crops = [(0, 0, int(62.0*ppu), image_size[1])]

def help_straight1m1gear1(widget = None):
    help_straight1m1(widget, 'gear1')

def help_straight1m1gear_bevel(widget = None):
    help_straight1m1(widget, 'gear_bevel')

def help_straight1m1gear3s(widget = None):
    help_straight1m1(widget, 'gear3s')

def help_straight1m1gear3l(widget = None):
    help_straight1m1(widget, 'gear3l')

def help_gear_axle2s(widget = None, gear = 'gear1'):
    global crops
    
    view_standard()

    join2f = pieces.join2flat()
    if gear != 'None':
        g = eval(gear + '()')
    gear_axle2s = pieces.gear_axle2s()

    glPushMatrix()
    glTranslatef(-60.0*pieces.sf, 0.0, 0.0)
    join2f.shape()
    glPopMatrix()

    glPushMatrix()
    if gear != 'None':
        glTranslatef(30.0*pieces.sf, 0.0, 0.0)
    else:
        glTranslatef(20.0*pieces.sf, 0.0, 0.0)
    join2f.shape()
    glPopMatrix()

    if gear != 'None':
        glPushMatrix()
        glTranslatef(-39.0*pieces.sf, 0.0, 0.0)
        glRotatef(90.0, 0.0, 1.0, 0.0)
        g.shape()
        glPopMatrix()

    if gear != 'None':
        glPushMatrix()
        glTranslatef(8.0*pieces.sf, 0.0, 0.0)
        glRotatef(-90.0, 0.0, 1.0, 0.0)
        g.shape()
        glPopMatrix()

    glPushMatrix()
    glTranslatef(-29.0*pieces.sf, 0.0, 0.0)
    gear_axle2s.shape()
    glPopMatrix()

    if gear != 'None':
        left_arrow(-48.0, 6.0)
        left_arrow(-33.0, 6.0)
        left_arrow(-2.0, 6.0)
        left_arrow(14.0, 6.0)
    else:
        left_arrow(-43.0, 6.0)
        left_arrow(4.0, 6.0)

    if gear != 'None':
        crops = [('_left', (0, 0, int(45.0*ppu), image_size[1])),
                 ('_right', (int(45.0*ppu), 0, int(90.0*ppu), image_size[1]))]
    else:
        crops = [('_left', (0, 0, int(45.0*ppu), image_size[1])),
                 ('_right', (int(45.0*ppu), 0, int(80.0*ppu), image_size[1]))]

def help_gear_axle2sNone(widget = None):
    help_gear_axle2s(widget, 'None')

def help_gear_axle2sgear1(widget = None):
    help_gear_axle2s(widget, 'gear1')

def help_gear_axle2sgear_bevel(widget = None):
    help_gear_axle2s(widget, 'gear_bevel')

def help_gear_axle2sgear3s(widget = None):
    help_gear_axle2s(widget, 'gear3s')

def help_gear_axle2sgear3l(widget = None):
    help_gear_axle2s(widget, 'gear3l')

def screen_capture(filename, background = 0):
    global captured, crops
    x0, y0, width, height = glGetIntegerv(GL_VIEWPORT)
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    if background:
        data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        im = Image.fromstring('RGB', (width, height), data)
    else:
        data = glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        im = Image.fromstring('RGBA', (width, height), data)

    im = im.transpose(Image.FLIP_TOP_BOTTOM)
    im = instructions_outline(im, 2, (0, 0, 0), expand = 0)

    for crop in crops:
        print 'crop', crop
        if type(crop[0]) == type(''):
            im2 = im.crop(crop[1])
            im2.save(filename[:-4] + crop[0] + filename[-4:])
        else:
            im = im.crop(crop)
            im.save(filename)
    captured = 1

def generate_helps(widget = None):
    global draw_called, to_draw, glarea

    screen_capture_path = 'helps/'

    for to_draw in ['help_bad_connection',
                    'help_good_connection',
                    'help_couplergear_axle1sgear_axle1s',
                    'help_couplerstraight1m1gear_axle1s',
                    'help_couplergear_axle2sgear_axle1s',
                    'help_couplergear_axle2sstraight1m1',
                    'help_couplergear_axle2sgear_axle2s',
                    'help_couplergear_axle2sgear_axle1sgear_axle1s',
                    'help_couplerstraight1m1straight1m1',
                    'help_wheel_axle1s1wwheelp5',
                    'help_wheel_axle1s1wwheel1',
                    'help_wheel_axle2s2wwheelp5',
                    'help_wheel_axle2s2wwheel1',
                    'help_wheel_axle1s3wwheelp5',
                    'help_wheel_axle1s3wwheel1',
                    'help_gear_axle1sgear1',
                    'help_gear_axle1sgear_bevel',
                    'help_gear_axle1sgear3s',
                    'help_gear_axle1sgear3l',
                    'help_straight1m1gear1',
                    'help_straight1m1gear_bevel',
                    'help_straight1m1gear3s',
                    'help_straight1m1gear3l',
                    'help_gear_axle2sNone',
                    'help_gear_axle2sgear1',
                    'help_gear_axle2sgear_bevel',
                    'help_gear_axle2sgear3s',
                    'help_gear_axle2sgear3l']:
                    
        draw_called = 0
        glarea.queue_draw()
        while not draw_called:
            gtk.main_iteration()
        screen_capture(os.path.join(screen_capture_path, to_draw + '.png'))

def opengl_init(widget):
    global glarea, ppu

    glcontext = gtk.gtkgl.widget_get_gl_context(glarea)
    gldrawable = gtk.gtkgl.widget_get_gl_drawable(glarea)
    if not gldrawable.gl_begin(glcontext):
        return

    glDrawBuffer(GL_FRONT)
    glReadBuffer(GL_FRONT)
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

def view_standard():
    global image_size, ppu

    ppu = 10.0
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glViewport(0, 0, image_size[0], image_size[1])
    dx = image_size[0]/2
    dy = image_size[1]/2
    xmin = (image_center[0] - dx/ppu)*pieces.sf
    xmax = (image_center[0] + dx/ppu)*pieces.sf
    ymin = (image_center[1] - dy/ppu)*pieces.sf
    ymax = (image_center[1] + dy/ppu)*pieces.sf
    glOrtho(xmin, xmax, ymin, ymax, -400.0, 400.0) # The screen's limits
    base_pieces.depth_scale = 1.0/800.0 # determined by glOrtho
    glMatrixMode(GL_MODELVIEW)

    angle = math.radians(5.0)
    dist = 100.0
    gluLookAt(dist*math.sin(angle), 0.0, dist*math.cos(angle), 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

def view_good_bad(center):
    global image_size, ppu

    ppu = 10.0
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glViewport(0, 0, image_size[0], image_size[1])
    dx = image_size[0]/2
    dy = image_size[1]/2
    xmin = (image_center[0] - dx/ppu)*pieces.sf
    xmax = (image_center[0] + dx/ppu)*pieces.sf
    ymin = (image_center[1] - dy/ppu)*pieces.sf
    ymax = (image_center[1] + dy/ppu)*pieces.sf
    glOrtho(xmin, xmax, ymin, ymax, -400.0, 400.0) # The screen's limits
    base_pieces.depth_scale = 1.0/800.0 # determined by glOrtho
    glMatrixMode(GL_MODELVIEW)

    dist = 30.0
    gluLookAt(center[0]+dist*math.sqrt(0.2), center[1]-dist*math.sqrt(0.2), center[2]+dist*math.sqrt(0.6), center[0], center[1], center[2], -math.sqrt(0.5), math.sqrt(0.5), 0.0)

def opengl_expose(widget = None, event = None):
    global views, glarea, draw_called, to_draw

    glcontext = gtk.gtkgl.widget_get_gl_context(glarea)
    gldrawable = gtk.gtkgl.widget_get_gl_drawable(glarea)
    if not gldrawable.gl_begin(glcontext):
        return

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glLoadIdentity()

    print to_draw
    if to_draw != 'pass':
        eval(to_draw + '()')
    #draw_part_outlines((0.0, 0.0, 0.0))

    glFlush()
    gldrawable.gl_end()
    draw_called = 1

if __name__ == '__main__':

    current_view = 'iso'
    screen_capture_type = '.png'
    screen_capture_path = 'helps/'
    pieces.detail = 2
    module = base_pieces.module()

    win = gtk.Window()
    win.set_default_size(image_size[0], image_size[1])
    win.connect('destroy', gtk.main_quit)
    win.show()

    vbox1 = gtk.VBox()
    win.add(vbox1)
    vbox1.show()

    menubar = gtk.MenuBar()
    vbox1.pack_start(menubar, False)
    menubar.show()

    file_container = gtk.Menu()

    file_bad_connection = gtk.MenuItem('bad_connection')
    file_bad_connection.connect('activate', draw_help, 'help_bad_connection')
    file_bad_connection.show()
    file_container.append(file_bad_connection)

    file_good_connection = gtk.MenuItem('good_connection')
    file_good_connection.connect('activate', draw_help, 'help_good_connection')
    file_good_connection.show()
    file_container.append(file_good_connection)

    file_couplergear_axle1sgear_axle1s = gtk.MenuItem('couplergear_axle1sgear_axle1s')
    file_couplergear_axle1sgear_axle1s.connect('activate', draw_help, 'help_couplergear_axle1sgear_axle1s')
    file_couplergear_axle1sgear_axle1s.show()
    file_container.append(file_couplergear_axle1sgear_axle1s)

    file_couplerstraight1m1gear_axle1s = gtk.MenuItem('couplerstraight1m1gear_axle1s')
    file_couplerstraight1m1gear_axle1s.connect('activate', draw_help, 'help_couplerstraight1m1gear_axle1s')
    file_couplerstraight1m1gear_axle1s.show()
    file_container.append(file_couplerstraight1m1gear_axle1s)

    file_couplergear_axle2sgear_axle1s = gtk.MenuItem('couplergear_axle2sgear_axle1s')
    file_couplergear_axle2sgear_axle1s.connect('activate', draw_help, 'help_couplergear_axle2sgear_axle1s')
    file_couplergear_axle2sgear_axle1s.show()
    file_container.append(file_couplergear_axle2sgear_axle1s)

    file_couplergear_axle2sstraight1m1 = gtk.MenuItem('couplergear_axle2sstraight1m1')
    file_couplergear_axle2sstraight1m1.connect('activate', draw_help, 'help_couplergear_axle2sstraight1m1')
    file_couplergear_axle2sstraight1m1.show()
    file_container.append(file_couplergear_axle2sstraight1m1)

    file_couplergear_axle2sgear_axle2s = gtk.MenuItem('couplergear_axle2sgear_axle2s')
    file_couplergear_axle2sgear_axle2s.connect('activate', draw_help, 'help_couplergear_axle2sgear_axle2s')
    file_couplergear_axle2sgear_axle2s.show()
    file_container.append(file_couplergear_axle2sgear_axle2s)

    file_couplergear_axle2sgear_axle1sgear_axle1s = gtk.MenuItem('couplergear_axle2sgear_axle1sgear_axle1s')
    file_couplergear_axle2sgear_axle1sgear_axle1s.connect('activate', draw_help, 'help_couplergear_axle2sgear_axle1sgear_axle1s')
    file_couplergear_axle2sgear_axle1sgear_axle1s.show()
    file_container.append(file_couplergear_axle2sgear_axle1sgear_axle1s)

    file_couplerstraight1m1straight1m1 = gtk.MenuItem('couplerstraight1m1straight1m1')
    file_couplerstraight1m1straight1m1.connect('activate', draw_help, 'help_couplerstraight1m1straight1m1')
    file_couplerstraight1m1straight1m1.show()
    file_container.append(file_couplerstraight1m1straight1m1)

    file_wheel_axle1s1wwheelp5 = gtk.MenuItem('wheel_axle1s1wwheelp5')
    file_wheel_axle1s1wwheelp5.connect('activate', draw_help, 'help_wheel_axle1s1wwheelp5')
    file_wheel_axle1s1wwheelp5.show()
    file_container.append(file_wheel_axle1s1wwheelp5)

    file_wheel_axle1s1wwheel1 = gtk.MenuItem('wheel_axle1s1wwheel1')
    file_wheel_axle1s1wwheel1.connect('activate', draw_help, 'help_wheel_axle1s1wwheel1')
    file_wheel_axle1s1wwheel1.show()
    file_container.append(file_wheel_axle1s1wwheel1)

    file_wheel_axle2s2wwheelp5 = gtk.MenuItem('wheel_axle2s2wwheelp5')
    file_wheel_axle2s2wwheelp5.connect('activate', draw_help, 'help_wheel_axle2s2wwheelp5')
    file_wheel_axle2s2wwheelp5.show()
    file_container.append(file_wheel_axle2s2wwheelp5)

    file_wheel_axle2s2wwheel1 = gtk.MenuItem('wheel_axle2s2wwheel1')
    file_wheel_axle2s2wwheel1.connect('activate', draw_help, 'help_wheel_axle2s2wwheel1')
    file_wheel_axle2s2wwheel1.show()
    file_container.append(file_wheel_axle2s2wwheel1)

    file_wheel_axle1s3wwheelp5 = gtk.MenuItem('wheel_axle1s3wwheelp5')
    file_wheel_axle1s3wwheelp5.connect('activate', draw_help, 'help_wheel_axle1s3wwheelp5')
    file_wheel_axle1s3wwheelp5.show()
    file_container.append(file_wheel_axle1s3wwheelp5)

    file_wheel_axle1s3wwheel1 = gtk.MenuItem('wheel_axle1s3wwheel1')
    file_wheel_axle1s3wwheel1.connect('activate', draw_help, 'help_wheel_axle1s3wwheel1')
    file_wheel_axle1s3wwheel1.show()
    file_container.append(file_wheel_axle1s3wwheel1)

    file_gear_axle1sgear1 = gtk.MenuItem('gear_axle1sgear1')
    file_gear_axle1sgear1.connect('activate', draw_help, 'help_gear_axle1sgear1')
    file_gear_axle1sgear1.show()
    file_container.append(file_gear_axle1sgear1)

    file_gear_axle1sgear_bevel = gtk.MenuItem('gear_axle1sgear_bevel')
    file_gear_axle1sgear_bevel.connect('activate', draw_help, 'help_gear_axle1sgear_bevel')
    file_gear_axle1sgear_bevel.show()
    file_container.append(file_gear_axle1sgear_bevel)

    file_gear_axle1sgear3s = gtk.MenuItem('gear_axle1sgear3s')
    file_gear_axle1sgear3s.connect('activate', draw_help, 'help_gear_axle1sgear3s')
    file_gear_axle1sgear3s.show()
    file_container.append(file_gear_axle1sgear3s)

    file_gear_axle1sgear3l = gtk.MenuItem('gear_axle1sgear3l')
    file_gear_axle1sgear3l.connect('activate', draw_help, 'help_gear_axle1sgear3l')
    file_gear_axle1sgear3l.show()
    file_container.append(file_gear_axle1sgear3l)

    file_straight1m1gear1 = gtk.MenuItem('straight1m1gear1')
    file_straight1m1gear1.connect('activate', draw_help, 'help_straight1m1gear1')
    file_straight1m1gear1.show()
    file_container.append(file_straight1m1gear1)

    file_straight1m1gear_bevel = gtk.MenuItem('straight1m1gear_bevel')
    file_straight1m1gear_bevel.connect('activate', draw_help, 'help_straight1m1gear_bevel')
    file_straight1m1gear_bevel.show()
    file_container.append(file_straight1m1gear_bevel)

    file_straight1m1gear3s = gtk.MenuItem('straight1m1gear3s')
    file_straight1m1gear3s.connect('activate', draw_help, 'help_straight1m1gear3s')
    file_straight1m1gear3s.show()
    file_container.append(file_straight1m1gear3s)

    file_straight1m1gear3l = gtk.MenuItem('straight1m1gear3l')
    file_straight1m1gear3l.connect('activate', draw_help, 'help_straight1m1gear3l')
    file_straight1m1gear3l.show()
    file_container.append(file_straight1m1gear3l)

    file_gear_axle2sgear1 = gtk.MenuItem('gear_axle2sgear1')
    file_gear_axle2sgear1.connect('activate', draw_help, 'help_gear_axle2sgear1')
    file_gear_axle2sgear1.show()
    file_container.append(file_gear_axle2sgear1)

    file_gear_axle2sNone = gtk.MenuItem('gear_axle2sNone')
    file_gear_axle2sNone.connect('activate', draw_help, 'help_gear_axle2sNone')
    file_gear_axle2sNone.show()
    file_container.append(file_gear_axle2sNone)

    file_generate = gtk.MenuItem('Generate')
    file_generate.connect('activate', generate_helps)
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
    glarea = gtk.gtkgl.DrawingArea(glconfig, direct = True)
    glarea.connect('realize', opengl_init)
    glarea.connect('expose-event', opengl_expose)
    gtk.gtkgl.widget_set_gl_capability(glarea, glconfig)
    glarea.show()
    glarea.set_size_request(image_size[0], image_size[1])

    vbox1.pack_start(glarea)

    pieces.init('.')

    gtk.main()
