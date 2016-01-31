#!/usr/bin/python

"""
Description
-----------
Crossbeams Modeller pdf instructions generator.  Heavily integrated
with the MainScreen class of cbmodel.

See cbmodel.py for a description of the package and its history.

Author
------
Charles Sharman

License
-------
Distributed under the GNU GENERAL PUBLIC LICENSE Version 3.  View
LICENSE for details.
"""

import os
import math
import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageChops as ImageChops

import vector_math

try:
    import reportlab.pdfgen.canvas as pdfcanvas
    import reportlab.lib.utils as pdfutils
    import reportlab.pdfbase.pdfmetrics as pdfmetrics
    import reportlab.pdfbase.ttfonts as ttfonts
except:
    pdfcanvas = None

def warning(num_pieces):
    if num_pieces < 250:
        warning = 'WARNING: Small parts.  Age 12+.  Handle responsibly.  U.S. Patent 9,086,087.'
    elif num_pieces < 700:
        warning = 'WARNING: Small parts.  Age 14+.  Not a toy.  Handle responsibly.  U.S. Patent 9,086,087.'
    else:
        warning = 'WARNING: Small parts.  Age 16+.  Not a toy.  Handle responsibly.  U.S. Patent 9,086,087.'
    return warning

# Routines that may be useful as imports are placed here

def color255(color):
    """
    Converts a floating point color (0 to 1.0) to a 255-based color (0
    to 0xff)
    """
    return tuple(map(lambda x: int(round(255*x)), color))

def rect(pdf, x0, y0, width, height, color):
    """
    Draws an image of a filled rectangle in the given color
    Assumes x0, y0, x1, y1 in pts
    """
    im = Image.new('RGB', (width, height), color255(color))
    pdf.drawInlineImage(im, x0, y0, width, height)

def draw_outlined_text(loc, font, pos, text):
    """
    Draws text with an outline around it.  Assumes colors already set.
    """
    #loc.setLineWidth(font[1]/5.0)
    loc.setLineWidth(2)
    text_object = loc.beginText(pos[0], pos[1])
    text_object.setFont(font[0], font[1])
    text_object.setTextRenderMode(1)
    text_object.textLine(text)
    text_object.setTextOrigin(pos[0], pos[1])
    text_object.setTextRenderMode(0)
    text_object.textLine(text)
    loc.drawText(text_object)

def fuzzy_frame(im, border, dpi, background_color):
    """
    Fades an image toward its borders
    """
    border = int(round(border/72.0*dpi))
    bg = color255(list(background_color) + [0])
    imbg = Image.new('RGBA', im.size, bg)
    draw = ImageDraw.Draw(imbg)
    for box in range(border-1, -1, -1):
        opacity = 255-int(255*float(box)/border)
        draw.line([(box, box), (im.size[0]-box, box), (im.size[0]-box, im.size[1]-box), (box, im.size[1]-box), (box, box)], fill = (bg[0], bg[1], bg[2], opacity))
    return Image.composite(imbg, im, imbg)

def fill_background(im, background_color, mode='RGB'):
    """
    Fills an RGBA image with a background_color (0 to 255 3-tuple)
    """
    retval = im.copy()
    if mode == 'RGBA':
        background_color = (background_color[0], background_color[1], background_color[2], 255)
    imbg = Image.new(mode, retval.size, background_color)
    retval = Image.composite(retval, imbg, retval)
    #retval.paste(background_color, (0, 0), ImageChops.invert(retval)) # also worked
    return retval

def outline(im, pixels, outline_color, expand = 1):
    """
    outlines an image in a color border pixels wide.
    """
    if len(im.getbands()) < 4:
        print 'Error: requires alpha channel'
        return
    if not im.im:
        im.load() # Necessary for split to work
    xsize, ysize = im.size
    new_im = Image.new('RGBA', (xsize + 2*pixels, ysize+2*pixels), (0, 0, 0, 0))
    #new_im.paste(im, (pixels, pixels, xsize+pixels, ysize+pixels))
    r, g, b, a = im.split()
    outline = a.point(lambda x: 255 * (x > 128)) # Not all is booleaned still but only noticeable on colored backgrounds ***
    #outline = ImageChops.invert(a)
    #data = np.array(outline.getdata())
    #print data[:10]
    r = outline.point(lambda x: x * outline_color[0])
    g = outline.point(lambda x: x * outline_color[1])
    b = outline.point(lambda x: x * outline_color[2])
    background = Image.merge('RGBA', (r, g, b, a))
    offsets = vector_math.offsets(pixels, pixels - 1) # outline pattern possible as long as distance is less than the minimum thickness of any feature
    for x, y in offsets:
        new_im.paste(background, (pixels + x, pixels + y, pixels + x + xsize, pixels + y + ysize), a)
    new_im.paste(im, (pixels, pixels, pixels + xsize, pixels + ysize), a)
    if not expand:
        new_im = new_im.crop((pixels, pixels, xsize + pixels, ysize + pixels))
    return new_im

def bbox(im):
    """
    PIL .getbbox() bounds at fully transparent pixels drawn in
    something besides black.  This bounds, assuming the upper left
    pixel color is the background
    """
    upper_left = im.getpixel((0, 0))
    bg_im = Image.new(im.mode, im.size, upper_left)
    return ImageChops.difference(im, bg_im).getbbox()

def sizestr(dimensions, units):
    """
    Converts a 3-tuple of cm to the given units and returns a string
    """
    unit_types = {'cm': (1.0, 0),
                  'm': (1.0/100, 1),
                  'in': (1.0/2.54, 0),
                  'ft': (1.0/(2.54*12), 1)}
    format = '%.' + str(unit_types[units][1]) + 'f' + units
    format = format + ' x ' + format + ' x ' + format
    dimstr = format % tuple(map(lambda x: unit_types[units][0]*round(float(x), unit_types[units][1]), dimensions))
    return dimstr

