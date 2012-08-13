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
"""Typing Turtle - Interactive typing tutor for Sugar."""

# Import standard Python modules.
import logging, os, math, time, copy, locale, datetime, random, re
from gettext import gettext as _
import json

# Set up remote debugging.
#import dbgp.client
#dbgp.client.brkOnExcept(host='192.168.1.104', port=12900)

# there is need to set up localization.
# since sugar3.activity.main already seted up gettext envronment
#locale.setlocale(locale.LC_ALL, '')


from gi.repository import Gtk

# Import Sugar UI modules.
import sugar3.activity.activity
from sugar3.graphics import *
from sugar3.graphics import toolbutton
from sugar3 import profile

from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton

# Initialize logging.
log = logging.getLogger('Typing Turtle')
log.setLevel(logging.DEBUG)
logging.basicConfig()

# Change to bundle directory.
bundle_path = sugar3.activity.activity.get_bundle_path() 
os.chdir(bundle_path)

# Set correct DPI for Rsvg and Screen
from gi.repository import PangoCairo

def _get_screen_dpi():
    xft_dpi = Gtk.Settings.get_default().get_property('gtk-xft-dpi')
    dpi = float(xft_dpi / 1024)
    logging.debug('Setting dpi to: %f', dpi)
    # HACK: if the DPI detected is 200.0 it seems we are on an XO, so
    # we return 133 because the XO manage its resolution in a complex
    # way. More information here:
    #     http://wiki.laptop.org/go/Display
    if 200 == int(dpi):
        return 133
    return dpi

dpi = _get_screen_dpi()
font_map_default = PangoCairo.font_map_get_default()
font_map_default.set_resolution(dpi)

# Import activity modules.
import mainscreen, editlessonlistscreen

# This is the main Typing Turtle activity class.
# 
# It owns the main application window, and all the various toolbars and options.
# Activity Screens are stored in a stack, with the currently active screen on top.
class TypingTurtle(sugar3.activity.activity.Activity):
    def __init__ (self, handle):
        sugar3.activity.activity.Activity.__init__(self, handle)
        self.set_title(_("Typing Turtle"))
	self.max_participants = 1
        
        self.build_toolbox()
        
        self.screens = []
        self.screenbox = Gtk.VBox()
        
        self.nick = profile.get_nick_name()
        
        self.wordlist = []
        
        # All data which is saved in the Journal entry is placed in this dictionary.
        self.data = {
            'motd': 'welcome',
            'history': [],
            'medals': {}
        }

        # This calls the read_file method when restoring from the Journal.
        self.set_canvas(self.screenbox)
        
        # Start with the main screen.
        self.mainscreen = mainscreen.MainScreen(self)
        self.push_screen(self.mainscreen)
        
        self.show_all()
        
        self.editorbtn = sugar3.graphics.toolbutton.ToolButton('view-source')
        self.editorbtn.set_tooltip(_("Edit Lessons"))
        self.editorbtn.connect('clicked', self.editor_clicked_cb)

        activity_toolbar = self.toolbar_box.toolbar
        activity_toolbar.insert(self.editorbtn, 1)

        self.editorbtn.show_all()

    def build_toolbox(self):
        self.toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        self.toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        self.toolbar_box.toolbar.insert(separator, -1)

        self.toolbar_box.toolbar.insert(StopButton(self), -1)

        self.set_toolbar_box(self.toolbar_box)
        self.toolbar_box.show_all()

    def editor_clicked_cb(self, btn):
        self.push_screen(editlessonlistscreen.EditLessonListScreen(self, self.mainscreen.lessons))

    def push_screen(self, screen):
        if len(self.screens):
            oldscreen = self.screens[-1]
            
            try:
                oldscreen.leave()
            except:
                pass
            
            self.screenbox.remove(oldscreen)
        
        self.screenbox.pack_start(screen, True, True, 0)
        self.screens.append(screen)
        
        try:
            screen.enter()
        except:
            pass

    def pop_screen(self):
        oldscreen = self.screens.pop()
        
        try:
            oldscreen.leave()
        except:
            pass
        
        self.screenbox.remove(oldscreen)
        
        if len(self.screens):
            screen = self.screens[-1]

            try:
                screen.enter()
            except:
                pass
            
            self.screenbox.pack_start(screen, True, True, 0)
            
    def add_history(self, entry):
        self.data['history'].append(entry)

    def read_file(self, file_path):
        if self.metadata['mime_type'] != 'text/plain':
            return
        
        fd = open(file_path, 'r')
        try:
            text = fd.read()
            self.data = json.loads(text)
            if self.data.has_key('lessons'):
                self.mainscreen.lessons = self.data['lessons']
        finally:
            fd.close()

        self.mainscreen.show_next_lesson()

    def write_file(self, file_path):
        if not self.metadata['mime_type']:
            self.metadata['mime_type'] = 'text/plain'
        
        fd = open(file_path, 'w')
        try:
            self.data['lessons'] = self.mainscreen.lessons
            text = json.dumps(self.data)
            fd.write(text)
        finally:
            fd.close()

