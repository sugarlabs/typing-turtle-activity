# Copyright 2008 by Kate Scheppke and Wade Brainerd.  
# This file is part of Typing Turtle.
#
# Typing Turtle is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Typing Turtle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Typing Turtle.  If not, see <http://www.gnu.org/licenses/>.

# Import standard Python modules.
import random
from gettext import gettext as _

# Import PyGTK.
import gobject, pygtk, gtk, pango

class TitleScene(gtk.DrawingArea):
    # Maximum portion of the screen the background can fill vertically.
    BACKGROUND_HEIGHT_RATIO = 0.6

    # Border from top right of screen to draw title at.
    TITLE_OFFSET = (20, 30)

    # Font used to display the title.
    TITLE_FONT = 'Times 45'

    def __init__(self):
        gtk.DrawingArea.__init__(self)

        pbuf = gtk.gdk.pixbuf_new_from_file('images/main-background.jpg')

        width_ratio = float(gtk.gdk.screen_width()) / pbuf.get_width()
        height_ratio = float(gtk.gdk.screen_height()*TitleScene.BACKGROUND_HEIGHT_RATIO) / pbuf.get_height()

        ratio = min(width_ratio, height_ratio)
        self.backgroundpixbuf = pbuf.scale_simple(int(pbuf.get_width()*ratio), int(pbuf.get_height()*ratio), gtk.gdk.INTERP_BILINEAR)
 
        self.set_size_request(self.backgroundpixbuf.get_width(), self.backgroundpixbuf.get_height())
        
        self.connect("expose-event", self.expose_cb)
        
        self.title_original = _('Typing Turtle')
        self.title_src = self.title_original
        self.title_text = ''

    def expose_cb(self, area, event):
        bounds = self.get_allocation()
        
        gc = self.get_style().fg_gc[gtk.STATE_NORMAL]

        # Background picture.
        x = (bounds.width - self.backgroundpixbuf.get_width())/2
        self.window.draw_pixbuf(
            gc, self.backgroundpixbuf, 0, 0, 
            x, 0, self.backgroundpixbuf.get_width(), self.backgroundpixbuf.get_height())
        pc = self.create_pango_context()
        
        self.layout = self.create_pango_layout('')
        self.layout.set_font_description(pango.FontDescription(TitleScene.TITLE_FONT))
        
        self.layout.set_text(self.title_original)
        original_size = self.layout.get_size()
        self.x_text = (bounds.width-original_size[0]/pango.SCALE)-TitleScene.TITLE_OFFSET[0]
        self.y_text = TitleScene.TITLE_OFFSET[1]
        gobject.timeout_add(50, self.timer_cb)

    def draw_text(self):
        # Animated Typing Turtle title.
        gc = self.get_style().fg_gc[gtk.STATE_NORMAL]
        self.layout.set_text(self.title_text)
        self.window.draw_layout(gc, self.x_text, self.y_text, self.layout)

    def timer_cb(self):
        if len(self.title_src) > 0:
            self.title_text += self.title_src[0]
            self.title_src = self.title_src[1:]
            self.draw_text()
        else:
            self.draw_text()
            return False

        return True
