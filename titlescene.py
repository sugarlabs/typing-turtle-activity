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
import pangocairo


class TitleScene(gtk.DrawingArea):
    # Maximum portion of the screen the background can fill vertically.
    BACKGROUND_HEIGHT_RATIO = 0.6

    # Border from top right of screen to draw title at.
    TITLE_OFFSET = (20, 50)

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

        cr = self.window.cairo_create()

        # Background picture.
        x = (bounds.width - self.backgroundpixbuf.get_width())/2
        cr.set_source_pixbuf(self.backgroundpixbuf, 0, 0)
        cr.rectangle(x, 0, self.backgroundpixbuf.get_width(),
                     self.backgroundpixbuf.get_height())
        cr.paint()

        cr = pangocairo.CairoContext(cr)
        cr.set_source_rgb(0, 0, 0)
        self.pango_layout = cr.create_layout()
        self.pango_layout.set_font_description(
            pango.FontDescription(TitleScene.TITLE_FONT))
        self.pango_layout.set_text(unicode(self.title_original))

        original_size = self.pango_layout.get_size()
        self.x_text = (bounds.width - original_size[0] / pango.SCALE) - \
            TitleScene.TITLE_OFFSET[0]
        self.y_text = TitleScene.TITLE_OFFSET[1]

        gobject.timeout_add(50, self.timer_cb)

    def draw_text(self):
        # Animated Typing Turtle title.
        cr = self.window.cairo_create()

        cr.move_to(self.x_text, self.y_text)
        self.pango_layout.set_text(unicode(self.title_text))
        cr.show_layout(self.pango_layout)
        cr.stroke()

    def timer_cb(self):
        if len(self.title_src) > 0:
            self.title_text += self.title_src[0]
            self.title_src = self.title_src[1:]
            self.draw_text()
        else:
            self.draw_text()
            return False

        return True
