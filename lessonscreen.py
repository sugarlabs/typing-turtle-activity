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
# vi:sw=4 et 

# Import standard Python modules.
import logging, os, math, time, copy, json, locale, datetime, random, re
from gettext import gettext as _

# Import PyGTK.
import gobject, pygtk, gtk, pango

# Import Sugar UI modules.
import sugar.activity.activity
from sugar.graphics import *

# Import activity modules.
import keyboard, medalscreen

# Paragraph symbol unicode character.
PARAGRAPH_CODE = u'\xb6'

# Maximium width of a text line in text lesson mode.
LINE_WIDTH = 80

# Requirements for earning medals.
# Words per minute goals came from http://en.wikipedia.org/wiki/Words_per_minute.
DEFAULT_MEDALS = [
    { 'name': 'bronze', 'wpm': 25, 'accuracy': 75 },
    { 'name': 'silver', 'wpm': 35, 'accuracy': 85 },
    { 'name': 'gold',   'wpm': 45, 'accuracy': 95 }
]

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
        #instructions_tag.props.size = 10000
        instructions_tag.props.justification = gtk.JUSTIFY_CENTER
        self.tagtable.add(instructions_tag)

        text_tag = gtk.TextTag('text')
        text_tag.props.family = 'Monospace'
        self.tagtable.add(text_tag)
        
        image_tag = gtk.TextTag('image')
        image_tag.props.justification = gtk.JUSTIFY_CENTER
        self.tagtable.add(image_tag)
        
        correct_copy_tag = gtk.TextTag('correct-copy')
        correct_copy_tag.props.family = 'Monospace'
        correct_copy_tag.props.foreground = '#0000ff'
        self.tagtable.add(correct_copy_tag)
        
        incorrect_copy_tag = gtk.TextTag('incorrect-copy')
        incorrect_copy_tag.props.family = 'Monospace'
        incorrect_copy_tag.props.foreground = '#ff0000'
        self.tagtable.add(incorrect_copy_tag)
        
        # Set up the scrolling lesson text view.
        self.lessonbuffer = gtk.TextBuffer(self.tagtable)
        self.lessontext = gtk.TextView(self.lessonbuffer)
        self.lessontext.set_editable(False)
        self.lessontext.set_left_margin(20)
        self.lessontext.set_right_margin(20)
        self.lessontext.set_wrap_mode(gtk.WRAP_WORD)
        self.lessontext.modify_base(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#ffffcc'))
        #self.lessontext.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#ffff80'))
        
        self.lessonscroll = gtk.ScrolledWindow()
        self.lessonscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.lessonscroll.add(self.lessontext)
        
        frame = gtk.Frame()
        frame.add(self.lessonscroll)
        
        self.keyboard = keyboard.Keyboard(self.activity)
        self.keyboard.set_layout(keyboard.DEFAULT_LAYOUT)
        
        self.pack_start(hbox, False, False, 10)
        self.pack_start(frame, True, True)
        self.pack_start(self.keyboard, True)
        
        # Connect keyboard grabbing and releasing callbacks.        
        self.connect('realize', self.realize_cb)
        self.connect('unrealize', self.unrealize_cb)
        
        self.show_all()
        
        # Load hand overlay SVGs.
        bundle_path = sugar.activity.activity.get_bundle_path()
        #for o in KEY_OVERLAYS.keys():
        #    pass
        
        self.begin_lesson()
        
        # Initialize stats update timer.        
        gobject.timeout_add(1000, self.timer_cb)

    def realize_cb(self, widget):
        self.activity.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.key_press_cb_id = self.activity.connect('key-press-event', self.key_cb)
        self.key_release_cb_id = self.activity.connect('key-release-event', self.key_cb)
        
    def unrealize_cb(self, widget):
        self.activity.disconnect(self.key_press_cb_id)
        self.activity.disconnect(self.key_release_cb_id)
        
    def update_stats(self):
        if self.lesson_finished:
            return
        
        if self.start_time:
            self.total_time = time.time() - self.start_time
            
            if self.total_time >= 1.0:
                self.wpm = 60 * (self.correct_keys / 5) / self.total_time
            else:
                self.wpm = 1.0
                
            self.wpmlabel.set_markup(_('<b>WPM:</b> %(wpm)d') % { 'wpm': int(self.wpm) } )
        else:
            self.total_time = 0.0
            self.wpm = 100.0
        
        if self.total_keys:                
            self.accuracy = 100.0 * self.correct_keys / self.total_keys
            
            self.accuracylabel.set_markup(_('<b>Accuracy:</b> %(accuracy)d%%') % { 'accuracy' : int(self.accuracy) } )
    
    def timer_cb(self):
        self.update_stats()
        return True
    
    def begin_lesson(self):
        self.lesson_finished = False
        
        self.medal = None
        
        self.total_keys = 0
        self.correct_keys = 0
        self.incorrect_keys = 0
        
        self.start_time = None
        
        self.step = None
        
        self.next_step_idx = 0
        self.advance_step()

    def wrap_line(self, line):
        r = re.compile('(\W+)', re.UNICODE)
        words = r.split(line)
        
        new_lines = []
        cur_line = ''
        for w in words:
            # TODO: Handle single word longer than a line.
            if not w.isspace() and len(cur_line) + len(w) > LINE_WIDTH:
                if len(cur_line):
                    new_lines.append(cur_line)
                    cur_line = ''
            cur_line += w
        
        if len(cur_line):
            new_lines.append(cur_line)
        
        return new_lines

    def advance_step(self):
        # Clear the buffer *after* key steps.
        if self.step and self.mode == 'key':
            self.lessonbuffer.set_text('')
        
        # Clear step related variables.
        self.step = None
        
        self.text = None
        self.line = None
        self.line_marks = None
        
        # Leave this screen if the lesson is finished.
        if self.next_step_idx >= len(self.lesson['steps']):
            self.end_lesson()
            return
        
        # Mark the lesson as finished if this is the last step.
        if self.next_step_idx == len(self.lesson['steps']) - 1:
            self.lesson_finished = True
        
        # TODO - Play 'step finished' sound here.
        
        self.step = self.lesson['steps'][self.next_step_idx]
        self.next_step_idx = self.next_step_idx + 1
        
        # Single character steps are handled differently from multi-character steps.
        self.mode = self.step['mode']
        
        # Clear the buffer *before* key steps.
        if self.mode == 'key':
            self.lessonbuffer.set_text('')
        
        # Output the instructions.
        self.instructions = self.step['instructions']
        if self.instructions == '$report':
            self.instructions = self.get_lesson_report()
        
        self.lessonbuffer.insert_with_tags_by_name(
            self.lessonbuffer.get_end_iter(), '\n\n' + self.step['instructions'] + '\n', 'instructions')
        
        self.text = unicode(self.step['text'])
        
        if self.mode == 'key':
            self.lines = [self.text.replace('\n', PARAGRAPH_CODE)]
            self.line_marks = {}
            
            self.lessonbuffer.insert_with_tags_by_name(
                self.lessonbuffer.get_end_iter(), '\n\n', 'instructions')
            
            self.line_marks[0] = self.lessonbuffer.create_mark(None, self.lessonbuffer.get_end_iter(), True)
            
            if self.text[0] == '\n' or self.text[0] == PARAGRAPH_CODE:
                key = self.keyboard.find_key_by_label('enter')
            else:
                key = self.keyboard.find_key_by_letter(self.text[0])
            if key:
                widget = self.keyboard.get_key_widget(key, 1)
                widget.show()
                anchor = self.lessonbuffer.create_child_anchor(self.lessonbuffer.get_end_iter())
                self.lessontext.add_child_at_anchor(widget, anchor)
            
            self.lessonbuffer.apply_tag_by_name('image',
                self.lessonbuffer.get_iter_at_mark(self.line_marks[0]),
                self.lessonbuffer.get_end_iter())
            
            self.lessontext.set_cursor_visible(False)

            self.keyboard.set_draw_hands(True)
            
        else:
            # Split text into lines.
            self.lines = self.text.splitlines(True)
            
            # Substitute paragraph codes.
            self.lines = [l.replace('\n', PARAGRAPH_CODE) for l in self.lines]
            
            # Split by line length in addition to by paragraphs.
            for i in range(0, len(self.lines)):
                line = self.lines[i]
                if len(line) > LINE_WIDTH:
                    self.lines[i:i+1] = self.wrap_line(line)
            
            # Center single line steps.
            indent = ''
            #if len(self.lines) == 1:
            #    indent = ' ' * ((LINE_LENGTH - len(self.lines[0]))/2)
            
            # Fill text buffer with text lines, each followed by room for the user to type.
            self.line_marks = {} 
            line_idx = 0
            for l in self.lines:
                # Add the text to copy.
                self.lessonbuffer.insert_with_tags_by_name(
                    self.lessonbuffer.get_end_iter(), '\n' + indent + l.encode('utf-8') + '\n' + indent, 'text')
                
                # Leave a marker where we will later insert text.
                self.line_marks[line_idx] = self.lessonbuffer.create_mark(None, self.lessonbuffer.get_end_iter(), True)
                
                line_idx += 1
            
            self.lessontext.set_cursor_visible(True)
        
            self.keyboard.set_draw_hands(False)

        self.line_idx = 0
        self.begin_line()
            
    def begin_line(self):
        self.line = self.lines[self.line_idx]
        self.line_mark = self.line_marks[self.line_idx]
        
        self.char_idx = 0
        
        self.hilite_next_key()

    def key_cb(self, widget, event):
        # Ignore either press or release events, depending on mode.
        if self.mode == 'key' and event.type == gtk.gdk.KEY_PRESS:
            return False
        if self.mode != 'key' and event.type == gtk.gdk.KEY_RELEASE:
            return False
        
        # Ignore hotkeys.
        if event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.MOD1_MASK):
            return False
        
        # Extract information about the key pressed.
        key = gtk.gdk.keyval_to_unicode(event.keyval)
        if key != 0: key = unichr(key)
        key_name = gtk.gdk.keyval_name(event.keyval)
        
        # Convert Return keys to paragraph symbols.
        if key_name == 'Return':
            key = PARAGRAPH_CODE
        
        #print "key_press_cb: key=%s key_name=%s event.keyval=%d" % (key, key_name, event.keyval)
        
        if self.mode == 'key':
            # Check to see if they pressed the correct key.
            if key == self.line[0]:
                self.correct_keys += 1
                self.total_keys += 1
                
                # Advance to the next step.
                self.advance_step()
                self.update_stats()
                self.hilite_next_key()
                
            else:
                # TODO - Play 'incorrect key' sound here.
                
                self.incorrect_keys += 1
                self.total_keys += 1
        
        elif self.mode == 'text':
            # Timer starts with first text mode keypress.
            if not self.start_time:
                self.start_time = time.time()
            
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
    
                self.hilite_next_key()
    
            # Process normal key presses.
            elif key != 0:
                
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
                
                # Insert the key into the bufffer.
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
                    return
                
                self.update_stats()
                
                self.hilite_next_key()
        
        return False

    def hilite_next_key(self):
        if not self.line:
            return
        
        if len(self.line) > 0:
            char = self.line[self.char_idx]
            self.keyboard.set_hilite_letter(char)
        
        # Move the cursor to the insert location.
        iter = self.lessonbuffer.get_iter_at_mark(self.line_mark)
        iter.forward_chars(self.char_idx)
        self.lessonbuffer.place_cursor(iter)
        
        # Gain focus (this causes the cursor line to draw).
        self.lessontext.grab_focus()
        
        # Scroll the TextView so the cursor is on screen.
        self.lessontext.scroll_to_mark(self.lessonbuffer.get_insert(), 0)

    def get_lesson_report(self):
        self.update_stats()

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
        
        medals = self.lesson.get('medals', DEFAULT_MEDALS)
        for medal in medals:
            if self.wpm >= medal['wpm'] and self.accuracy >= medal['accuracy']:
                got_medal = medal['name']

        if got_medal:
            # Award the medal.
            medal = {
                'lesson': lesson_name,
                'type': got_medal,
                'date': datetime.date.today().strftime('%B %d, %Y'),
                'nick': self.activity.owner.props.nick,
                'time': self.total_time,
                'wpm': report['wpm'],
                'accuracy': report['accuracy']
            }
            self.medal = medal

            # Compare this medal with any existing medals for this lesson.
            # Only record the best one.
            add_medal = True
            if self.activity.data['medals'].has_key(lesson_name):
                old_medal = self.activity.data['medals'][lesson_name]

                order = ' '.join([m['name'] for m in MEDALS])
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
                # Upgrade the player's level if needed.
                if self.lesson['level'] > self.activity.data['level']:
                    self.activity.data['level'] = self.lesson['level']
                    self.activity.data['motd'] = 'newlevel'
                
                self.activity.data['medals'][lesson_name] = medal
                self.activity.mainscreen.show_highest_available_lesson()
        
        # Display results to the user.
        text = '\n'
        
        congrats = [
            _('Good job!'),
            _('Well done!'),
            _('Nice work!'),
            _('Way to go!')
        ]
        text += random.choice(congrats) + '\n\n'
        
        text += _('You finished the lesson in %(time)d seconds, with %(errors)d errors.\n\n') % \
            { 'time': int(self.total_time), 'errors': self.incorrect_keys }
        text += _('Your words per minute (WPM) was %(wpm)d, and your accuracy was %(accuracy)d%%.\n\n') % \
            report
        
        if self.medal:
            # TODO: Play medal sound here.
            
            text += _('Congratulations!  You earned a %(type)s medal!\n\nPress Enter to see your certificate.') % \
            medal
            
        else:
            # Comment on what the user needs to do better.
            need_wpm = report['wpm'] < MEDALS[0]['wpm']
            need_accuracy = report['accuracy'] < MEDALS[0]['accuracy']
            
            if need_accuracy and need_wpm:
                text += _('You need to practice this lesson more before moving on.  If you are having a hard time, '
                          'repeat the earlier lessons until you have mastered them completely before trying this one '
                          'again.\n\n')
                
            elif need_accuracy:
                text += _('You almost got a medal!  Next time, try not to make as many errors!\n\n')
                
            elif need_wpm:
                text += _('You almost got a medal!  Next time, try to type a little faster!\n\n')
                
            text += _('Press Enter to return to the main screen.')
            
        return text
        
    def end_lesson(self):
        self.activity.pop_screen()
        
        # Show the new medal if there was one.
        if self.medal:
            self.activity.push_screen(medalscreen.MedalScreen(self.medal, self.activity))

    def stop_cb(self, widget):
        self.activity.pop_screen()
