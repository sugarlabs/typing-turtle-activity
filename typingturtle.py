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
#!/usr/bin/env python
"""Typing Turtle - Interactive typing tutor for the OLPC XO."""

# Import standard Python modules.
import logging, os, math, time, copy, json
from gettext import gettext as _

# Import PyGTK.
import gobject, pygtk, gtk, pango

# Import Sugar UI modules.
import sugar.activity.activity
from sugar.graphics import *

# Initialize logging.
log = logging.getLogger('Typing Turtle')
log.setLevel(logging.DEBUG)
logging.basicConfig()

import keyboard

class LessonScreen(gtk.VBox):
    def __init__(self, lesson, activity):
        gtk.VBox.__init__(self)

        self.lesson = lesson
        self.activity = activity

        # Build the user interface.
        title = gtk.Label()
        title.set_markup("<span size='20000'><b>" + lesson['name'] + "</b></span>")
        title.set_alignment(1.0, 0.0)

        stoplabel = gtk.Label(_('Go Back'))
        stopbtn =  gtk.Button()
        stopbtn.add(stoplabel)
        stopbtn.connect('clicked', self.stop_cb)

        hbox = gtk.HBox()
        hbox.pack_start(stopbtn, False, False, 10)
        hbox.pack_end(title, True, True, 10)

        self.lessontext = gtk.Label()
        self.lessontext.set_alignment(0, 0)

        self.lessonscroll = gtk.ScrolledWindow()
        self.lessonscroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.lessonscroll.add_with_viewport(self.lessontext)
 
        frame = gtk.Frame()
        frame.add(self.lessonscroll)

        self.keyboard = keyboard.Keyboard()
        self.keyboard.set_layout(keyboard.default_layout)

        self.pack_start(hbox, False, False, 10)
        self.pack_start(frame, True)
        self.pack_start(self.keyboard, True)

        self.show_all()

        # Initialize the lesson playback.
        self.content = lesson['content']
        self.content_pos = 0
        self.markup = ''
        self.delay = 0
        self.span_count = 0

        gobject.timeout_add(50, self.timer_cb)

    def timer_cb(self):
        if self.delay > 0:
            self.delay -= 1
            return True

        # This loop keeps processing until at least one character has been emitted.
        # We don't want to slow down the typing when there are control codes.
        while True:
            # Read the next piece of content.
            if self.content_pos >= len(self.content):
                return False

            c = self.content[self.content_pos]
            self.content_pos += 1

            # Handle any control codes.
            if c == '<':
                # Extract and skip the contents of the < > brackets.
                code_begin = self.content_pos
                while self.content_pos < len(self.content) and \
                    self.content[self.content_pos] != '>':
                    self.content_pos += 1

                code = self.content[code_begin:self.content_pos]
                self.content_pos += 1

                # Process the control code.
                args = code.split(' ')
                if args[0] == 'delay':
                    self.delay = int(args[1])
                    return True

                elif args[0] == 'br':
                    # Line break.
                    self.markup += '\n'

                elif args[0] == 'p':
                    # Start a new paragraph.  End the current line if needed.
                    if len(self.markup) and self.markup[-1] != '\n':
                        self.markup += '\n\n'
                    else:
                        self.markup += '\n'

                elif args[0] == 'span':
                    # Pango span.
                    self.markup += '<' + code + '>'
                    self.span_count += 1

                elif args[0] == '/span':
                    # End of pango span.
                    if self.span_count > 0:
                        self.markup += '<' + code + '>'
                        self.span_count -= 1

                elif args[0] == 'type':
                    # Typing section.
                    self.markup += '<' + code + '>'
                    self.span_count += 1

                elif args[0] == '/type':
                    # End of typing section.
                    if self.span_count > 0:
                        self.markup += '<' + code + '>'
                        self.span_count -= 1


            else:
                # A plain character, insert it and return.
                # Extra </span>'s are added for Pango spans we are still in the middle of.
                self.markup += c
                self.lessontext.set_markup(self.markup + ('</span>' * self.span_count))

                return True

    def stop_cb(self, widget):
        self.activity.pop_screen()

class MainScreen(gtk.VBox):
    def __init__(self, activity):
        gtk.VBox.__init__(self)

        self.activity = activity

        # Build background.
        title = gtk.Label()
        title.set_markup("<span size='40000'><b>" + _('Typing Turtle') + "</b></span>")

        subtitle = gtk.Label()
        subtitle.set_markup(_('Welcome to Typing Turtle! To begin, select a lesson from the list below.'))

        spacer = gtk.HBox()

        # Lessons header.
        headerbox = gtk.VBox()
        label = gtk.Label()
        label.set_alignment(0.0, 0.5)
        label.set_markup("<span size='large'><b>"+_('Available Lessons')+"</b></span>")
        headerbox.pack_start(label, False)
        headerbox.pack_start(gtk.HSeparator(), False)

        # Build lessons list.
        self.lessonbox = gtk.VBox()
        self.lessonbox.set_spacing(10)

        lessons = []
        fd = open(sugar.activity.activity.get_bundle_path() + '/lessons/INDEX', 'r')
        try:
            lessons = json.read(fd.read())
        finally:
            fd.close()

        log.debug("Lessons: %r", lessons)
        for l in lessons:
            label = gtk.Label()
            label.set_alignment(0.0, 0.5)
            label.set_markup("<span size='large'>" + l['name'] + "</span>\n" + l['description'])

            medal = gtk.Image()
            medal.set_from_file(sugar.activity.activity.get_bundle_path() + '/images/gold-medal.jpg')

            hbox = gtk.HBox()
            hbox.pack_start(label, True, True, 10)
            hbox.pack_end(medal, False, False)            
      
            btn = gtk.Button()
            btn.add(hbox)

            btn.lesson = l

            btn.connect('clicked', self.button_cb)

            self.lessonbox.pack_start(btn, False)

        self.lessonscroll = gtk.ScrolledWindow()
        self.lessonscroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.lessonscroll.add_with_viewport(self.lessonbox)

        self.pack_start(title, False, True, 10)
        self.pack_start(subtitle, False)
        self.pack_start(spacer, False, False, 50)
        self.pack_start(headerbox, False)
        self.pack_start(self.lessonscroll, True)

    def button_cb(self, widget):
        self.activity.push_screen(LessonScreen(widget.lesson, self.activity))

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

        # This has to happen last, because it calls the read_file method when restoring from the Journal.
        self.set_canvas(self.screenbox)

        # Start with the main screen.
        self.push_screen(MainScreen(self))
  
        self.show_all()

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

