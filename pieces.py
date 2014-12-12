"""
Description
-----------
Crossbeams Modeller Pieces Library

Author
------
Charles Sharman

License
-------
Distributed under the GNU GENERAL PUBLIC LICENSE Version 3.  View
LICENSE for details.
"""

import base_pieces
import math
import vector_math
import gzip
import os
import time
import sys

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLE import *

import numpy as np

sf = 1.0/4.0 # scale factor.  Probably archaic, but keep to avoid rework.
base_rad = 4.2*sf # Multiplier for radius, 1x is 40, 2x is 80
join_len = base_rad + 5.2*sf
join_ext = 3.8*sf
stick_hold = 1.6*sf # Estimate for straight parts of angles
len1 = 44.8*sf
len1p5 = 1.5*len1
len2 = 2*len1
lenp5 = 0.5*len1

len1s = len1 - 2*join_len
len2s = len2 - 2*join_len
len1h = len1 - join_len
len2h = len2 - join_len
len1p5s = len1p5 - 2*join_len
len1p5h = len1p5 - join_len
lenp5s = lenp5 - 2*join_len
lenh1h = lenp5 - join_len
rot_rad = 5.5*sf # Rotate joints radius
gearw = 5.4*sf # Gear Width
wheelw = lenp5/2 # Wheel Width
wheels = wheelw - join_len # Wheel Spacer Width
panel_space = lenp5/2 # Spacing between a panel strut and regular strut

detail = 1
share_directory = ''

#detail0_gllists = {} # Seemed to be no benefit in calllist for lines
detail1_gllists = {}
detail2_gllists = {}

aliases = {}
masses = {}
prices = {}

colors = {'total': (1.0, 1.0, 1.0), # overridden by cbmodel
          'straight': (1.0, 1.0, 1.0),
          'angle': (1.0, 1.0, 1.0),
          'arc': (1.0, 1.0, 1.0),
          'part': (0.0, 1.0, 0.0),
          'edit': (0.302, 0.4, 0.8),
          'outline': (0.0, 0.0, 0.0),
          'newpart': (0.302, 0.4, 0.8),
          'futurepart': (0.33, 0.33, 0.33),
          'tire': (0.33, 0.33, 0.33),
          'wheel': (1.0, 1.0, 1.0),
          'clip': (1.0, 1.0, 1.0),
          'gear': (1.0, 1.0, 1.0),
          'shaft': (1.0, 1.0, 1.0),
          'region0': (1.0, 0.5, 0.5),
          'region1': (0.5, 1.0, 0.5),
          'region2': (0.5, 0.5, 1.0),
          'region3': (0.8, 0.8, 0.4),
          'region4': (0.4, 0.8, 0.8),
          'region5': (0.8, 0.4, 0.4)}

#gear_list = ['None', 'gear1', 'gear2s', 'gear2l', 'gear3s', 'gear3l', 'gear_rack_spur', '-gear_rack_spur', 'gear_bevel'] # Experimental
gear_list = ['None', 'gear1', 'gear3s', 'gear3l', 'gear_bevel']

configure_aliases = {'stiff1': 'stiffen',
                     'stiff2': 'stiffen',
                     'stiff3': 'stiffen',
                     'stiff4': 'stiffen'}

# Useful for display speed-up
def init(dir = None):
    """
    Called after importing.  Speeds up later work
    """
    global circle_coords, share_directory, masses, prices

    share_directory = dir

    # Generate circle coords
    segments = 8
    coords = []
    for count in range(segments+1):
        theta = math.pi/2.0*float(count)/float(segments)
        x = math.cos(theta)
        y = math.sin(theta)
        coords.append((x, y, 0.0))
    #coords.insert(0, coords[0])
    #coords.append(coords[-1])
    circle_coords = tuple(coords)

    # Read Masses
    masses = read_masses()

    # Read prices
    prices = read_prices()

def read_masses():
    """
    Read the mass of each piece and place it in a dictionary
    """
    masses = {}
    try:
        fp = open(os.path.join(share_directory, 'masses.csv'))
    except:
        fp = None
    if fp:
        for line in fp:
            key, value = (line.strip()).split(',')
            masses[key] = float(value)
        fp.close()
    return masses

def read_prices():
    """
    Read the price of each piece and place it in a dictionary
    """
    prices = {}
    try:
        fp = open(os.path.join(share_directory, 'prices.csv'))
    except:
        fp = None
    if fp:
        for line in fp:
            key, value = (line.strip()).split(',')
            prices[key] = float(value)
        fp.close()
    return prices

def default_material():
    """
    Set up the plastic material properties
    """
    # Default
    glMaterialfv(GL_FRONT, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
    glMaterialfv(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
    glMaterialfv(GL_FRONT, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))
    glMaterialfv(GL_FRONT, GL_SHININESS, 0.0)

    #glMaterialfv(GL_FRONT, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
    #glMaterialfv(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
    #glMaterialfv(GL_FRONT, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
    #glMaterialfv(GL_FRONT, GL_SHININESS, 32)

def exec_raw(name):
    """
    Read in a triangular representation of a piece for rendering.
    Used a home-grown format which was much faster than stl or ogl.gz
    reading.
    """
    full_name = os.path.join(share_directory, 'ogl_drawings', name + '.raw')
    try:
        rawdata = np.fromfile(full_name, np.float32)
    except IOError:
        print 'Couldn\'t find', full_name
        sys.exit()
    rawdata = np.reshape(rawdata, (len(rawdata)/3, 3))
    normals = np.repeat(rawdata[::4], 3, 0)
    vertices = np.delete(rawdata, np.s_[::4], 0)
    glEnable(GL_VERTEX_ARRAY)
    glEnable(GL_NORMAL_ARRAY)
    glVertexPointerf(vertices)
    glNormalPointerf(normals)
    glDrawArrays(GL_TRIANGLES, 0, len(vertices))

def draw_drawing(name, color = None):
    """
    Draw the rendered version of a piece
    """
    # Display lists was much faster, but the recursive call messed up
    # the outer display list call.
    if not detail2_gllists.has_key(name):
        gllist = glGenLists(1)

        if gllist != 0:
            glNewList(gllist, GL_COMPILE)

        time1 = time.time()
        #print 'Generating drawing', name,
        exec_raw(name)
        time2 = time.time()
        #print 'in %.1fs' % (time2-time1)

        if gllist != 0:
            glEndList()
            detail2_gllists[name] = gllist

    if color != None:
        glColor3fv(color)
    glCallList(detail2_gllists[name])

def draw_end(end, end_type):
    """
    Draws an open end on every stick and joint.
    Warning: only works for orthogonal joints.
    """

    # Transform the end
    glPushMatrix()
    glTranslatef(end[0][0], end[0][1], end[0][2])
    vout = end[0] - end[1]
    vup = end[0] - end[2]
    align_trans = [[np.array([1.0, 0.0, 0.0]), (90.0, 0.0, 1.0, 0.0), np.array([0.0, 0.0, 1.0])],
                   [np.array([-1.0, 0.0, 0.0]), (-90.0, 0.0, 1.0, 0.0), np.array([0.0, 0.0, 1.0])],
                   [np.array([0.0, 1.0, 0.0]), (-90.0, 1.0, 0.0, 0.0), np.array([1.0, 0.0, 0.0])],
                   [np.array([0.0, -1.0, 0.0]), (90.0, 1.0, 0.0, 0.0), np.array([1.0, 0.0, 0.0])],
                   [np.array([0.0, 0.0, 1.0]), (0.0, 1.0, 0.0, 0.0), np.array([1.0, 0.0, 0.0])],
                   [np.array([0.0, 0.0, -1.0]), (180.0, 1.0, 0.0, 0.0), np.array([1.0, 0.0, 0.0])]]
    for align_tran in align_trans:
        if np.allclose(vout, align_tran[0], atol=base_pieces.xabstol):
            ap = align_tran[1]
            sv = align_tran[2]
            break
    glRotatef(ap[0], ap[1], ap[2], ap[3])
    if np.allclose(sv, abs(vup), atol=base_pieces.xabstol):
        glRotatef(90.0, 0.0, 0.0, 1.0)
    #glScalef(sf, sf, sf)

    # Draw the end

    if end_type == 's':
        xw = 6.4*sf/2 # width/2
        xt = 1.6*sf/2 # thickness/2
        xl = 4.4*sf # length
        #xsection = np.array([[-xw, xt], [-xt, xt], [-xt, xw], [xt, xw], [xt, xt], [xw, xt], [xw, -xt], [xt, -xt], [xt, -xw], [-xt, -xw], [-xt, -xt], [-xw, -xt]])
        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-xw, xt, 0.0)
        glVertex3f(-xw, xt, xl)
        glVertex3f(-xt, xt, xl)
        glVertex3f(-xt, xt, 0.0)

        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(-xt, xt, 0.0)
        glVertex3f(-xt, xt, xl)
        glVertex3f(-xt, xw, xl)
        glVertex3f(-xt, xw, 0.0)

        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-xt, xw, 0.0)
        glVertex3f(-xt, xw, xl)
        glVertex3f(xt, xw, xl)
        glVertex3f(xt, xw, 0.0)

        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(xt, xw, 0.0)
        glVertex3f(xt, xw, xl)
        glVertex3f(xt, xt, xl)
        glVertex3f(xt, xt, 0.0)

        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(xt, xt, 0.0)
        glVertex3f(xt, xt, xl)
        glVertex3f(xw, xt, xl)
        glVertex3f(xw, xt, 0.0)

        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(xw, xt, 0.0)
        glVertex3f(xw, xt, xl)
        glVertex3f(xw, -xt, xl)
        glVertex3f(xw, -xt, 0.0)

        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(xw, -xt, 0.0)
        glVertex3f(xw, -xt, xl)
        glVertex3f(xt, -xt, xl)
        glVertex3f(xt, -xt, 0.0)

        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(xt, -xt, 0.0)
        glVertex3f(xt, -xt, xl)
        glVertex3f(xt, -xw, xl)
        glVertex3f(xt, -xw, 0.0)

        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(xt, -xw, 0.0)
        glVertex3f(xt, -xw, xl)
        glVertex3f(-xt, -xw, xl)
        glVertex3f(-xt, -xw, 0.0)

        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(-xt, -xw, 0.0)
        glVertex3f(-xt, -xw, xl)
        glVertex3f(-xt, -xt, xl)
        glVertex3f(-xt, -xt, 0.0)

        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-xt, -xt, 0.0)
        glVertex3f(-xt, -xt, xl)
        glVertex3f(-xw, -xt, xl)
        glVertex3f(-xw, -xt, 0.0)

        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(-xw, -xt, 0.0)
        glVertex3f(-xw, -xt, xl)
        glVertex3f(-xw, xt, xl)
        glVertex3f(-xw, xt, 0.0)

        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(-xw, -xt, xl)
        glVertex3f(-xw, xt, xl)
        glVertex3f(xw, xt, xl)
        glVertex3f(xw, -xt, xl)
        glVertex3f(-xt, -xw, xl)
        glVertex3f(-xt, xw, xl)
        glVertex3f(xt, xw, xl)
        glVertex3f(xt, -xw, xl)
        glEnd()

    elif end_type == 'j':
        w = 2.8*sf
        rad = 5.5*sf
        glePolyCylinder( ((0.0, 0.0, -1.0-w), (0.0, 0.0, -w),
                          (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                         None, rad)

    else:
        print 'Unknown end type', end_type
        
    glPopMatrix()

def draw_pipe(ro, ri, h, num_sections = 16):
    """
    Draws a hollowed cylinder centered at (0,0,0) extending in the z-direction
    """
    da = 2*math.pi / num_sections
    angles = np.arange(0.0, 2*math.pi + da/2, da)
    pts = np.transpose([np.cos(angles), np.sin(angles)])
    outer_edge = ro*pts
    inner_edge = ri*pts
    xsection = np.concatenate((outer_edge,
                               inner_edge[::-1],
                               [outer_edge[0]]))
    normal = np.concatenate((pts, -pts[::-1], [pts[0]])).tolist()
    xsection = xsection.tolist()
    gleExtrusion(xsection, normal, (0.0, 1.0, 0.0), ((0.0, 0.0, -h/2-1.0), (0.0, 0.0, -h/2), (0.0, 0.0, h/2), (0.0, 0.0, h/2+1.0)), None)
    return inner_edge

def draw_hub(cored = 0):
    """
    Draws a joint hub.  Uses a stitch line to make holes.
    """

    # Pipe
    inner_edge = draw_pipe(5.4*sf, 3.8*sf, 8.4*sf)

    # Cylinder
    bottom = -3.3*sf
    if cored == 0:
        top = 3.3*sf
    else:
        top = -1.9*sf
    glePolyCylinder( ((0.0, 0.0, bottom-1.0),
                      (0.0, 0.0, bottom),
                      (0.0, 0.0, top),
                      (0.0, 0.0, top+1.0)), None, 4.0*sf)

    # Core
    if cored:
        bottom = top
        top = 3.3*sf
        ls = 1.2*sf
        ll = 2.4*sf
        cross = [(ll, ls), (ll, -ls), (ls, -ls), (ls, -ll),
                 (-ls, -ll), (-ls, -ls), (-ll, -ls), (-ll, ls),
                 (-ls, ls), (-ls, ll), (ls, ll), (ls, ls), (ll, ls)]
        xsection = np.concatenate((inner_edge,
                                   cross,
                                   [inner_edge[0]]))
        
        normal = []
        for count in range(1, len(xsection)):
            dir = vector_math.normalize(xsection[count] - xsection[count-1])
            normal.append((dir[1], -dir[0]))
        normal.append(normal[0])
        xsection = xsection.tolist()
        gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
        gleExtrusion(xsection, normal, (0.0, 1.0, 0.0), ((0.0, 0.0, bottom-1.0), (0.0, 0.0, bottom), (0.0, 0.0, top), (0.0, 0.0, top+1.0)), None)
        gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)

def draw_gear(name, offset, orientation = 1):
    """
    Draws a gear
    """

    if name[0] == '-':
        name = name[1:]
        orientation = -orientation
    gear_outlines = {
        'gear1': (11.7*sf, 8.0*sf, 12),
        'gear2s': (8.0*sf, 5.5*sf, 12),
        'gear2l': (14.2*sf, 11.7*sf, 24),
        'gear3s': (6.0*sf, 4.1*sf, 12),
        'gear3l': (15.8*sf, 13.7*sf, 36),
        'gear_rack_spur': (12.3*sf, 9.3*sf, 16),
        'gear_bevel': (11.7*sf, 8.0*sf, 12)}
    ra, rd, num_teeth = gear_outlines[name]
    aa = np.arange(2*math.pi/(2.0*num_teeth), 2*math.pi, 2*math.pi/num_teeth)
    ad = np.arange(0.0, 2*math.pi*(1+1.0/(2.0*num_teeth)), 2*math.pi/num_teeth)
    xsection = []
    for count in range(len(aa)):
        xsection.append(rd*np.array([math.cos(ad[count]), math.sin(ad[count])]))
        xsection.append(ra*np.array([math.cos(aa[count]), math.sin(aa[count])]))
    xsection = np.array(xsection)
    normal = []
    for count in range(1, len(xsection)):
        dir = vector_math.normalize(xsection[count] - xsection[count-1])
        normal.append((dir[1], -dir[0]))
    #normal.insert(0, normal[-1])
    normal.append(normal[0])
    xsection = xsection.tolist()

    if detail == 1 or name in ['gear2s', 'gear2l', 'gear_rack_spur']:
        gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
        if name == 'gear_bevel':
            gear_rad = (ra + rd)/2
            gear_width = 3.5*sf
            scale = (gear_rad - gear_width) / gear_rad
            if orientation > 0:
                scale1 = 1.0
                scale2 = scale
            else:
                scale1 = scale
                scale2 = 1.0
            gleSuperExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((offset-gear_width/2-1.0, 0.0, 0.0), (offset-gear_width/2, 0.0, 0.0), (offset+gear_width/2, 0.0, 0.0), (offset+gear_width/2+1.0, 0.0, 0.0)), None, (((scale1, 0.0, 0.0), (0.0, scale1, 0.0)), ((scale1, 0.0, 0.0), (0.0, scale1, 0.0)), ((scale2, 0.0, 0.0), (0.0, scale2, 0.0)), ((scale2, 0.0, 0.0), (0.0, scale2, 0.0))))
        else:
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((offset-gearw/2-1.0, 0.0, 0.0), (offset-gearw/2, 0.0, 0.0), (offset+gearw/2, 0.0, 0.0), (offset+gearw/2+1.0, 0.0, 0.0)), None)
        gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)

    elif detail == 2:
        glPushMatrix()
        glTranslatef(offset, 0.0, 0.0)
        if orientation < 0:
            glRotatef(180.0, 0.0, 0.0, 1.0)
        if name == 'gear_bevel':
            glRotatef(90.0, 0.0, 1.0, 0.0)
        else:
            glRotatef(90.0, 0.0, 1.0, 0.0)
        draw_drawing(name)
        glPopMatrix()

