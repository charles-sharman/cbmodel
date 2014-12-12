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

def draw_par(pdf, x0, y0, width, leading, text, calculate_only = 0):
    """
    Draws a block of text, breaking it at logical spaces according to width.
    """
    start_index = 0
    end_index = 0
    y = y0
    while start_index < len(text):
        line = ''
        while pdf.stringWidth(line) < width and end_index < len(text):
            old_end_index = end_index
            old_line = line
            end_index = text.find(' ', end_index+1)
            if end_index < 0: # No spaces left
                end_index = len(text)
            line = text[start_index:end_index]
        if pdf.stringWidth(line) < width:
            if not calculate_only:
                pdf.drawString(x0, y, line)
        else:
            if not calculate_only:
                pdf.drawString(x0, y, old_line)
            end_index = old_end_index
        y = y - leading
        start_index = end_index
        while start_index < len(text) and text[start_index] == ' ':
            start_index = start_index + 1
    return y

def fill_background(im, background_color):
    """
    Fills an RGBA image with a background_color (0 to 255 3-tuple)
    """
    retval = im.copy()
    imbg = Image.new('RGB', retval.size, background_color)
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

def draw_title(pdf, cover_image, logo_image, dimensions, author, num_pieces, title, paper_size, background_color, annotate_color, title_font, label_font, term_font, units, x0 = 0, y0 = 0, dpi = 300.0):
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
    pdf.drawString(x0 + column1_width + 72*BLOCK_INNER_MARGIN, y0 + 1*row_height + 0.2*label_font[1], num_pieces)
    pdf.drawString(x0 + column1_width + 72*BLOCK_INNER_MARGIN, y0 + 0.2*label_font[1], 'U.S.A.')
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
            x0 = x0 - width/4
            y0 = y0 + 1*row_height
            pdf.drawString(x0, y0, title[:index].upper())
            y0 = y0 - title_font[1]
            pdf.drawString(x0, y0, title[index+1:].upper())

    # Restore Rotation
    if rotated:
        pdf.rotate(-90.0)

