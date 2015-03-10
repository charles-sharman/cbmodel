# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'c:\\Program Files\\CBModel\\cbmodel.py'],
             pathex=['C:\\Users\\Administrator\\Downloads\\pyinstaller-1.5.1'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\cbmodel', 'cbmodel.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=False )

# Adapted from setup.py
base_dir = 'c:/Program Files/CBModel'
docs = ['README', 'LICENSE', 'cbmodel.pdf']
shares = ['logo_white.png', 'logo_black.png', 'logo_install.bmp', 'symbol.png', 'symbol.ico', 'mirror.png', 'xhair.png', 'scale.png', 'warning.png', 'masses.csv', 'prices.csv']
data_files = Tree(os.path.join(base_dir, 'icons'), prefix='icons') + \
             Tree(os.path.join(base_dir, 'helps'), prefix='helps') + \
             Tree(os.path.join(base_dir, 'examples'), prefix='examples') + \
             [(x, os.path.join(base_dir, x), 'DATA') for x in docs] + \
             [(x, os.path.join(base_dir, x), 'DATA') for x in shares]

#print 'a.binaries', repr(a.binaries) # To see the names

# For some reason, seemed to think it needed all of these
#a.binaries = a.binaries - TOC([
#    ('tcl84.dll', '', ''),
#    ('tk84.dll', '', ''),
#    ('numpy.fft.fftpack_lite', '', ''),
#    ('numpy.linalg.lapack_lite', '', ''),
#    ('numpy.random.mtrand', '', '')])

a.binaries = a.binaries + [
    ('opengl32.dll', 'c:/Windows/System32/opengl32.dll', 'BINARY'),
    ('glu32.dll', 'c:/Windows/System32/glu32.dll', 'BINARY'),
    ('gle32.dll', 'c:/Python25/Lib/site-packages/OpenGL/DLLS/gle32.dll', 'BINARY'),
    ('glut32.dll', 'c:/Python25/Lib/site-packages/OpenGL/DLLS/glut32.dll', 'BINARY')]

coll = COLLECT( exe, data_files,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name=os.path.join('dist', 'cbmodel'))