def draw_wheel(name, offset, orientation = 1, rotation = 0.0):
    """
    Draws a wheel and tire
    """

    wheel_outlines = {
        'wheelp5': (14.0*sf, 3.0*sf),
        'wheel1': (32.4*sf, 3.0*sf)}
    wheel_rad, thickness = wheel_outlines[name]

    glPushMatrix()
    glTranslatef(offset, 0.0, 0.0)
    glRotatef(rotation, 1.0, 0.0, 0.0)
    if orientation < 0:
        glRotatef(180.0, 0.0, 0.0, 1.0)
    glRotatef(90.0, 0.0, 1.0, 0.0)

    if detail == 1:
        # Hub
        glePolyCylinder( ((0.0, 0.0, -wheelw/2-1.0),
                          (0.0, 0.0, -wheelw/2),
                          (0.0, 0.0, wheelw/2+wheels),
                          (0.0, 0.0, wheelw/2+wheels+1.0)),
                         None, 5.2*sf)

        # Rim
        draw_pipe(wheel_rad-2.0*sf, wheel_rad-5.0*sf, wheelw-0.2*sf)
        
        # Spokes
        if name == 'wheelp5':
            num_spokes = 4
        else: # wheel1
            num_spokes = 8
        w = 2.0*sf
        h = wheelw-0.2*sf
        xsection = [(w/2, h/2), (-w/2, h/2), (-w/2, -h/2), (w/2, -h/2), (w/2, h/2)]
        normal = [(0.0, 1.0), (-1.0, 0.0), (0.0, -1.0), (1.0, 0.0), (0.0, 1.0)]
        da = 2*math.pi / num_spokes
        angles = np.arange(0.0, 2*math.pi - da/2, da)
        gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
        for angle in angles:
            glPushMatrix()
            glRotatef(math.degrees(angle), 0.0, 0.0, 1.0)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (wheel_rad-2.0*sf, 0.0, 0.0), (wheel_rad-2.0*sf + 1.0, 0.0, 0.0)), None)
            glPopMatrix()

        # Webbing
        if name == 'wheelp5':
            glePolyCylinder( ((0.0, 0.0, -w/2-1.0),
                              (0.0, 0.0, -w/2),
                              (0.0, 0.0, w/2),
                              (0.0, 0.0, w/2+1.0)),
                             None, wheel_rad-2.0*sf)
        else: # wheel1
            h = w
            w = 6.0*sf
            xsection = [(w/2, h/2), (-w/2, h/2), (-w/2, -h/2), (w/2, -h/2), (w/2, h/2)]
            for angle in angles:
                glPushMatrix()
                glRotatef(math.degrees(angle), 0.0, 0.0, 1.0)
                gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (wheel_rad-2.0*sf, 0.0, 0.0), (wheel_rad-2.0*sf + 1.0, 0.0, 0.0)), None)
                glPopMatrix()
            draw_pipe(wheel_rad-5.0*sf, wheel_rad-5.0*sf - w, h)

        gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
        
        # Tire
        glColor3fv(colors['tire'])
        draw_pipe(wheel_rad, wheel_rad-3.0*sf, wheelw)

    elif detail == 2:
        wheel_type = name[5:]
        draw_drawing('wheel' + wheel_type)
        draw_drawing('tire' + wheel_type, colors['tire'])

    glPopMatrix()

def draw_clipxp(color):
    """
    Draws a clip at x+
    """
    if color == None:
        color = colors['clip']
    glPushMatrix()
    glRotatef(90.0, 0.0, 0.0, 1.0)
    glTranslatef(0.0, -(join_len+0.05*sf), 0.0)
    glRotatef(90.0, 1.0, 0.0, 0.0)
    draw_drawing('clip', color)
    glPopMatrix()

def draw_clipxm(color):
    """
    Draws a clip at x-
    """
    if color == None:
        color = colors['clip']
    glPushMatrix()
    glRotatef(-90.0, 0.0, 0.0, 1.0)
    glTranslatef(0.0, -(join_len+0.05*sf), 0.0)
    glRotatef(90.0, 1.0, 0.0, 0.0)
    draw_drawing('clip', color)
    glPopMatrix()