def draw_insets(pdf, help_tuples, x, y, background_color, annotate_color, title_color, title_background_color, title_font, label_font, dpi, share_directory):
    """
    Draws a help inset on the frame.
    x, y are the upper left position
    """
    full_tuples = []
    for help_tuple in help_tuples:
        name, title, annotation = help_tuple
        margin = 0.5*label_font[1]
        # draw the image
        if type(name) == type(()):
            im1 = Image.open(os.path.join(share_directory, 'helps', 'help_' + name[0] + '_left.png'))
            im2 = Image.open(os.path.join(share_directory, 'helps', 'help_' + name[1] + '_right.png'))
            im = Image.new('RGBA', (im1.size[0] + im2.size[0], max(im1.size[1], im2.size[1])))
            im.paste(im1, (0, 0, im1.size[0], im1.size[1]))
            im.paste(im2, (im1.size[0], 0, im1.size[0] + im2.size[0], im2.size[1]))
        else:
            im = Image.open(os.path.join(share_directory, 'helps', 'help_' + name + '.png'))
        full_tuples.append((im.size[0], name, title, annotation, im))
    full_tuples.sort()
    full_tuples.reverse()
    for full_tuple in full_tuples:
        size0, name, title, annotation, im = full_tuple
        box = bbox(im)
        imcrop = im.crop((0, box[1], im.size[0], box[3]))
        #print 'imcrop.size', imcrop.size
        im_width = 72*imcrop.size[0]/dpi
        im_height = 72*imcrop.size[1]/dpi
        annotation_height = -draw_par(pdf, 0, 0, im_width - 2*margin, 1.2*label_font[1], annotation, calculate_only = 1)
        #print 'annotation_height', annotation_height
        im = Image.new('RGBA', (imcrop.size[0], int(imcrop.size[1] + dpi/72.0*(title_font[1] + annotation_height + 4*margin))))
        #print 'im.size', im.size
        im.paste(imcrop, (0, int(dpi/72.0*(title_font[1] + 2*margin)), imcrop.size[0], int(dpi/72.0*(title_font[1] + 2*margin) + imcrop.size[1])))
        im = fill_background(im, color255(background_color))
        pdf.drawInlineImage(im, x, y - 72*im.size[1]/dpi, im_width, 72*im.size[1]/dpi)
        # draw the border
        pdf.setStrokeColorRGB(annotate_color[0], annotate_color[1], annotate_color[2])
        pdf.setFillColorRGB(annotate_color[0], annotate_color[1], annotate_color[2])
        pdf.setLineWidth(1.0)
        pdf.rect(x, y - 72*im.size[1]/dpi, im_width, 72*im.size[1]/dpi, fill = 0)
        # draw the annotation
        pdf.setFont(title_font[0], title_font[1])
        text_width = pdf.stringWidth(title)
        #pdf.setStrokeColorRGB(title_color[0], title_color[1], title_color[2])
        #pdf.setFillColorRGB(title_background_color[0], title_background_color[1], title_background_color[2])
        #draw_outlined_text(pdf, title_font, (x + im_width/2 - text_width/2, y - margin - title_font[1]), title)
        pdf.setStrokeColorRGB(annotate_color[0], annotate_color[1], annotate_color[2])
        pdf.setFillColorRGB(annotate_color[0], annotate_color[1], annotate_color[2])
        pdf.drawString(x + im_width/2 - text_width/2, y - margin - title_font[1], title)
        pdf.setStrokeColorRGB(annotate_color[0], annotate_color[1], annotate_color[2])
        pdf.setFillColorRGB(annotate_color[0], annotate_color[1], annotate_color[2])
        pdf.setFont(label_font[0], label_font[1])
        #pdf.drawCentredString(x + im_width/2, ypos + 0.5*label_font[1], annotation)
        draw_par(pdf, x + margin, y - 72*im.size[1]/dpi + annotation_height - 1.2*label_font[1] + margin, im_width - 2*margin, 1.2*label_font[1], annotation)
        y = y - 72*im.size[1]/dpi

