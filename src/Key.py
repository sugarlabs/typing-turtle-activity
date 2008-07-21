import pygtk
pygtk.require('2.0')
import gtk

class Key(gtk.Widget):
    def __init__(self, text, rectangle):
        self.text = text
        self.specs = rectangle

        
    