def draw_clipyp(color):
    """
    Draws a clip at y+
    """
    if color == None:
        color = colors['clip']
    glPushMatrix()
    glRotatef(180.0, 0.0, 0.0, 1.0)
    glTranslatef(0.0, -(join_len+0.05*sf), 0.0)
    glRotatef(90.0, 1.0, 0.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    draw_drawing('clip', color)
    glPopMatrix()

def draw_clipym(color):
    """
    Draws a clip at y-
    """
    if color == None:
        color = colors['clip']
    glPushMatrix()
    glTranslatef(0.0, -(join_len+0.05*sf), 0.0)
    glRotatef(90.0, 1.0, 0.0, 0.0)
    glRotatef(90.0, 0.0, 0.0, 1.0)
    draw_drawing('clip', color)
    glPopMatrix()

def draw_clipzp(color):
    """
    Draws a clip at z+
    """
    if color == None:
        color = colors['clip']
    glPushMatrix()
    glTranslatef(0.0, 0.0, join_len+0.05*sf)
    draw_drawing('clip', color)
    glPopMatrix()

def draw_clipzm(color):
    """
    Draws a clip at z-
    """
    if color == None:
        color = colors['clip']
    glPushMatrix()
    glRotatef(180.0, 1.0, 0.0, 0.0)
    glTranslatef(0.0, 0.0, join_len+0.05*sf)
    draw_drawing('clip', color)
    glPopMatrix()

# The Pieces    
class stick(base_pieces.piece):
    """
    A base class for all sticks
    """
    def draw_ends(self):
        for end, end_type in zip(self.unaligned_ends, self.ends_types):
            draw_end(end, end_type)

class straightp5(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[lenp5s, 0.0, 0.0],
                                [lenp5s-1.0, 0.0, 0.0],
                                [lenp5s, 0.0, -1.0]]])
    ends_types = ['s', 's']

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['straight'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (lenp5s, 0.0, 0.0), (lenp5s+1.0, 0.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            length = 0.5*len1 - 2*join_len
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('straightp5')

class straight1(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len1s, 0.0, 0.0],
                                [len1s-1.0, 0.0, 0.0],
                                [len1s, 0.0, -1.0]]])
    ends_types = ['s', 's']
    icon_extent = 4.0

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['straight'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (len1s, 0.0, 0.0), (len1s+1.0, 0.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            length = len1 - 2*join_len
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('straight1')

class axle(stick):
    """
    A base class for axles
    """

    def inset_files(self):
        retval = self.name
        for config in self.configure:
            if config != 'None':
                retval = retval + config
        return retval

    def label(self):
        retval = [self.name]
        for config in self.configure:
            name = self.configure_name(config)[0]
            if name != 'None':
                retval.append(name)
        return retval

class straight1m1(axle):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len1s-panel_space, 0.0, 0.0],
                                [len1s-panel_space-1.0, 0.0, 0.0],
                                [len1s-panel_space, 0.0, -1.0]]])
    ends_types = ['s', 's']
    icon_extent = 3.0
    detail1 = 'Separate'

    query_options = [['Position 1', gear_list]]

    def help_text(self):
        if self.configure[0] == 'None':
            return ''
        else:
            return 'Slide ' + aliases['straight1m1'] + ' through ' + aliases[self.configure[0]] + ' and join.  Make hub face joint.'

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['straight'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        thickness = 6.7*sf
        width = 2.4*sf
        if detail == 1:
            glePolyCylinder( ((0.5*(len1s-panel_space-width)-1.0, 0.0, 0.0),
                              (0.5*(len1s-panel_space-width), 0.0, 0.0),
                              (len1s-panel_space, 0.0, 0.0),
                              (len1s-panel_space+1.0, 0.0, 0.0)),
                             None, base_rad)
            xsection = [[-base_rad, 0.0], [-base_rad, 0.0], [base_rad, 0.0], [base_rad, 0.0], [base_rad, thickness], [base_rad, thickness], [-base_rad, thickness], [-base_rad, thickness]]
            normal = [[-1.0, 0.0], [0.0, -1.0], [0.0, -1.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [-1.0, 0.0]]
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), (((len1s-panel_space)/2-width/2-1.0, 0.0, 0.0), ((len1s-panel_space)/2-width/2, 0.0, 0.0), ((len1s-panel_space)/2+width/2, 0.0, 0.0), ((len1s-panel_space/2+width/2+1.0, 0.0, 0.0))), None)
            side_len = 3.2*sf
            divrt2 = 1.0/math.sqrt(2.0)
            xsection = [[side_len, 0.0], [0.0, side_len], [-side_len, 0.0], [0.0, -side_len]]
            normal = [[divrt2, divrt2], [-divrt2, divrt2], [-divrt2, -divrt2], [divrt2, -divrt2]]
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0),
                         ((-1.0, 0.0, 0.0),
                          (0.0, 0.0, 0.0),
                          (0.5*(len1s-panel_space), 0.0, 0.0),
                          (0.5*(len1s-panel_space)+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            self.draw_ends()
        elif detail == 2:
            length = len1 - panel_space - 2*join_len
            
            glPushMatrix()
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('straight1m1')
            glPopMatrix()

        if self.configure[0] not in ['None', 'spacer']:
            draw_gear(self.configure[0], gearw/2, 1)

class straight1p5(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len1p5s, 0.0, 0.0],
                                [len1p5s-1.0, 0.0, 0.0],
                                [len1p5s, 0.0, -1.0]]])
    ends_types = ['s', 's']

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['straight'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (len1p5s, 0.0, 0.0), (len1p5s+1.0, 0.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            length = 1.5*len1 - 2*join_len
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('straight1p5')

class straight2(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len2s, 0.0, 0.0],
                                [len2s-1.0, 0.0, 0.0],
                                [len2s, 0.0, -1.0]]])
    ends_types = ['s', 's']

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['straight'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (len2s, 0.0, 0.0), (len2s+1.0, 0.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            length = 2*len1 - 2*join_len
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('straight2')

class anglep5xp5(stick):

    unaligned_ends = np.array([[[0.0, lenh1h, 0.0],
                                [1.0, lenh1h, 0.0],
                                [0.0, lenh1h, 1.0]],
                               [[lenh1h, 0.0, 0.0],
                                [lenh1h, 1.0, 0.0],
                                [lenh1h, 0.0, 1.0]]])
    ends_types = ['s', 's']
    icon_view = 'back'
    icon_extent = 3.0

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['angle'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, lenh1h, 0.0), (0.0, lenh1h, 0.0),
                              (stick_hold, lenh1h, 0.0),
                              (lenh1h, stick_hold, 0.0),
                              (lenh1h, 0.0, 0.0), (lenh1h, 0.0-1.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            offset = 0.5*len1 - join_len
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('anglep5xp5')

class angle1x1(stick):

    unaligned_ends = np.array([[[0.0, len1h, 0.0],
                                [1.0, len1h, 0.0],
                                [0.0, len1h, 1.0]],
                               [[len1h, 0.0, 0.0],
                                [len1h, 1.0, 0.0],
                                [len1h, 0.0, 1.0]]])
    ends_types = ['s', 's']
    icon_view = 'back'

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['angle'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, len1h, 0.0), (0.0, len1h, 0.0),
                              (stick_hold, len1h, 0.0),
                              (len1h, stick_hold, 0.0),
                              (len1h, 0.0, 0.0), (len1h, 0.0-1.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            offset = 1.0*len1 - join_len
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('angle1x1')

class angle1xp5(stick):

    unaligned_ends = np.array([[[0.0, lenh1h, 0.0],
                                [1.0, lenh1h, 0.0],
                                [0.0, lenh1h, 1.0]],
                               [[len1h, 0.0, 0.0],
                                [len1h, 1.0, 0.0],
                                [len1h, 0.0, 1.0]]])
    ends_types = ['s', 's']
    icon_view = 'back'
    icon_extent = 6.0

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['angle'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, lenh1h, 0.0), (0.0, lenh1h, 0.0),
                              (base_rad*0.31, lenh1h, 0.0),
                              (len1h, base_rad*0.7, 0.0),
                              (len1h, 0.0, 0.0), (len1h, 0.0-1.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            offset = 1.0*len1 - join_len
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('angle1xp5')

class angle1p5x1p5(stick):

    unaligned_ends = np.array([[[0.0, len1p5h, 0.0],
                                [1.0, len1p5h, 0.0],
                                [0.0, len1p5h, 1.0]],
                               [[len1p5h, 0.0, 0.0],
                                [len1p5h, 1.0, 0.0],
                                [len1p5h, 0.0, 1.0]]])
    ends_types = ['s', 's']
    icon_view = 'back'
    icon_extent = 9.5

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['angle'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, len1p5h, 0.0), (0.0, len1p5h, 0.0),
                              (stick_hold, len1p5h, 0.0),
                              (len1p5h, stick_hold, 0.0),
                              (len1p5h, 0.0, 0.0), (len1p5h, 0.0-1.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            offset = 1.5*len1 - join_len
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('angle1p5x1p5')

class angle2x1(stick):

    unaligned_ends = np.array([[[0.0, len1h, 0.0],
                                [1.0, len1h, 0.0],
                                [0.0, len1h, 1.0]],
                               [[len2h, 0.0, 0.0],
                                [len2h, 1.0, 0.0],
                                [len2h, 0.0, 1.0]]])
    ends_types = ['s', 's']
    icon_view = 'back'
    icon_extent = 11.5

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['angle'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, len1h, 0.0), (0.0, len1h, 0.0),
                              (base_rad*0.31, len1h, 0.0),
                              (len2h, base_rad*0.7, 0.0),
                              (len2h, 0.0, 0.0), (len2h, 0.0-1.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            offset = 2*len1 - join_len
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('angle2x1')

class angle2x2(stick):

    unaligned_ends = np.array([[[0.0, len2h, 0.0],
                                [1.0, len2h, 0.0],
                                [0.0, len2h, 1.0]],
                               [[len2h, 0.0, 0.0],
                                [len2h, 1.0, 0.0],
                                [len2h, 0.0, 1.0]]])
    ends_types = ['s', 's']
    icon_view = 'back'
    icon_extent = 11.5

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['angle'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, len2h, 0.0), (0.0, len2h, 0.0),
                              (stick_hold, len2h, 0.0),
                              (len2h, stick_hold, 0.0),
                              (len2h, 0.0, 0.0), (len2h, 0.0-1.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            offset = 2*len1 - join_len
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('angle2x2')

class arc1x1(stick):

    # ends format is (end point, (coming from)
    unaligned_ends = np.array([[[len1h, 0.0, 0.0],
                                [len1h, 1.0, 0.0],
                                [len1h, 0.0, 1.0]],
                               [[0.0, len1h, 0.0],
                                [1.0, len1h, 0.0],
                                [0.0, len1h, 1.0]]])
    unaligned_center = np.array([len1h*math.cos(math.pi/4.0), len1h*math.sin(math.pi/4.0), 0.0])
    ends_types = ['s', 's']
    icon_view = 'back'

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['arc'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        a = len1
        b = len1
        coords = []
        start_index = int((2.0*math.asin(join_len/a)/math.pi)*len(circle_coords))+1
        end_index = len(circle_coords) - int((2.0*math.asin(join_len/b)/math.pi)*len(circle_coords))-1
        lsf = 1.0/circle_coords[start_index][0]
        for coord in circle_coords[start_index:end_index]:
            coords.append((lsf*a*coord[0]-join_len, lsf*b*coord[1]-join_len, coord[2]))
        coords.insert(0, (a-join_len, 0.0, 0.0))
        coords.append((0.0, b-join_len, 0.0))

        if detail == 1:
            coords.insert(0, (a-join_len, 0.0-1.0, 0.0))
            coords.append((0.0-1.0, b-join_len, 0.0))
            glePolyCylinder(tuple(coords), None, base_rad)
            self.draw_ends()
        elif detail == 2:
            offset = 1.0*len1 - join_len
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('arc1x1')

class arc1p5x1p5(stick):

    # ends format is (end point, (coming from)
    unaligned_ends = np.array([[[len1p5h, 0.0, 0.0],
                                [len1p5h, 1.0, 0.0],
                                [len1p5h, 0.0, 1.0]],
                               [[0.0, len1p5h, 0.0],
                                [1.0, len1p5h, 0.0],
                                [0.0, len1p5h, 1.0]]])
    unaligned_center = np.array([len1p5h*math.cos(math.pi/4.0), len1p5h*math.sin(math.pi/4.0), 0.0])
    ends_types = ['s', 's']
    icon_view = 'back'
    icon_extent = 9.5

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['arc'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        a = len1p5
        b = len1p5
        coords = []
        start_index = int((2.0*math.asin(join_len/a)/math.pi)*len(circle_coords))+1
        end_index = len(circle_coords) - int((2.0*math.asin(join_len/b)/math.pi)*len(circle_coords))-1
        lsf = len1p5/(a*circle_coords[start_index][0])
        for coord in circle_coords[start_index:end_index]:
            coords.append((lsf*a*coord[0]-join_len, lsf*b*coord[1]-join_len, coord[2]))
        coords.insert(0, (len1p5h, 0.0, 0.0))
        coords.append((0.0, len1p5h, 0.0))

        if detail == 1:
            coords.insert(0, (len1p5h, 0.0-1.0, 0.0))
            coords.append((0.0-1.0, len1p5h, 0.0))
            glePolyCylinder(tuple(coords), None, base_rad)
            self.draw_ends()
        elif detail == 2:
            offset = 1.5*len1 - join_len
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('arc1p5x1p5')

class arc2x1(stick):

    # ends format is (end point, (coming from)
    unaligned_ends = np.array([[[0.0, len1h, 0.0],
                                [1.0, len1h, 0.0],
                                [0.0, len1h, 1.0]],
                               [[len2h, 0.0, 0.0],
                                [len2h, 1.0, 0.0],
                                [len2h, 0.0, 1.0]]])
    unaligned_center = np.array([len2h*math.cos(math.pi/4.0), len1h*math.sin(math.pi/4.0), 0.0])
    ends_types = ['s', 's']
    icon_view = 'back'
    icon_extent = 11.5

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['arc'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        a = len2
        b = len1
        coords = []
        start_index = int((2.0*math.asin(join_len/b)/math.pi)*len(circle_coords))+1
        end_index = len(circle_coords) - int((2.0*math.asin(join_len/a)/math.pi)*len(circle_coords))-1
        lsfa = len2/(a*circle_coords[start_index][0])
        lsfb = len1/(b*circle_coords[end_index-1][1])
        for coord in circle_coords[start_index:end_index]:
            coords.append((lsfa*a*coord[0]-join_len, lsfb*b*coord[1]-join_len, coord[2]))
        if detail == 1:
            coords.insert(0, (len2h, 0.0, 0.0))
            coords.insert(0, (len2h, 0.0-1.0, 0.0))
            coords.append((0.0, len1h, 0.0))
            coords.append((0.0-1.0, len1h, 0.0))
            glePolyCylinder(tuple(coords), None, base_rad)
            self.draw_ends()
        elif detail == 2:
            offset = 2*len1 - join_len
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('arc2x1')

class arc2x2(stick):

    # ends format is (end point, (coming from)
    unaligned_ends = np.array([[[len2h, 0.0, 0.0],
                                [len2h, 1.0, 0.0],
                                [len2h, 0.0, 1.0]],
                               [[0.0, len2h, 0.0],
                                [1.0, len2h, 0.0],
                                [0.0, len2h, 1.0]]])
    unaligned_center = np.array([len2h*math.cos(math.pi/4.0), len2h*math.sin(math.pi/4.0), 0.0])
    ends_types = ['s', 's']
    icon_view = 'back'
    icon_extent = 11.5

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['arc'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        a = len2
        b = len2
        coords = []
        start_index = int((2.0*math.asin(join_len/a)/math.pi)*len(circle_coords))+1
        end_index = len(circle_coords) - int((2.0*math.asin(join_len/b)/math.pi)*len(circle_coords))-1
        lsf = len2/(a*circle_coords[start_index][0])
        for coord in circle_coords[start_index:end_index]:
            coords.append((lsf*a*coord[0]-join_len, lsf*b*coord[1]-join_len, coord[2]))
        if detail == 1:
            coords.insert(0, (len2h, 0.0, 0.0))
            coords.insert(0, (len2h, 0.0-1.0, 0.0))
            coords.append((0.0, len2h, 0.0))
            coords.append((0.0-1.0, len2h, 0.0))
            glePolyCylinder(tuple(coords), None, base_rad)
            self.draw_ends()
        elif detail == 2:
            offset = 2*len1 - join_len
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('arc2x2')

class gear_axle1s(axle):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]]])
    unaligned_center = np.array([gearw/2, 0.0, 0.0])
    ends_types = ['s']
    side_len = 3.2*sf
    divrt2 = 1.0/math.sqrt(2.0)
    xsection = [[side_len, 0.0], [0.0, side_len], [-side_len, 0.0], [0.0, -side_len]]
    normal = [[divrt2, divrt2], [-divrt2, divrt2], [-divrt2, -divrt2], [divrt2, -divrt2]]
    detail1 = 'Separate'

    query_options = [['Position 1', gear_list]]

    def help_text(self):
        if self.configure[0] == 'None':
            return ''
        else:
            return 'Slide ' + aliases['gear_axle1s'] + ' through ' + aliases[self.configure[0]] + ' and join.  Make hub face joint.'

    def shape(self, color = None): 

        stub_len = 1.6*sf
        if detail == 1:
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(self.xsection, self.normal, (0.0, 0.0, 1.0), ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            glePolyCylinder( ((gearw-1.0, 0.0, 0.0), (gearw, 0.0, 0.0),
                              (gearw+stub_len, 0.0, 0.0), (gearw+stub_len+1.0, 0.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            draw_drawing('gear_axle1s')
            glPopMatrix()

        if self.configure[0] not in ['None', 'spacer']:
            if color == None:
                glColor3fv(colors['gear'])
            draw_gear(self.configure[0], gearw/2, 1)

class gear_axle2s(axle):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len1s, 0.0, 0.0],
                                [len1s-1.0, 0.0, 0.0],
                                [len1s, 0.0, -1.0]]])
    ends_types = ['s', 's']
    side_len = 3.2*sf
    divrt2 = 1.0/math.sqrt(2.0)
    xsection = [[side_len, 0.0], [0.0, side_len], [-side_len, 0.0], [0.0, -side_len]]
    normal = [[divrt2, divrt2], [-divrt2, divrt2], [-divrt2, -divrt2], [divrt2, -divrt2]]
    icon_extent = 4.0

    detail1 = 'Separate'

    query_options = [['Position 1', gear_list], ['Position 2', gear_list]]

    def inset_files(self):
        if self.configure[0] == 'None' and self.configure[1] == 'None':
            return ''
        else:
            return (self.name + self.configure[0], self.name + self.configure[1])

    def help_text(self):
        if self.configure[0] == 'None' and self.configure[1] == 'None':
            return ''
        elif self.configure[0] == 'None':
            return 'Slide ' + aliases['gear_axle2s'] + ' through ' + aliases[self.configure[1]] + ' and join.  Make hub face joint.'
        elif self.configure[1] == 'None':
            return 'Slide ' + aliases['gear_axle2s'] + ' through ' + aliases[self.configure[0]] + ' and join.  Make hub face joint.'
        else:
            return 'Slide ' + aliases['gear_axle2s'] + ' through ' + aliases[self.configure[0]] + ' and ' + aliases[self.configure[1]] + ' and join.  Make hub face joint.'

    def shape(self, color = None): 

        if detail == 1:
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(self.xsection, self.normal, (0.0, 0.0, 1.0), ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)), None)
            gleExtrusion(self.xsection, self.normal, (0.0, 0.0, 1.0), ((len1s-gearw-1.0, 0.0, 0.0), (len1s-gearw, 0.0, 0.0), (len1s, 0.0, 0.0), (len1s+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            glePolyCylinder( ((gearw-1.0, 0.0, 0.0), (gearw, 0.0, 0.0),
                              (len1s-gearw, 0.0, 0.0), (len1s-gearw+1.0, 0.0, 0.0)),
                             None, base_rad)
            self.draw_ends()
        elif detail == 2:
            length = len1 - 2*join_len

            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('gear_axle2s')
            glPopMatrix()

        offsets = (gearw/2, len1s - gearw/2)
        for count, option in enumerate(self.configure):
            if option not in ['None', 'spacer']:
                draw_gear(self.configure[count], offsets[count], 1-2*count)

class join1(stick):

    jlen = 6.0*sf
    unaligned_ends = np.array([[[jlen, 0.0, 0.0],
                                [jlen-1.0, 0.0, 0.0],
                                [jlen, -1.0, 0.0]]])
    unaligned_center = np.array([0.0, 0.0, 0.0])
    ends_types = ['j']
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    def shape(self, color = None): 
        
        if detail == 1:
            glePolyCylinder( ((self.jlen+1.0, 0.0, 0.0), (self.jlen, 0.0, 0.0),
                              (0.0, 0.0, 0.0), (0.0-1.0, 0.0, 0.0)),
                             None, base_rad)
            gluSphere(gluNewQuadric(), base_rad, 16, 16)
            self.draw_ends()

        elif detail == 2:
            offset = 6.0*sf

            glPushMatrix()
            glTranslatef(offset, 0.0, 0.0)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            draw_drawing('join1')
            glPopMatrix()

            glPushMatrix()
            glRotatef(90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, -(offset+0.05*sf), 0.0)
            glRotatef(90.0, 1.0, 0.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            if not color:
                color = colors['clip']
            draw_drawing('clip', color)
            glPopMatrix()

class join2(stick):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]]])
    unaligned_center = np.array([0.0, 0.0, 0.0])
    ends_types = ['j', 'j']
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    def shape(self, color = None): 
        
        if detail == 1:
            #glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
            #                  (0.0, 0.0, 0.0), (0.0, join_len, 0.0),
            #                  (0.0, join_len+1.0, 0.0)), None, base_rad)
            #glePolyCylinder( ((0.0, 0.0, base_rad+1.0), (0.0, 0.0, base_rad),
            #                  (0.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
            #                 None, base_rad)
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0),
                              (join_len, 0.0, 0.0),
                              (join_ext, 0.0, 0.0),
                              (join_ext-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, join_len+1.0, 0.0),
                              (0.0, join_len, 0.0),
                              (0.0, join_ext, 0.0),
                              (0.0, join_ext-1.0, 0.0)), None, base_rad)
            draw_hub(cored = 1)
            self.draw_ends()

        elif detail == 2:

            glPushMatrix()
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('join3')
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)

class join2flat(stick):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]]])
    unaligned_center = np.array([0.0, 0.0, 0.0])
    ends_types = ['j', 'j']
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    def shape(self, color = None, locked = 1): 

        if detail == 1:
            glePolyCylinder( ((-join_len-1.0, 0.0, 0.0), (-join_len, 0.0, 0.0),
                              (join_len, 0.0, 0.0), (join_len+1.0, 0.0, 0.0)),
                             None, base_rad)
            self.draw_ends()

        elif detail == 2:
            draw_drawing('join2flat')
            if not locked:
                glRotatef(-45.0, 1.0, 0.0, 0.0)
            draw_clipxp(color)
            draw_clipxm(color)

