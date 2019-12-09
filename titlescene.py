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

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Pango
from gi.repository import PangoCairo
from gi.repository import GdkPixbuf


class TitleScene(Gtk.DrawingArea):
    # Maximum portion of the screen the background can fill vertically.
    BACKGROUND_HEIGHT_RATIO = 0.6

    # Border from top right of screen to draw title at.
    TITLE_OFFSET = (20, 50)

    # Font used to display the title.
    TITLE_FONT = 'Times 45'

    def __init__(self):
        Gtk.DrawingArea.__init__(self)

        pbuf = GdkPixbuf.Pixbuf.new_from_file('images/main-background.jpg')

        width_ratio = float(Gdk.Screen.width()) / pbuf.get_width()
        height_ratio = float(Gdk.Screen.height()*TitleScene.BACKGROUND_HEIGHT_RATIO) / pbuf.get_height()

        ratio = min(width_ratio, height_ratio)
        self.backgroundpixbuf = pbuf.scale_simple(int(pbuf.get_width()*ratio), int(pbuf.get_height()*ratio), GdkPixbuf.InterpType.BILINEAR)
 
        self.set_size_request(self.backgroundpixbuf.get_width(), self.backgroundpixbuf.get_height())
        
        self.connect("draw", self.draw_cb)
        
        self.title_original = _('Typing Turtle')
        self.title_src = self.title_original
        self.title_text = ''

    def draw_cb(self, area, cr):
        bounds = self.get_allocation()

        # Background picture.
        x = (bounds.width - self.backgroundpixbuf.get_width())/2

        Gdk.cairo_set_source_pixbuf(cr, self.backgroundpixbuf, 0, 0)
        cr.rectangle(x, 0, self.backgroundpixbuf.get_width(),
                     self.backgroundpixbuf.get_height())
        cr.paint()

        cr.set_source_rgb(0, 0, 0)
        self.pango_layout = PangoCairo.create_layout(cr)
        self.pango_layout.set_font_description(
            Pango.FontDescription(TitleScene.TITLE_FONT))
        self.pango_layout.set_text(str(self.title_original),
                                   len(self.title_original))

        original_size = self.pango_layout.get_size()
        self.x_text = (bounds.width - original_size[0] / Pango.SCALE) - \
            TitleScene.TITLE_OFFSET[0]
        self.y_text = TitleScene.TITLE_OFFSET[1]

        GObject.timeout_add(50, self.timer_cb)

    def draw_text(self):
        # Animated Typing Turtle title.
        window = self.get_window()
        if window is None:
            return
        cr = window.cairo_create()

        cr.move_to(self.x_text, self.y_text)
        self.pango_layout.set_text(str(self.title_text),
                                   len(self.title_text))
        PangoCairo.update_layout(cr, self.pango_layout)
        PangoCairo.show_layout(cr, self.pango_layout)

    def timer_cb(self):
        if len(self.title_src) > 0:
            self.title_text += self.title_src[0]
            self.title_src = self.title_src[1:]
            self.draw_text()
        else:
            self.draw_text()
            return False

        return True