def draw_title(pdf, cover_image, logo_image, warning_image, dimensions, author, num_pieces, title, paper_size, background_color, annotate_color, title_color, title_font, label_font, term_font, units, x0 = 0, y0 = 0, dpi = 300.0, warning_num_pieces = -1):
    """
    draws the title page
    """
    COVER_LOGO_TOP_MARGIN = 0.5
    COVER_PHOTO_MARGIN = 0.25
    BLOCK_INNER_MARGIN = 0.2
    BLOCK_TERM_MARGIN = 0.1
    BLOCK_SIDE_MARGIN = 0.5
    BLOCK_BOTTOM_MARGIN = 0.5
    cover_x0 = x0
    cover_y0 = y0
    # Fonts relative to 8.5x11 paper_size
    row_height = 1.1*term_font[1] + 1.1*label_font[1]
    background_color255 = color255(background_color)
    dimstr = sizestr(dimensions, 'ft')

    logo_cover = fill_background(logo_image, background_color255)

    cover = cover_image.copy()
    cover = cover.crop(bbox(cover))
    xsize, ysize = cover.size
    cover_image_xscale = min((paper_size[0] - 2*BLOCK_SIDE_MARGIN) / (xsize/dpi), (paper_size[1] - COVER_LOGO_TOP_MARGIN - 2*COVER_PHOTO_MARGIN - BLOCK_BOTTOM_MARGIN - 2*row_height/72.0 - logo_cover.size[1]/dpi) / (ysize/dpi))
    cover_image_yscale = min((paper_size[1] - 2*BLOCK_SIDE_MARGIN) / (xsize/dpi), (paper_size[0] - COVER_LOGO_TOP_MARGIN - 2*COVER_PHOTO_MARGIN - BLOCK_BOTTOM_MARGIN - 2*row_height/72.0 - logo_cover.size[1]/dpi) / (ysize/dpi))
    logo_pos = 'center'
    if cover_image_yscale > cover_image_xscale:
        cover_image_yscale_full = min((paper_size[1] - 1.0) / (xsize/dpi), (paper_size[0] - COVER_LOGO_TOP_MARGIN - COVER_PHOTO_MARGIN - BLOCK_BOTTOM_MARGIN - 2*row_height/72.0) / (ysize/dpi)) # logo right/left
        if cover_image_yscale_full > cover_image_yscale:
            top_image = cover.crop((0, 0, xsize, ysize/2))
            extents = bbox(top_image)
            if dpi*paper_size[1]/2 - dpi*BLOCK_SIDE_MARGIN - cover_image_yscale_full*(extents[2] - xsize/2) > logo_cover.size[0] + dpi*COVER_PHOTO_MARGIN:
                cover_image_yscale = cover_image_yscale_full
                logo_pos = 'right'
            elif dpi*paper_size[1]/2 - dpi*BLOCK_SIDE_MARGIN - cover_image_yscale_full*(xsize/2 - extents[0]) > logo_cover.size[0] + dpi*COVER_PHOTO_MARGIN:
                cover_image_yscale = cover_image_yscale_full
                logo_pos = 'left'
        cover_image_scale = cover_image_yscale
        rotated = 1
    else:
        cover_image_scale = cover_image_xscale
        rotated = 0
    cover = fill_background(cover, background_color255)
    cover = cover.resize((int(cover_image_scale*xsize), int(cover_image_scale*ysize)), Image.BILINEAR)
    xsize, ysize = cover.size
    if rotated:
        pdf.rotate(90.0)
        x0 = 72*(cover_y0 + paper_size[1]/2 - xsize/2/dpi)
        if logo_pos == 'center':
            y0 = 72*(-cover_x0 - paper_size[0]) + 72*(BLOCK_BOTTOM_MARGIN + 2*row_height/72.0 - COVER_LOGO_TOP_MARGIN - logo_cover.size[1]/dpi)/2 + 72*paper_size[0]/2 - 72*ysize/2/dpi
        else:
            y0 = 72*(-cover_x0 - paper_size[0]) + 72*(BLOCK_BOTTOM_MARGIN + 2*row_height/72.0 + COVER_PHOTO_MARGIN - COVER_LOGO_TOP_MARGIN)/2 + 72*paper_size[0]/2 - 72*ysize/2/dpi
    else:
        x0 = 72*(cover_x0 + paper_size[0]/2 - xsize/2/dpi)
        y0 = 72*(BLOCK_BOTTOM_MARGIN + 2*row_height/72.0 - COVER_LOGO_TOP_MARGIN - logo_cover.size[1]/dpi)/2 + 72*paper_size[1]/2 + 72*cover_y0 - 72*ysize/2/dpi
    pdf.drawInlineImage(cover, x0, y0, 72*xsize/dpi, 72*ysize/dpi)

    # Cover Logo
    if rotated:
        if logo_pos == 'right':
            x0 = 72*(cover_y0 + paper_size[1] - BLOCK_SIDE_MARGIN - logo_cover.size[0]/dpi) # right
        elif logo_pos == 'left':
            x0 = 72*(cover_y0 + BLOCK_SIDE_MARGIN) # left
        else:
            x0 = 72*(cover_y0 + paper_size[1]/2 - logo_cover.size[0]/2/dpi)
        y0 = 72*(-cover_x0 - COVER_LOGO_TOP_MARGIN - logo_cover.size[1]/dpi)
    else:
        x0 = 72*(cover_x0 + paper_size[0]/2 - logo_cover.size[0]/2/dpi)
        y0 = 72*(cover_y0 + paper_size[1] - COVER_LOGO_TOP_MARGIN - logo_cover.size[1]/dpi)
    pdf.drawInlineImage(logo_cover, x0, y0, 72*logo_cover.size[0]/dpi, 72*logo_cover.size[1]/dpi)

    # Cover Title Block
    pdf.setStrokeColorRGB(annotate_color[0], annotate_color[1], annotate_color[2])
    pdf.setFillColorRGB(annotate_color[0], annotate_color[1], annotate_color[2])
    pdf.setFont(label_font[0], label_font[1])
    column1_width = max(pdf.stringWidth(dimstr), pdf.stringWidth(author)) + 2*72*BLOCK_INNER_MARGIN
    column2_width = max(pdf.stringWidth(num_pieces), pdf.stringWidth('U.S.A.')) + 2*72*BLOCK_INNER_MARGIN
    if rotated:
        x0 = 72*(cover_y0 + paper_size[1] - BLOCK_SIDE_MARGIN) - column1_width - column2_width
        y0 = 72*(-cover_x0 - paper_size[0] + BLOCK_BOTTOM_MARGIN)
    else:
        x0 = 72*(cover_x0 + paper_size[0] - BLOCK_SIDE_MARGIN) - column1_width - column2_width
        y0 = 72*(cover_y0 + BLOCK_BOTTOM_MARGIN)
    pdf.line(x0, y0 + row_height, x0 + column1_width + column2_width, y0 + row_height)
    pdf.line(x0, y0, x0, y0 + 2*row_height)
    pdf.line(x0 + column1_width, y0, x0 + column1_width, y0 + 2*row_height)
    # Draw Terms
    pdf.setFont(term_font[0], term_font[1])
    pdf.drawString(x0 + 72*BLOCK_TERM_MARGIN, y0 + 2*row_height - term_font[1], 'SIZE')
    pdf.drawString(x0 + 72*BLOCK_TERM_MARGIN, y0 + 1*row_height - term_font[1], 'DESIGNER')
    pdf.drawString(x0 + 72*BLOCK_TERM_MARGIN + column1_width, y0 + 2*row_height - term_font[1], 'PIECES')
    pdf.drawString(x0 + 72*BLOCK_TERM_MARGIN + column1_width, y0 + 1*row_height - term_font[1], 'MADE IN')
    # Draw Labels
    pdf.setFont(label_font[0], label_font[1])
    pdf.drawString(x0 + 72*BLOCK_INNER_MARGIN, y0 + 1*row_height + 0.2*label_font[1], dimstr)
    pdf.drawString(x0 + 72*BLOCK_INNER_MARGIN, y0 + 0.2*label_font[1], author)
    pdf.drawString(x0 + column1_width + 72*BLOCK_INNER_MARGIN, y0 + 0.2*label_font[1], 'U.S.A.')
    pdf.setStrokeColorRGB(title_color[0], title_color[1], title_color[2])
    pdf.setFillColorRGB(title_color[0], title_color[1], title_color[2])
    pdf.drawString(x0 + column1_width + 72*BLOCK_INNER_MARGIN, y0 + 1*row_height + 0.2*label_font[1], num_pieces)
    # Draw Title.
    pdf.setFont(title_font[0], title_font[1])
    if rotated:
        x0 = (x0 + 72*BLOCK_SIDE_MARGIN)/2
        max_width = 72*(paper_size[1] - 2*BLOCK_SIDE_MARGIN - column1_width/72.0 - column2_width/72.0 - COVER_PHOTO_MARGIN)

    else:
        x0 = (x0 + 72*(cover_x0 + BLOCK_SIDE_MARGIN))/2
        max_width = 72*(paper_size[0] - 2*BLOCK_SIDE_MARGIN - column1_width/72.0 - column2_width/72.0 - COVER_PHOTO_MARGIN)
    width = pdf.stringWidth(title.upper(), title_font[0], title_font[1])
    #print rotated, max_width, width, title
    if width <= max_width:
        y0 = y0 + 1*row_height - 0.5*title_font[1]
        pdf.drawCentredString(x0, y0, title.upper())
    else: # Word wrap
        # Break in two rows at most
        start = 0
        len_title = len(title)
        index = len_title
        best = len_title / 2
        while start >= 0:
            start = title.find(' ', start + 1)
            if start >= 0:
                if abs(start - best) < abs(index - best):
                    index = start
        if index >= len_title: # Only one word
            y0 = y0 + 1*row_height - 0.5*title_font[1]
            pdf.drawCentredString(x0, y0, title.upper())
        else:
            title1 = title[:index].upper()
            title2 = title[index+1:].upper()
            width = max(pdf.stringWidth(title1, title_font[0], title_font[1]),
                        pdf.stringWidth(title2, title_font[0], title_font[1]))
            x0 = x0 - width/2
            #x0 = x0 - width/4
            y0 = y0 + 1*row_height
            pdf.drawString(x0, y0, title1)
            y0 = y0 - title_font[1]
            pdf.drawString(x0, y0, title2)
    # Draw Legal Jargon
    pdf.setFont(term_font[0], term_font[1])
    pdf.setStrokeColorRGB((annotate_color[0]+background_color[0])/2, (annotate_color[1]+background_color[1])/2, (annotate_color[2]+background_color[2])/2)
    pdf.setFillColorRGB((annotate_color[0]+background_color[0])/2, (annotate_color[1]+background_color[1])/2, (annotate_color[2]+background_color[2])/2)
    if rotated:
        x0 = 72*(cover_y0 + paper_size[1]/2)
        y0 = 72*(-cover_x0 - paper_size[0] + 0.5*BLOCK_BOTTOM_MARGIN) - term_font[1]/2
    else:
        x0 = 72*(cover_x0 + paper_size[0]/2)
        y0 = 72*(cover_y0 + 0.5*BLOCK_BOTTOM_MARGIN) - term_font[1]/2
    if warning_num_pieces < 0:
        warning_num_pieces = num_pieces
    text = warning(int(warning_num_pieces))
    space = 0.25*term_font[1]
    warning_cover = fill_background(warning_image, background_color255)
    text_width = pdf.stringWidth(text) + 72*warning_cover.size[0]/dpi + space
    pdf.drawInlineImage(warning_cover, x0 - text_width/2, y0, 72*warning_cover.size[0]/dpi, 72*warning_cover.size[1]/dpi)
    pdf.drawString(x0 - text_width/2 + 72*warning_cover.size[0]/dpi + space, y0, text)
    pdf.setStrokeColorRGB(annotate_color[0], annotate_color[1], annotate_color[2])
    pdf.setFillColorRGB(annotate_color[0], annotate_color[1], annotate_color[2])

    # Restore Rotation
    if rotated:
        pdf.rotate(-90.0)

