import os, sys

from distutils.core import setup

# Hack to remove the .py extension.  Neither symbolic nor hard links worked.
if sys.argv[1] != 'install':
    from distutils.file_util import copy_file
    copy_file('cbmodel.py', 'cbmodel')

docs = ['README', 'LICENSE', 'cbmodel.pdf']
shares = ['instructions.py', 'base_pieces.py', 'pieces.py', 'vector_math.py', 'logo_white.png', 'logo_black.png', 'symbol.png', 'mirror.png', 'xhair.png', 'scale.png', 'masses.csv', 'prices.csv']
icons = map(lambda x: 'icons/' + x, os.listdir('icons'))
examples = map(lambda x: 'examples/' + x, os.listdir('examples'))
helps = map(lambda x: 'helps/' + x, os.listdir('helps'))
# Surprised the share/ prefix is needed
data_files = [('share/doc/cbmodel', docs),
              ('share/doc/cbmodel/examples', examples),
              ('share/cbmodel', shares),
              ('share/cbmodel/icons', icons),
              ('share/cbmodel/helps', helps)]
name = 'cbmodel'
version = '1.00' # Change also in cbmodel.py

if 0: # Change to 1 for render mode
    ogl_drawings = map(lambda x: 'ogl_drawings/' + x, os.listdir('ogl_drawings'))
    data_files.append(('share/cbmodel/ogl_drawings', ogl_drawings))
    name = name + '_render'

setup(name = name,
      version = version,
      maintainer = 'Seven:Twelve Engineering LLC',
      maintainer_email = 'contact@seventwelveengineering.com',
      description = 'Crossbeams Modeller',
      long_description = '''Crossbeams Modeller allows you to rapidly
develop Crossbeams models in a virtual environment.  Quickly connect,
delete, duplicate, mirror, translate, rotate, break, and rejoin
multiple pieces for rapid design.  When you're satisfied with the
model, enter the Instruction environment and generate step-by-step
Instructions for others to duplicate your work.''',
      url = 'https://crossbeamstoy.com',
      data_files = data_files,
      scripts = ['cbmodel'],
      requires = ['numpy', 'OpenGL', 'gtk', 'gtk.gtkgl', 'PIL', 'reportlab']
      )