class join3(stick):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[0.0, 0.0, join_len],
                                [0.0, 0.0, join_len-1.0],
                                [-1.0, 0.0, join_len]]])
    unaligned_center = np.array([0.0, 0.0, 0.0])
    ends_types = ['j', 'j', 'j']
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    def shape(self, color = None): 

        if detail == 1:
            #glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
            #                  (0.0, 0.0, 0.0), (0.0, join_len, 0.0),
            #                  (0.0, join_len+1.0, 0.0)), None, base_rad)
            #glePolyCylinder( ((0.0, 0.0, join_len+1.0), (0.0, 0.0, join_len),
            #                  (0.0, 0.0, -base_rad), (0.0, 0.0, -base_rad-1.0)), None, base_rad)
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0),
                              (join_len, 0.0, 0.0),
                              (join_ext, 0.0, 0.0),
                              (join_ext-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, join_len+1.0, 0.0),
                              (0.0, join_len, 0.0),
                              (0.0, join_ext, 0.0),
                              (0.0, join_ext-1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, 0.0, join_len+1.0),
                              (0.0, 0.0, join_len),
                              (0.0, 0.0, join_ext),
                              (0.0, 0.0, join_ext-1.0)), None, base_rad)
            draw_hub()
            self.draw_ends()

        elif detail == 2:

            glPushMatrix()
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('join3')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, base_rad)
            glRotatef(180.0, 1.0, 0.0, 0.0)
            draw_drawing('receive_m')
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)
            draw_clipzp(color)

class join3flat(stick):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]]])
    unaligned_center = np.array([0.0, 0.0, 0.0])
    ends_types = ['j', 'j', 'j']
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    def shape(self, color = None): 

        if detail == 1:
            #glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
            #                  (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)
            #glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
            #                  (0.0, 0.0, 0.0), (0.0, 0.0-1.0, 0.0)), None, base_rad)
            #glePolyCylinder( ((0.0, 0.0, 0.0-1.0), (0.0, 0.0, 0.0),
            #                  (0.0, 0.0, base_rad), (0.0, 0.0, base_rad+1.0)), None, base_rad)
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0),
                              (join_len, 0.0, 0.0),
                              (join_ext, 0.0, 0.0),
                              (join_ext-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((-join_len-1.0, 0.0, 0.0),
                              (-join_len, 0.0, 0.0),
                              (-join_ext, 0.0, 0.0),
                              (-join_ext+1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, join_len+1.0, 0.0),
                              (0.0, join_len, 0.0),
                              (0.0, join_ext, 0.0),
                              (0.0, join_ext-1.0, 0.0)), None, base_rad)
            draw_hub(cored = 1)
            self.draw_ends()

        elif detail == 2:

            glPushMatrix()
            glRotatef(180.0, 0.0, 0.0, 1.0)
            draw_drawing('join4')
            glPopMatrix()

            draw_clipxp(color)
            draw_clipxm(color)
            draw_clipyp(color)