def generate_instructions(screen, share_directory, filename, scale=1.0, pages=['front', 'joining', 'frames', 'combined', 'back'], custom_inventory={}):
    """
    Uses reportlab to generate a pdf instruction sheet for cbmodel.

    I didn't like splitting the class across two files, but it was
    getting unwieldy.

    Replacing OpenGL text with pdf text shrinks filesize by 5% and it
    allows anti-aliased fonts.
    """

    def draw_back(ybottom, ytop, labels):
        scale_leading = scale*11.2/25.4*72
        scale_offset = scale*4.2/25.4*72 - inventory_font[1]/4
        yscale = 4*scale_leading + scale_offset + 0.67*subtitle_font[1]
        #print 'font_height', subtitle_font[1]/72.0
        #print 'yscale', yscale/72

        def balance(cum_heights, num_piles):
            """
            Takes an array of ordered heights and balances them into a
            number of piles
            """
            perfect_height = cum_heights[-1] / float(num_piles)
            indices = [0]
            for count in range(num_piles - 1):
                index = np.argmin(np.abs(cum_heights - perfect_height * (count + 1)))
                indices.append(index)
            indices.append(len(cum_heights)-1)
            return indices

        # Inventory Items
        pdf.setFillColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
        pdf.setFont(inventory_font[0], inventory_font[1])
        leading = 1.2*inventory_font[1]
        pictures = []
        for label in labels:
            im = Image.open(os.path.join(share_directory, 'icons', screen.alias2name[label[0]] + '.png'))
            imbg = Image.new('RGB', im.size, color255(screen.background_color))
            im = Image.composite(im, imbg, im) # Fill alpha with bg
            im_width = 72*im.size[0]/float(screen.IMAGE_SCALE*screen.PS_SCALE*screen.SCREEN_SCALE)
            im_height = 72*im.size[1]/float(screen.IMAGE_SCALE*screen.PS_SCALE*screen.SCREEN_SCALE)
            pictures.append((im, im_width, im_height, str(label[1]) + 'x ' + label[0]))
        #aspect = (screen.PAPER_SIZE[0] - 2*screen.MARGIN_SIZE) / (screen.PAPER_SIZE[1] - 2*screen.MARGIN_SIZE)
        aspect = (screen.PAPER_SIZE[0] - 2*screen.MARGIN_SIZE) / ((ytop - ybottom - yscale) / 72.0)
        im_heights = np.array(map(lambda x: x[2], pictures))
        im_heights = im_heights + 2*leading*np.ones(len(labels))
        cum_heights = np.cumsum(im_heights)
        cum_heights = np.concatenate(([0.0], cum_heights))
        im_widths = np.array(map(lambda x: x[1], pictures))
        txt_widths = np.array(map(lambda x: pdf.stringWidth(x[3]), pictures))
        full_widths = np.maximum(im_widths, txt_widths)
        nom_width = 0.5*full_widths.mean() + 0.5*full_widths.max()
        #num_columns = int(math.ceil(math.sqrt(aspect*cum_heights[-1] / nom_width)))
        num_columns = int(round(math.sqrt(aspect*cum_heights[-1] / nom_width)))
        #print 'num_columns', num_columns, aspect, nom_width, cum_heights[-1]

        column_leads = balance(cum_heights, num_columns)
        #print 'cum_heights', cum_heights
        #print 'column_leads', column_leads
        column_heights = []
        column_widths = []
        for count in range(len(column_leads) - 1):
            column_heights.append(cum_heights[column_leads[count+1]] - cum_heights[column_leads[count]])
            column_widths.append(max(full_widths[column_leads[count]:column_leads[count+1]]))
        column_widths = np.array(column_widths)
        column_height = max(column_heights)
        label_index = 0
        yinventory = column_height + 0.67*subtitle_font[1]
        #print 'yinventory', yinventory/72
        yspace = (ytop - ybottom - yscale - yinventory) / 3.0
        y0 = ytop - yspace - leading - 0.67*subtitle_font[1]
        pdf.setFont(subtitle_font[0], subtitle_font[1])
        pdf.drawCentredString(72*screen.PAPER_SIZE[0]/2, y0 + leading, 'INVENTORY')
        pdf.setFont(inventory_font[0], inventory_font[1])
        for column_index in range(num_columns):
            x = 72*screen.PAPER_SIZE[0]/2 - (column_widths.sum() + leading*(num_columns - 1))/2 + column_widths[:column_index].sum() + leading*column_index + column_widths[column_index]/2
            #print 'column_widths', column_widths, leading, column_leads
            column_offset = 0.0
            if column_leads[column_index+1] - column_leads[column_index] - 1 <= 0:
                local_space = leading
            else:
                local_space = leading + (column_height - column_heights[column_index]) / (column_leads[column_index+1] - column_leads[column_index] - 1)
            for label_index in range(column_leads[column_index], column_leads[column_index+1]):
                column_offset = column_offset + pictures[label_index][2]
                pdf.drawInlineImage(pictures[label_index][0], x-pictures[label_index][1]/2, y0 - column_offset, pictures[label_index][1], pictures[label_index][2])
                column_offset = column_offset + leading
                #text = labels[label_index][0] + 'x ' + labels[label_index][1]
                text = pictures[label_index][3]
                pdf.drawCentredString(x, y0-column_offset, text)
                column_offset = column_offset + local_space

        pdf.setFillColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
        pdf.setFont(inventory_font[0], inventory_font[1])
        labelwidth = pdf.stringWidth('straight1 ')
        im = Image.open(os.path.join(share_directory, 'scale.png'))
        xsize, ysize = im.size
        len2s_pixels = 2712-588 # Empirical
        len2s = 2*44.8-2*9.4
        scalef = scale * (DPI*len2s/25.4) / len2s_pixels
        im = im.resize((int(scalef*xsize), int(scalef*ysize)), Image.BILINEAR)
        im = im.crop(bbox(im))
        im = fill_background(im, color255(screen.background_color))
        x0 = 72*screen.PAPER_SIZE[0]/2 - 72*im.size[0]/2/DPI + labelwidth/2
        y0 = ybottom + yspace # bottom-referenced
        pdf.drawInlineImage(im, x0, y0, 72*im.size[0]/DPI, 72*im.size[1]/DPI)
        x0 = x0 - labelwidth
        y0 = y0 + scale_offset
        pdf.drawString(x0, y0 + 3*scale_leading, 'straight1')
        pdf.drawString(x0, y0 + 2*scale_leading, 'straight2')
        pdf.drawString(x0, y0 + 1*scale_leading, 'straight3')
        pdf.drawString(x0, y0, 'straight4')
        pdf.setFont(subtitle_font[0], subtitle_font[1])
        pdf.drawCentredString(72*screen.PAPER_SIZE[0]/2, y0 + 4*scale_leading, 'ACTUAL SIZE')

    def draw_joining():
        """
        Draws the joint connection
        """
        pdf.setStrokeColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
        pdf.setFillColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
        #pdf.setFont(subtitle_font[0], subtitle_font[1])
        #y0 = 72*screen.PAPER_SIZE[1] - margin - 0.5*subtitle_font[1]
        #pdf.drawCentredString(72*screen.PAPER_SIZE[0]/2, y0, 'JOINING')
        scale = 72.0 / 300
        background_color255 = color255(screen.background_color)
        pdf.setFont(inventory_font[0], inventory_font[1])

        xhalf = 72*(screen.MARGIN_SIZE+screen.FRAME_SIZE[0]+screen.SEP_SIZE)
        xcenter = 72*screen.PAPER_SIZE[0]/2
        frame_size_third = (screen.PAPER_SIZE[1] - 2*screen.MARGIN_SIZE-2*screen.SEP_SIZE)/3.0
        y1 = 72*(screen.MARGIN_SIZE+frame_size_third+screen.SEP_SIZE)
        y2 = 72*(screen.MARGIN_SIZE+2*frame_size_third+screen.SEP_SIZE)
        width_half = 72*screen.FRAME_SIZE[0]
        width_full = 72*screen.COVER_SIZE[0]
        height_third = 72*frame_size_third
        height_full = 72*screen.COVER_SIZE[1]
        widths = [width_half, width_half, width_full, width_half, width_half]
        heights = [height_third, height_third, height_third, height_third, height_third]
        positions = [(margin, y2), (xhalf, y2), (margin, y1), (margin, margin), (xhalf, margin)]
        images = ['help_joining1.png',
                  'help_joining2.png',
                  'help_joining3.png',
                  'help_bad_connection.png',
                  'help_good_connection.png']
        captions = ['Slide beam into joint.',
                    'Twist ring 45 degrees.',
                    'When the marks align, you\'re done!',
                    'Wrong\nConnecting/Disconnecting Two Directions',
                    'Right\nConnecting/Disconnecting One Direction']
        for frame, position, in enumerate(positions):
            width = widths[frame]
            height = heights[frame]
            #print 'width, height', width/scale, height/scale
            image = Image.open(os.path.join(share_directory, 'helps', images[frame]))
            image = fill_background(image, background_color255)
            xsize, ysize = image.size
            x0 = 0
            y0 = 0
            if frame >= 3: # Raise The Connection ones a bit higher because of the two-line caption
                y0 = y0 + 3.6*inventory_font[1]
            else:
                yscale = float(height) / ysize
                cropx = int((xsize - width / yscale) / 2.0)
                #cropy = 2*inventory_font[1] / scale
                #y0 = y0 + 2*inventory_font[1]
                cropy = 0
                y0 = 0
                image = image.crop((cropx, cropy, xsize - cropx, ysize))
            pdf.drawInlineImage(fuzzy_frame(image, int(FADE/screen.ps_scale*screen.PS_SCALE), DPI, screen.background_color), position[0]+x0, position[1]+y0, scale*image.size[0], scale*image.size[1])
            if frame == 2:
                x0 = position[0] + 0.25*width
                #x0 = position[0] + width/2
            else:
                x0 = position[0] + width/2
            caption_lines = captions[frame].split('\n')[::-1]
            for count, caption_line in enumerate(caption_lines):
                pdf.drawCentredString(x0, position[1]+(count+1)*inventory_font[1]*1.2, caption_line)
            #draw_outlined_text(pdf, inventory_font, (position[0] + width/2 - 0.5*pdf.stringWidth(captions[frame]), position[1]+part_font[1]*1.2), captions[frame])
            
        # Done Frame's annotations
        pdf.drawCentredString(xcenter - 0.08*widths[2], y2 - 0.15*heights[2], 'Mark')
        pdf.drawCentredString(xcenter - 0.03*widths[2], y2 - 0.21*heights[2], 'Mark')
        #draw_outlined_text(pdf, inventory_font, (xcenter - 0.10*width - 0.5*pdf.stringWidth('Mark'), ycenter-0.21*height), 'Mark')
        #draw_outlined_text(pdf, inventory_font, (xcenter - 0.5*pdf.stringWidth('Tab'), ycenter - 0.31*height), 'Tab')
        #pdf.line(xcenter, ycenter + 72*screen.SEP_SIZE, xcenter, y0 - 72*screen.SEP_SIZE)

        # Frame's lines
        pdf.line(xcenter, y2 + 72*screen.SEP_SIZE, xcenter, y2 + height_third)
        pdf.line(72*screen.MARGIN_SIZE, y2, 72*(screen.PAPER_SIZE[0]-screen.MARGIN_SIZE), y2)
        pdf.line(72*screen.MARGIN_SIZE, y1, 72*(screen.PAPER_SIZE[0]-screen.MARGIN_SIZE), y1)
        pdf.showPage()

    def draw_frames(start_index, end_index, frame_type):

        xhalf = 72*(screen.MARGIN_SIZE+screen.FRAME_SIZE[0]+screen.SEP_SIZE)
        yhalf = 72*(screen.MARGIN_SIZE+screen.FRAME_SIZE[1]+screen.SEP_SIZE)
        xcenter = 72*(screen.MARGIN_SIZE+screen.FRAME_SIZE[0]+screen.SEP_SIZE/2+0.5/72) # 0.5/72 for line thickness
        ycenter = 72*(screen.MARGIN_SIZE+screen.FRAME_SIZE[1]+screen.SEP_SIZE/2+0.5/72) # 0.5/72 for line thickness
        width_half = 72*screen.FRAME_SIZE[0]
        width_full = 72*screen.COVER_SIZE[0]
        height_half = 72*screen.FRAME_SIZE[1]
        height_full = 72*screen.COVER_SIZE[1]

        frame_index = start_index
        len_instructions = end_index + 1
        helper_labels = []
        if frame_type == 'title':
            layouts = [screen.total.instructions[0]['size'][0]]
        else:
            layouts = screen.page_layouts()
        layout_index = 0
        num_frames = 0

        while num_frames < frame_index - 1:
            num_frames = num_frames + len(layouts[layout_index])
            layout_index = layout_index + 1

        while frame_index < len_instructions:

            rotated = 0
            layout = layouts[layout_index]

            # Background
            pdf.setStrokeColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
            pdf.setFillColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
            pdf.rect(0, 0, 72*screen.PAPER_SIZE[0], 72*screen.PAPER_SIZE[1], fill = 1)
            pdf.setStrokeColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
            pdf.setLineWidth(1.0)

            if layout == 'f':
                if screen.total.instructions[frame_index]['size'] == 'full':
                    widths = [width_full]
                    heights = [height_full]
                    positions = [(margin, margin)]
                else: # 'fullr'
                    widths = [height_full]
                    heights = [width_full]
                    positions = [(margin, -72*screen.PAPER_SIZE[0] + margin)]
                    pdf.rotate(90.0)
                    rotated = 1

            elif layout == 'qqqq':
                widths = [width_half, width_half, width_half, width_half]
                heights = [height_half, height_half, height_half, height_half]
                positions = [(margin, yhalf), (xhalf, yhalf), (margin, margin), (xhalf, margin)]
                pdf.line(xcenter, ycenter + 72*screen.SEP_SIZE, xcenter, ycenter + height_half)
                pdf.line(xcenter, ycenter - height_half, xcenter, ycenter - 72*screen.SEP_SIZE)
                pdf.line(xcenter - width_half, ycenter, xcenter - 72*screen.SEP_SIZE, ycenter)
                pdf.line(xcenter + 72*screen.SEP_SIZE, ycenter, xcenter + width_half, ycenter)

            elif layout == 'qqh':
                widths = [width_half, width_half, width_full]
                heights = [height_half, height_half, height_half]
                positions = [(margin, yhalf), (xhalf, yhalf), (margin, margin)]
                pdf.line(xcenter, ycenter + 72*screen.SEP_SIZE, xcenter, ycenter + height_half)
                pdf.line(xcenter - width_half, ycenter, xcenter + width_half, ycenter)

            elif layout == 'hqq':
                widths = [width_full, width_half, width_half]
                heights = [height_half, height_half, height_half]
                positions = [(margin, yhalf), (margin, margin), (xhalf, margin)]
                pdf.line(xcenter, ycenter - height_half, xcenter, ycenter - 72*screen.SEP_SIZE)
                pdf.line(xcenter - width_half, ycenter, xcenter + width_half, ycenter)

            elif layout == 'hh':
                widths = [width_full, width_full]
                heights = [height_half, height_half]
                positions = [(margin, yhalf), (margin, margin)]
                pdf.line(xcenter - width_half, ycenter, xcenter + width_half, ycenter)

            elif layout == 'qh':
                widths = [width_half, width_full]
                heights = [height_half, height_half]
                positions = [(margin, yhalf), (margin, margin)]
                pdf.line(xcenter, ycenter + 72*screen.SEP_SIZE, xcenter, ycenter + height_half)
                pdf.line(xcenter - width_half, ycenter, xcenter + width_half, ycenter)

            elif layout == 'qqq':
                widths = [width_half, width_half, width_half]
                heights = [height_half, height_half, height_half]
                positions = [(margin, yhalf), (xhalf, yhalf), (margin, margin)]
                pdf.line(xcenter, ycenter + 72*screen.SEP_SIZE, xcenter, ycenter + height_half)
                pdf.line(xcenter, ycenter - height_half, xcenter, ycenter - 72*screen.SEP_SIZE)
                pdf.line(xcenter - width_half, ycenter, xcenter - 72*screen.SEP_SIZE, ycenter)
                pdf.line(xcenter + 72*screen.SEP_SIZE, ycenter, xcenter + width_half, ycenter)

            elif layout == 'hq':
                widths = [width_full, width_half]
                heights = [height_half, height_half]
                positions = [(margin, yhalf), (margin, margin)]
                pdf.line(xcenter, ycenter - height_half, xcenter, ycenter - 72*screen.SEP_SIZE)
                pdf.line(xcenter - width_half, ycenter, xcenter + width_half, ycenter)

            elif layout == 'qq':
                widths = [width_half, width_half]
                heights = [height_half, height_half]
                positions = [(margin, yhalf), (xhalf, yhalf)]
                pdf.line(xcenter, ycenter + 72*screen.SEP_SIZE, xcenter, ycenter + height_half)
                pdf.line(xcenter - width_half, ycenter, xcenter + width_half, ycenter)

            elif layout == 'q':
                widths = [width_half]
                heights = [height_half]
                positions = [(margin, yhalf)]
                pdf.line(xcenter, ycenter + 72*screen.SEP_SIZE, xcenter, ycenter + height_half)
                pdf.line(xcenter - width_half, ycenter, xcenter - 72*screen.SEP_SIZE, ycenter)

            elif layout == 'h':
                widths = [width_full]
                heights = [height_half]
                positions = [(margin, yhalf)]
                pdf.line(xcenter - width_half, ycenter, xcenter + width_half, ycenter)

            else:
                print 'Error: Unexpected layout', layout
                sys.exit()

            # Draw each frame
            for frame, position, in enumerate(positions):
                width = widths[frame]
                height = heights[frame]
                inst = screen.total.instructions[frame + frame_index]
                screen.toggle_frame(None, 1, 0)
                #print 'Drawing frame', str(screen.total.frame)
                screen.status_bar.set_text('Drawing frame ' + str(screen.total.frame))
                if inst['size'] != screen.total.instructions[frame + frame_index - 1]['size']:
                    screen.toggle_frame(None, 0, 0) # Force another draw on frame resize to circumvent bug with glDrawPixels not taking effect quickly.  There should be a better way ***

                # compressed file size about 20%, didn't seem worth it
                # because of /tmp usage.  Cannot do in-place jpeg
                # conversion, because reportlab looks for a fp with
                # jpegs
                #local_im = fill_background(fuzzy_frame(screen.screen_capture(), int(FADE), DPI, screen.background_color), color255(screen.background_color))
                #local_im.save('/tmp/tmp.jpg', 'jpeg')
                #local_im = Image.open('/tmp/tmp.jpg')
                #pdf.drawInlineImage(local_im, position[0], position[1], width, height)

                pdf.drawInlineImage(fuzzy_frame(screen.screen_capture(), int(FADE), DPI, screen.background_color), position[0], position[1], width, height)
                #pdf.drawInlineImage(screen.screen_capture(), position[0], position[1], width, height)

                if frame_type == 'frame':
                    screen.annotate.annotate_post((position[0]/72.0, position[1]/72.0))
            if rotated:
                pdf.rotate(-90.0)
            pdf.showPage()
            frame_index = frame_index + len(layout)
            layout_index = layout_index + 1

    screen.glarea.window.set_cursor(screen.WAIT_CURSOR)

    #pdfmetrics.registerFont(ttfonts.TTFont('Trebuchet_MS_Bold', '/usr/share/fonts/truetype/msttcorefonts/Trebuchet_MS_Bold.ttf'))
    #pdfmetrics.registerFont(ttfonts.TTFont('Trebuchet_MS', '/usr/share/fonts/truetype/msttcorefonts/Trebuchet_MS.ttf'))
    #normal_font = 'Trebuchet_MS'
    #bold_font = normal_font + '_Bold'

    #pdfmetrics.registerFont(ttfonts.TTFont('DejaVuSansCondensed-Bold', '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansCondensed-Bold.ttf'))
    #pdfmetrics.registerFont(ttfonts.TTFont('DejaVuSansCondensed', '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansCondensed.ttf'))
    #normal_font = 'DejaVuSansCondensed'
    #bold_font = normal_font + '-Bold'

    #pdfmetrics.registerFont(ttfonts.TTFont('FreeSans-Bold', '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'))
    #pdfmetrics.registerFont(ttfonts.TTFont('FreeSans', '/usr/share/fonts/truetype/freefont/FreeSans.ttf'))
    #normal_font = 'FreeSans'
    #bold_font = normal_font + '-Bold'

    pdfmetrics.registerFont(pdfmetrics.Font('ZapfDingbats', 'ZapfDingbats', 'ZapfDingbatsEncoding'))

    title_font = screen.annotate.print_fonts['title']
    term_font = screen.annotate.print_fonts['term']
    label_font = screen.annotate.print_fonts['label']
    subtitle_font = screen.annotate.print_fonts['subtitle']
    inventory_font = screen.annotate.print_fonts['inventory']
    framenum_font = screen.annotate.print_fonts['framenum']
    part_font = screen.annotate.print_fonts['part']
    footnote_font = screen.annotate.print_fonts['footnote']
    footnote_text_font = screen.annotate.print_fonts['footnote_text']
    symbol_font = screen.annotate.print_fonts['symbol']
    website_font = screen.annotate.print_fonts['website']

    DPI = screen.SCREEN_SCALE * screen.PS_SCALE
    SUB_HEIGHT = framenum_font[1]/6.0
    FMS = 72*screen.FRAME_MARGIN_SIZE
    FRAME_RAD = 5.0
    FADE = 2.0 * screen.ps_scale

    pdf = pdfcanvas.Canvas(filename, pagesize = (72*screen.PAPER_SIZE[0], 72*screen.PAPER_SIZE[1]))
    screen.annotate.set_type('print', pdf)
    screen.toggle_frame(None) # Save current frame

    if screen.creationmode == 'group':
        groups = screen.total.groups
        group_indices = range(len(groups))
    else:
        group_indices = [-1]
    for group_index in group_indices:
        screen.total.group_index = group_index
        if group_index >= 0:
            bookmark = 'Group ' + str(group_index + 1)
            pdf.bookmarkPage(bookmark)
            pdf.addOutlineEntry(bookmark, bookmark)
            prefix = 'Group ' + str(group_index) + ': '
        else:
            prefix = ''
        # Make the Title Page
        screen.total.frame = 0
        screen.status_bar.set_text(prefix + 'Drawing title page')
        screen.omit_logo = 1
        screen.window_color(None, screen.PRINT_COVER_COLOR)
        screen.toggle_frame(None, 0, 0)
        screen.toggle_frame(None, 0, 0) # Double Render necessary for proper draw ***
        pdf.setStrokeColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
        pdf.setFillColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
        if screen.background_color[0] + screen.background_color[1] + screen.background_color[2] > 1.5:
            logo_color = 'black'
        else:
            logo_color = 'white'
        margin = 72*screen.MARGIN_SIZE
        width = 72*screen.COVER_SIZE[0]
        height = 72*screen.COVER_SIZE[1]
        if 'front' in pages:
            im = screen.screen_capture()
            dimensions = screen.total.dimensions()
            try:
                author = screen.total.instructions[0]['author']
            except:
                try:
                    author = screen.total.individual_instructions[0]['author']
                except:
                    author = ''
            if custom_inventory:
                num_pieces = 0
                for key in custom_inventory:
                    num_pieces = num_pieces + custom_inventory[key]
                warning_num_pieces = num_pieces
            elif group_index >= 0:
                num_pieces = screen.total.total_inventory(screen.total.group_pieces[group_index])
                warning_num_pieces = screen.total.total_inventory()
                title_color = screen.PIECE_COLORS['region' + str(group_index % 6)]
            else:
                num_pieces = screen.total.total_inventory()
                warning_num_pieces = num_pieces
                title_color = screen.annotate_color
            try:
                title = screen.total.instructions[0]['title']
            except:
                try:
                    title = screen.total.individual_instructions[0]['title']
                except:
                    title = ''

            pdf.rect(0, 0, 72*screen.PAPER_SIZE[0], 72*screen.PAPER_SIZE[1], fill = 1)
            draw_title(pdf, im,
                       screen.annotate.get_image('logo_' + logo_color)['im_print'],
                       screen.annotate.get_image('warning')['im_print'],
                       dimensions, author, str(num_pieces),
                       title, screen.PAPER_SIZE,
                       screen.background_color, screen.annotate_color, title_color,
                       title_font, label_font, term_font, 'ft', 0, 0,
                       screen.SCREEN_SCALE * screen.PS_SCALE,
                       warning_num_pieces = warning_num_pieces)
            pdf.showPage()

        screen.window_color(None, screen.PRINT_BODY_COLOR)

        # Make the first inner page blank if there are too many pages
        # Booklet conversion done externally -- no longer needed
        #num_pages = screen.page_count()
        #if num_pages % 4 != 0:
        #    pdf.showPage()
        #    num_pages = num_pages + 1

        if 'frames' in pages:
            # Make the pose pages
            if group_index < 0:
                draw_frames(1, screen.total.instruction_start - 1, 'pose')

        if 'joining' in pages:
            # Make the connection page
            draw_joining()

        # Make the individual pages
        if group_index < 0:
            start_frame = screen.total.instruction_start
            end_frame = len(screen.total.instructions) - 1
            indices = None
        else:
            start_frame = groups[group_index]
            if group_index >= len(groups)-1:
                end_frame = len(screen.total.instructions) - 1
            else:
                end_frame = groups[group_index + 1] - 1
            # Find the group inventory
            indices = []
            for framenum in range(start_frame, end_frame + 1):
                inst = screen.total.instructions[framenum]
                indices = indices + inst['new_parts']
        if custom_inventory:
            inventory = custom_inventory.items()
            inventory.sort()
        else:
            inventory = screen.alias_inventory(indices)

        screen.total.frame = start_frame - 1
        if 'frames' in pages:
            draw_frames(start_frame, end_frame, 'frame')

        ## Draw a combined page at back
        if group_index >= 0:
            screen.total.group_index = -1
            screen.total.frame = -1
            if 'combined' in pages:
                draw_frames(0, 0, 'title')

        if 'back' in pages:
            # Make the Back Cover
            margin = 72*screen.MARGIN_SIZE
            margin = 2*margin # twice on back cover
            screen.status_bar.set_text(prefix + 'Drawing inventory page')
            screen.window_color(None, screen.PRINT_COVER_COLOR)
            # Background
            pdf.setStrokeColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
            pdf.setFillColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
            pdf.rect(0, 0, 72*screen.PAPER_SIZE[0], 72*screen.PAPER_SIZE[1], fill = 1)
            # Website
            pdf.setStrokeColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
            pdf.setFillColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
            pdf.setFont(website_font[0], website_font[1])
            pdf.drawCentredString(72*screen.PAPER_SIZE[0]/2, 72*screen.PAPER_SIZE[1] - margin - website_font[1], 'crossbeamstoy.com')
            ytop = 72*screen.PAPER_SIZE[1] - margin - website_font[1] - 0.5*margin
            pdf.setLineWidth(1.0)
            pdf.line(margin, ytop, 72*screen.PAPER_SIZE[0] - margin, ytop)
            # Logo
            pdf.setStrokeColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
            pdf.setFillColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
            logo_cover = screen.annotate.get_image('logo_' + logo_color)['im_print'].copy()
            background_color255 = color255(screen.background_color)
            logo_cover = fill_background(logo_cover, background_color255)
            xsize, ysize = logo_cover.size
            ybottom = margin + 72*ysize/DPI + 0.5*margin
            pdf.setLineWidth(1.0)
            pdf.line(margin, ybottom, 72*screen.PAPER_SIZE[0] - margin, ybottom)
            pdf.drawInlineImage(logo_cover, 72*screen.PAPER_SIZE[0]/2 - 72*xsize/2/DPI, margin, 72*xsize/DPI, 72*ysize/DPI)
            #pdf.setFont(website_font[0], website_font[1])
            #pdf.drawString(margin, (ybottom - 0.5*margin)/2 + 0.5*margin + 0.1*website_font[1], 'Need help?  Try:')
            #pdf.drawString(margin, (ybottom - 0.5*margin)/2 + 0.5*margin - 1.1*website_font[1], 'crossbeamstoy.com/static/instructions_guide.pdf')
            # inventory
            draw_back(ybottom, ytop, inventory)
            pdf.showPage()

    screen.total.group_index = -1
    pdf.save()
    screen.annotate.set_type('screen')

    screen.glarea.window.set_cursor(screen.REGULAR_CURSOR)
    screen.status_bar.set_text('Instructions done')

