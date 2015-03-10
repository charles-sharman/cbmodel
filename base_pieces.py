"""
Description
-----------
Crossbeams Modeller base_pieces library--a base library for piece
manipulation.  Describes various routines for manipulating a fairly
arbitrary rod/connector system.

See cbmodel.py for a description of the package and its history.

Author
------
Charles Sharman

License
-------
Distributed under the GNU GENERAL PUBLIC LICENSE Version 3.  View
LICENSE for details.
"""

from OpenGL.GL import *
from OpenGL.GLE import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import numpy as np # The opengl number-crunching module is called np

import math
import vector_math
import string
import copy

# Global Variables
draw_outline = 0 # 0/1
draw_future_parts = 1 # 0/1 used in instructions
generate_pdf = 0 # 0/1
depth_scale = 1.0 # Used in draw_part_outlines
dim_scale = 1.0 # Multiplier for lines/text for print display
pixperunit = 10.0 # Set by cbmodel.py later
xabstol = 10e-3 # A non-zero number which is insignificant
# These colors are overwritten by cbmodel.py
colors = {'total': (1.0, 1.0, 1.0),
          'straight': (1.0, 1.0, 1.0),
          'angle': (1.0, 1.0, 1.0),
          'arc': (1.0, 1.0, 1.0),
          'part': (0.0, 1.0, 0.0),
          'edit': (0.45, 0.675, 0.9),
          'outline': (0.0, 0.0, 0.0),
          'newpart': (0.45, 0.675, 0.9),
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

def absinvert(x):
    """
    Returns the number if >= 0.  Otherwise, returns the inversion of
    the number.
    """
    if x >= 0:
        return x
    else:
        return ~x

class piece(object):
    """
    A base class for every piece
    """

    detail1 = 'Yes'
    query_options = [] # a piece which can be configured
    unaligned_center = []
    unaligned_ends = []
    ends_types = [] # 's'/'j' (stick or joint)
    combination = [] # a piece which is a combination of pieces
    axis = [] # indicates which ends are on a rotating axis

    def __init__(self):
        self.port = 0 #port is an index
        self.flip = 0
        if len(self.unaligned_center) == 0:
            self.unaligned_center = np.array([0.0, 0.0, 0.0])
            count = 0
            for count in range(len(self.unaligned_ends)):
                self.unaligned_center = self.unaligned_center + self.unaligned_ends[count][0]
            self.unaligned_center = self.unaligned_center/(count + 1.0)
        self.configure = []
        for query_option in self.query_options:
            self.configure.append(query_option[1][0])

    def configure_name(self, configure):
        """
        Some configures are prefixed or postfixed with special
        characters.  Returns the base aliased name of a configure and
        its extras.
        """
        if configure[0] in ['-', '^']:
            name = configure[1:]
            extra = configure[0]
        else:
            name = configure
            extra = ''
        if pieces.configure_aliases.has_key(name):
            name = pieces.configure_aliases[name]
        return (name, extra)

    def label(self):
        """
        Returns the text label for this part
        """
        return [self.name]

    def inset_files(self):
        """
        Returns the inset files for this part
        """
        return ''

    def help_text(self):
        """
        Returns the instruction help text for this part
        """
        return ''

    def nextport(self, next = 1):
        """
        Toggles ports, making the next one align with the module.
        """
        end_type = self.ends_types[self.port]
        if next == 1:
            try:
                self.port = self.ends_types.index(end_type, self.port + 1)
            except ValueError:
                self.port = self.ends_types.index(end_type)
        else:
            rev_types = self.ends_types[:]
            rev_types.reverse()
            try:
                rev_port = rev_types.index(end_type, len(rev_types) - self.port)
            except ValueError:
                rev_port = rev_types.index(end_type)
            self.port = len(rev_types) - rev_port - 1

    def flipport(self, dir = 1):
        """
        Rotates the port 90 degrees relative to the module.
        """
        self.flip = (self.flip + dir*90) % 360

    def shape_color(self, color = None):
        """
        Sets the piece color
        """
        if not color:
            glColor3fv(colors['total'])
        else:
            glColor3fv(color)

    def draw(self, color = None):
        """
        Draws the piece
        """
        glPushMatrix()
        glMultMatrixf(self.matrix)
        self.shape_color(color)
        if pieces.detail == 2:
            self.shape(color)
        else: # pieces.detail == 1
            if pieces.detail1_gllists.has_key(self.name):
                glCallList(pieces.detail1_gllists[self.name])
            else:
                if self.detail1 != 'Separate':
                    gllist = glGenLists(1)
                else:
                    gllist = 0

                if gllist != 0:
                    glNewList(gllist, GL_COMPILE)
                    
                self.shape(color)
                #for end, end_type in zip(self.unaligned_ends, self.ends_types):
                #    pieces.draw_end(end, end_type)

                if gllist != 0:
                    glEndList()
                    pieces.detail1_gllists[self.name] = gllist
                    glCallList(gllist)
        glPopMatrix()

    def calc_draw(self, color):
        """
        Aligns the piece to the module then draws the piece.
        """
        global xabstol
        to_end = self.to_end
        from_end = copy.copy(self.unaligned_ends[self.port])
        #print 'to_end+', to_end, from_end

        # Rotate 1
        vfrom = from_end[0] - from_end[1]
        vto = to_end[0] - to_end[1]
        vrot = np.array([0.0, 0.0, 1.0])
        if not np.allclose(-vfrom, vto, atol=xabstol, rtol=0.0): # Not already aligned
            if np.allclose(vfrom, vto, atol=xabstol, rtol=0.0): # 180 degrees apart
                vrot = to_end[0] - to_end[2]
                angle = 180.0
            else:
                vrot = vector_math.cross(vfrom, vto)
                angle = 180.0 + math.degrees(vector_math.acos_care(np.dot(vto, vfrom)))
            #print 'angle = ' + repr(angle) + ' vrot = ' + repr(vrot)
            glPushMatrix()
            glLoadIdentity()
            glRotatef(angle, vrot[0], vrot[1], vrot[2])
            m = glGetFloatv(GL_MODELVIEW_MATRIX)[:3,:3]
            glPopMatrix()
            rot_end = (np.dot(m, from_end[0]),
                       np.dot(m, from_end[1]),
                       np.dot(m, from_end[2]))
        else:
            angle = 0.0
            rot_end = copy.copy(from_end)
        #print 'rot_end = ' + repr(rot_end)
    
        # Rotate 2
        vfrom = rot_end[0] - rot_end[2]
        vto = to_end[0] - to_end[2]
        vrot2 = rot_end[0] - rot_end[1]
        if not np.allclose(vfrom, vto, atol=xabstol, rtol=0.0): # Not aligned
            if np.allclose(-vfrom, vto, atol=xabstol, rtol=0.0): # 180 degrees
                angle2 = 180.0
            else:
                angle2 = 180.0 + math.degrees(vector_math.acos_care(np.dot(vto, vfrom)))
        else:
            angle2 = 0.0
        if self.flip != 0:
            if angle2 >= 180.0: angle2 = angle2 - float(self.flip)
            else: angle2 = angle2 + float(self.flip)

        # Do the transformation
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(to_end[0][0], to_end[0][1], to_end[0][2])
        glRotatef(angle2, vrot2[0], vrot2[1], vrot2[2])
        glRotatef(angle, vrot[0], vrot[1], vrot[2])
        glTranslatef(-from_end[0][0], -from_end[0][1], -from_end[0][2])
        # I need the 4x4 matrix, because translations are stored in
        # the extra column
        self.matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        #print 'self.matrix', self.matrix
        self.calc_ends()
        glPopMatrix()

        # Calculate new ends
        self.draw(color)

    def calc_ends(self):
        """
        Calculates the absolute position of each end after an alignment.
        """
        matrix = np.transpose(self.matrix)
        self.ends = []
        for count in range(len(self.unaligned_ends)):
            self.ends.append((np.dot(matrix, np.concatenate((self.unaligned_ends[count][0], [1.0])))[:3],
                              np.dot(matrix, np.concatenate((self.unaligned_ends[count][1], [1.0])))[:3],
                              np.dot(matrix, np.concatenate((self.unaligned_ends[count][2], [1.0])))[:3]))
        self.ends = np.array(self.ends)
        self.center = np.dot(matrix, np.concatenate((self.unaligned_center, [1.0])))[:3]
        self.center_save = self.center[:]

    def align(self, to_end):
        """
        Sets the end to align to
        """
        self.to_end = to_end

class module(object):
    """
    A base class for a collection of pieces, called a module.
    """

    HISTORY_LENGTH = 10

    def __init__(self):
        self.netlist = []
        self.port = 0
        self.ends = []
        self.ends_types = []
        self.selected = []
        
        # Instructions 
        self.frame = 0
        # self.instructions format is:
        # [{vcenter, vout, vup, pixperunit, title, author, date}, # Frame 0 (Title)
        #  {vcenter, vout, vup, pixperunit, new_parts}, # Frame 1
        #  {vcenter, vout, vup, pixperunit, new_parts}, # Frame 2
        # etc.] (where new_pieces is a list of pieces to add for that frame)
        self.instructions = []
        self.old_parts = []
        self.hidden_parts = []
        self.instruction_start = 1 # frame where instructions start; poses are before this
        self.submodel = 0 # -1 pop, 0 none, 1 pop
        self.submodel_stack = []
        self.hold_pose = 0

        # History
        # Currently a crude form of undo/redo.  Stores the module
        # after every module change
        self.history = []
        self.history_index = -1

        self.redraw_called = 0 # Signals redraw started and finished

    def history_push(self):
        """
        Saves the module onto the stack
        """

        # disallow redos after a push
        for count in range(self.history_index, -1):
            del self.history[-1]
        self.history_index = -1
            
        if len(self.history) >= self.HISTORY_LENGTH:
            del self.history[0]
        self.history.append((copy.deepcopy(self.netlist), self.port, self.ends[:], self.ends_types[:], copy.deepcopy(self.instructions)))

    def history_undo(self):
        """
        Use the last module store
        """
        new_index = self.history_index - 1
        if len(self.history) >= -new_index:
            self.history_index = new_index
            self.netlist, self.port, self.ends, self.ends_types, self.instructions = self.history[self.history_index]
            self.selected = []

    def history_redo(self):
        """
        Use the next module store
        """
        new_index = min(self.history_index + 1, -1)
        if len(self.history) >= -new_index:
            self.history_index = new_index
            self.netlist, self.port, self.ends, self.ends_types, self.instructions = self.history[self.history_index]
            self.selected = []

    def start_ends(self, end_type):
        """
        The positions of the invisible cross hair before any piece
        has been placed.
        """
        e0 = pieces.join_len
        if end_type == 's':
            self.ends = [(np.array([e0, 0.0, 0.0]), np.array([e0-1.0, 0.0, 0.0]), np.array([e0, 0.0, -1.0])),
                         (np.array([0.0, e0, 0.0]), np.array([0.0, e0-1.0, 0.0]), np.array([0.0, e0, -1.0])),
                         (np.array([0.0, 0.0, e0]), np.array([0.0, 0.0, e0-1.0]), np.array([-1.0, 0.0, e0])),
                         (np.array([-e0, 0.0, 0.0]), np.array([-(e0-1.0), 0.0, 0.0]), np.array([-e0, 0.0, -1.0])),
                         (np.array([0.0, -e0, 0.0]), np.array([0.0, -(e0-1.0), 0.0]), np.array([0.0, -e0, -1.0])),
                         (np.array([0.0, 0.0, -e0]), np.array([0.0, 0.0, -(e0-1.0)]), np.array([-1.0, 0.0, -e0]))]
        else: # 'j'
            self.ends = [(np.array([e0, 0.0, 0.0]), np.array([e0+1.0, 0.0, 0.0]), np.array([e0, 0.0, -1.0])),
                         (np.array([0.0, e0, 0.0]), np.array([0.0, e0+1.0, 0.0]), np.array([0.0, e0, -1.0])),
                         (np.array([0.0, 0.0, e0]), np.array([0.0, 0.0, e0+1.0]), np.array([-1.0, 0.0, e0])),
                         (np.array([-e0, 0.0, 0.0]), np.array([-(e0+1.0), 0.0, 0.0]), np.array([-e0, 0.0, -1.0])),
                         (np.array([0.0, -e0, 0.0]), np.array([0.0, -(e0+1.0), 0.0]), np.array([0.0, -e0, -1.0])),
                         (np.array([0.0, 0.0, -e0]), np.array([0.0, 0.0, -(e0+1.0)]), np.array([-1.0, 0.0, -e0]))]

    def draw_base(self):
        """
        Draws the module by copying pixels from the back buffer to the
        front buffer.  Used in conjuction with capture_background.
        """
        #print 'draw_base', self.total_bmd
        glDrawBuffer(GL_FRONT)

        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthMask(GL_TRUE)
        glClear(GL_DEPTH_BUFFER_BIT) # This should *not* be necessary
        glDrawPixelsf(GL_DEPTH_COMPONENT, self.total_bmd)

        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        glDepthMask(GL_FALSE)
        glDrawPixelsf(GL_RGBA, self.total_rgb)
        glDepthMask(GL_TRUE)

    def capture_background(self):
        """
        Captures the background image for rapid redisplay.  Used in
        conjuction with draw_base.

        glReadPixels seems to be quite slow on many graphics hardware,
        so this is probably a poor way to do things.  Many claim
        textures are better.
        """
        viewport = glGetIntegerv(GL_VIEWPORT)
        glReadBuffer(GL_FRONT)
        self.total_bmd = glReadPixelsf(viewport[0], viewport[1], viewport[2], viewport[3], GL_DEPTH_COMPONENT)
        self.total_rgb = glReadPixelsf(viewport[0], viewport[1], viewport[2], viewport[3], GL_RGBA)

    def draw_selected(self, vout, vup, creationmode):
        """
        Draws selected pieces a different color by redrawing the piece
        slightly in front of where it should be.
        """
        global colors

        # glScalef did not work because the center about which to
        # scale was unclear
        #glDepthFunc(GL_EQUAL) # fine, but z-fighting for def draw()
        # When all parts are selected, doubles redraw time ***

        glDrawBuffer(GL_FRONT)
        voffset = vout*0.1
        glPushMatrix()
        glTranslatef(voffset[0], voffset[1], voffset[2])
        for count in self.selected:
            if self.hold_pose and creationmode == 'instructions' and self.frame >= self.instruction_start:
                matrix = self.region_matrices[self.region_lookups[count]]
                glPushMatrix()
                glMultMatrixf(matrix)
                self.netlist[count].draw(colors['edit'])
                glPopMatrix()
            else:
                self.netlist[count].draw(colors['edit'])
            #self.draw_part_outline(self.netlist[count], vout, vup, colors['edit'], 2.0)
        glPopMatrix()

        #if self.newparts != []:
        #    for newpart in self.newparts:
        #        self.netlist[newpart].draw(colors['edit'])

    def draw_part_outline(self, part, vout, vup, color, width_scale = 1.0):
        """
        Draws an outline around a single part in the module.
        Expensive and inaccurate.  Currently unused.
        """
        global colors

        voffset = -vout*pieces.base_rad
        width = width_scale * 2 * pieces.base_rad/10.0
        vy = vup*width
        vx = vector_math.cross(vout, vup)*width
        va = vector_math.normalize(vx + vy)*width
        vb = vector_math.normalize(-vx - vy)*width
        glDisable(GL_LIGHTING)
        #glScalef(1.1, 1.1, 1.1) # Scaling about (0,0,0) makes outline funny ***
        #glTranslatef(voffset[0], voffset[1], voffset[2])
        # The 4 draws make this very expensive, and a large vx/vy
        # distorts the outline. ***

        # Orthogonal Directions
        glPushMatrix()
        glTranslatef(voffset[0]+vy[0], voffset[1]+vy[1], voffset[2]+vy[2])
        part.draw(color)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(voffset[0]-vy[0], voffset[1]-vy[1], voffset[2]-vy[2])
        part.draw(color)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(voffset[0]+vx[0], voffset[1]+vx[1], voffset[2]+vx[2])
        part.draw(color)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(voffset[0]-vx[0], voffset[1]-vx[1], voffset[2]-vx[2])
        part.draw(color)
        glPopMatrix()

        if pieces.detail > 0:
            glEnable(GL_LIGHTING)

    def draw_part_outlines(self):
        """
        Captures all object shadows with a depth buffer screen and
        broadens their background footprint with a smearing algorithm.
        (Could use scipy binary_erosion, but I didn't want to add yet
        another special import.)  By broadening the depth buffer along
        with it, I can even create outlines with one piece overlapping
        another.

        Although more complicated than draw_part_outline, it is much
        faster:

        Corvette redraw times:
        0.6s line (detail=0), screen colors
        0.8s solid (detail=1), screen colors
        3.9s rendered (detail=2), screen colors
        10.8s rendered, print colors, draw_part_outline
        4.2s rendered, print colors, draw_part_outlines
        """

        global colors, depth_scale, pixperunit

        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)

        # reshape needed to circumvent pyopengl bug ***
        total_bmd = np.reshape(self.total_bmd, (viewport[3], viewport[2]))

        binary_depth = (total_bmd < 1.0).astype(np.uint8)
        #iterations = 2*dim_scale # Increase for thicker outlines
        #iterations = max(2, int(round(2*dim_scale*pixperunit/10.0))) # Increase for thicker outlines
        iterations = min(int(2*dim_scale), max(2, int(round(2*dim_scale*pixperunit/10.0)))) # Increase for thicker outlines
        outline = binary_depth.copy()
        shadow_bmd = total_bmd.copy()+2*pieces.base_rad*depth_scale # The second term defines the shadow offset.
        offsets = vector_math.offsets(iterations, iterations - 1) # outline pattern possible as long as distance is less than the minimum thickness of any feature
        ol = np.zeros(outline.shape, np.uint8)
        sh = np.ones(outline.shape, np.float32)
        ymax, xmax = outline.shape
        for x, y in offsets:
            y1 = max(0, y)
            y2 = min(ymax, ymax + y)
            x1 = max(0, x)
            x2 = min(xmax, xmax + x)
            y3 = max(0, -y)
            y4 = min(ymax, ymax - y)
            x3 = max(0, -x)
            x4 = min(xmax, xmax - x)
            ol[y1:y2,x1:x2] = ol[y1:y2,x1:x2] | outline[y3:y4,x3:x4]
            sh[y1:y2,x1:x2] = np.minimum(sh[y1:y2,x1:x2], shadow_bmd[y3:y4,x3:x4])
        outline = ol & (sh < total_bmd) # Remove this check and all shadow_bmd lines if I only want background highlighted
        column_adds = viewport[2] % 8
        if column_adds > 0:
            column_adds = 8 - column_adds
            full_outline = np.zeros((viewport[3], viewport[2] + column_adds), np.uint8)
            full_outline[:,:viewport[2]] = outline
            outline = full_outline
        outline = np.reshape(outline, (-1, 8)) * np.array([128, 64, 32, 16, 8, 4, 2, 1], np.uint8)
        outline = np.sum(outline, 1).astype(np.uint8)
        glColor3fv(colors['outline'])
        #glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        p = gluUnProject(0.001, 0.001, 0.001, model, projection, viewport) # Set z to 0.999 (almost back) if I only want background highlighted
        glRasterPos3fv(p)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glBitmap(viewport[2], viewport[3], 0, 0, 0, 0, outline)
        if pieces.detail > 0:
            glEnable(GL_LIGHTING)
        #glEnable(GL_DEPTH_TEST)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
        p = gluUnProject(0.001, 0.001, 0.001, model, projection, viewport)
        glRasterPos3fv(p)
        # Put outlines at the proper depth (can skip if I only want background highlighted)
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glClear(GL_DEPTH_BUFFER_BIT)
        glDrawPixelsf(GL_DEPTH_COMPONENT, self.total_bmd)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    def draw(self, vout, vup, creationmode):
        """
        Draws the module by using previous draws.  Faster than redraw.
        """
        #print 'draw'
        self.draw_base()
        self.draw_selected(vout, vup, creationmode)

    def generate_submodel_stack(self):
        """
        Generates the submodel stack
        """
        self.submodel_stack = []
        for frame_index in range(self.instruction_start, self.frame):
            inst = self.instructions[frame_index]
            if inst.has_key('submodel'):
                if inst['submodel'] == 1:
                    self.submodel_stack.append(frame_index)
                else:
                    del self.submodel_stack[-1]
        # Add the current frame
        if self.submodel == 1:
            self.submodel_stack.append(self.frame)
        elif self.submodel == -1:
            del self.submodel_stack[-1]

    def clean_submodel_stack(self):
        """
        Removes any extra pops in a submodel stack after a delete or
        end_submodel.
        """
        depth = 0
        for frame_index in range(self.instruction_start, len(self.instructions)):
            inst = self.instructions[frame_index]
            if inst.has_key('submodel'):
                if inst['submodel'] == 1:
                    depth = depth + 1
                else: # a pop
                    if depth > 0:
                        depth = depth - 1
                    else:
                        del self.instructions[frame_index]['submodel']

    def pose_transform(self, path, axes, rotates):
        """
        Determines a transformation for a region
        """
        glPushMatrix()
        glLoadIdentity()

        # Determine the transformation
        last_region = path[0]
        for connecting_region in path[1:]:
            if last_region > connecting_region:
                key = (connecting_region, last_region)
            else:
                key = (last_region, connecting_region)
            end = axes[key]
            about = end[0] - end[1]
            angle = rotates[connecting_region]

            glTranslatef(end[0][0], end[0][1], end[0][2])
            glRotatef(angle, about[0], about[1], about[2])
            glTranslatef(-end[0][0], -end[0][1], -end[0][2])

            last_region = connecting_region

        # Calculate new matrix
        matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        glPopMatrix()
        glMultMatrixf(matrix)

        return matrix

    def hold_pose_matrices(self):
        self.region_matrices = []
        for region_index, region in enumerate(self.regions):

            glPushMatrix()

            matrix = self.pose_transform(self.region_paths[region_index], self.region_axes, self.instructions[0]['rotates']) # Pose fixed at frame 0
            self.region_matrices.append(matrix)

            glPopMatrix()

    def pose_centers(self):
        for matrix, region in zip(self.region_matrices, self.regions):
            for part_index in region:
                if part_index >= 0:
                    center = self.netlist[part_index].center_save
                    new_center = np.dot(np.transpose(matrix), np.concatenate((center, [1.0])))[:3]
                    self.netlist[part_index].center = new_center

    def restore_centers(self):
        for part in self.netlist:
            part.center = part.center_save

    def redraw(self, vout, vup, creationmode):
        """
        Draws the module from scratch
        """
        global colors, draw_future_parts, generate_pdf, draw_outline
        #print 'redraw'

        glDrawBuffer(GL_FRONT)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if creationmode == 'modelling':
            for p in self.netlist:
                p.draw()

            self.capture_background()
                
            if draw_outline:
                self.draw_part_outlines()

            # Draw selected
            self.draw_selected(vout, vup, creationmode)

        elif creationmode == 'instructions' and self.frame < self.instruction_start: # pose
            # Used this to draw each region a different color
            #for region_index, region in enumerate(self.regions):
            #    color = colors['region' + str(region_index % 6)]
            #    for part_index in region:
            #        if part_index >= 0:
            #            self.netlist[part_index].draw(color)
            something_selected = len(self.selected)
            for region_index, region in enumerate(self.regions):

                glPushMatrix()

                matrix = self.pose_transform(self.region_paths[region_index], self.region_axes, self.region_rotates)
                self.region_centers[region_index] = np.dot(np.transpose(matrix), np.concatenate((self.region_fixed_centers[region_index], [1.0])))[:3]
                
                if not generate_pdf:
                    if something_selected and region_index == self.selected[0]: # Moving Region
                        color = colors['edit']
                    elif region_index == self.region_fixed: # Fixed Region
                        color = colors['total']
                    else:
                        color = colors['futurepart']
                else:
                    color = None # Allow piece colors
                for part_index in region:
                    if part_index >= 0:
                        self.netlist[part_index].draw(color)

                glPopMatrix()

            self.capture_background()

            if draw_outline:
                self.draw_part_outlines()

        elif creationmode == 'instructions' and self.frame >= self.instruction_start:
            len_self_netlist = len(self.netlist)
            self.part_flags = 2*np.ones(len_self_netlist, np.uint8)
            frame_inc = 0
            if len(self.submodel_stack) > 0:
                hide_old_index = reduce(lambda x, y: x + y, map(lambda z: len(z['new_parts']), self.instructions[:self.submodel_stack[-1]]))
            else:
                hide_old_index = 0
            self.part_flags[self.old_parts[:hide_old_index]] = 3 # discard
            self.part_flags[self.old_parts[hide_old_index:]] = 0
            if self.submodel == -1: # Pop
                # Find the start
                submodel_level = -1
                for frame_index in range(self.frame - 1, -1, -1):
                    submodel_level = submodel_level + self.instructions[frame_index].get('submodel', 0)
                    if submodel_level == 0:
                        break
                show_old_index = reduce(lambda x, y: x + y, map(lambda z: len(z['new_parts']), self.instructions[:frame_index]))
                self.part_flags[self.old_parts[show_old_index:]] = 1
            if generate_pdf:
                self.part_flags[self.selected] = 1
            if not generate_pdf:
                self.part_flags[self.hidden_parts] = 3

            local_colors = [None, colors['newpart'], colors['futurepart']]
            for part_index in range(len_self_netlist):
                if self.part_flags[part_index] == 3:
                    pass
                elif self.part_flags[part_index] == 2 and draw_future_parts == 0:
                    pass
                else:
                    p = self.netlist[part_index]
                    color = local_colors[self.part_flags[part_index]]
                    if self.hold_pose:
                        matrix = self.region_matrices[self.region_lookups[part_index]]
                        glPushMatrix()
                        glMultMatrixf(matrix)
                        p.draw(color)
                        #if draw_outline:
                        #    self.draw_part_outline(p, vout, vup)
                        glPopMatrix()
                    else:
                        p.draw(color)
                        #if draw_outline:
                        #    self.draw_part_outline(p, vout, vup)

            self.capture_background()
            if draw_outline:
                self.draw_part_outlines()

            if not generate_pdf:
                self.draw_selected(vout, vup, creationmode)

        self.redraw_called = 1

    def ends_aligned(self, end1, ends, same_dir = 0):
        """
        Returns whether end1 is aligned with any end in ends
        Returns the index+1 of only one of the ends that are aligned
        Returns 0 if none are aligned
        Returns -1 if there is an error
        """
        if len(ends) <= 0:
            return 0
        #local_ends = np.array(ends)
        sametips = vector_math.mag(end1[0] - ends[:,0]) < xabstol
        sametip_indices = np.nonzero(sametips)[0]
        for sametip_index in sametip_indices:
            end2 = ends[sametip_index]
            if ((same_dir == 0 and np.allclose(end1[0]-end1[1], end2[1]-end2[0], atol=xabstol, rtol=0.0)) or (same_dir == 1 and np.allclose(end1[0]-end1[1], end2[0]-end2[1], atol=xabstol, rtol=0.0))):
                dp = np.dot(end1[0]-end1[2], end2[0]-end2[2])
                if (-1.0 - xabstol < dp < -1.0 + xabstol) or \
                        (-xabstol < dp < xabstol) or \
                        (1.0 - xabstol < dp < 1.0 + xabstol):
                    return sametip_index+1
                else:
                    print 'bad_angle', end1, end2
                    return -1 # aligned but bad angle
        return 0

    def write_netlist(self):
        """
        Returns a string representation of the module
        """
        netlist_version = 1.0
        sf = 1.0/pieces.sf
        # Write version
        written = 'v' + str(netlist_version) + '\n'
        # Write parts
        for part in self.netlist:
            if len(part.configure) > 0:
                configs = reduce(lambda x, y: str(x) + ' ' + str(y), part.configure) + ' '
            else:
                configs = ''
            # May want to change the round in the future depending on parts
            written = written + part.name + ' ' + configs + reduce(lambda x, y: str(x) + ' ' + str(y), map(lambda z: round(z, 1), (sf*part.matrix.reshape(16)).tolist())) + '\n'
        # Write ends
        for end, end_type in zip(self.ends, self.ends_types):
            # May want to change the round in the future depending on parts
            written = written + 'end ' + end_type + ' ' + reduce(lambda x, y: str(x) + ' ' + str(y), map(lambda z: round(z, 1), (sf*np.reshape(end, (1, 9))[0]).tolist())) + '\n'

        # Write instructions
        sizes = {'fullr': 'r', 'full': 'f', 'quarter': 'q', 'halfh': 'h'}
        # Add mass, price, dimensions for easy read-out later
        if len(self.instructions) > 0:
            self.instructions[0]['count'] = '%d' % self.total_inventory()
            self.instructions[0]['mass'] = '%.0f' % self.mass()
            self.instructions[0]['price'] = '%.2f' % self.price()
            self.instructions[0]['dims'] = '%.1f,%.1f,%.1f' % self.dimensions()
        for count, inst in enumerate(self.instructions):
            written = written + 'i %.6e %.6e %.6e %.6e %.6e %.6e %.6e %.6e %.6e %.6e' % (inst['vcenter'][0], inst['vcenter'][1], inst['vcenter'][2], inst['vout'][0], inst['vout'][1], inst['vout'][2], inst['vup'][0], inst['vup'][1], inst['vup'][2], inst['pixperunit'])
            if len(inst['new_parts']) > 1:
                written = written + ' ' + reduce(lambda x, y: str(x) + ' ' + str(y), inst['new_parts'])
            elif len(inst['new_parts']) == 1: # Some numpy bug couldn't reduce a len == 1 list
                written = written + ' ' + str(inst['new_parts'][0])
            written = written + ' ' + sizes[inst['size']]
            remaining_keys = filter(lambda x: x not in ['vcenter', 'vout', 'vup', 'pixperunit', 'new_parts', 'size'], inst.keys())
            for key in remaining_keys:
                written = written + ' ' + key + ': ' + repr(inst[key])
            written = written + '\n'
                
        return written

    def read_netlist(self, netlist):
        """
        Reads a string representation of a module and converts it into
        a module.
        """
        # This newer version takes a few more lines, but it makes
        # files about half-size.
        global colors, xabstol
        glDrawBuffer(GL_FRONT)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        #print 'netlist[0]', netlist[0]

        if netlist[0][0] == '[': # Prior to version 0.4 style netlist
            netlist = eval(netlist[0]) # Convert to list
            for part_line in netlist[0]:
                part = eval('pieces.' + part_line[0] + '()')
                part.name, angle, vrot, angle2, vrot2, delta, flip, part.ends, part.center = part_line
                angle = float(angle)
                vrot = np.array(vrot)/10.0
                angle2 = float(angle2)
                vrot2 = np.array(vrot2)/10.0
                delta = np.array(delta)/10.0
                flip = float(flip)
                part.ends = map(lambda x: (np.array(x[0])/10.0, np.array(x[1])/10.0, np.array(x[2])/10.0), part.ends)
                part.center = np.array(part.center)/10.0
                glPushMatrix()
                glLoadIdentity()
                glRotatef(angle, vrot[0], vrot[1], vrot[2])
                glRotatef(angle2, vrot2[0], vrot2[1], vrot2[2])
                glTranslatef(-delta[0], -delta[1], -delta[2])
                part.matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
                glPopMatrix()
                part.draw()
                self.netlist.append(part)
            self.ends = copy.copy(netlist[1])
            if len(netlist) > 2:
                self.ends_types = copy.copy(netlist[2])
            else:
                self.ends_types = []
                for end in self.ends:
                    done = 0
                    for count, part in enumerate(self.netlist):
                        for part_end in part.ends:
                            aligned_index = self.ends_aligned(part_end, np.array([end]), same_dir=1)
                            #if self.ends_aligned(part_end, end, same_dir=1):
                            if aligned_index > 0:
                                done = 1
                                self.ends_types.append(part.ends_types[count])
                                break
                        if done == 1:
                            break

        elif netlist[0].strip() == 'v0.4': # prior to version 1.0 style netlist
            #lines = netlist.split('\n')
            line_number = 1
            # Pieces
            while line_number < len(netlist) and netlist[line_number][0:3] != 'end' and netlist[line_number][0:2] != 'i ':
                part_line = netlist[line_number].split()
                part = eval('pieces.' + part_line[0] + '()')
                part.name = part_line[0]
                len_configs = len(part_line) - 17 # 17 = name + 16 pos matrix
                if len_configs > 0:
                    for config_index in range(len_configs):
                        part.configure[config_index] = part_line[1+config_index]
                part.matrix = (np.array(map(lambda x: float(x), part_line[1+len_configs:]))/10.0).reshape((4,4))
                part.calc_ends()
                part.draw()
                self.netlist.append(part)
                line_number = line_number + 1
            # Ends
            self.ends = []
            self.ends_types = []
            while line_number < len(netlist) and netlist[line_number][0:2] != 'i ':
                end_line = netlist[line_number].split()
                self.ends_types.append(end_line[1])
                num_end = np.array(map(lambda x: float(x), end_line[2:]))/10.0
                self.ends.append((num_end[0:3], num_end[3:6], num_end[6:9]))
                line_number = line_number + 1

            # Instructions
            sizes = {'f': 'full', 'r': 'fullr', 'q': 'quarter', 'h': 'halfh'}
            while line_number < len(netlist):
                line = netlist[line_number]
                for size in sizes.keys():
                    sizei = line.find(' ' + size)
                    if line[sizei+2] != ' ' and line[sizei+2] != '\n':
                        sizei = -1
                    if sizei >= 0:
                        break
                line_start = line[:sizei].split()[1:]
                line_floats = map(lambda x: float(x), line_start[:10])
                inst = {'vcenter': np.array(line_floats[0:3]),
                        'vout': np.array(line_floats[3:6]),
                        'vup': np.array(line_floats[6:9]),
                        'pixperunit': line_floats[9]}
                inst['new_parts'] = map(lambda x: int(x), line_start[10:])
                inst['size'] = sizes[size]
                # Parse defaults
                line = line[sizei+2:].strip()
                if line:
                    line_split = line.split()
                    default_index = 0
                    while default_index < len(line_split):
                        ls_index = default_index + 1
                        while ls_index < len(line_split) and line_split[ls_index][-1] != ':':
                            ls_index = ls_index + 1
                        inst[line_split[default_index][:-1]] = eval(' '.join(line_split[default_index+1:ls_index]))
                        default_index = ls_index
                # Convert draw_old_parts_from to submodel
                if inst.has_key('draw_old_parts_from'):
                    if inst['draw_old_parts_from'] == 0: # a pop
                        inst['submodel'] = -1
                    else:
                        inst['submodel'] = 1
                    del inst['draw_old_parts_from']
                self.instructions.append(inst)
                line_number = line_number + 1

        elif netlist[0].strip() == 'v1.0': # Latest style netlist
            #lines = netlist.split('\n')
            line_number = 1
            sf = 1.0/pieces.sf
            # Pieces
            while line_number < len(netlist) and netlist[line_number][0:3] != 'end' and netlist[line_number][0:2] != 'i ':
                part_line = netlist[line_number].split()
                try:
                    part = eval('pieces.' + part_line[0] + '()')
                except:
                    print 'Warning: ' + part_line[0] + ' missing'
                    part = None
                if part:
                    part.name = part_line[0]
                    len_configs = len(part_line) - 17 # 17 = name + 16 pos matrix
                    #print part_line, len_configs
                    if len_configs > 0:
                        for config_index in range(len_configs):
                            part.configure[config_index] = part_line[1+config_index]
                    part.matrix = (np.array(map(lambda x: float(x), part_line[1+len_configs:]))/sf).reshape((4,4))
                    part.calc_ends()
                    part.draw()
                    self.netlist.append(part)
                line_number = line_number + 1
            # Ends
            self.ends = []
            self.ends_types = []
            while line_number < len(netlist) and netlist[line_number][0:2] != 'i ':
                end_line = netlist[line_number].split()
                self.ends_types.append(end_line[1])
                num_end = np.array(map(lambda x: float(x), end_line[2:]))/sf
                self.ends.append((num_end[0:3], num_end[3:6], num_end[6:9]))
                line_number = line_number + 1

            # Instructions
            sizes = {'f': 'full', 'r': 'fullr', 'q': 'quarter', 'h': 'halfh'}
            title_line = line_number
            self.instruction_start = 0
            while line_number < len(netlist):
                line = netlist[line_number].strip()
                for size in sizes.keys():
                    sizei = line.find(' ' + size)
                    if sizei + 2 < len(line) and line[sizei+2] != ' ':
                        sizei = -1
                    if sizei >= 0:
                        break
                line_start = line[:sizei].split()[1:]
                line_floats = map(lambda x: float(x), line_start[:10])
                inst = {'vcenter': np.array(line_floats[0:3]),
                        'vout': np.array(line_floats[3:6]),
                        'vup': np.array(line_floats[6:9]),
                        'pixperunit': line_floats[9]}
                inst['new_parts'] = map(lambda x: int(x), line_start[10:])
                if self.instruction_start <= 0 and len(inst['new_parts']) > 0: # Frames started
                    self.instruction_start = line_number - title_line
                inst['size'] = sizes[size]
                # Parse defaults
                line = line[sizei+2:].strip()
                if line:
                    line_split = line.split()
                    default_index = 0
                    while default_index < len(line_split):
                        ls_index = default_index + 1
                        while ls_index < len(line_split) and line_split[ls_index][-1] != ':':
                            ls_index = ls_index + 1
                        inst[line_split[default_index][:-1]] = eval(' '.join(line_split[default_index+1:ls_index]))
                        default_index = ls_index
                # Convert draw_old_parts_from to submodel
                if inst.has_key('draw_old_parts_from'):
                    if inst['draw_old_parts_from'] == 0: # a pop
                        inst['submodel'] = -1
                    else:
                        inst['submodel'] = 1
                    del inst['draw_old_parts_from']
                self.instructions.append(inst)
                line_number = line_number + 1
            if len(self.instructions) > 0 and self.instructions[0].has_key('hold_pose'):
                self.hold_pose = 1

        if self.instruction_start <= 0:
            self.instruction_start = max(1, len(self.instructions))

        glDrawBuffer(GL_FRONT)

        self.capture_background()

        self.history_push()

    def screen_capture(self):
        """
        Returns an np.array representation of the screen
        """
        viewport = glGetIntegerv(GL_VIEWPORT)

        # glReadPixelsub caused a seg fault on old python-opengl
        # versions.  Haven't revisitied.
        return glReadPixels(viewport[0], viewport[1],
                            viewport[2], viewport[3],
                            GL_RGBA, GL_UNSIGNED_INT_8_8_8_8_REV)

    def inventory(self):
        """
        Returns the pieces in the module in a list of (quantity, name)
        """
        i = {}
        for part in self.netlist:
            if len(part.combination) > 0:
                for subpart in part.combination:
                    if i.has_key(subpart):
                        i[subpart] = i[subpart] + 1
                    else:
                        i[subpart] = 1
            else:
                if i.has_key(part.name):
                    i[part.name] = i[part.name] + 1
                else:
                    i[part.name] = 1
            if len(part.configure) > 0:
                for count, config in enumerate(part.configure):
                    config_name, config_ext = part.configure_name(config)
                    if hasattr(part, 'query_options_quantities'):
                        q = part.query_options_quantities[count]
                    else:
                        q = 1
                    if i.has_key(config_name):
                        i[config_name] = i[config_name] + q
                    else:
                        i[config_name] = q
        if i.has_key('None'):
            del i['None']
        names = i.keys()
        retval = []
        for name in names:
            retval.append((i[name], name))

        return retval

    def total_inventory(self):
        """
        Returns the total number of pieces in a module
        """
        return reduce(lambda x, y: x + y, map(lambda z: z[0], self.inventory()))

    def connect(self, part, vout, vup, capture = 1, only_move = 0, record = 1):
        """
        Connects a part to the module
        """
        global colors, xabstol, draw_outline

        bad_angle = 0
        xted_ports = []
        if len(self.netlist) == 0: # Remove the start_ends, if needed
            self.ends = []
            new_ports = range(len(part.ends))
        else:
            new_ports = []
            self_ends = np.array(self.ends)
            for port_index, part_port in enumerate(part.ends):
                aligned_index = self.ends_aligned(part_port, self_ends)
                if aligned_index > 0: # aligned and good angle
                    xted_ports.append(aligned_index-1)
                else:
                    new_ports.append(port_index)
                    if aligned_index == -1:
                        bad_angle = 1

        if not bad_angle:
            if capture:
                self.draw_base()
                glDrawBuffer(GL_FRONT)
                part.draw()

                self.capture_background()

                if draw_outline:
                    self.draw_part_outlines()

                self.draw_selected(vout, vup, 'modelling')

            xted_ports.sort()
            count = 0
            for xted_port in xted_ports: # remove the xted ends
                del self.ends[xted_port - count]
                del self.ends_types[xted_port - count]
                count = count + 1
            for new_port in new_ports: # add the new ends
                self.ends.append(part.ends[new_port])
                self.ends_types.append(part.ends_types[new_port])

            if self.port >= len(self.ends_types):
                self.port = 0

            if not only_move:
                self.netlist.append(part)

            if record:
                self.history_push()

        return bad_angle

    def find_next_port(self, port_type):
        """
        Return the next port of a given type
        """
        if len(self.ends) > 0 and len(self.ends_types) <= 0: # no parts yet
            self.port = 0
            return self.ends[0]
        elif self.ends_types[self.port] == port_type:
            if port_type == 'j':
                search_for = 's'
            else:
                search_for = 'j'
            try:
                self.port = self.ends_types.index(search_for)
            except ValueError:
                print 'No more correct ports' # I don't expect to get here
                return -1
        return self.ends[self.port]

    def remove_part(self, part_index, only_move = 0, record = 1):
        """
        Remove a part from the netlist
        """
        global xabstol
        part = self.netlist[part_index]
        # Fix Ends
        rm_ports = []
        add_ports = []
        self_ends = np.array(self.ends)
        for port_index, part_port in enumerate(part.ends):
            aligned_index = self.ends_aligned(part_port, self_ends, same_dir=1)
            if aligned_index > 0:
                rm_ports.append(aligned_index-1)
            else:
                add_ports.append(port_index)
        rm_ports.sort()
        count = 0
        for rm_port in rm_ports:
            del self.ends[rm_port - count]
            del self.ends_types[rm_port - count]
            count = count + 1
        for add_port in add_ports: # The inverted end is added
            end = part.ends[add_port].copy()
            end[1] = end[0] + end[0] - end[1]
            self.ends.append(end)
            if part.ends_types[add_port] == 'j':
                self.ends_types.append('s')
            else:
                self.ends_types.append('j')

        if not only_move:
            # Remove part
            del self.netlist[part_index]
            if self.port >= len(self.ends_types):
                self.port = 0
            
            # Fix Instructions
            for instruction_index in range(len(self.instructions)):
                inst = self.instructions[instruction_index]
                # Fix new_parts
                new_parts = inst['new_parts']
                try:
                    new_parts.remove(part_index)
                except:
                    pass
                new_parts = np.array(new_parts, np.int32)
                offset = (new_parts > part_index).astype(np.int32)
                new_parts = new_parts - offset
                inst['new_parts'] = new_parts.tolist()
                # Fix magnify
                if inst.has_key('show_magnify'):
                    if len(inst['show_magnify']) == 3:
                        x, y, magnify_index = inst['show_magnify']
                        if magnify_index == part_index:
                            inst['show_magnify'] = (x, y)
                        elif magnify_index > part_index:
                            inst['show_magnify'] = (x, y, magnify_index - 1)
                # Save new instruction
                self.instructions[instruction_index] = inst
                    
        if record:
            self.history_push()

    def remove_parts(self):
        """
        Remove multiple parts from the netlist
        """
        a = np.sort(np.array(self.selected))
        while len(a) > 0:
            self.remove_part(a[0], record = 0)
            a = a[1:]-1
        self.selected = []
        self.history_push()

    def move_selected(self, delta):
        """
        Move the selected parts in a temporary way
        """
        #pdelta = delta*pieces.lenp5
        pdelta = 0.5*delta*pieces.lenp5 # possible with new scales

        glPushMatrix()
        glLoadIdentity()
        glTranslatef(pdelta[0], pdelta[1], pdelta[2])
        
        for count in self.selected:
            glPushMatrix()
            glMultMatrixf(self.netlist[count].matrix)
            self.netlist[count].matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
            glPopMatrix()
        glPopMatrix()

    def rotate_selected(self, angle, about, offset):
        """
        Rotate the selected parts in a temporary way
        """
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(offset[0], offset[1], offset[2])
        glRotatef(angle, about[0], about[1], about[2])
        glTranslatef(-offset[0], -offset[1], -offset[2])

        for count in self.selected:
            glPushMatrix()
            glMultMatrixf(self.netlist[count].matrix)
            self.netlist[count].matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
            glPopMatrix()
        glPopMatrix()

    def mirror_selected(self, axis, offset):
        """
        Mirror the selected parts in a temporary way
        """
        if axis == 0: # x
            m = np.array([[-1.0, 0.0, 0.0, 0.0],
                          [0.0, 1.0, 0.0, 0.0],
                          [0.0, 0.0, 1.0, 0.0],
                          [0.0, 0.0, 0.0, 1.0]])
        elif axis == 1: # y
            m = np.array([[1.0, 0.0, 0.0, 0.0],
                          [0.0, -1.0, 0.0, 0.0],
                          [0.0, 0.0, 1.0, 0.0],
                          [0.0, 0.0, 0.0, 1.0]])
        else: # z
            m = np.array([[1.0, 0.0, 0.0, 0.0],
                          [0.0, 1.0, 0.0, 0.0],
                          [0.0, 0.0, -1.0, 0.0],
                          [0.0, 0.0, 0.0, 1.0]])
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(offset[0], offset[1], offset[2])
        glMultMatrixf(m)
        glTranslatef(-offset[0], -offset[1], -offset[2])

        for count in self.selected:
            glPushMatrix()
            glMultMatrixf(self.netlist[count].matrix)
            self.netlist[count].matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
            glPopMatrix()
        glPopMatrix()

    def write_move(self):
        """
        Write (make it fixed) the move, rotate, or mirror.

        This is simple and works, but for moving many connecting
        parts, it performs many redundant calculations.  I had a more
        complex write_move, but it was buggy.
        """
        for count in self.selected:
            self.remove_part(count, only_move = 1, record = 0)
            self.netlist[count].calc_ends()
            self.connect(self.netlist[count], None, None, capture = 0, only_move = 1, record = 0)
        self.history_push()

    def merge_common(self):
        """
        Merge any common ports in self.ends
        """
        xted_ports = []
        self_ends = np.array(self.ends)
        for count1, end1 in enumerate(self_ends):
            aligned_index = self.ends_aligned(end1, self_ends[count1:])
            if aligned_index > 0:
                count2 = count1 + aligned_index - 1
                xted_ports.append(count1)
                xted_ports.append(count2)
        xted_ports.sort()
        xted_ports.reverse()
        for xted_port in xted_ports:
            del self.ends[xted_port]
            del self.ends_types[xted_port]

        # Correct self.port index
        if self.port >= len(self.ends_types):
            self.port = 0

    def connectivity(self):
        """
        Determines the connectivity of a module.
        """

        # Make blank xtions
        xtions = []
        for p1 in self.netlist:
            xtion = []
            for count in range(len(p1.ends)):
                xtion.append(())
            xtions.append(xtion)

        len_netlist = len(self.netlist)
        for p1i in range(len_netlist):
            p1 = self.netlist[p1i]
            for e1i, e1 in enumerate(p1.ends):
                if xtions[p1i][e1i] == ():
                    for p2i in range(p1i + 1, len_netlist):
                        p2 = self.netlist[p2i]
                        aligned_index = self.ends_aligned(e1, p2.ends)
                        if aligned_index > 0:
                            xtions[p1i][e1i] = [p2i, aligned_index-1]
                            xtions[p2i][aligned_index-1] = [p1i, e1i]
                            break

        return xtions

    def fix(self):
        """
        Tries to fix broken models by
        1. Calculating connectivity and re-deriving self.ends
        2. Should do more ***
        """
        
        # Re-derive self.ends
        xtions = self.connectivity()
        self.ends = []
        self.ends_types = []
        for p1i in range(len(self.netlist)):
            p1 = self.netlist[p1i]
            for e1i, e1 in enumerate(p1.ends):
                if xtions[p1i][e1i] == (): # No connection
                    self.ends.append(e1)
                    self.ends_types.append(p1.ends_types[e1i])

    def find_regions(self):
        """
        Isolate the parts into specific regions that must stay
        together.  2 types of regions: those that are disconnected and
        those that are connected through joinrots.  A joinrot spans
        two regions.  In one region it will be positive.  In the
        other, it will be inverted.  Used inversion instead of
        negative, because 0 does not have a negative.
        """

        xtions = self.connectivity()
        regions = [] # a list of lists of part_indices.  Each list defines a region
        region_lookups = {} # a dictionary of part_index: region_index
        for part_index in range(len(self.netlist)):
            part = self.netlist[part_index]
            try:
                region_indexf = region_lookups[part_index]
            except KeyError: # Region doesn't exist; create it
                regions.append([part_index])
                region_indexf = len(regions)-1
                region_lookups[part_index] = region_indexf

            if len(part.axis) > 0: # a joinrot
                try:
                    region_indexr = region_lookups[~part_index]
                except KeyError: # Region doesn't exist; create it
                    regions.append([~part_index])
                    region_indexr = len(regions)-1
                    region_lookups[~part_index] = region_indexr

            for end_index in range(len(part.ends)):
                xtion = xtions[part_index][end_index]
                if len(xtion) > 0: # is connected
                    xted_part_index, xted_end_index = xtion
                    xtions[xted_part_index][xted_end_index] = [] # Keep the connection back from being processed
                    xted_part = self.netlist[xted_part_index]
                    if end_index in part.axis: # an axis
                        region_index = region_indexr
                        writeback = -1
                    else:
                        region_index = region_indexf
                        writeback = 1
                    if xted_end_index in xted_part.axis: # a joinrot
                        key = ~xted_part_index
                    else:
                        key = xted_part_index
                    if region_lookups.has_key(key):
                        merge_region_index = region_lookups[key]
                        if merge_region_index != region_index:
                            regions[merge_region_index] = regions[merge_region_index] + regions[region_index]
                            for key in regions[region_index]:
                                region_lookups[key] = merge_region_index
                            regions[region_index] = []
                            if writeback == -1:
                                region_indexr = merge_region_index
                            else:
                                region_indexf = merge_region_index
                    else:
                        regions[region_index].append(key)
                        region_lookups[key] = region_index
        regions = filter(lambda x: len(x) > 0, regions)
        self.regions = regions
        region_lookups = {}
        for region_index, region in enumerate(regions):
            for part_index in region:
                region_lookups[part_index] = region_index
        self.region_lookups = region_lookups
        #print region_lookups

        # Now, that we know which joinrots really rotate, versus those
        # that are connected stiff, we can find out what axes we have.

        region_axes = {} # a dictionary of (region_index1, region_index2): end, where region_index1 < region_index2 and end is the axis end
        if len(regions) == 1:
            self.region_axes = []
        else:
            fast_regions = map(lambda x: np.array(x), regions)
            for region_index1, region1 in enumerate(fast_regions):
                joinrot_indices = np.nonzero(region1 < 0)[0]
                for part_index in region1[joinrot_indices]:
                    part_index = absinvert(part_index)
                    for region_index2, region2 in enumerate(fast_regions):
                        if region_index2 != region_index1:
                            matching_indices = np.nonzero(region2 == part_index)[0]
                            if len(matching_indices) > 0: # regions are connected
                                if region_index1 < region_index2:
                                    key = (region_index1, region_index2)
                                else:
                                    key = (region_index2, region_index1)
                                part = self.netlist[part_index]
                                region_axes[key] = part.ends[part.axis[0]] # Okay to keep over-writing, because they should all be the same.
                                break

        self.region_axes = region_axes

        # For now, set the rotational values of each axis to 0.0 ***
        #region_rotates = {}
        #for key in region_axes.keys():
        #    region_rotates[key] = 0.0 # a positive angle makes the first fixed and the second rotated.  a negative angle makes the second fixed and the first rotated.
        #self.region_rotates = region_rotates
        self.region_rotates = [0]*len(regions)

        # Now, let's set up the region centers for selection

        region_centers = []
        for region in regions:
            centers = np.array(map(lambda x: self.netlist[absinvert(x)].center, region))
            region_centers.append(np.mean(centers, 0))
        self.region_centers = np.array(region_centers)
        #self.region_fixed_centers = self.region_centers[:] # does not copy
        self.region_fixed_centers = self.region_centers.copy()

        # Take a guess that the fixed region has the most parts

        if len(regions) > 0:
            fixed = np.argmax(np.array(map(lambda x: len(x), regions)))
            self.set_region_fixed(fixed)
        
        # Now, all regions rotate relative to the fixed region.  Some
        # more, some less.

    def set_region_fixed(self, region_index):
        """
        Sets the fixed region and calculates the path from each region
        to the fixed_region.
        """
        self.region_fixed = region_index
        self.region_paths = []
        region_connections = self.region_axes.keys()
        region_iterator = range(len(self.regions))
        for count in region_iterator:
            self.region_paths.append([])
        trunks = [self.region_fixed]
        while len(region_connections) > 0:
            next_trunks = []
            removed = 0
            for trunk in trunks:
                removes = []
                for count in range(len(region_connections)):
                    region_index1, region_index2 = region_connections[count]
                    if region_index1 == trunk:
                        self.region_paths[region_index2] = self.region_paths[trunk] + [trunk]
                        next_trunks.append(region_index2)
                        removes.append(count)
                    elif region_index2 == trunk:
                        self.region_paths[region_index1] = self.region_paths[trunk] + [trunk]
                        next_trunks.append(region_index1)
                        removes.append(count)
                removes.sort()
                removes.reverse()
                for remove in removes:
                    del region_connections[remove]
                    removed = 1
            if not removed: # a disconnected region
                break
            trunks = next_trunks
        # Append the index to the end
        for count in region_iterator:
            self.region_paths[count].append(count)

    def mass(self):
        """
        Returns the mass of the module
        """
        mass = 0.0
        for part in self.netlist:
            if len(part.combination) > 0:
                names = part.combination
            else:
                names = [part.name]
            for name in names:
                try:
                    mass = mass + pieces.masses[name]
                except:
                    print 'Warning: Couldn\'t find mass of', name
                for config in part.configure:
                    config_name, config_ext = part.configure_name(config)
                    if config_name != 'None':
                        try:
                            mass = mass + pieces.masses[config_name]
                        except:
                            print 'Warning: Couldn\'t find mass of', config_name
        return mass

    def price(self):
        """
        Returns the price of the module.  Excludes instruction
        printing and packaging.
        """
        price = 0.0
        for part in self.netlist:
            if len(part.combination) > 0:
                names = part.combination
            else:
                names = [part.name]
            for name in names:
                try:
                    price = price + pieces.prices[name]
                except:
                    print 'Warning: Couldn\'t find price of', name
                for config in part.configure:
                    config_name, config_ext = part.configure_name(config)
                    if config_name != 'None':
                        try:
                            price = price + pieces.prices[config_name]
                        except:
                            print 'Warning: Couldn\'t find price of', config_name
        return price
        
    def dimensions(self):
        """
        Returns the dimensions of the module in cm.  This is a little
        erroneous since it only calculates the extents of all the
        joints.
        """
        if len(self.netlist) > 0:
            first_pt = self.netlist[0].ends[0][0]
            xmin = first_pt[0]
            xmax = first_pt[0]
            ymin = first_pt[1]
            ymax = first_pt[1]
            zmin = first_pt[2]
            zmax = first_pt[2]
            for part in self.netlist:
                for end in part.ends:
                    pt = end[0]
                    xmin = min(xmin, pt[0])
                    xmax = max(xmax, pt[0])
                    ymin = min(ymin, pt[1])
                    ymax = max(ymax, pt[1])
                    zmin = min(zmin, pt[2])
                    zmax = max(zmax, pt[2])
        else:
            xmin, xmax, ymin, ymax, zmin, zmax = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        sf = 0.1/pieces.sf # conversion to cm
        return tuple(sorted([sf*(xmax-xmin), sf*(ymax-ymin), sf*(zmax-zmin)], reverse = True))

# Don't like using piece library, since this is supposed to be a base for it.
import pieces
