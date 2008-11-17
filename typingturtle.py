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
import logging, os, math, time, copy, json, locale, datetime
from gettext import gettext as _

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

# Import onscreen keyboard.
import keyboard

# Paragraph symbol unicode character.
PARAGRAPH_CODE = u'\xb6'

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
        oklabel.set_markup("<span size='10000'>" + _('Go Back') + '</span>')
        okbtn =  gtk.Button()
        okbtn.add(oklabel)
        okbtn.connect('clicked', self.ok_cb)

        btnbox = gtk.HBox()
        btnbox.pack_start(okbtn, True, False)

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

        # TODO- These will be replaced by graphical displays using gtk.DrawingArea.
        self.wpmlabel = gtk.Label()
        self.accuracylabel = gtk.Label()

        #self.wpmarea = gtk.DrawingArea()
        #self.wpmarea.connect('expose-event', self.wpm_expose_cb)
        #self.accuracyarea = gtk.DrawingArea()
        #self.accuracyarea.connect('expose-event', self.accuracy_expose_cb)

        hbox = gtk.HBox()
        hbox.pack_start(stopbtn, False, False, 10)
        hbox.pack_start(self.wpmlabel, True, False, 10)
        hbox.pack_start(self.accuracylabel, True, False, 10)
        hbox.pack_end(title, False, False, 10)

        # Set up font styles.
        self.tagtable = gtk.TextTagTable()
        instructions_tag = gtk.TextTag('instructions')
        instructions_tag.props.size = 10000

        self.tagtable.add(instructions_tag)
        text_tag = gtk.TextTag('text')
        text_tag.props.family = 'Monospace'
        self.tagtable.add(text_tag)

        correct_copy_tag = gtk.TextTag('correct-copy')
        correct_copy_tag.props.family = 'Monospace'
        correct_copy_tag.props.foreground = '#0000ff'
        self.tagtable.add(correct_copy_tag)

        incorrect_copy_tag = gtk.TextTag('incorrect-copy')
        incorrect_copy_tag.props.family = 'Monospace'
        incorrect_copy_tag.props.foreground = '#ff0000'
        self.tagtable.add(incorrect_copy_tag)

        # Set up the scrolling lesson text.
        self.lessonbuffer = gtk.TextBuffer(self.tagtable)
        self.lessontext = gtk.TextView(self.lessonbuffer)
        self.lessontext.set_editable(False)
        #self.lessontext.set_cursor_visible(False)
        self.lessontext.set_left_margin(20)
        self.lessontext.set_right_margin(20)

        self.lessonscroll = gtk.ScrolledWindow()
        self.lessonscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.lessonscroll.add_with_viewport(self.lessontext)
 
        frame = gtk.Frame()
        frame.add(self.lessonscroll)

        self.keyboard = keyboard.Keyboard(self.activity)
        self.keyboard.set_layout(keyboard.DEFAULT_LAYOUT)

        activity.add_events(gtk.gdk.KEY_PRESS_MASK)
        activity.connect('key-press-event', self.key_press_cb)

        self.pack_start(hbox, False, False, 10)
        self.pack_start(frame, True, True)
        self.pack_start(self.keyboard, True)

        self.show_all()

        self.begin_lesson()

    def begin_lesson(self):
        self.step = None
        self.line = None
        self.line_marks = None

        self.total_keys = 0
        self.correct_keys = 0
        self.incorrect_keys = 0

        self.next_step_idx = 0
        self.advance_step()

        self.start_time = None

    def update_stats(self):
        self.total_time = time.time() - self.start_time
        if self.total_time >= 1.0:
            self.wpm = 60 * (len(self.step['text']) / 5) / self.total_time
        else:
            self.wpm = 1.0
        self.accuracy = 100.0 * self.correct_keys / self.total_keys

        self.accuracylabel.set_markup(_('<b>Accuracy:</b> %(accuracy)d%%') % { 'accuracy' : int(self.accuracy) } )
        self.wpmlabel.set_markup(_('<b>WPM:</b> %(wpm)d') % { 'wpm': int(self.wpm) } )

    def wrap_line(self, line):
        LINE_LENGTH = 80

        words = line.split(' ')
        new_lines = []
        cur_line = ''
        for w in words:
            # TODO: Handle single word longer than a line.
            #if len(w) > LINE_LENGTH:
            #    new_lines.append(cur_line)
            #    while len(w):
            #        new_lines.append(w[:LINE_LENGTH])
            #        w = w[LINE_LENGTH:]
            #    cur_line = ''
            if len(cur_line) + len(w) + 1 > LINE_LENGTH:
                if len(cur_line):
                    new_lines.append(cur_line)
                cur_line = ''
            cur_line += w + ' '
        
        if len(cur_line):
            # Remove trailing spaces from last line before adding.
            while cur_line[-1] == ' ':
                cur_line = cur_line[:-1]
            new_lines.append(cur_line)
        
        return new_lines

    def advance_step(self):
        if self.next_step_idx < len(self.lesson['steps']):
            # TODO - Play 'step finished' sound here.

            self.step = self.lesson['steps'][self.next_step_idx]
            self.next_step_idx = self.next_step_idx + 1

            # Clear the text buffer and output the instructions.
            self.lessonbuffer.set_text('')
            self.lessonbuffer.insert_with_tags_by_name(
                self.lessonbuffer.get_end_iter(), self.step['instructions'] + '\n\n', 'instructions')

            # Replace newlines with paragraph marks.
            text = unicode(self.step['text'])

            # Split text into lines.
            self.lines = text.split('\n')

            # Append paragraph codes.
            self.lines = [l + PARAGRAPH_CODE for l in self.lines]

            # TODO: Split by line length in addition to by paragraphs.
            for i in range(0, len(self.lines)):
                line = self.lines[i]
                if len(line) > 30:
                    self.lines[i:i+1] = self.wrap_line(line)

            # Fill text buffer with text lines, each followed by room for the user to type.
            self.line_marks = {} 
            line_idx = 0
            for l in self.lines:
                self.lessonbuffer.insert_with_tags_by_name(
                    self.lessonbuffer.get_end_iter(), l.encode('utf-8') + '\n', 'text')

                self.line_marks[line_idx] = self.lessonbuffer.create_mark(None, self.lessonbuffer.get_end_iter(), True)
                self.lessonbuffer.insert_at_cursor('\n')

                line_idx += 1

            self.line_idx = 0
            self.begin_line()
        
        else:
            self.finish_lesson()

    def begin_line(self):
        self.line = self.lines[self.line_idx]
        self.line_mark = self.line_marks[self.line_idx]

        self.char_idx = 0
        self.hilite_next_key()

    def key_press_cb(self, widget, event):
        # Ignore hotkeys.
        if event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.MOD1_MASK):
            return

        # Extract information about the key pressed.
        key = gtk.gdk.keyval_to_unicode(event.keyval)
        if key != 0: key = chr(key)
        key_name = gtk.gdk.keyval_name(event.keyval)

        # Convert Return keys to paragraph symbols.
        if key_name == 'Return':
            key = PARAGRAPH_CODE

        print "key_press_cb: key=%s key_name=%s event.keyval=%d" % (key, key_name, event.keyval)

        # Handle backspace by deleting text and optionally moving up lines.
        if key_name == 'BackSpace':
            # Move to previous line if at the end of the current one.
            if self.char_idx == 0 and self.line_idx > 0:
                self.line_idx -= 1 
                self.begin_line()

                self.char_idx = len(self.line)

            # Then delete the current character.
            if self.char_idx > 0:
                self.char_idx -= 1

                iter = self.lessonbuffer.get_iter_at_mark(self.line_mark)
                iter.forward_chars(self.char_idx)

                iter_end = iter.copy()
                iter_end.forward_char()

                self.lessonbuffer.delete(iter, iter_end)

        # Process normal key presses.
        elif key != 0:

            # Timer starts with first keypress.
            if not self.start_time:
                self.start_time = time.time()

            # Check to see if they pressed the correct key.
            if key == self.line[self.char_idx]:
                tag_name = 'correct-copy'
                self.correct_keys += 1
                self.total_keys += 1

            else:
                # TODO - Play 'incorrect key' sound here.

                tag_name = 'incorrect-copy'
                self.incorrect_keys += 1
                self.total_keys += 1

            # Insert the key itno the bufffer.
            iter = self.lessonbuffer.get_iter_at_mark(self.line_mark)
            iter.forward_chars(self.char_idx)

            self.lessonbuffer.insert_with_tags_by_name(iter, key, tag_name)

            # Advance to the next character (or else).
            self.char_idx += 1
            if self.char_idx >= len(self.line):
                self.line_idx += 1
                if self.line_idx >= len(self.lines):
                    self.advance_step()
                else:
                    self.begin_line()

            self.update_stats()

        self.hilite_next_key()

        return False

    def hilite_next_key(self):
        # Hilite the next key on the virtual keyboard.
        self.keyboard.clear_hilite()
        if len(self.line) > 0:
            key = self.keyboard.find_key_by_letter(self.line[self.char_idx])
            if key:
                key.set_hilite(True)

        # Move the cursor to the insert location.
        iter = self.lessonbuffer.get_iter_at_mark(self.line_mark)
        iter.forward_chars(self.char_idx)
        self.lessonbuffer.place_cursor(iter)

        # Gain focus (this causes the cursor line to draw).
        self.lessontext.grab_focus()

        # Scroll the TextView so the cursor is on screen.
        self.lessontext.scroll_to_mark(self.lessonbuffer.get_insert(), 0)

    def finish_lesson(self):
        self.activity.pop_screen()
        
        self.update_stats()
        #self.add_text(_('Congratulations!  You finished the lesson in %(time)d seconds.\n\n') % 
        #    { 'time': int(self.total_time) } )

        lesson_name = self.lesson['name']

        # Add to the lesson history.
        report = { 
            'lesson': lesson_name,
            'time': self.total_time,
            'wpm': self.wpm, 
            'accuracy': self.accuracy
        }
        self.activity.add_history(report)

        # Show the medal screen, if one should be given.
        got_medal = None
        for medal_name in ['bronze', 'silver', 'gold']:
            medal = self.lesson['medals'][medal_name]
            if self.wpm >= medal['wpm'] and self.accuracy >= medal['accuracy']:
                got_medal = medal_name

        if got_medal:
            # Award the medal.
            medal = {
                'lesson': lesson_name,
                'type': medal_name,
                'date': datetime.date.today().strftime('%B %d, %Y'),
                'nick': self.activity.owner.props.nick,
                'time': self.total_time,
                'wpm': report['wpm'],
                'accuracy': report['accuracy']
            }

            add_medal = True
            if self.activity.data['medals'].has_key(lesson_name):
                old_medal = self.activity.data['medals'][lesson_name]

                order = 'bronze silver gold'
                add_idx = order.index(medal['type'])
                old_idx = order.index(old_medal['type']) 

                if add_idx < old_idx:
                    add_medal = False
                elif add_idx == old_idx:
                    if medal['accuracy'] < old_medal['accuracy']:
                        add_medal = False
                    elif medal['accuracy'] == old_medal['accuracy']:
                        if medal['wpm'] < old_medal['wpm']:
                            add_medal = False

            if add_medal:
                self.activity.data['medals'][lesson_name] = medal
                self.activity.mainscreen.update_medals()

            # Show the new medal (regardless of whether it was recorded).
            self.activity.push_screen(MedalScreen(medal, self.activity))

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

        bundle_path = sugar.activity.activity.get_bundle_path() 
        code = locale.getlocale(locale.LC_ALL)[0]
        path = bundle_path + '/lessons/' + code + '/'
 
        # Find all .lesson files in ./lessons/en_US/ for example.
        lessons = []
        for f in os.listdir(path):
            fd = open(path + f, 'r')
            try:
                lesson = json.read(fd.read())
                lessons.append(lesson)
            finally:
                fd.close()

        for l in lessons:
            label = gtk.Label()
            label.set_alignment(0.0, 0.5)
            label.set_markup("<span size='large'>" + l['name'] + "</span>\n" + l['description'])

            btn = gtk.Button()
            btn.lesson = l
            btn.add(label)
            btn.connect('clicked', self.lesson_clicked_cb)

            medalimage = gtk.Image()

            medalbtn = gtk.Button()
            medalbtn.lesson = l
            medalbtn.add(medalimage)
            medalbtn.connect('clicked', self.medal_clicked_cb)

            hbox = gtk.HBox()
            hbox.pack_start(btn, True, True, 10)
            hbox.pack_end(medalbtn, False, False)            

            hbox.lesson = l
            hbox.medalimage = medalimage
      
            self.lessonbox.pack_start(hbox, False)

        self.lessonscroll = gtk.ScrolledWindow()
        self.lessonscroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.lessonscroll.add_with_viewport(self.lessonbox)

        self.pack_start(title, False, True, 10)
        self.pack_start(subtitle, False)
        self.pack_start(spacer, False, False, 50)
        self.pack_start(headerbox, False)
        self.pack_start(self.lessonscroll, True)

        self.update_medals()

    def update_medals(self):
        for l in self.lessonbox:
            medal_type = 'none'
            if self.activity.data['medals'].has_key(l.lesson['name']):
                medal_type = self.activity.data['medals'][l.lesson['name']]['type']

            bundle = sugar.activity.activity.get_bundle_path()
            images = {
                'none':   bundle+'/images/no-medal.jpg',
                'bronze': bundle+'/images/bronze-medal.jpg',
                'silver': bundle+'/images/silver-medal.jpg',
                'gold':   bundle+'/images/gold-medal.jpg'
            }
            l.medalimage.set_from_file(images[medal_type])

    def lesson_clicked_cb(self, widget):
        self.activity.push_screen(LessonScreen(widget.lesson, self.activity))

    def medal_clicked_cb(self, widget):
        if self.activity.data['medals'].has_key(widget.lesson['name']):
            medal = self.activity.data['medals'][widget.lesson['name']]
            self.activity.push_screen(MedalScreen(medal, self.activity))

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
            'history': [],
            'medals': {}
        }

        # This has to happen last, because it calls the read_file method when restoring from the Journal.
        self.set_canvas(self.screenbox)

        # Start with the main screen.
        self.mainscreen = MainScreen(self)
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