class join4(stick):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[0.0, 0.0, join_len],
                                [0.0, 0.0, join_len-1.0],
                                [-1.0, 0.0, join_len]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]]])
    unaligned_center = np.array([0.0, 0.0, 0.0])
    ends_types = ['j', 'j', 'j', 'j']
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    def shape(self, color = None): 

        if detail == 1:
            #glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
            #                  (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)
            #glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
            #                  (0.0, 0.0, 0.0), (0.0, 0.0, join_len),
            #                  (0.0, 0.0, join_len+1.0)), None, base_rad)
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0),
                              (join_len, 0.0, 0.0),
                              (join_ext, 0.0, 0.0),
                              (join_ext-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((-join_len-1.0, 0.0, 0.0),
                              (-join_len, 0.0, 0.0),
                              (-join_ext, 0.0, 0.0),
                              (-join_ext+1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, join_len+1.0, 0.0),
                              (0.0, join_len, 0.0),
                              (0.0, join_ext, 0.0),
                              (0.0, join_ext-1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, 0.0, join_len+1.0),
                              (0.0, 0.0, join_len),
                              (0.0, 0.0, join_ext),
                              (0.0, 0.0, join_ext-1.0)), None, base_rad)
            draw_hub()
            self.draw_ends()

        elif detail == 2:

            glPushMatrix()
            glRotatef(180.0, 0.0, 0.0, 1.0)
            draw_drawing('join4')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, base_rad)
            glRotatef(180.0, 1.0, 0.0, 0.0)
            draw_drawing('receive_m')
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)
            draw_clipzp(color)
            draw_clipxm(color)

class join4flat(stick):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]],
                               [[0.0, -join_len, 0.0],
                                [0.0, -join_len+1.0, 0.0],
                                [0.0, -join_len, -1.0]]])
    unaligned_center = np.array([0.0, 0.0, 0.0])
    ends_types = ['j', 'j', 'j', 'j']
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    def shape(self, color = None): 

        if detail == 1:
            #glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
            #                  (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)
            #glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
            #                  (0.0, -join_len, 0.0), (0.0, -join_len-1.0, 0.0)), None, base_rad)
            #glePolyCylinder( ((0.0, 0.0, 0.0-1.0), (0.0, 0.0, 0.0),
            #                  (0.0, 0.0, base_rad), (0.0, 0.0, base_rad+1.0)), None, base_rad)
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0),
                              (join_len, 0.0, 0.0),
                              (join_ext, 0.0, 0.0),
                              (join_ext-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((-join_len-1.0, 0.0, 0.0),
                              (-join_len, 0.0, 0.0),
                              (-join_ext, 0.0, 0.0),
                              (-join_ext+1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, join_len+1.0, 0.0),
                              (0.0, join_len, 0.0),
                              (0.0, join_ext, 0.0),
                              (0.0, join_ext-1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, -join_len-1.0, 0.0),
                              (0.0, -join_len, 0.0),
                              (0.0, -join_ext, 0.0),
                              (0.0, -join_ext+1.0, 0.0)), None, base_rad)
            draw_hub(cored = 1)
            self.draw_ends()

        elif detail == 2:
            draw_drawing('join5')
            draw_clipxp(color)
            draw_clipxm(color)
            draw_clipyp(color)
            draw_clipym(color)

class join5(stick):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[0.0, 0.0, join_len],
                                [0.0, 0.0, join_len-1.0],
                                [-1.0, 0.0, join_len]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]],
                               [[0.0, -join_len, 0.0],
                                [0.0, -join_len+1.0, 0.0],
                                [0.0, -join_len, -1.0]]])
    unaligned_center = np.array([0.0, 0.0, 0.0])
    ends_types = ['j', 'j', 'j', 'j', 'j']
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    def shape(self, color = None): 

        if detail == 1:
            #glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
            #                  (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)
            #glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
            #                  (0.0, -join_len, 0.0), (0.0, -join_len-1.0, 0.0)), None, base_rad)
            #glePolyCylinder( ((0.0, 0.0, 0.0-1.0), (0.0, 0.0, 0.0),
            #                  (0.0, 0.0, join_len), (0.0, 0.0, join_len+1.0)), None, base_rad)
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0),
                              (join_len, 0.0, 0.0),
                              (join_ext, 0.0, 0.0),
                              (join_ext-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((-join_len-1.0, 0.0, 0.0),
                              (-join_len, 0.0, 0.0),
                              (-join_ext, 0.0, 0.0),
                              (-join_ext+1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, join_len+1.0, 0.0),
                              (0.0, join_len, 0.0),
                              (0.0, join_ext, 0.0),
                              (0.0, join_ext-1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, -join_len-1.0, 0.0),
                              (0.0, -join_len, 0.0),
                              (0.0, -join_ext, 0.0),
                              (0.0, -join_ext+1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, 0.0, join_len+1.0),
                              (0.0, 0.0, join_len),
                              (0.0, 0.0, join_ext),
                              (0.0, 0.0, join_ext-1.0)), None, base_rad)
            draw_hub()
            self.draw_ends()

        elif detail == 2:

            glPushMatrix()
            draw_drawing('join5')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, base_rad)
            glRotatef(180.0, 1.0, 0.0, 0.0)
            draw_drawing('receive_m')
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)
            draw_clipxm(color)
            draw_clipym(color)
            draw_clipzp(color)

class join6(stick):
    #Currently identical to joinrot4flat2

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[0.0, 0.0, join_len],
                                [0.0, 0.0, join_len-1.0],
                                [-1.0, 0.0, join_len]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]],
                               [[0.0, -join_len, 0.0],
                                [0.0, -join_len+1.0, 0.0],
                                [0.0, -join_len, -1.0]],
                               [[0.0, 0.0, -join_len],
                                [0.0, 0.0, -join_len+1.0],
                                [-1.0, 0.0, -join_len]]])
    unaligned_center = np.array([0.0, 0.0, 0.0])
    ends_types = ['j', 'j', 'j', 'j', 'j', 'j']
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    detail1 = 'Separate'

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
                              (0.0, -join_len, 0.0), (0.0, -join_len-1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, 0.0, -base_rad-1.0), (0.0, 0.0, -base_rad),
                              (0.0, 0.0, base_rad), (0.0, 0.0, base_rad+1.0)),
                             None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((0.0, 0.0, join_len+1.0), (0.0, 0.0, join_len),
                              (0.0, 0.0, -join_len), (0.0, 0.0, -join_len-1.0)), None, base_rad)

        elif detail == 2:

            draw_drawing('joinrot4flat')

            glPushMatrix()
            glTranslatef(0.0, 0.0, base_rad)
            glRotatef(180.0, 1.0, 0.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, -base_rad)
            draw_drawing('receive_m', colors['shaft'])
            glPopMatrix()

            draw_clipxp(color)
            draw_clipxm(color)
            draw_clipyp(color)
            draw_clipym(color)
            draw_clipzp(color)
            draw_clipzm(color)

class joinrot11(axle): # axle-based for configure only

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]]])
    ends_types = ['j', 'j']
    axis = [0] # end indices which are rotating axes
    unaligned_center = np.array([0.0, 0.0, 0.0])
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    stiffen_rad = 6.0*sf
    elbow_len = 10.75*sf
    depth = 1.5*sf
    divrt2 = 1.0/math.sqrt(2.0)
    xsection = [[-stiffen_rad, 0.0],
                [0.0, -stiffen_rad],
                [elbow_len, -stiffen_rad],
                [elbow_len, stiffen_rad],
                [0.0, stiffen_rad]]
    normal = [[-divrt2, -divrt2], [0.0, -1.0], [1.0, 0.0], [0.0, 1.0], [-divrt2, divrt2]]

    detail1 = 'Separate'

    query_options = [['Rotate 1', ['None', 'stiff1']]]

    def shape_stiffen(self, color):
        if detail == 1:
            if not color:
                glColor3fv(colors['total'])
            else:
                glColor3fv(color)
            gleExtrusion(self.xsection, self.normal, (0.0, 0.0, 1.0), ((self.elbow_len+1.0, 0.0, 0.0), (self.elbow_len, 0.0, 0.0), (self.elbow_len - self.depth, 0.0, 0.0), (self.elbow_len - self.depth -1.0, 0.0, 0.0)), None)
            gleExtrusion(self.xsection, self.normal, (0.0, 0.0, 1.0), ((0.0, self.elbow_len - self.depth -1.0, 0.0), (0.0, self.elbow_len - self.depth, 0.0), (0.0, self.elbow_len, 0.0), (0.0, self.elbow_len+1.0, 0.0)), None)
        elif detail == 2:
            glRotatef(270.0, 0.0, 1.0, 0.0)
            draw_drawing('stiffen', color)

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0, -1.0, 0.0), (0.0, 0.0, 0.0),
                              (0.0, join_len, 0.0), (0.0, join_len+1.0, 0.0)),
                             None, base_rad)
            glePolyCylinder( ((base_rad+1.0, 0.0, 0.0), (base_rad, 0.0, 0.0),
                              (-base_rad, 0.0, 0.0), (-base_rad-1.0, 0.0, 0.0)),
                              None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (0.0, 0.0, 0.0), (-1.0, 0.0, 0.0)),
                              None, base_rad)
                
        elif detail == 2:

            glPushMatrix()
            glRotatef(90.0, 0.0, 0.0, 1.0)
            glRotatef(90.0, 1.0, 0.0, 0.0)
            draw_drawing('joinrot1')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(-base_rad, 0.0, 0.0)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('receive_cap', color)
            glPopMatrix()

            glPushMatrix()
            glTranslatef(base_rad, 0.0, 0.0)
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)

        if self.configure[0] == 'stiff1':
            self.shape_stiffen(color)
        
class joinrot12(joinrot11):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]]])
    ends_types = ['j', 'j', 'j']
    axis = [0, 2] # end indices which are rotating axes
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    query_options = [['Rotate 1', ['None', '^stiff1']],
                     ['Rotate 2', ['None', '^stiff1']]]

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
                              (0.0, 0.0, 0.0), (0.0, 0.0-1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((base_rad+1.0, 0.0, 0.0), (base_rad, 0.0, 0.0),
                              (-base_rad, 0.0, 0.0), (-base_rad-1.0, 0.0, 0.0)),
                             None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)

        elif detail == 2:

            glPushMatrix()
            glRotatef(90.0, 0.0, 0.0, 1.0)
            glRotatef(90.0, 1.0, 0.0, 0.0)
            draw_drawing('joinrot1')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(base_rad, 0.0, 0.0)
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()

            glPushMatrix()
            glTranslatef(-base_rad, 0.0, 0.0)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('receive_m', colors['shaft'])
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)
            draw_clipxm(color)

        if self.configure[0] == '^stiff1':
            self.shape_stiffen(color)
        if self.configure[1] == '^stiff1':
            glRotatef(180.0, 0.0, 1.0, 0.0)
            self.shape_stiffen(color)

class joinrot21(joinrot11):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[0.0, 0.0, join_len],
                                [0.0, 0.0, join_len-1.0],
                                [-1.0, 0.0, join_len]]])
    ends_types = ['j', 'j', 'j']
    axis = [2] # end indices which are rotating axes
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    query_options = [['Rotate 1', ['None', 'stiff1', 'stiff2']]]

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (0.0, 0.0, 0.0), (0.0, join_len, 0.0),
                              (0.0, join_len+1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, 0.0, -base_rad-1.0), (0.0, 0.0, -base_rad),
                              (0.0, 0.0, base_rad), (0.0, 0.0, base_rad+1.0)),
                             None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((0.0, 0.0, join_len+1.0), (0.0, 0.0, join_len),
                              (0.0, 0.0, 0.0), (0.0, 0.0, 0.0-1.0)), None, base_rad)

        elif detail == 2:
            
            glPushMatrix()
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('joinrot2')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, -base_rad)
            draw_drawing('receive_cap')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, base_rad)
            glRotatef(180.0, 1.0, 0.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)
            draw_clipzp(color)

        if self.configure[0] != 'None':
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            if self.configure[0] == 'stiff2':
                glRotatef(-90.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)

