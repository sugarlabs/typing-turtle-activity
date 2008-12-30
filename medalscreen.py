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
import logging, os, math, time, copy, json, locale, datetime, random, re
from gettext import gettext as _

# Import PyGTK.
import gobject, pygtk, gtk, pango

# Import Sugar UI modules.
import sugar.activity.activity
from sugar.graphics import *

class MedalScreen(gtk.EventBox):
    def __init__(self, medal, activity):
        gtk.EventBox.__init__(self)
        
        self.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#ffffff'))
        
        self.medal = medal
        self.activity = activity
        
        cert0 = gtk.Label()
        cert0.set_markup("<span size='35000'><b><i>" + _('Certificate of\nAchievement') + "</i></b></span>")
        
        cert1 = gtk.Label()
        cert1.set_markup("<span size='18000'>" + 
            (_('This certifies that on <i><b><u>%(date)s</u></b></i>,\n<i><b><u>%(nick)s</u></b></i> earned a %(type)s medal\nin Typing Turtle lesson <i><b><u>%(lesson)s</u></b></i>.') % medal) +
            "</span>")
        
        wpmlabel = gtk.Label()
        wpmlabel.set_markup("<span size='18000'>" + (_('<b>Words Per Minute:</b> %(wpm)d') % medal) + "</span>" )
        
        accuracylabel = gtk.Label()
        accuracylabel.set_markup("<span size='15000'>" + (_('<b>Accuracy:</b> %(accuracy)d%%') % medal) + "</span>" )
        
        statbox = gtk.HBox()
        statbox.pack_start(wpmlabel, True)
        statbox.pack_start(accuracylabel, True)
        
        oklabel = gtk.Label()
        oklabel.set_markup("<span size='10000'>" + _('Ok') + '</span>')
        okbtn = gtk.Button()
        okbtn.add(oklabel)
        okbtn.connect('clicked', self.ok_cb)
        
        btnbox = gtk.HBox()
        btnbox.pack_start(okbtn, True, True, 100)
        
        vbox = gtk.VBox()
        
        vbox.pack_start(cert0, True, False, 0)
        vbox.pack_start(cert1, False, False, 0)
        vbox.pack_start(gtk.HSeparator(), False, False, 20)
        vbox.pack_start(statbox, False, False, 0)
        vbox.pack_start(gtk.HSeparator(), False, False, 20)
        vbox.pack_start(btnbox, False, False, 40)
        
        self.add(vbox)
        
        self.show_all()

    def ok_cb(self, widget):
        self.activity.pop_screen()
