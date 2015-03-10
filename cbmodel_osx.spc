# -*- mode: python -*-
a = Analysis(['cbmodel.py'],
             pathex=['/Users/apple/Downloads/cbmodel-0.92'],
             hiddenimports=['reportlab.rl_settings'],
             hookspath=None,
             runtime_hooks=['osx_rthook.py'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts, # + [('v', '', 'OPTION')],
          exclude_binaries=True,
          name='cbmodel',
          debug=False,
          strip=None,
          upx=True,
          console=False )

base_dir = '.'
docs = ['README', 'LICENSE', 'cbmodel.pdf']
shares = ['logo_white.png', 'logo_black.png', 'logo_install.bmp', 'symbol.png', 'symbol.ico', 'mirror.png', 'xhair.png', 'scale.png', 'warning.png', 'masses.csv', 'prices.csv']
gtks = ['osx_loaders.cache', 'osx_pangorc', 'osx_pango.modules', 'osx_pangox.aliases']
data_files = Tree(os.path.join(base_dir, 'icons'), prefix='icons') + \
             Tree(os.path.join(base_dir, 'helps'), prefix='helps') + \
             Tree(os.path.join(base_dir, 'examples'), prefix='examples') + \
             [(x, os.path.join(base_dir, x), 'DATA') for x in docs] + \
             [(x, os.path.join(base_dir, x), 'DATA') for x in shares] + \
             [(x[4:], os.path.join(base_dir, x), 'DATA') for x in gtks]

more_binaries = []
pixbuf_dir = '/usr/local/lib/gdk-pixbuf-2.0/2.10.0/loaders'
for pixbuf_type in os.listdir(pixbuf_dir):
    if pixbuf_type.endswith('.so'):
        more_binaries.append((pixbuf_type, os.path.join(pixbuf_dir, pixbuf_type), 'BINARY'))

pango_dir = '/usr/local/lib/pango/1.8.0/modules'
for pango_type in os.listdir(pango_dir):
    if pango_type.endswith('.so'):
        more_binaries.append((os.path.join('pango/1.8.0/modules', pango_type), os.path.join(pango_dir, pango_type), 'BINARY'))

coll = COLLECT(exe, data_files,
               a.binaries + more_binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='cbmodel')

app = BUNDLE(coll,
             name='cbmodel.app',
             icon='symbol.icns')