class joinrot22(joinrot11):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[0.0, 0.0, join_len],
                                [0.0, 0.0, join_len-1.0],
                                [-1.0, 0.0, join_len]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]]])
    unaligned_center = np.array([0.0, 0.0, 0.0])
    axis = [0, 3] # end indices which are rotating axes
    ends_types = ['j', 'j', 'j', 'j']
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    query_options = [['Rotate 1', ['None', '^stiff1', '^stiff2']],
                     ['Rotate 2', ['None', '^stiff1', '^stiff2']]]

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
                              (0.0, 0.0, 0.0), (0.0, 0.0, join_len),
                              (0.0, 0.0, join_len+1.0)), None, base_rad)
            glePolyCylinder( ((-base_rad-1.0, 0.0, 0.0), (-base_rad, 0.0, 0.0),
                              (base_rad, 0.0, 0.0), (base_rad+1.0, 0.0, 0.0)),
                             None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (-join_len, 0.0, 0.0),
                              (-join_len-1.0, 0.0, 0.0)), None, base_rad)

        elif detail == 2:

            glPushMatrix()
            glRotatef(90.0, 0.0, 0.0, 1.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            draw_drawing('joinrot2')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(base_rad, 0.0, 0.0)
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()

            glPushMatrix()
            glTranslatef(-base_rad, 0.0, 0.0)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('receive_m', colors['shaft'])
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)
            draw_clipzp(color)
            draw_clipxm(color)

        if self.configure[0] != 'None':
            glPushMatrix()
            if self.configure[0] == '^stiff2':
                glRotatef(90.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)
            glPopMatrix()
        if self.configure[1] != 'None':
            glPushMatrix()
            glRotatef(180.0, 0.0, 1.0, 0.0)
            if self.configure[1] == '^stiff2':
                glRotatef(-90.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)
            glPopMatrix()

class joinrot2flat1(joinrot11):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]]])
    ends_types = ['j', 'j', 'j']
    axis = [1] # end indices which are rotating axes
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    query_options = [['Rotate 1', ['None', 'stiff1', 'stiff2']]]

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (-join_len, 0.0, 0.0),
                              (-join_len-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, -base_rad-1.0, 0.0), (0.0, -base_rad, 0.0),
                              (0.0, base_rad, 0.0), (0.0, base_rad+1.0, 0.0)),
                              None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
                              (0.0, 0.0, 0.0), (0.0, 0.0-1.0, 0.0)),
                             None, base_rad)

        elif detail == 2:

            glPushMatrix()
            glRotatef(90.0, 1.0, 0.0, 0.0)
            draw_drawing('joinrot2flat')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, -base_rad, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            draw_drawing('receive_cap')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, base_rad, 0.0)
            glRotatef(90.0, 1.0, 0.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)
            draw_clipxm(color)

        if self.configure[0] != 'None':
            glRotatef(90.0, 0.0, 0.0, 1.0)
            if self.configure[0] == 'stiff2':
                glRotatef(180.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)

class joinrot2flat2(joinrot11):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]],
                               [[0.0, -join_len, 0.0],
                                [0.0, -join_len+1.0, 0.0],
                                [0.0, -join_len, -1.0]]])
    ends_types = ['j', 'j', 'j', 'j']
    axis = [0, 2] # end indices which are rotating axes
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    query_options = [['Rotate 1', ['None', '^stiff1', '^stiff2']],
                     ['Rotate 2', ['None', '^stiff1', '^stiff2']]]

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
                              (0.0, -join_len, 0.0), (0.0, -join_len-1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((-base_rad-1.0, 0.0, 0.0), (-base_rad, 0.0, 0.0),
                              (base_rad, 0.0, 0.0), (base_rad+1.0, 0.0, 0.0)),
                             None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)

        elif detail == 2:

            glPushMatrix()
            glRotatef(90.0, 0.0, 0.0, 1.0)
            glRotatef(90.0, 1.0, 0.0, 0.0)
            draw_drawing('joinrot2flat')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(base_rad, 0.0, 0.0)
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()

            glPushMatrix()
            glTranslatef(-base_rad, 0.0, 0.0)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('receive_m', colors['shaft'])
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)
            draw_clipxm(color)
            draw_clipym(color)

        if self.configure[0] != 'None':
            glPushMatrix()
            if self.configure[0] == '^stiff2':
                glRotatef(180.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)
            glPopMatrix()
        if self.configure[1] != 'None':
            glPushMatrix()
            glRotatef(180.0, 0.0, 1.0, 0.0)
            if self.configure[1] == '^stiff2':
                glRotatef(180.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)
            glPopMatrix()

class joinrot3flat1(joinrot11):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[0.0, 0.0, join_len],
                                [0.0, 0.0, join_len-1.0],
                                [-1.0, 0.0, join_len]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]]])
    ends_types = ['j', 'j', 'j', 'j']
    axis = [2] # end indices which are rotating axes
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    query_options = [['Rotate 1', ['None', 'stiff1', 'stiff2', 'stiff3']]]

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
                              (0.0, 0.0, 0.0), (0.0, -1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, 0.0, -base_rad-1.0), (0.0, 0.0, -base_rad),
                              (0.0, 0.0, base_rad), (0.0, 0.0, base_rad+1.0)),
                              None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((0.0, 0.0, -1.0), (0.0, 0.0, 0.0),
                              (0.0, 0.0, join_len),
                              (0.0, 0.0, join_len+1.0)), None, base_rad)

        elif detail == 2:

            glPushMatrix()
            glRotatef(180.0, 0.0, 0.0, 1.0)
            draw_drawing('joinrot3flat')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, -base_rad)
            draw_drawing('receive_cap')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, base_rad)
            glRotatef(180.0, 1.0, 0.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)
            draw_clipxm(color)
            draw_clipzp(color)

        if self.configure[0] != 'None':
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            if self.configure[0] == 'stiff1':
                glRotatef(-90.0, 1.0, 0.0, 0.0)
            if self.configure[0] == 'stiff2':
                pass
            elif self.configure[0] == 'stiff3':
                glRotatef(90.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)

class joinrot3flat2(joinrot11):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[0.0, 0.0, join_len],
                                [0.0, 0.0, join_len-1.0],
                                [-1.0, 0.0, join_len]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]],
                               [[0.0, -join_len, 0.0],
                                [0.0, -join_len+1.0, 0.0],
                                [0.0, -join_len, -1.0]]])
    ends_types = ['j', 'j', 'j', 'j', 'j']
    axis = [0, 3] # end indices which are rotating axes
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    query_options = [['Rotate 1', ['None', '^stiff1', '^stiff2', '^stiff3']],
                     ['Rotate 2', ['None', '^stiff1', '^stiff2', '^stiff3']]]

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
                              (0.0, -join_len, 0.0), (0.0, -join_len-1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, 0.0, 0.0-1.0), (0.0, 0.0, 0.0),
                              (0.0, 0.0, join_len), (0.0, 0.0, join_len+1.0)), None, base_rad)
            glePolyCylinder( ((-base_rad-1.0, 0.0, 0.0), (-base_rad, 0.0, 0.0),
                              (base_rad, 0.0, 0.0), (base_rad+1.0, 0.0, 0.0)),
                             None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)

        elif detail == 2:

            glPushMatrix()
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('joinrot3flat')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(base_rad, 0.0, 0.0)
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()

            glPushMatrix()
            glTranslatef(-base_rad, 0.0, 0.0)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            draw_drawing('receive_m', colors['shaft'])
            glPopMatrix()

            draw_clipxp(color)
            draw_clipyp(color)
            draw_clipxm(color)
            draw_clipym(color)
            draw_clipzp(color)

        if self.configure[0] != 'None':
            glPushMatrix()
            if self.configure[0] == '^stiff2':
                glRotatef(90.0, 1.0, 0.0, 0.0)
            elif self.configure[0] == '^stiff3':
                glRotatef(180.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)
            glPopMatrix()
        if self.configure[1] != 'None':
            glPushMatrix()
            glRotatef(180.0, 0.0, 1.0, 0.0)
            if self.configure[1] == '^stiff2':
                glRotatef(-90.0, 1.0, 0.0, 0.0)
            elif self.configure[1] == '^stiff3':
                glRotatef(180.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)
            glPopMatrix()

class joinrot4flat1(joinrot11):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[0.0, 0.0, join_len],
                                [0.0, 0.0, join_len-1.0],
                                [-1.0, 0.0, join_len]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]],
                               [[0.0, -join_len, 0.0],
                                [0.0, -join_len+1.0, 0.0],
                                [0.0, -join_len, -1.0]]])
    ends_types = ['j', 'j', 'j', 'j', 'j']
    axis = [2] # end indices which are rotating axes
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    query_options = [['Rotate 1', ['None', 'stiff1', 'stiff2', 'stiff3', 'stiff4']]]

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
                              (0.0, -join_len, 0.0), (0.0, -join_len-1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, 0.0, -base_rad-1.0), (0.0, 0.0, -base_rad),
                              (0.0, 0.0, base_rad), (0.0, 0.0, base_rad+1.0)),
                             None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((0.0, 0.0, 0.0-1.0), (0.0, 0.0, 0.0),
                              (0.0, 0.0, join_len), (0.0, 0.0, join_len+1.0)), None, base_rad)

        elif detail == 2:

            draw_drawing('joinrot4flat')

            glPushMatrix()
            glTranslatef(0.0, 0.0, -base_rad)
            draw_drawing('receive_cap')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, base_rad)
            glRotatef(180.0, 1.0, 0.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()
            
            draw_clipxp(color)
            draw_clipxm(color)
            draw_clipyp(color)
            draw_clipym(color)
            draw_clipzp(color)

        if self.configure[0] != 'None':
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            if self.configure[0] == 'stiff2':
                glRotatef(-90.0, 1.0, 0.0, 0.0)
            elif self.configure[0] == 'stiff3':
                glRotatef(180.0, 1.0, 0.0, 0.0)
            elif self.configure[0] == 'stiff4':
                glRotatef(90.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)

class joinrot4flat2(joinrot11):

    unaligned_ends = np.array([[[join_len, 0.0, 0.0],
                                [join_len-1.0, 0.0, 0.0],
                                [join_len, -1.0, 0.0]],
                               [[0.0, join_len, 0.0],
                                [0.0, join_len-1.0, 0.0],
                                [0.0, join_len, -1.0]],
                               [[0.0, 0.0, join_len],
                                [0.0, 0.0, join_len-1.0],
                                [-1.0, 0.0, join_len]],
                               [[-join_len, 0.0, 0.0],
                                [-join_len+1.0, 0.0, 0.0],
                                [-join_len, -1.0, 0.0]],
                               [[0.0, -join_len, 0.0],
                                [0.0, -join_len+1.0, 0.0],
                                [0.0, -join_len, -1.0]],
                               [[0.0, 0.0, -join_len],
                                [0.0, 0.0, -join_len+1.0],
                                [-1.0, 0.0, -join_len]]])
    ends_types = ['j', 'j', 'j', 'j', 'j', 'j']
    axis = [2, 5] # end indices which are rotating axes
    icon_center = (0.0, 0.0, 0.0)
    icon_extent = 3.0

    query_options = [['Rotate 1', ['None', '^stiff1', '^stiff2', '^stiff3', '^stiff4']],
                     ['Rotate 2', ['None', '^stiff1', '^stiff2', '^stiff3', '^stiff4']]]

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((join_len+1.0, 0.0, 0.0), (join_len, 0.0, 0.0),
                              (-join_len, 0.0, 0.0), (-join_len-1.0, 0.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, join_len+1.0, 0.0), (0.0, join_len, 0.0),
                              (0.0, -join_len, 0.0), (0.0, -join_len-1.0, 0.0)), None, base_rad)
            glePolyCylinder( ((0.0, 0.0, -base_rad-1.0), (0.0, 0.0, -base_rad),
                              (0.0, 0.0, base_rad), (0.0, 0.0, base_rad+1.0)),
                             None, rot_rad)
            self.draw_ends()
            glColor3fv(colors['shaft'])
            glePolyCylinder( ((0.0, 0.0, join_len+1.0), (0.0, 0.0, join_len),
                              (0.0, 0.0, -join_len), (0.0, 0.0, -join_len-1.0)), None, base_rad)
                
        elif detail == 2:
            
            draw_drawing('joinrot4flat')

            glPushMatrix()
            glTranslatef(0.0, 0.0, base_rad)
            glRotatef(180.0, 1.0, 0.0, 0.0)
            draw_drawing('receive_f', colors['shaft'])
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, -base_rad)
            draw_drawing('receive_m', colors['shaft'])
            glPopMatrix()

            draw_clipxp(color)
            draw_clipxm(color)
            draw_clipyp(color)
            draw_clipym(color)
            draw_clipzp(color)
            draw_clipzm(color)

        if self.configure[0] != 'None':
            glPushMatrix()
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            if self.configure[0] == '^stiff2':
                glRotatef(-90.0, 1.0, 0.0, 0.0)
            elif self.configure[0] == '^stiff3':
                glRotatef(180.0, 1.0, 0.0, 0.0)
            elif self.configure[0] == '^stiff4':
                glRotatef(90.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)
            glPopMatrix()
        if self.configure[1] != 'None':
            glPushMatrix()
            glRotatef(90.0, 0.0, 1.0, 0.0)
            if self.configure[1] == '^stiff2':
                glRotatef(90.0, 1.0, 0.0, 0.0)
            elif self.configure[1] == '^stiff3':
                glRotatef(180.0, 1.0, 0.0, 0.0)
            elif self.configure[1] == '^stiff4':
                glRotatef(-90.0, 1.0, 0.0, 0.0)
            self.shape_stiffen(color)
            glPopMatrix()

