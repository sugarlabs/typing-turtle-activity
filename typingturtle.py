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
"""Typing Turtle - Interactive typing tutor for the OLPC XO."""

# Import standard Python modules.
import logging, os, math, time, copy, locale, datetime, random, re
from gettext import gettext as _
from port import json

# Set up remote debugging.
#import dbgp.client
#dbgp.client.brkOnExcept(host='192.168.1.104', port=12900)

# Set up localization.
locale.setlocale(locale.LC_ALL, '')

# Import PyGTK.
import gobject, pygtk, gtk, pango

# Import Sugar UI modules.
import sugar.activity.activity
from sugar.graphics import *

from sugar.presence import presenceservice

# Initialize logging.
log = logging.getLogger('Typing Turtle')
log.setLevel(logging.DEBUG)
logging.basicConfig()

# Change to bundle directory.
bundle_path = sugar.activity.activity.get_bundle_path() 
os.chdir(bundle_path)

# Import activity modules.
import mainscreen, lessonscreen, medalscreen

# This is the main Typing Turtle activity class.
# 
# It owns the main application window, and all the various toolbars and options.
# Activity Screens are stored in a stack, with the currently active screen on top.
class TypingTurtle(sugar.activity.activity.Activity):
    def __init__ (self, handle):
        sugar.activity.activity.Activity.__init__(self, handle)
        self.set_title(_("Typing Turtle"))
        
        self.build_toolbox()
        
        self.screens = []
        self.screenbox = gtk.VBox()
        
        self.owner = presenceservice.get_instance().get_owner()
        
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
        
        # Hide the sharing button from the activity toolbar since we don't support sharing.
        activity_toolbar = self.tbox.get_activity_toolbar()
        activity_toolbar.share.props.visible = False

    def build_toolbox(self):
        self.tbox = sugar.activity.activity.ActivityToolbox(self)
        self.tbox.show_all()
        
        self.set_toolbox(self.tbox)

    def push_screen(self, screen):
        if len(self.screens):
            self.screenbox.remove(self.screens[-1])
        
        self.screenbox.pack_start(screen, True, True)
        self.screens.append(screen)

    def pop_screen(self):
        self.screenbox.remove(self.screens[-1])
        self.screens.pop()
        if len(self.screens):
            self.screenbox.pack_start(self.screens[-1])

    def add_history(self, entry):
        self.data['history'].append(entry)

    def read_file(self, file_path):
        print 'read_file'

        if self.metadata['mime_type'] != 'text/plain':
            return
        
        fd = open(file_path, 'r')
        try:
            text = fd.read()
            print "read %s" % text
            self.data = json.loads(text)
        finally:
            fd.close()

        self.mainscreen.show_next_lesson()

    def write_file(self, file_path):
        print 'write_file'

        if not self.metadata['mime_type']:
            self.metadata['mime_type'] = 'text/plain'
        
        fd = open(file_path, 'w')
        try:
            text = json.dumps(self.data)
            fd.write(text)
            print "wrote %s" % text
        finally:
            fd.close()

