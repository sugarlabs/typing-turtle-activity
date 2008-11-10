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
import logging, os, math, time, copy, json, locale
from gettext import gettext as _

# Set up localization.
locale.setlocale(locale.LC_ALL, '')

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

        self.wpmlabel = gtk.Label()
        self.accuracylabel = gtk.Label()

        hbox = gtk.HBox()
        hbox.pack_start(stopbtn, False, False, 10)
        hbox.pack_start(self.wpmlabel, True, False, 10)
        hbox.pack_start(self.accuracylabel, True, False, 10)
        hbox.pack_end(title, False, False, 10)

        self.lessontext = gtk.Label()
        self.lessontext.set_alignment(0, 0)
        self.lessontext.set_line_wrap(True)

        self.lessonscroll = gtk.ScrolledWindow()
        self.lessonscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.lessonscroll.add_with_viewport(self.lessontext)
 
        frame = gtk.Frame()
        frame.add(self.lessonscroll)

        self.keyboard = keyboard.Keyboard()
        self.keyboard.set_layout(keyboard.default_layout)

        activity.add_events(gtk.gdk.KEY_PRESS_MASK)
        activity.connect('key-press-event', self.key_press_cb)

        self.pack_start(hbox, False, False, 10)
        self.pack_start(frame, True, True)
        self.pack_start(self.keyboard, True)

        self.show_all()

        self.begin_lesson()

    def begin_lesson(self):
        self.step = None
        self.markup = ''

        self.total_keys = 0
        self.correct_keys = 0
        self.incorrect_keys = 0

        self.count_words()

        self.next_step_idx = 0
        self.advance_step()

        self.start_time = None

    def count_words(self):
        self.total_words = 0
        for s in self.lesson['steps']:
            in_word = False
            for c in s['text']:
                if not in_word and not c.isspace():
                    self.total_words += 1
                    in_word = True
                elif c.isspace():
                    in_word = False

    def update_stats(self):
        self.total_time = time.time() - self.start_time
        self.wpm = 60.0 * self.total_words / self.total_time
        self.accuracy = 100.0 * self.correct_keys / self.total_keys

        self.accuracylabel.set_markup(_('<b>Accuracy:</b> %(accuracy)d%%') % { 'accuracy' : int(self.accuracy) } )
        self.wpmlabel.set_markup(_('<b>WPM:</b> %(wpm)d') % { 'wpm': int(self.wpm) } )

    def add_text(self, text):
        self.markup += text
        self.lessontext.set_markup(self.markup + '_')

    def advance_step(self):
        if self.next_step_idx < len(self.lesson['steps']):
            # TODO - Play 'step finished' sound here.

            self.step = self.lesson['steps'][self.next_step_idx]
            self.next_step_idx = self.next_step_idx + 1

            self.add_text(self.step['instructions'] + '\n\n')
            self.add_text('<span font_family="monospace">' + self.step['text'] + '</span>\n')

            self.char_idx = 0
        
        else:
            self.finish_lesson()

    def finish_lesson(self):
        self.step = None

        self.update_stats()

        self.add_text(_('Congratulations!  You finished the lesson in %(time)d seconds.\n\n') % 
            { 'time': int(self.total_time) } )

        # Add to the game history.
        self.activity.add_history({ 
            'lesson': self.lesson['name'], 
            'time': self.time,
            'wpm': self.wpm, 
            'accuracy': self.accuracy
        })
        
    def key_press_cb(self, widget, event):
        if not self.step:
            return False

        # Timer starts with first keypress.
        if not self.start_time:
            self.start_time = time.time()

        # Check to see if they pressed the correct key.
        if event.keyval == ord(self.step['text'][self.char_idx]):
            self.correct_keys += 1
            self.total_keys += 1

            self.add_text('<span font_family="monospace">' + chr(event.keyval) + '</span>')

            self.char_idx += 1
            if self.char_idx >= len(self.step['text']):
                self.add_text('\n\n')
                self.advance_step()

        else:
            # TODO - Play 'incorrect key' sound here.

            self.incorrect_keys += 1
            self.total_keys += 1

        self.update_stats()

        return False

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

        code = locale.getlocale(locale.LC_ALL)[0]
 
        lessons = []
        fd = open(sugar.activity.activity.get_bundle_path() + '/lessons/LESSONS.'+code, 'r')
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

        # All data which is saved in the Journal entry is placed in this dictionary.
        self.data = {
            'history': []
        }

        # This has to happen last, because it calls the read_file method when restoring from the Journal.
        self.set_canvas(self.screenbox)

        # Start with the main screen.
        self.push_screen(MainScreen(self))
  
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
        self.data['history'].push(entry)

    def read_file(self, file_path):
        if self.metadata['mime_type'] != 'text/plain':
            return

        fd = open(file_path, 'r')
        try:
            text = fd.read()
            print "read %s" % text
            self.data = json.read(text)
        finally:
            fd.close()

    def write_file(self, file_path):
        if not self.metadata['mime_type']:
            self.metadata['mime_type'] = 'text/plain'

        fd = open(file_path, 'w')
        try:
            text = json.write(self.data)
            fd.write(text)
            print "wrote %s" % text
        finally:
            fd.close()