class wheel_axle1s1w(axle):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]]])
    unaligned_center = np.array([wheelw/2, 0.0, 0.0])
    ends_types = ['s']
    side_len = 3.2*sf
    divrt2 = 1.0/math.sqrt(2.0)
    xsection = [[side_len, 0.0], [0.0, side_len], [-side_len, 0.0], [0.0, -side_len]]
    normal = [[divrt2, divrt2], [-divrt2, divrt2], [-divrt2, -divrt2], [divrt2, -divrt2]]
    icon_center = (wheelw/2, 0.0, 0.0)

    detail1 = 'Separate'

    query_options = [['Wheel Type', ['None', 'wheelp5', 'wheel1']]]

    def help_text(self):
        if self.configure[0] == 'None':
            return ''
        else:
            return 'Slide ' + aliases['wheel_axle1s1w'] + ' through ' + aliases[self.configure[0]] + ' and join.  Make hub face joint.'

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['wheel'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        cap_len = 1.6*sf
        cap_rad = 5.0*sf

        if detail == 1:
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(self.xsection, self.normal, (0.0, 0.0, 1.0), ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (wheels+wheelw, 0.0, 0.0), (wheels+wheelw+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            glePolyCylinder( ((wheels+wheelw-1.0, 0.0, 0.0), (wheels+wheelw, 0.0, 0.0),
                              (wheels+wheelw+cap_len, 0.0, 0.0), (wheels+wheelw+cap_len+1.0, 0.0, 0.0)),
                             None, cap_rad)
            self.draw_ends()

        elif detail == 2:
            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            draw_drawing('wheel_axle1s1w')
            glPopMatrix()

        if self.configure[0] != 'None':
            draw_wheel(self.configure[0], wheels + 0.5*wheelw, -1)

class wheel_axle2s2w(axle):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len1s, 0.0, 0.0],
                                [len1s-1.0, 0.0, 0.0],
                                [len1s, 0.0, -1.0]]])
    ends_types = ['s', 's']
    side_len = 3.2*sf
    divrt2 = 1.0/math.sqrt(2.0)
    xsection = [[side_len, 0.0], [0.0, side_len], [-side_len, 0.0], [0.0, -side_len]]
    normal = [[divrt2, divrt2], [-divrt2, divrt2], [-divrt2, -divrt2], [divrt2, -divrt2]]
    icon_extent = 4.0

    detail1 = 'Separate'

    query_options = [['Wheel Type', ['None', 'wheelp5', 'wheel1']]]
    query_options_quantities = [2]

    def help_text(self):
        if self.configure[0] == 'None':
            return ''
        else:
            return 'Slide ' + aliases['wheel_axle2s2w'] + ' through two ' + aliases[self.configure[0]] + 's and join.  Make hubs face joint.'

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['wheel'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        if detail == 1:
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(self.xsection, self.normal, (0.0, 0.0, 1.0), ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (len1s, 0.0, 0.0), (len1s+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            self.draw_ends()
        elif detail == 2:
            length = len1 - 2*join_len

            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('wheel_axle2s2w')
            glPopMatrix()

        offsets = (wheels+0.5*wheelw, wheels+1.5*wheelw)
        current_color = glGetFloatv(GL_CURRENT_COLOR)[:3]
        if self.configure[0] != 'None':
            glColor3fv(current_color)
            draw_wheel(self.configure[0], offsets[0], -1, 90.0)
            glColor3fv(current_color)
            draw_wheel(self.configure[0], offsets[1], 1, 0.0)

class wheel_axle1s3w(axle):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]]])
    unaligned_center = np.array([3*wheelw/2, 0.0, 0.0])
    ends_types = ['s']
    side_len = 3.2*sf
    divrt2 = 1.0/math.sqrt(2.0)
    xsection = [[side_len, 0.0], [0.0, side_len], [-side_len, 0.0], [0.0, -side_len]]
    normal = [[divrt2, divrt2], [-divrt2, divrt2], [-divrt2, -divrt2], [divrt2, -divrt2]]
    icon_center = (1.5*wheelw, 0.0, 0.0)
    icon_extent = 5.0

    detail1 = 'Separate'

    query_options = [['Wheel Type', ['None', 'wheelp5', 'wheel1']]]
    query_options_quantities = [3]

    def help_text(self):
        if self.configure[0] == 'None':
            return ''
        else:
            return 'Slide ' + aliases['wheel_axle1s3w'] + ' through three ' + aliases[self.configure[0]] + 's and join.  Make hubs face joint.'

    def shape_color(self, color = None):
        if not color:
            glColor3fv(colors['wheel'])
        else:
            glColor3fv(color)

    def shape(self, color = None): 

        cap_len = 1.6*sf
        cap_rad = 5.0*sf
        if detail == 1:
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(self.xsection, self.normal, (0.0, 0.0, 1.0), ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (wheels+3*wheelw, 0.0, 0.0), (wheels+3*wheelw+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            glePolyCylinder( ((wheels+3*wheelw-1.0, 0.0, 0.0), (wheels+3*wheelw, 0.0, 0.0),
                              (wheels+3*wheelw+cap_len, 0.0, 0.0), (wheels+3*wheelw+cap_len+1.0, 0.0, 0.0)),
                             None, cap_rad)
            self.draw_ends()
        elif detail == 2:
            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            draw_drawing('wheel_axle1s3w')
            glPopMatrix()

        offsets = (wheels+0.5*wheelw, wheels+1.5*wheelw, wheels+2.5*wheelw)
        current_color = glGetFloatv(GL_CURRENT_COLOR)[:3]
        if self.configure[0] != 'None':
            glColor3fv(current_color)
            draw_wheel(self.configure[0], offsets[0], -1, 90.0)
            glColor3fv(current_color)
            draw_wheel(self.configure[0], offsets[1], 1, 0.0)
            glColor3fv(current_color)
            draw_wheel(self.configure[0], offsets[2], 1, 0.0)

class pivot(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len1s, 0.0, 0.0],
                                [len1s-1.0, 0.0, 0.0],
                                [len1s, 0.0, -1.0]],
                               [[0.0, 0.0, panel_space],
                                [1.0, 0.0, panel_space],
                                [0.0, -1.0, panel_space]],
                               [[len1s, 0.0, panel_space],
                                [len1s-1.0, 0.0, panel_space],
                                [len1s, -1.0, panel_space]]])
    ends_types = ['s', 's', 's', 's']
    icon_extent = 4.5
    combination = ['coupler', 'gear_axle2s', 'gear_axle2s', 'coupler']

    def label(self):
        return self.combination[:-1]

    def inset_files(self):
        return reduce(lambda x, y: x + y, self.combination[:-1])

    def help_text(self):
        return 'Slide two ' + aliases['gear_axle2s'] + ' through two ' + aliases['coupler'] + ' and join.'

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (len1s, 0.0, 0.0), (len1s+1.0, 0.0, 0.0)),
                             None, base_rad)
            glePolyCylinder( ((0.0-1.0, 0.0, panel_space), (0.0, 0.0, panel_space),
                              (len1s, 0.0, panel_space), (len1s+1.0, 0.0, panel_space)),
                             None, base_rad)
            xsection = [[-base_rad, 0.0], [-base_rad, 0.0], [base_rad, 0.0], [base_rad, 0.0], [base_rad, panel_space], [base_rad, panel_space], [-base_rad, panel_space], [-base_rad, panel_space]]
            normal = [[-1.0, 0.0], [0.0, -1.0], [0.0, -1.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [-1.0, 0.0]]
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)), None)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((len1s-gearw-1.0, 0.0, 0.0), (len1s-gearw, 0.0, 0.0), (len1s, 0.0, 0.0), (len1s+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            self.draw_ends()
        elif detail == 2:
            length = len1 - 2*join_len

            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('gear_axle2s')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, panel_space)
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('gear_axle2s')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.5*gearw, 0.0, panel_space/2)
            glRotatef(270.0, 0.0, 1.0, 0.0)
            draw_drawing('coupler')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(len1s-0.5*gearw, 0.0, panel_space/2)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            draw_drawing('coupler')
            glPopMatrix()

class pivotm1(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len1s, 0.0, 0.0],
                                [len1s-1.0, 0.0, 0.0],
                                [len1s, 0.0, -1.0]],
                               [[0.0, 0.0, panel_space],
                                [1.0, 0.0, panel_space],
                                [0.0, -1.0, panel_space]],
                               [[len1s-panel_space, 0.0, panel_space],
                                [len1s-panel_space-1.0, 0.0, panel_space],
                                [len1s-panel_space, -1.0, panel_space]]])
    ends_types = ['s', 's', 's', 's']
    icon_extent = 4.5
    icon_center = (len1s/2, 0.0, panel_space/2.0)
    combination = ['coupler', 'gear_axle2s', 'straight1m1']

    def label(self):
        return self.combination[:]

    def inset_files(self):
        return reduce(lambda x, y: x + y, self.combination)

    def help_text(self):
        return 'Slide ' + aliases['gear_axle2s'] + ' and ' + aliases['straight1m1'] + ' through ' + aliases['coupler'] + ' and join.'

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (len1s, 0.0, 0.0), (len1s+1.0, 0.0, 0.0)),
                             None, base_rad)
            glePolyCylinder( ((0.0-1.0, 0.0, panel_space), (0.0, 0.0, panel_space),
                              (len1s-panel_space, 0.0, panel_space), (len1s-panel_space+1.0, 0.0, panel_space)),
                             None, base_rad)
            xsection = [[-base_rad, 0.0], [-base_rad, 0.0], [base_rad, 0.0], [base_rad, 0.0], [base_rad, panel_space], [base_rad, panel_space], [-base_rad, panel_space], [-base_rad, panel_space]]
            normal = [[-1.0, 0.0], [0.0, -1.0], [0.0, -1.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [-1.0, 0.0]]
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            self.draw_ends()
        elif detail == 2:
            length = len1 - 2*join_len

            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('gear_axle2s')
            glPopMatrix()

            length = len1 - panel_space - 2*join_len

            glPushMatrix()
            glTranslatef(0.0, 0.0, panel_space)
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            draw_drawing('straight1m1')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.5*gearw, 0.0, panel_space/2)
            glRotatef(270.0, 0.0, 1.0, 0.0)
            draw_drawing('coupler')
            glPopMatrix()

