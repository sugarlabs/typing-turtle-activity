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
import logging, os, math, time, copy, locale, datetime, random, re
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GObject

# Import Sugar UI modules.
import sugar3.activity.activity
import sugar3.graphics.style

class MedalScreen(Gtk.EventBox):
    MEDAL_SIZE = int(4.5 * sugar3.graphics.style.GRID_CELL_SIZE)

    def __init__(self, medal, activity):
        GObject.GObject.__init__(self)
        
        self.modify_bg(Gtk.StateType.NORMAL, Gdk.Color.parse('#ffffff')[1])
        
        self.medal = medal
        self.activity = activity
        
        # Load the image.
        medal_type = medal['type']
        images = {
            'bronze': 'images/bronze-medal.svg',
            'silver': 'images/silver-medal.svg',
            'gold':   'images/gold-medal.svg'
        }
        medalpixbuf = GdkPixbuf.Pixbuf.new_from_file(images[medal_type])
        medalpixbuf = medalpixbuf.scale_simple(MedalScreen.MEDAL_SIZE, MedalScreen.MEDAL_SIZE, GdkPixbuf.InterpType.BILINEAR)
        
        medalimage = Gtk.Image()
        medalimage.set_from_pixbuf(medalpixbuf)

        # Certifications section.
        title = Gtk.Label()
        title.set_markup(_("<span font_desc='Serif Bold Italic 28'>Certificate of Achievement</span>"))
        
        text0 = Gtk.Label()
        text0.set_markup(_("<span font_desc='Sans 16'>This certifies that</span>"))

        text1 = Gtk.Label()
        text1.set_markup(_("<span font_desc='Sans 16'><b><u><i>%(nick)s</i></u></b></span>") % medal)

        text2 = Gtk.Label()
        text2.set_markup(_("<span font_desc='Sans 16'>earned a %(type)s medal in </span>") % medal)

        text3 = Gtk.Label()
        text3.set_markup(_("<span font_desc='Sans 16'>in <b><u><i>%(lesson)s</i></u></b></span>") % medal)

        text4 = Gtk.Label()
        text4.set_markup(_("<span font_desc='Sans 16'>on <b><u><i>%(date)s</i></u></b>.</span>") % medal)

        textbox = Gtk.VBox()
        textbox.pack_start(text0, True, True, 0)
        textbox.pack_start(text1, True, True, 0)
        textbox.pack_start(text2, True, True, 0)
        textbox.pack_start(text3, True, True, 0)
        textbox.pack_start(text4, True, True, 0)

        medalbox = Gtk.HBox()
        medalbox.pack_start(textbox, True, True, 0)
        medalbox.pack_end(medalimage, True, True, 0)

        # Stats section.
        statbox = Gtk.HBox()
        if medal.has_key('wpm'):
            stat1 = Gtk.Label()
            stat1.set_markup("<span size='18000'>" + (_('<b>Words Per Minute:</b> %(wpm)d') % medal) + "</span>" )
            statbox.pack_start(stat1, True, True, 0)
        
            stat2 = Gtk.Label()
            stat2.set_markup("<span size='18000'>" + (_('<b>Accuracy:</b> %(accuracy)d%%') % medal) + "</span>" )
            statbox.pack_start(stat2, True, True, 0)

        elif medal.has_key('score'):
            stat1 = Gtk.Label()
            stat1.set_markup("<span size='18000'>" + (_('<b>SCORE:</b> %(score)d') % medal) + "</span>" )
            statbox.pack_start(stat1, True, True, 0)
        
        oklabel = Gtk.Label()
        oklabel.set_markup("<span size='10000'>" + _('Press the ENTER key to continue.') + '</span>')
        self.okbtn = Gtk.Button()
        self.okbtn.add(oklabel)
        self.okbtn.connect('clicked', self.ok_cb)

        btnbox = Gtk.HBox()
        btnbox.pack_start(self.okbtn, True, True, 100)
        
        vbox = Gtk.VBox()
        
        vbox.pack_start(title, False, False, 0)
        vbox.pack_start(medalbox, True, False, 0)
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 20)
        vbox.pack_start(statbox, False, False, 0)
        
        frame = Gtk.Frame()
        frame.add(vbox)
        frame.set_border_width(10)

        box = Gtk.VBox()
        box.pack_start(frame, True, True, 0)
        box.pack_start(btnbox, False, False, 40)

        self.add(box)
        
        self.show_all()

        self.connect('realize', self.realize_cb)

    def realize_cb(self, widget):
        # For some odd reason, if I do this in the constructor, nothing happens.
        self.okbtn.set_can_default(True)
        self.okbtn.grab_default()

    def ok_cb(self, widget):
        self.activity.pop_screen()