class Annotate(object):
    """
    Units are inches
    """
    
    def __init__(self, screen, share_directory):
        self.screen = screen
        self.share_directory = share_directory

        self.images = {}
        self.screen_fonts = {}
        self.screen_font_map = {'title': 'Sans 30',
                                'term': 'Sans 9',
                                'label': 'Sans 15',
                                'subtitle': 'Sans 18',
                                'inventory': 'Sans 9',
                                'framenum': 'Sans Bold 18',
                                'part': 'Sans Bold 8',
                                'footnote': 'Sans Bold 8',
                                'footnote_text': 'Sans 8',
                                'symbol': None,
                                'website': 'Sans Bold 10'}
                                
        self.print_fonts = {'title': ('Helvetica', 40),
                            'term': ('Helvetica', 12),
                            'label': ('Helvetica', 20),
                            'subtitle': ('Helvetica', 24),
                            'inventory': ('Helvetica', 12),
                            'framenum': ('Helvetica-Bold', 24),
                            'part': ('Helvetica-Bold', 10),
                            'footnote': ('Helvetica-Bold', 10),
                            'footnote_text': ('Helvetica', 10),
                            'symbol': ('ZapfDingbats', 10, 'ZapfDingbatsEncoding'),
                            'website': ('Helvetica-Bold', 10)}

    def set_type(self, annotate_type, pdf=None):
        self.annotate_type = annotate_type
        self.pdf = pdf

    def get_image(self, name, filename=None):
        if not filename:
            filename = name
        if name not in self.images:
            self.images[name] = self.screen.make_image(name, filename)
        return self.images[name]

    def set_stroke_color(self, color):
        if self.annotate_type == 'screen':
            glColor3fv(color)
        else:
            self.pdf.setStrokeColorRGB(color[0], color[1], color[2])

    def set_fill_color(self, color):
        if self.annotate_type == 'screen':
            glColor3fv(color)
        else:
            self.pdf.setFillColorRGB(color[0], color[1], color[2])

    def set_font(self, fontname):
        if self.annotate_type == 'screen':
            if self.screen_font_map[fontname]:
                if fontname not in self.screen_fonts:
                    screen_font = self.screen_font_map[fontname]
                    screen_fonts_keys = self.screen_fonts.keys()
                    screen_fonts_values = self.screen_fonts.values()
                    try:
                        index = screen_fonts_values.index(screen_font)
                    except:
                        index = -1
                    if index >= 0:
                        self.screen_fonts[fontname] = self.screen_fonts[screen_fonts_keys[index]].copy()
                    else:
                        self.screen_fonts[fontname] = self.screen.make_font(self.screen_font_map[fontname])
                self.font = self.screen_fonts[fontname]
            else:
                self.font = None
        else:
            self.font = self.print_fonts[fontname]
            self.pdf.setFont(self.print_fonts[fontname][0], self.print_fonts[fontname][1])

    def font_height(self):
        if self.annotate_type == 'screen':
            retval = self.font['height'] / self.dpi
        else:
            retval = self.font[1] / 72.0
        return retval

    def text_width(self, text):
        if self.annotate_type == 'screen':
            return len(text)*self.font['width'] / self.dpi
        else:
            return self.pdf.stringWidth(text) / 72.0

    def draw_text(self, position, text):
        if self.annotate_type == 'screen':
            p = gluUnProject(self.dpi*position[0],
                             self.dpi*position[1],
                             0.001, self.model, self.projection,
                             self.viewport)
            glRasterPos3fv(p)
            glListBase(self.font['base'])
            glCallLists(text)
        else:
            draw_outlined_text(self.pdf, self.font, (72*position[0], 72*position[1]), text)

    def draw_par(self, pos, width, leading, text, calculate_only = 0):
        """
        Draws a block of text, breaking it at logical spaces according to width.
        """
        x0, y0 = pos
        start_index = 0
        end_index = 0
        y = y0
        while start_index < len(text):
            line = ''
            while self.text_width(line) < width and end_index < len(text):
                old_end_index = end_index
                old_line = line
                end_index = text.find(' ', end_index+1)
                if end_index < 0: # No spaces left
                    end_index = len(text)
                line = text[start_index:end_index]
            if self.text_width(line) < width:
                if not calculate_only:
                    self.draw_text((x0, y), line)
            else:
                if not calculate_only:
                    self.draw_text((x0, y), old_line)
                end_index = old_end_index
            y = y - leading
            start_index = end_index
            while start_index < len(text) and text[start_index] == ' ':
                start_index = start_index + 1
        return y

    def draw_rect(self, position, width, height, line_width=0):
        """
        Draws a rectangle.  If line_width is set to a positive number,
        makes the rectangle hollow.
        """
        if self.annotate_type == 'screen':
            p1 = np.array(gluUnProject(self.dpi*position[0],
                                       self.dpi*position[1], 0.001,
                                       self.model, self.projection,
                                       self.viewport))
            p2 = np.array(gluUnProject(self.dpi*(position[0] + width),
                                       self.dpi*position[1], 0.001,
                                       self.model, self.projection,
                                       self.viewport))
            p3 = np.array(gluUnProject(self.dpi*(position[0] + width),
                                       self.dpi*(position[1] + height), 0.001,
                                       self.model, self.projection,
                                       self.viewport))
            p4 = np.array(gluUnProject(self.dpi*position[0],
                                       self.dpi*(position[1] + height), 0.001,
                                       self.model, self.projection,
                                       self.viewport))
            glDepthMask(GL_FALSE)
            if line_width > 0: # Hollow
                glLineWidth(self.dpi*line_width)
                glBegin(GL_LINE_LOOP)
            else:
                glBegin(GL_QUADS)
            glVertex3fv(p1)
            glVertex3fv(p2)
            glVertex3fv(p3)
            glVertex3fv(p4)
            glEnd()
            glLineWidth(2.0)
            glDepthMask(GL_TRUE)
        else:
            if line_width > 0: # Hollow
                self.pdf.setLineWidth(72*line_width)
                self.pdf.rect(72*position[0], 72*position[1], 72*width, 72*height, fill=0)
            else:
                self.pdf.setLineWidth(1)
                self.pdf.roundRect(72*position[0], 72*position[1], 72*width, 72*height, 72*height/2.0, 1, 1) # Shouldn't really default to round

    def draw_image(self, position, im):
        if self.annotate_type == 'print' and self.captured: # draw straight to pdf
            self.pdf.drawInlineImage(im, 72*position[0], 72*position[1], 72*im.size[0]/self.dpi, 72*im.size[1]/self.dpi)
        else:
            p = np.array(gluUnProject(self.dpi*position[0], self.dpi*position[1], 0.001, self.model, self.projection, self.viewport)) # offset by 0.001 to avoid possible rectangle clipping
            glRasterPos3fv(p)
            glDepthMask(GL_FALSE)
            #glAlphaFunc(GL_GREATER, 0.5)
            #glEnable(GL_ALPHA_TEST)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_BLEND)
            glDrawPixels(im.size[0], im.size[1], GL_RGBA, GL_UNSIGNED_INT_8_8_8_8_REV, np.frombuffer(im.transpose(Image.FLIP_TOP_BOTTOM).tostring(), dtype=np.uint32))
            #glDisable(GL_ALPHA_TEST)
            glDisable(GL_BLEND)
            glDepthMask(GL_TRUE)

    def draw_logo(self, local_image_type):
        if self.annotate_type == 'screen': # draw_title does with print
            if self.screen.background_color == self.screen.SCREEN_COLOR[0]:
                logo = self.get_image('logo_white')
            else:
                logo = self.get_image('logo_black')
            if logo:
                im = logo['im_' + local_image_type]
                width, height = im.size
                self.draw_image(((self.viewport[2]/2-width/2)/self.dpi, (self.viewport[3]-height)/self.dpi-self.screen.FRAME_MARGIN_SIZE), im)

    def draw_mirror(self, local_image_type):
        mirror = self.get_image('mirror')
        if mirror:
            self.draw_image((self.screen.mirror_pos[0]/float(self.screen.SCREEN_SCALE), self.screen.mirror_pos[1]/float(self.screen.SCREEN_SCALE)), mirror['im_' + local_image_type])

    def draw_magnify(self, local_image_type):
        magnify = self.get_image('xhair')
        if magnify:
            im = magnify['im_' + local_image_type]
            width, height = im.size
            if len(self.screen.magnify_pos) == 2: # a coordinate
                x, y = self.screen.ps_scale*self.screen.magnify_pos[0], self.screen.ps_scale*self.screen.magnify_pos[1]
            else: # a part index
                part_index = self.screen.magnify_pos[-1]
                center = self.screen.total.netlist[part_index].center
                snap_pos = gluProject(center[0], center[1], center[2], self.model, self.projection, self.viewport)
                x = snap_pos[0] - width/2
                y = snap_pos[1] - height/2
                x = max(x, 0)
                x = min(x, self.viewport[2]-width)
                y = max(y, 0)
                y = min(y, self.viewport[3]-height)
                self.screen.magnify_pos = (int(x/self.screen.ps_scale), int(y/self.screen.ps_scale), part_index)
            self.draw_image((x/self.dpi, y/self.dpi), im)

    def generate_helper_labels(self, frame, start_frame = 0):
        helper_labels = []
        for i in range(start_frame, frame):
            inst = self.screen.total.instructions[i]
            framenum = i - start_frame + 1
            if 'crosshair' not in helper_labels and 'show_magnify' in inst:
                helper_labels.append('crosshair')
            if 'mirror' not in helper_labels and 'show_mirror' in inst:
                helper_labels.append('mirror')
            if 'submodel_start' not in helper_labels and 'submodel' in inst:
                helper_labels.append('submodel_start')
            if 'submodel_end' not in helper_labels and 'submodel' in inst and inst['submodel'] == -1:
                helper_labels.append('submodel_end')
            if 'connect_pieces' not in helper_labels and ((framenum == 2 and 'submodel_start' not in helper_labels) or framenum == 3):
                helper_labels.append('connect_pieces')
            if 'piece_labels' not in helper_labels and framenum == 1:
                helper_labels.append('piece_labels')
            if 'new_pieces' not in helper_labels and framenum == 1:
                helper_labels.append('new_pieces')
            for part_index in inst['new_parts']:
                label = self.screen.total.netlist[part_index].label()
                if (len(label) > 1) and (label not in helper_labels):
                    helper_labels.append(label)
        #print 'ghl', start_frame, frame, helper_labels
        return helper_labels

    def draw_insets(self, position, help_tuples):
        """
        Draws a help inset on the frame.
        x, y are the upper left position
        """
        x, y = position
        full_tuples = []
        self.set_font('footnote_text')
        label_font_height = self.font_height()
        margin = 0.5*label_font_height
        im_scale = self.screen.ps_scale / self.screen.PS_SCALE
        for help_tuple in help_tuples:
            name, title, annotation = help_tuple
            # draw the image
            if type(name) == type(()):
                im1 = Image.open(os.path.join(self.share_directory, 'helps', 'help_' + name[0] + '_left.png'))
                im2 = Image.open(os.path.join(self.share_directory, 'helps', 'help_' + name[1] + '_right.png'))
                if im_scale < 0.999:
                    im1 = im1.resize((int(im_scale*im1.size[0]), int(im_scale*im1.size[1])), Image.BILINEAR)
                    im2 = im2.resize((int(im_scale*im2.size[0]), int(im_scale*im2.size[1])), Image.BILINEAR)
                im = Image.new('RGBA', (im1.size[0] + im2.size[0], max(im1.size[1], im2.size[1])))
                im.paste(im1, (0, 0, im1.size[0], im1.size[1]))
                im.paste(im2, (im1.size[0], 0, im1.size[0] + im2.size[0], im2.size[1]))
            else:
                im = Image.open(os.path.join(self.share_directory, 'helps', 'help_' + name + '.png'))
                if im_scale < 0.999:
                    im = im.resize((int(im_scale*im.size[0]), int(im_scale*im.size[1])), Image.BILINEAR)
            full_tuples.append((im.size[0], name, title, annotation, im))
        full_tuples.sort()
        full_tuples.reverse()
        for full_tuple in full_tuples:
            size0, name, title, annotation, im = full_tuple
            box = bbox(im)
            imcrop = im.crop((0, box[1], im.size[0], box[3]))
            #print 'imcrop.size', imcrop.size
            im_width = imcrop.size[0]/self.dpi
            im_height = imcrop.size[1]/self.dpi
            annotation_height = -self.draw_par((0, 0), im_width - 2*margin, 1.2*label_font_height, annotation, calculate_only = 1)
            self.set_font('part')
            title_font_height = self.font_height()
            #print 'annotation_height', annotation_height
            im = Image.new('RGBA', (imcrop.size[0], int(imcrop.size[1] + self.dpi*(title_font_height + annotation_height + 4*margin))))
            #print 'im.size', im.size
            im.paste(imcrop, (0, int(self.dpi*(title_font_height + 2*margin)), imcrop.size[0], int(self.dpi*(title_font_height + 2*margin) + imcrop.size[1])))
            im = fill_background(im, color255(self.screen.background_color), 'RGBA')
            self.draw_image((x, y - im.size[1]/self.dpi), im)
            # draw the border
            self.set_stroke_color(self.screen.annotate_color)
            self.set_fill_color(self.screen.annotate_color)
            self.draw_rect((x, y - im.size[1]/self.dpi), im_width, im.size[1]/self.dpi, 1.0/72)
            # draw the annotation
            self.set_stroke_color(self.screen.background_color)
            self.set_fill_color(self.screen.annotate_color)
            text_width = self.text_width(title)
            self.draw_text((x + im_width/2 - text_width/2,
                            y - margin - title_font_height), title)
            self.set_font('footnote_text')
            self.draw_par((x + margin,
                           y - im.size[1]/self.dpi + annotation_height - 1.2*label_font_height + margin),
                          im_width - 2*margin, 1.2*label_font_height,
                          annotation)
            y = y - im.size[1]/self.dpi

    def annotate_opengl(self):
        """
        Annotate an instruction frame with all openGL window components
        """
        self.model = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.projection = glGetDoublev(GL_PROJECTION_MATRIX)
        self.viewport = glGetIntegerv(GL_VIEWPORT)

        if self.screen.ps_scale == 3 and self.screen.image_type == 'print':
            self.local_image_type = 'print'
        else:
            self.local_image_type = 'screen'
        self.dpi = float(self.screen.ps_scale*self.screen.SCREEN_SCALE)
        glDisable(GL_LIGHTING)
        self.captured = False

        # Draw Title Page
        if self.screen.total.frame == 0 and not self.screen.omit_logo:
            self.draw_logo(self.local_image_type)

        # Draw Mirror
        if len(self.screen.mirror_pos) > 0:
            self.draw_mirror(self.local_image_type)

        # Draw Magnify
        if len(self.screen.magnify_pos) > 0:
            self.draw_magnify(self.local_image_type)

        glEnable(GL_LIGHTING)
        if self.annotate_type == 'screen':
            self.annotate_post()

    def annotate_post(self, position=(0,0)):
        """
        Annotates the rest after the OpenGL draw
        """
        fms = self.screen.FRAME_MARGIN_SIZE
        width = self.viewport[2] / self.dpi
        height = self.viewport[3] / self.dpi
        self.captured = True
        glDisable(GL_LIGHTING)

        # Draw Frame Number
        if self.screen.creationmode == 'group':
            df = self.screen.total.groups[self.screen.total.calc_group_index()]
        else:
            df = self.screen.total.instruction_start
        framenum = self.screen.total.frame - df + 1
        if self.screen.total.frame >= self.screen.total.instruction_start:
            self.set_stroke_color(self.screen.background_color)
            self.set_fill_color(self.screen.annotate_color)
            text = str(framenum)
            self.set_font('framenum')
            font_height = self.font_height()
            sub_height = font_height/6.0
            framenum_text_width = self.text_width(text)
            self.draw_text((position[0] + width - framenum_text_width - fms,
                            position[1] + height - 0.75*font_height - fms),
                           text)

        # Draw submodels, if need be
        if len(self.screen.total.submodel_stack) > 0:
            # Some parameters set in Draw Frame Number
            x0 = position[0] + width - framenum_text_width - fms
            y = position[1] + height - 0.75*font_height - fms - 0.2*sub_height
            for count in range(1, len(self.screen.total.submodel_stack)+1):
                y = y - 1.2*sub_height
                self.draw_rect((x0, y), framenum_text_width, sub_height)

        self.set_stroke_color(self.screen.PRINT_BODY_COLOR[1])
        self.set_fill_color(self.screen.PRINT_BODY_COLOR[2])

        # Draw Part Labels
        try:
            inst = self.screen.total.instructions[self.screen.total.frame]
        except:
            inst = {}
        if self.screen.total.submodel != -1 and len(self.screen.mirror_pos) == 0:
            #print 'inst', inst
            self.set_font('part')
            for label in self.screen.part_labels:
                #print 'label', label
                x = label[0][0] / self.dpi
                y = label[0][1] / self.dpi
                if len(label[1]) > 1 and label[1][0] == label[1][-1]: # Eliminate the last coupler from the label
                    local_label = label[1][:-1]
                else:
                    local_label = label[1][:]
                for config_index in range(len(local_label)):
                    text = self.screen.name2simple[local_label[config_index]]
                    text_width = self.text_width(text)
                    self.draw_text((position[0] + x - text_width/2, position[1] + y + (-0.5 + 1.2*((len(local_label)-1)/2.0 - config_index))*self.font_height()), text)

        # Draw Helper Labels
        self.set_stroke_color(self.screen.background_color)
        self.set_fill_color(self.screen.annotate_color)
        self.set_font('footnote_text')
        y0 = position[1] + fms
        dy = 1.2*self.font_height()
        helper_labels = self.generate_helper_labels(self.screen.total.frame, df)

        # Labels in reverse order of importance
        # Add crosshair label
        if 'crosshair' not in helper_labels and len(self.screen.magnify_pos) > 0:
            magnify = self.get_image('xhair')
            if magnify:
                im = magnify['im_' + self.local_image_type]
                im = fill_background(im, color255(self.screen.background_color), 'RGBA')
                im = im.resize((int(im.size[0]/3), int(im.size[1]/3)))
                text = ' : The next frame is centered on this piece.'
                total_width = self.text_width(text) + im.size[0]/self.dpi
                self.draw_image((position[0] + width/2 - total_width/2, y0), im)
                self.draw_text((position[0] + width/2 - total_width/2 + im.size[0]/self.dpi, y0), text)
                y0 = y0 + dy

        # Add mirror label
        if 'mirror' not in helper_labels and len(self.screen.mirror_pos) > 0:
            mirror = self.get_image('mirror')
            if mirror:
                im = mirror['im_' + self.local_image_type]
                im = fill_background(im, color255(self.screen.background_color), 'RGBA')
                im = im.resize((int(im.size[0]/3), int(im.size[1]/3)))
                text = ' : Copy new pieces from old pieces.'
                total_width = self.text_width(text) + im.size[0]/self.dpi
                self.draw_image((position[0] + width/2 - total_width/2, y0), im)
                self.draw_text((position[0] + width/2 - total_width/2 + im.size[0]/self.dpi, y0), text)
                y0 = y0 + dy

        # Add submodel end
        if 'submodel_start' in helper_labels and 'submodel_end' not in helper_labels and len(self.screen.total.submodel_stack) <= 0:
            text = 'Submodel ends'
            text_width = self.text_width(text)
            arrow_width = self.text_width('XX')
            x = position[0] + width - framenum_text_width - fms - text_width - arrow_width - fms
            y = position[1] + height - 0.75*font_height - fms - 1.4*sub_height - self.font_height()/4.0
            self.draw_text((x, y), text)
            self.set_font('symbol')
            if self.font:
                self.draw_text((x + text_width + self.text_width('x'), y), chr(222).decode(self.font[2], 'ignore').encode('utf8'))
            self.set_font('footnote_text')
            text = 'Connect submodel to model.'
            text_width = self.text_width(text)
            self.draw_text((position[0] + width/2 - text_width/2, y0), text)
            y0 = y0 + dy

        # Add submodel start
        if 'submodel_start' not in helper_labels and len(self.screen.total.submodel_stack) > 0:
            text = 'Submodel begins'
            text_width = self.text_width(text)
            arrow_width = self.text_width('XX')
            x = position[0] + width - framenum_text_width - fms - text_width - arrow_width - fms
            y = position[1] + height - 0.75*font_height - fms - 1.4*sub_height - self.font_height()/4.0
            self.draw_text((x, y), text)
            self.set_font('symbol')
            if self.font:
                self.draw_text((x + text_width + self.text_width('x'), y), chr(222).decode(self.font[2], 'ignore').encode('utf8'))
            self.set_font('footnote_text')

        # Add connect label
        if 'connect_pieces' not in helper_labels and ((framenum == 2 and len(self.screen.total.submodel_stack) <= 0) or framenum == 3):
            text = 'Connect new pieces together before connecting to old pieces.'
            text_width = self.text_width(text)
            self.draw_text((position[0] + width/2 - text_width/2, y0), text)
            y0 = y0 + dy

        # Add Piece Names label
        if 'piece_labels' not in helper_labels and framenum == 1:
            text = 'See back for piece names.'
            text_width = self.text_width(text)
            self.draw_text((position[0] + width/2 - text_width/2, y0), text)
            y0 = y0 + dy

        # Add new part label
        if 'new_pieces' not in helper_labels and framenum == 1:
            text = 'New pieces are drawn blue.  Old pieces are drawn white.'
            text_width = self.text_width(text)
            self.draw_text((position[0] + width/2 - text_width/2, y0), text)
            y0 = y0 + dy

        # Check for insets
        insets = []
        for label in self.screen.part_labels:
            #print 'label', label
            text = ''
            if (len(label[1]) > 1) and (label[1] not in helper_labels): # an inset
                name = label[3]
                local_label = label[1]
                alias_label = map(lambda x: self.screen.name2alias[x], local_label)
                title = reduce(lambda x, y: x + ' ' + y, alias_label)
                text = label[2]
                if text:
                    inset_tuple = (name, title, text)
                    if inset_tuple not in insets:
                        insets.append(inset_tuple)
        if len(insets) > 0:
            self.draw_insets((position[0] + self.screen.MARGIN_SIZE,
                              position[1] + height - self.screen.MARGIN_SIZE),
                             insets)
        glEnable(GL_LIGHTING)
