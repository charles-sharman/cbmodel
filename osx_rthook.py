import sys

#os.environ['PANGO_LIBDIR'] = os.environ['PWD']
#os.environ['PANGO_SYSCONFDIR'] = os.environ['PWD']
#os.environ['PANGO_RC_FILE'] = os.environ['PWD'] + '/pangorc'
#os.environ['GDK_PIXBUF_MODULE_FILE'] = os.environ['PWD'] + '/loaders.cache'

os.environ['PANGO_LIBDIR'] = sys._MEIPASS
#os.environ['PANGO_SYSCONFDIR'] = os.environ['PWD']
os.environ['PANGO_RC_FILE'] = sys._MEIPASS + '/pangorc'
os.environ['GDK_PIXBUF_MODULE_FILE'] = sys._MEIPASS + '/loaders.cache'