def generate_instructions(screen, share_directory, filename, scale = 1.0):
    """
    Uses reportlab to generate a pdf instruction sheet for cbmodel.

    I didn't like splitting the class across two files, but it was
    getting unwieldy.

    Replacing OpenGL text with pdf text shrinks filesize by 5% and it
    allows anti-aliased fonts.  However, it requires maintaining two
    code bases.  I chose to make the OpenGL text annotations minimal,
    spending most of the time on the pdf annotations.
    """

    def draw_back(ybottom, ytop):
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
        labels = screen.alias_inventory()
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
        pdf.setFillColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
        #pdf.setFont(subtitle_font[0], subtitle_font[1])
        #y0 = 72*screen.PAPER_SIZE[1] - margin - 0.5*subtitle_font[1]
        #pdf.drawCentredString(72*screen.PAPER_SIZE[0]/2, y0, 'JOINING')
        scale = 72.0 / 300
        background_color255 = color255(screen.background_color)
        pdf.setFont(inventory_font[0], inventory_font[1])

        xhalf = 72*(screen.MARGIN_SIZE+screen.FRAME_SIZE[0]+screen.SEP_SIZE)
        yhalf = 72*(screen.MARGIN_SIZE+screen.FRAME_SIZE[1]+screen.SEP_SIZE)
        xcenter = 72*(screen.MARGIN_SIZE+screen.FRAME_SIZE[0]+screen.SEP_SIZE/2+0.5/72) # 0.5/72 for line thickness
        ycenter = 72*(screen.MARGIN_SIZE+screen.FRAME_SIZE[1]+screen.SEP_SIZE/2+0.5/72) # 0.5/72 for line thickness
        width_half = 72*screen.FRAME_SIZE[0]
        width_full = 72*screen.COVER_SIZE[0]
        height_half = 72*screen.FRAME_SIZE[1]
        height_full = 72*screen.COVER_SIZE[1]
        widths = [width_half, width_half, width_full]
        heights = [height_half, height_half, height_half]
        positions = [(margin, yhalf), (xhalf, yhalf), (margin, margin)]
        images = ['joint_asmbly1.png',
                  'joint_asmbly2.png',
                  'joint_asmbly3.png']
        captions = ['Slide beam into joint.',
                    'Twist ring 45 degrees.',
                    'When the marks align, you\'re done!']
        for frame, position, in enumerate(positions):
            width = widths[frame]
            height = heights[frame]
            #print 'width, height', width/scale, height/scale
            image = Image.open(os.path.join(share_directory, 'helps', images[frame]))
            image = fill_background(image, background_color255)
            xsize, ysize = image.size
            yscale = float(height) / ysize
            cropx = int((xsize - width / yscale) / 2.0)
            #if frame == len(images)-1:
            #    cropy = 2*inventory_font[1]
            #    position = (position[0], position[1] + cropy)
            #else:
            #    cropy = 0
            cropy = 0
            image = image.crop((cropx, cropy/yscale, xsize - cropx, ysize))
            pdf.drawInlineImage(fuzzy_frame(image, FADE/screen.ps_scale*screen.PS_SCALE, DPI, screen.background_color), position[0], position[1]+cropy, scale*image.size[0], scale*image.size[1])
            if frame == len(images)-1:
                x0 = position[0] + 0.25*width
            else:
                x0 = position[0] + width/2
            pdf.drawCentredString(x0, position[1]+part_font[1]*1.2, captions[frame])
            #draw_outlined_text(pdf, inventory_font, (position[0] + width/2 - 0.5*pdf.stringWidth(captions[frame]), position[1]+part_font[1]*1.2), captions[frame])
            
        # Done Frame's annotations
        pdf.drawCentredString(xcenter - 0.10*width, ycenter - 0.21*height, 'Mark')
        pdf.drawCentredString(xcenter, ycenter - 0.31*height, 'Mark')
        #draw_outlined_text(pdf, inventory_font, (xcenter - 0.10*width - 0.5*pdf.stringWidth('Mark'), ycenter-0.21*height), 'Mark')
        #draw_outlined_text(pdf, inventory_font, (xcenter - 0.5*pdf.stringWidth('Tab'), ycenter - 0.31*height), 'Tab')
        #pdf.line(xcenter, ycenter + 72*screen.SEP_SIZE, xcenter, y0 - 72*screen.SEP_SIZE)

        # Frame's lines
        pdf.line(xcenter, ycenter + 72*screen.SEP_SIZE, xcenter, ycenter + height_half)
        pdf.line(xcenter - width_half, ycenter, xcenter + width_half, ycenter)
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
                pdf.setStrokeColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
                pdf.setFillColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
                pdf.drawInlineImage(fuzzy_frame(screen.screen_capture(), FADE, DPI, screen.background_color), position[0], position[1], width, height)
                #pdf.drawInlineImage(screen.screen_capture(), position[0], position[1], width, height)

                if frame_type == 'frame':
                    pdf.setStrokeColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
                    pdf.setFillColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
                    framenum = screen.total.frame - screen.total.instruction_start + 1
                    text = str(framenum)
                    pdf.setFont(framenum_font[0], framenum_font[1])
                    framenum_text_width = pdf.stringWidth(text)
                    draw_outlined_text(pdf, framenum_font, (position[0] + width - framenum_text_width - FMS, position[1] + height - 0.75*framenum_font[1] - FMS), text)
                    if len(screen.total.submodel_stack) > 0: # Draw submodels, if need be
                        x0 = position[0] + width - framenum_text_width - FMS
                        y = position[1] + height - 0.75*framenum_font[1] - FMS - 0.2*SUB_HEIGHT
                        pdf.setLineWidth(1)
                        for count in range(1, len(screen.total.submodel_stack)+1):
                            y = y - 1.2*SUB_HEIGHT
                            pdf.roundRect(x0, y, framenum_text_width, SUB_HEIGHT, SUB_HEIGHT/2.0, 1, 1)

                    pdf.setStrokeColorRGB(screen.PRINT_BODY_COLOR[1][0], screen.PRINT_BODY_COLOR[1][1], screen.PRINT_BODY_COLOR[1][2])
                    pdf.setFillColorRGB(screen.PRINT_BODY_COLOR[2][0], screen.PRINT_BODY_COLOR[2][1], screen.PRINT_BODY_COLOR[2][2])
                    if not inst.has_key('hide_part_labels'):
                        pdf.setFont(part_font[0], part_font[1])
                        for label in screen.part_labels:
                            x = 72*float(label[0][0])/(screen.ps_scale*screen.SCREEN_SCALE)
                            y = 72*float(label[0][1])/(screen.ps_scale*screen.SCREEN_SCALE)
                            if len(label[1]) > 1 and label[1][0] == label[1][-1]: # Eliminate the last coupler from the label
                                local_label = label[1][:-1]
                            else:
                                local_label = label[1][:]
                            for config_index in range(len(local_label)):
                                text = screen.name2simple[local_label[config_index]]
                                text_width = pdf.stringWidth(text)
                                draw_outlined_text(pdf, part_font, (position[0] + x - text_width/2, position[1] + y + (-0.5 + 1.2*((len(local_label)-1)/2.0 - config_index))*part_font[1]), text)
                    pdf.setStrokeColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
                    pdf.setFillColorRGB(screen.annotate_color[0], screen.annotate_color[1], screen.annotate_color[2])
                    pdf.setFont(footnote_text_font[0], footnote_text_font[1])
                    y0 = position[1] + FMS
                    dy = 1.2*footnote_text_font[1]
                    # Labels in reverse order of importance
                    # Add crosshair label
                    if 'crosshair' not in helper_labels and len(screen.magnify_pos) > 0:
                        im = screen.images['magnify']['im_print']
                        im = fill_background(im, color255(screen.background_color))
                        im = im.resize((int(im.size[0]/3), int(im.size[1]/3)))
                        text = ' : The next frame is centered on this piece.'
                        total_width = pdf.stringWidth(text) + 72*im.size[0]/DPI
                        pdf.drawInlineImage(im, position[0] + width/2 - total_width/2, y0, 72*im.size[0]/DPI, 72*im.size[1]/DPI)
                        draw_outlined_text(pdf, footnote_text_font, (position[0] + width/2 - total_width/2 + 72*im.size[0]/DPI, y0), text)
                        y0 = y0 + dy
                        helper_labels.append('crosshair')
                    # Add mirror label
                    if 'mirror' not in helper_labels and len(screen.mirror_pos) > 0:
                        im = screen.images['mirror']['im_print']
                        im = fill_background(im, color255(screen.background_color))
                        im = im.resize((int(im.size[0]/3), int(im.size[1]/3)))
                        text = ' : Copy new pieces from old pieces.'
                        total_width = pdf.stringWidth(text) + 72*im.size[0]/DPI
                        pdf.drawInlineImage(im, position[0] + width/2 - total_width/2, y0, 72*im.size[0]/DPI, 72*im.size[1]/DPI)
                        draw_outlined_text(pdf, footnote_text_font, (position[0] + width/2 - total_width/2 + 72*im.size[0]/DPI, y0), text)
                        y0 = y0 + dy
                        helper_labels.append('mirror')
                    # Add submodel end
                    if 'submodel_start' in helper_labels and 'submodel_end' not in helper_labels and len(screen.total.submodel_stack) <= 0:
                        text = 'Submodel ends'
                        text_width = pdf.stringWidth(text)
                        arrow_width = pdf.stringWidth('XX')
                        x = position[0] + width - framenum_text_width - FMS - text_width - arrow_width - FMS
                        y = position[1] + height - 0.75*framenum_font[1] - FMS - 1.4*SUB_HEIGHT - footnote_text_font[1]/4.0
                        draw_outlined_text(pdf, footnote_text_font, (x, y), text)
                        draw_outlined_text(pdf, symbol_font, (x + text_width + pdf.stringWidth('x'), y), chr(222).decode(symbol_font[2], 'ignore').encode('utf8'))
                        text = 'Connect submodel to model.'
                        text_width = pdf.stringWidth(text)
                        draw_outlined_text(pdf, footnote_text_font, (position[0] + width/2 - text_width/2, y0), text)
                        y0 = y0 + dy
                        helper_labels.append('submodel_end')
                    # Add submodel start
                    if 'submodel_start' not in helper_labels and len(screen.total.submodel_stack) > 0:
                        text = 'Submodel begins'
                        text_width = pdf.stringWidth(text)
                        arrow_width = pdf.stringWidth('XX')
                        x = position[0] + width - framenum_text_width - FMS - text_width - arrow_width - FMS
                        y = position[1] + height - 0.75*framenum_font[1] - FMS - 1.4*SUB_HEIGHT - footnote_text_font[1]/4.0
                        draw_outlined_text(pdf, footnote_text_font, (x, y), text)
                        draw_outlined_text(pdf, symbol_font, (x + text_width + pdf.stringWidth('x'), y), chr(222).decode(symbol_font[2], 'ignore').encode('utf8'))
                        helper_labels.append('submodel_start')
                    # Add connect label
                    if 'connect_pieces' not in helper_labels and ((framenum == 2 and len(screen.total.submodel_stack) <= 0) or framenum == 3):
                        text = 'Connect new pieces together before connecting to old pieces.'
                        text_width = pdf.stringWidth(text)
                        draw_outlined_text(pdf, footnote_text_font, (position[0] + width/2 - text_width/2, y0), text)
                        y0 = y0 + dy
                        helper_labels.append('connect_pieces')
                    # Add Piece Names label
                    if 'piece_labels' not in helper_labels and framenum == 1:
                        text = 'See back for piece names.'
                        text_width = pdf.stringWidth(text)
                        draw_outlined_text(pdf, footnote_text_font, (position[0] + width/2 - text_width/2, y0), text)
                        y0 = y0 + dy
                        helper_labels.append('piece_labels')
                    # Add new part label
                    if 'new_pieces' not in helper_labels and framenum == 1:
                        text = 'New pieces are drawn blue.  Old pieces are drawn white.'
                        text_width = pdf.stringWidth(text)
                        draw_outlined_text(pdf, footnote_text_font, (position[0] + width/2 - text_width/2, y0), text)
                        y0 = y0 + dy
                        helper_labels.append('new_pieces')
                    # Check for insets
                    insets = []
                    for label in screen.part_labels:
                        text = ''
                        if len(label[1]) > 1: # an inset box
                            name = label[3]
                            local_label = label[1]
                            alias_label = map(lambda x: screen.name2alias[x], local_label)
                            title = reduce(lambda x, y: x + ' ' + y, alias_label)
                            text = label[2]
                        if text and name not in helper_labels:
                            insets.append((name, title, text))
                            helper_labels.append(name)
                    draw_insets(pdf, insets, position[0] + margin, position[1] + height - margin, screen.background_color, screen.annotate_color, screen.PRINT_BODY_COLOR[1], screen.PRINT_BODY_COLOR[2], part_font, footnote_text_font, DPI, share_directory)
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

    normal_font = 'Helvetica'
    bold_font = normal_font + '-Bold'

    title_font = (normal_font, 40)
    term_font = (normal_font, 12)
    label_font = (normal_font, 20)
    subtitle_font = (normal_font, 24)
    inventory_font = (normal_font, 12)
    framenum_font = (bold_font, 24)
    part_font = (bold_font, 10)
    footnote_font = (bold_font, 10)
    footnote_text_font = (normal_font, 10)
    symbol_font = ('ZapfDingbats', 10, 'ZapfDingbatsEncoding')
    website_font = (bold_font, 10)

    DPI = screen.SCREEN_SCALE * screen.PS_SCALE
    SUB_HEIGHT = framenum_font[1]/6.0
    FMS = 72*screen.FRAME_MARGIN_SIZE
    FRAME_RAD = 5.0
    FADE = 2.0 * screen.ps_scale

    pdf = pdfcanvas.Canvas(filename, pagesize = (72*screen.PAPER_SIZE[0], 72*screen.PAPER_SIZE[1]))
    screen.toggle_frame(None) # Save current frame
    screen.total.frame = 0

    # Make the Title Page
    screen.status_bar.set_text('Drawing title page')
    screen.omit_logo = 1
    screen.window_color(None, screen.PRINT_COVER_COLOR)
    screen.toggle_frame(None, 0, 0)
    screen.toggle_frame(None, 0, 0) # Double Render necessary for proper draw ***
    im = screen.screen_capture()
    margin = 72*screen.MARGIN_SIZE
    width = 72*screen.COVER_SIZE[0]
    height = 72*screen.COVER_SIZE[1]
    dimensions = screen.total.dimensions()
    try:
        author = screen.total.instructions[0]['author']
    except:
        author = ''
    num_pieces = str(screen.total.total_inventory())
    try:
        title = screen.total.instructions[0]['title']
    except:
        title = ''
    
    pdf.setStrokeColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
    pdf.setFillColorRGB(screen.background_color[0], screen.background_color[1], screen.background_color[2])
    if screen.background_color[0] + screen.background_color[1] + screen.background_color[2] > 1.5:
        logo_color = 'black'
    else:
        logo_color = 'white'
    pdf.rect(0, 0, 72*screen.PAPER_SIZE[0], 72*screen.PAPER_SIZE[1], fill = 1)
    draw_title(pdf, im, screen.images['logo_' + logo_color]['im_print'], dimensions, author, num_pieces, title, screen.PAPER_SIZE, screen.background_color, screen.annotate_color, title_font, label_font, term_font, 'ft', 0, 0, screen.SCREEN_SCALE * screen.PS_SCALE)
    pdf.showPage()
    screen.window_color(None, screen.PRINT_BODY_COLOR)

    # Make the first inner page blank if there are too many pages
    # Booklet conversion done externally -- no longer needed
    #num_pages = screen.page_count()
    #if num_pages % 4 != 0:
    #    pdf.showPage()
    #    num_pages = num_pages + 1

    # Make the pose pages
    draw_frames(1, screen.total.instruction_start - 1, 'pose')

    # Make the connection page
    draw_joining()

    # Make the individual pages
    frame_index = screen.total.instruction_start
    draw_frames(frame_index, len(screen.total.instructions) - 1, 'frame')

    # Make the total pages a multiple of 4
    # Booklet conversion done externally -- no longer needed
    #while num_pages % 4 != 0:
    #    pdf.showPage()
    #    num_pages = num_pages + 1

    # Make the Back Cover
    margin = 72*screen.MARGIN_SIZE
    margin = 2*margin # twice on back cover
    screen.status_bar.set_text('Drawing inventory page')
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
    logo_cover = screen.images['logo_' + logo_color]['im_print'].copy()
    background_color255 = color255(screen.background_color)
    logo_cover = fill_background(logo_cover, background_color255)
    xsize, ysize = logo_cover.size
    ybottom = margin + 72*ysize/DPI + 0.5*margin
    pdf.setLineWidth(1.0)
    pdf.line(margin, ybottom, 72*screen.PAPER_SIZE[0] - margin, ybottom)
    pdf.drawInlineImage(logo_cover, 72*screen.PAPER_SIZE[0]/2 - 72*xsize/2/DPI, margin, 72*xsize/DPI, 72*ysize/DPI)
    # inventory
    draw_back(ybottom, ytop)
    pdf.showPage()
    pdf.save()

    screen.glarea.window.set_cursor(screen.REGULAR_CURSOR)
    screen.status_bar.set_text('Instructions done')