class pivot00(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[0.0, 0.0, panel_space],
                                [1.0, 0.0, panel_space],
                                [0.0, -1.0, panel_space]]])
    ends_types = ['s', 's']
    icon_extent = 3.0
    combination = ['coupler', 'gear_axle1s', 'gear_axle1s']

    def label(self):
        return self.combination[:]

    def inset_files(self):
        return reduce(lambda x, y: x + y, self.combination)

    def help_text(self):
        return 'Slide two ' + aliases['gear_axle1s'] + ' through ' + aliases['coupler'] + ' and join.'

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)),
                             None, base_rad)
            glePolyCylinder( ((0.0-1.0, 0.0, panel_space), (0.0, 0.0, panel_space),
                              (gearw, 0.0, panel_space), (gearw+1.0, 0.0, panel_space)),
                             None, base_rad)
            xsection = [[-base_rad, 0.0], [-base_rad, 0.0], [base_rad, 0.0], [base_rad, 0.0], [base_rad, panel_space], [base_rad, panel_space], [-base_rad, panel_space], [-base_rad, panel_space]]
            normal = [[-1.0, 0.0], [0.0, -1.0], [0.0, -1.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [-1.0, 0.0]]
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            self.draw_ends()
        elif detail == 2:
            
            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            draw_drawing('gear_axle1s')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, panel_space)
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            draw_drawing('gear_axle1s')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.5*gearw, 0.0, panel_space/2)
            glRotatef(270.0, 0.0, 1.0, 0.0)
            draw_drawing('coupler')
            glPopMatrix()

class pivot01(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len1s, 0.0, 0.0],
                                [len1s-1.0, 0.0, 0.0],
                                [len1s, 0.0, -1.0]],
                               [[0.0, 0.0, panel_space],
                                [1.0, 0.0, panel_space],
                                [0.0, -1.0, panel_space]]])
    ends_types = ['s', 's', 's']
    icon_center = (len1s/2, 0.0, panel_space/2)
    icon_extent = 4.5
    combination = ['coupler', 'gear_axle2s', 'gear_axle1s']

    def label(self):
        return self.combination[:]

    def inset_files(self):
        return reduce(lambda x, y: x + y, self.combination)

    def help_text(self):
        return 'Slide ' + aliases['gear_axle2s'] + ' and ' + aliases['gear_axle1s'] + ' through ' + aliases['coupler'] + ' and join.'

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (len1s, 0.0, 0.0), (len1s+1.0, 0.0, 0.0)),
                             None, base_rad)
            glePolyCylinder( ((0.0-1.0, 0.0, panel_space), (0.0, 0.0, panel_space),
                              (gearw, 0.0, panel_space), (gearw+1.0, 0.0, panel_space)),
                             None, base_rad)
            xsection = [[-base_rad, 0.0], [-base_rad, 0.0], [base_rad, 0.0], [base_rad, 0.0], [base_rad, panel_space], [base_rad, panel_space], [-base_rad, panel_space], [-base_rad, panel_space]]
            normal = [[-1.0, 0.0], [0.0, -1.0], [0.0, -1.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [-1.0, 0.0]]
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            self.draw_ends()
        elif detail == 2:
            length = len1 - 2*join_len
            
            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('gear_axle2s')
            glPopMatrix()
            
            length = len1 - panel_space - 2*join_len

            glPushMatrix()
            glTranslatef(0.0, 0.0, panel_space)
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            draw_drawing('gear_axle1s')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.5*gearw, 0.0, panel_space/2)
            glRotatef(270.0, 0.0, 1.0, 0.0)
            draw_drawing('coupler')
            glPopMatrix()

class pivot0m1(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[0.0, 0.0, panel_space],
                                [1.0, 0.0, panel_space],
                                [0.0, -1.0, panel_space]],
                               [[len1s-panel_space, 0.0, panel_space],
                                [len1s-panel_space-1.0, 0.0, panel_space],
                                [len1s-panel_space, -1.0, panel_space]]])
    ends_types = ['s', 's', 's']
    icon_extent = 4.0
    combination = ['coupler', 'straight1m1', 'gear_axle1s']

    def label(self):
        return self.combination[:]

    def inset_files(self):
        return reduce(lambda x, y: x + y, self.combination)

    def help_text(self):
        return 'Slide ' + aliases['straight1m1'] + ' and ' + aliases['gear_axle1s'] + ' through ' + aliases['coupler'] + ' and join.'

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)),
                             None, base_rad)
            glePolyCylinder( ((0.0-1.0, 0.0, panel_space), (0.0, 0.0, panel_space),
                              (len1s-panel_space, 0.0, panel_space), (len1s-panel_space+1.0, 0.0, panel_space)),
                             None, base_rad)
            xsection = [[-base_rad, 0.0], [-base_rad, 0.0], [base_rad, 0.0], [base_rad, 0.0], [base_rad, panel_space], [base_rad, panel_space], [-base_rad, panel_space], [-base_rad, panel_space]]
            normal = [[-1.0, 0.0], [0.0, -1.0], [0.0, -1.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [-1.0, 0.0]]
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            self.draw_ends()
        elif detail == 2:
            length = len1 - 2*join_len
            
            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            draw_drawing('gear_axle1s')
            glPopMatrix()

            length = len1 - panel_space - 2*join_len

            glPushMatrix()
            glTranslatef(0.0, 0.0, panel_space)
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            draw_drawing('straight1m1')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.5*gearw, 0.0, panel_space/2)
            glRotatef(270.0, 0.0, 1.0, 0.0)
            draw_drawing('coupler')
            glPopMatrix()

class pivotm1m1(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len1s-panel_space, 0.0, 0.0],
                                [len1s-panel_space-1.0, 0.0, 0.0],
                                [len1s-panel_space, 0.0, -1.0]],
                               [[0.0, 0.0, panel_space],
                                [1.0, 0.0, panel_space],
                                [0.0, -1.0, panel_space]],
                               [[len1s-panel_space, 0.0, panel_space],
                                [len1s-panel_space-1.0, 0.0, panel_space],
                                [len1s-panel_space, -1.0, panel_space]]])
    ends_types = ['s', 's', 's', 's']
    icon_extent = 4.5
    icon_center = (len1s/2, 0.0, panel_space/2.0)
    combination = ['coupler', 'straight1m1', 'straight1m1']

    def label(self):
        return self.combination[:-1]

    def inset_files(self):
        return reduce(lambda x, y: x + y, self.combination[:-1])

    def help_text(self):
        return 'Slide two ' + aliases['straight1m1'] + ' through ' + aliases['coupler'] + ' and join.'

    def shape(self, color = None): 

        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (len1s-panel_space, 0.0, 0.0), (len1s-panel_space+1.0, 0.0, 0.0)),
                             None, base_rad)
            glePolyCylinder( ((0.0-1.0, 0.0, panel_space), (0.0, 0.0, panel_space),
                              (len1s-panel_space, 0.0, panel_space), (len1s-panel_space+1.0, 0.0, panel_space)),
                             None, base_rad)
            xsection = [[-base_rad, 0.0], [-base_rad, 0.0], [base_rad, 0.0], [base_rad, 0.0], [base_rad, panel_space], [base_rad, panel_space], [-base_rad, panel_space], [-base_rad, panel_space]]
            normal = [[-1.0, 0.0], [0.0, -1.0], [0.0, -1.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [-1.0, 0.0]]
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)), None)
            #gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((len1s-panel_space-gearw-1.0, 0.0, 0.0), (len1s-panel_space-gearw, 0.0, 0.0), (len1s-panel_space, 0.0, 0.0), (len1s-panel_space+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            self.draw_ends()
        elif detail == 2:
            length = len1 - panel_space - 2*join_len

            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            draw_drawing('straight1m1')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, panel_space)
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            glRotatef(270.0, 0.0, 1.0, 0.0)
            draw_drawing('straight1m1')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.5*gearw, 0.0, panel_space/2)
            glRotatef(270.0, 0.0, 1.0, 0.0)
            draw_drawing('coupler')
            glPopMatrix()

class pivot0(stick):

    unaligned_ends = np.array([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 0.0, -1.0]],
                               [[len1s, 0.0, 0.0],
                                [len1s-1.0, 0.0, 0.0],
                                [len1s, 0.0, -1.0]],
                               [[0.0, 0.0, panel_space],
                                [1.0, 0.0, panel_space],
                                [0.0, -1.0, panel_space]],
                               [[len1s, 0.0, panel_space],
                                [len1s-1.0, 0.0, panel_space],
                                [len1s, -1.0, panel_space]]])
    ends_types = ['s', 's', 's', 's']
    icon_extent = 4.5
    combination = ['coupler', 'gear_axle2s', 'gear_axle1s', 'gear_axle1s', 'coupler']

    def label(self):
        return self.combination[:-1]

    def inset_files(self):
        return reduce(lambda x, y: x + y, self.combination[:-1])

    def help_text(self):
        return 'Slide ' + aliases['gear_axle2s'] + ' and two ' + aliases['gear_axle1s'] + ' through two ' + aliases['coupler'] + ' and join.'

    def shape(self, color = None): 

        stub_len = 1.6*sf
        if detail == 1:
            glePolyCylinder( ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                              (len1s, 0.0, 0.0), (len1s+1.0, 0.0, 0.0)),
                             None, base_rad)
            glePolyCylinder( ((0.0-1.0, 0.0, panel_space), (0.0, 0.0, panel_space),
                              (gearw+stub_len, 0.0, panel_space), (gearw+stub_len+1.0, 0.0, panel_space)),
                             None, base_rad)
            glePolyCylinder( ((len1s-gearw-stub_len-1.0, 0.0, panel_space), (len1s-gearw-stub_len, 0.0, panel_space),
                              (len1s, 0.0, panel_space), (len1s+1.0, 0.0, panel_space)),
                             None, base_rad)
            xsection = [[-base_rad, 0.0], [-base_rad, 0.0], [base_rad, 0.0], [base_rad, 0.0], [base_rad, panel_space], [base_rad, panel_space], [-base_rad, panel_space], [-base_rad, panel_space]]
            normal = [[-1.0, 0.0], [0.0, -1.0], [0.0, -1.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [-1.0, 0.0]]
            gleSetJoinStyle(TUBE_NORM_FACET | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((0.0-1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (gearw, 0.0, 0.0), (gearw+1.0, 0.0, 0.0)), None)
            gleExtrusion(xsection, normal, (0.0, 0.0, 1.0), ((len1s-gearw-1.0, 0.0, 0.0), (len1s-gearw, 0.0, 0.0), (len1s, 0.0, 0.0), (len1s+1.0, 0.0, 0.0)), None)
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ROUND | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)
            self.draw_ends()
        elif detail == 2:
            length = len1 - 2*join_len

            glPushMatrix()
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            glTranslatef(0.0, length/2, 0.0)
            draw_drawing('gear_axle2s')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, panel_space)
            glRotatef(-90.0, 0.0, 0.0, 1.0)
            #glTranslatef(0.0, length/2, 0.0)
            draw_drawing('gear_axle1s')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(len1s, 0.0, panel_space)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            #glTranslatef(0.0, 0.0, 0.0)
            draw_drawing('gear_axle1s')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.5*gearw, 0.0, panel_space/2)
            glRotatef(270.0, 0.0, 1.0, 0.0)
            draw_drawing('coupler')
            glPopMatrix()

            glPushMatrix()
            glTranslatef(len1s-0.5*gearw, 0.0, panel_space/2)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            draw_drawing('coupler')
            glPopMatrix()

