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
import logging, os, math, time, copy, locale, datetime, random, re
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
LINE_WIDTH = 70

FINGERS = {
    'LP': _('left little finger'),
    'LR': _('left ring finger'),
    'LM': _('left middle finger'),
    'LI': _('left index finger'),
    'LT': _('left thumb'),
    'RP': _('right little finger'),
    'RR': _('right ring finger'),
    'RM': _('right middle finger'),
    'RI': _('right index finger'),
    'RT': _('right thumb'),
}

class LessonScreen(gtk.VBox):
    def __init__(self, lesson, keyboard_images, activity):
        gtk.VBox.__init__(self)
        
        self.lesson = lesson
        self.keyboard_images = keyboard_images
        self.activity = activity
        
        # Build the user interface.
        title = gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>" + lesson['name'] + "</span>")
        title.set_alignment(1.0, 0.0)
        
        stoplabel = gtk.Label(_('Go Back'))
        stopbtn =  gtk.Button()
        stopbtn.add(stoplabel)
        stopbtn.connect('clicked', self.stop_cb)
        
        # TODO- These will be replaced by graphical displays using gtk.DrawingArea.
        self.wpm = 0
        self.accuracy = 0
        
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
        instructions_tag.props.justification = gtk.JUSTIFY_CENTER
        self.tagtable.add(instructions_tag)

        text_tag = gtk.TextTag('text')
        text_tag.props.family = 'Monospace'
        self.tagtable.add(text_tag)
        
        spacer_tag = gtk.TextTag('spacer')
        spacer_tag.props.size = 3000
        self.tagtable.add(spacer_tag)
        
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
        
        self.lessonscroll = gtk.ScrolledWindow()
        self.lessonscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.lessonscroll.add(self.lessontext)
        
        frame = gtk.Frame()
        frame.add(self.lessonscroll)
        
        self.keyboard = keyboard.KeyboardWidget(self.keyboard_images, self.activity)
        
        # Attempt to load a letter map for the current locale.
        code = locale.getdefaultlocale()[0] or 'en_US'
        try:
            self.keyboard.load_letter_map('lessons/%s.key' % code)
        except:
            self.keyboard.load_letter_map('lessons/en_US.key')

        self.keyboard.set_layout(keyboard.OLPC_LAYOUT)

        self.pack_start(hbox, False, False, 10)
        self.pack_start(frame, True, True)
        self.pack_start(self.keyboard, False)
        
        # Connect keyboard grabbing and releasing callbacks.        
        self.connect('realize', self.realize_cb)
        self.connect('unrealize', self.unrealize_cb)
        
        self.show_all()

        self.timer_id = None
        
        self.begin_lesson()
        
    def realize_cb(self, widget):
        self.activity.add_events(gtk.gdk.KEY_PRESS_MASK|gtk.gdk.KEY_RELEASE_MASK)
        self.key_press_cb_id = self.activity.connect('key-press-event', self.key_cb)
        self.key_release_cb_id = self.activity.connect('key-release-event', self.key_cb)
        
    def unrealize_cb(self, widget):
        self.activity.disconnect(self.key_press_cb_id)
        self.activity.disconnect(self.key_release_cb_id)

    def start_timer(self):
        self.start_time = time.time()
        self.timer_id = gobject.timeout_add(1000, self.timer_cb)

    def stop_timer(self):
        if self.timer_id:
            gobject.source_remove(self.timer_id)
        self.start_time = None
        self.timer_id = None

    def timer_cb(self):
        self.update_stats()
        return True
    
    def update_stats(self):
        if self.lesson_finished:
            return
        
        if self.start_time:
            self.total_time += time.time() - self.start_time
        self.start_time = time.time()

        if self.total_time >= 1.0:
            self.wpm = 60 * (self.correct_keys / 5) / self.total_time
            self.wpmlabel.set_markup(_('<b>WPM:</b> %(wpm)d') % { 'wpm': int(self.wpm) } )

        else:
            self.wpm = 1.0
                
        if self.total_keys:                
            self.accuracy = 100.0 * self.correct_keys / self.total_keys
            
            self.accuracylabel.set_markup(_('<b>Accuracy:</b> %(accuracy)d%%') % { 'accuracy' : int(self.accuracy) } )
    
    def begin_lesson(self):
        self.lesson_finished = False
        
        self.medal = None
        
        self.total_keys = 0
        self.correct_keys = 0
        self.incorrect_keys = 0
        
        self.start_time = None
        self.total_time = 0

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
        # Stop the WPM timer.
        self.stop_timer()

        # Clear step related variables.
        self.line = None
        self.line_marks = None
       
        # TODO: Play 'step finished' sound here.
        
        # Set up step if a valid index.
        if self.next_step_idx < len(self.lesson['steps']):
            step = self.lesson['steps'][self.next_step_idx]
            self.next_step_idx = self.next_step_idx + 1
            
            self.text = unicode(step['text'])
            self.instructions = unicode(step['instructions'])
            if step.has_key('mode'):
                self.mode = step['mode']
            else:
                if len(self.text) == 1:
                    self.mode = 'key'
                else:
                    self.mode = 'text'
        
        # Show report after the last step.
        elif self.next_step_idx == len(self.lesson['steps']) and not self.lesson_finished:
            self.lesson_finished = True
            
            self.instructions = self.get_lesson_report()
            self.text = '\n'
            self.mode = 'key'
        
        # Leave this screen when the lesson is finished.
        else:
            self.end_lesson()
            return      
        
        # Fix empty steps.
        if len(self.text) == 0:
            self.text = '\n'
        
        # Clear the buffer *before* key steps.
        self.lessonbuffer.set_text('')
        
        # Output the instructions.        
        self.lessonbuffer.insert_with_tags_by_name(
            self.lessonbuffer.get_end_iter(), '\n\n' + self.instructions + '\n', 'instructions')
        
        # Key steps have just one key to press, and show a picture of the key to be pressed beneath the text.
        if self.mode == 'key':
            self.lines = [self.text.replace('\n', PARAGRAPH_CODE)]
            self.line_marks = {}
            
            self.lessonbuffer.insert_with_tags_by_name(
                self.lessonbuffer.get_end_iter(), '\n', 'instructions')
            
            self.line_marks[0] = self.lessonbuffer.create_mark(None, self.lessonbuffer.get_end_iter(), True)
            
            self.lessontext.set_cursor_visible(False)
            
            # Enable hands for key mode.            
            self.keyboard.set_draw_hands(True)
        
        # Text steps require the user to copy out the text that is displayed. 
        elif self.mode == 'text':
            # Split text into lines.
            self.lines = self.text.splitlines(True)
            
            # Substitute paragraph codes for newlines.
            self.lines = [l.replace('\n', PARAGRAPH_CODE) for l in self.lines]
            
            # Split by line length in addition to by paragraphs.
            for i in range(0, len(self.lines)):
                line = self.lines[i]
                if len(line) > LINE_WIDTH:
                    self.lines[i:i+1] = self.wrap_line(line)
            
            # Fill text buffer with text lines, each followed by room for the user to type.
            self.line_marks = {} 
            line_idx = 0
            for l in self.lines:
                # Add a little space between lines.
                self.lessonbuffer.insert_with_tags_by_name(
                    self.lessonbuffer.get_end_iter(), '\n', 'text')
                self.lessonbuffer.insert_with_tags_by_name(
                    self.lessonbuffer.get_end_iter(), '\n', 'spacer')

                # Add the text to copy.
                self.lessonbuffer.insert_with_tags_by_name(
                    self.lessonbuffer.get_end_iter(), l.encode('utf-8') + '\n', 'text')
                
                # Leave a marker where we will later insert text.
                self.line_marks[line_idx] = self.lessonbuffer.create_mark(None, self.lessonbuffer.get_end_iter(), True)
                
                line_idx += 1
            
            self.lessontext.set_cursor_visible(True)
            
            # Enable hands for typing mode now that it's fast enough.            
            self.keyboard.set_draw_hands(True)

        self.line_idx = 0
        self.begin_line()

    def begin_line(self):
        self.line = self.lines[self.line_idx]
        self.line_mark = self.line_marks[self.line_idx]
        
        self.char_idx = 0
        
        self.hilite_next_key()

    def key_cb(self, widget, event):
        # Pass events on to the keyboard.
        self.keyboard.key_press_release_cb(widget, event)

        # Extract information about the key pressed.
        key = event.string
        key_name = gtk.gdk.keyval_name(event.keyval)
        
        # Ignore events which don't produce a character, except backspace.
        if not (key_name == 'BackSpace' or key):
            return True

        # Ignore either press or release events, depending on mode.
        if self.mode == 'key' and event.type == gtk.gdk.KEY_PRESS:
            return True 
        if self.mode != 'key' and event.type == gtk.gdk.KEY_RELEASE:
            return True
        
        # Ignore hotkeys.
        if event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.MOD1_MASK):
            return True
        
        # Convert Return keys to paragraph symbols.
        if key_name == 'Return':
            key = PARAGRAPH_CODE
               
        if self.mode == 'key':
            # Check to see if they pressed the correct key.
            if key == self.line[self.char_idx]:
                self.correct_keys += 1
                self.total_keys += 1
                
                # Advance to the next character (or else step).
                self.char_idx += 1
                if self.char_idx >= len(self.line):
                    self.advance_step()

                self.update_stats()
                self.hilite_next_key()
                
            else:
                # TODO - Play 'incorrect key' sound here.
               
                self.incorrect_keys += 1
                self.total_keys += 1
        
        elif self.mode == 'text':
            # WPM timer starts with first text mode keypress.
            if not self.timer_id:
                self.start_timer()
            
            # Handle backspace by deleting text and optionally moving up lines.
            if key_name == 'BackSpace':
                if self.lesson.get('options', {}).get('backspace', True):               
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

                # Insert the key into the buffer if correct or if mistakes are allowed.
                if tag_name == 'correct-copy' or self.lesson.get('options', {}).get('mistakes', True):
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
                        return True
                
                self.update_stats()
                
                self.hilite_next_key()
        
        return True 

    def hilite_next_key(self):
        char = self.line[self.char_idx]
        self.keyboard.set_hilite_letter(char)

        # In Text mode, move the cursor to the insert location.
        if self.mode == 'text':
            iter = self.lessonbuffer.get_iter_at_mark(self.line_mark)
            iter.forward_chars(self.char_idx)
            self.lessonbuffer.place_cursor(iter)
            
            # Gain focus (this causes the cursor line to draw).
            self.lessontext.grab_focus()
            
            # Scroll the TextView so the cursor is on screen.
            self.lessontext.scroll_to_mark(self.lessonbuffer.get_insert(), 0)

        # In Key mode, display the finger hint and the key image.
        if self.mode == 'key':
            iter = self.lessonbuffer.get_iter_at_mark(self.line_mark)
            self.lessonbuffer.delete(iter, self.lessonbuffer.get_end_iter())

            # Determine what modifier keys are needed.
            key, state, group = self.keyboard.get_key_state_group_for_letter(char)
            
            # Append the instructions and key images.
            if key:
                letter = char
                if letter == PARAGRAPH_CODE:
                    letter = 'enter'
                if letter == ' ':
                    letter = 'space'

                instructions = ''                
                
                try:
                    finger = FINGERS[key['key-finger']]
                except:
                    finger = ''
        
                if state == gtk.gdk.SHIFT_MASK:
                    # Choose the finger to press the SHIFT key with.
                    if key['key-finger'][0] == 'R':
                        shift_finger = FINGERS['LP']
                    else:
                        shift_finger = FINGERS['RP']

                    instructions = _('Press and hold the shift key with your %(finger)s, ') % { 'finger': shift_finger }
                    instructions += _('then press the %(letter)s key with your %(finger)s.') % { 'letter': letter, 'finger': finger }
        
                elif state == gtk.gdk.MOD5_MASK:
                    instructions = _('Press and hold the altgr key, ') 
                    instructions += _('then press the %(letter)s key with your %(finger)s.') % { 'letter': letter, 'finger': finger }
        
                elif state == gtk.gdk.SHIFT_MASK | gtk.gdk.MOD5_MASK:
                    instructions = _('Press and hold the altgr and shift keys, ')
                    instructions += _('then press the %(letter)s key with your %(finger)s.') % { 'letter': letter, 'finger': finger }
        
                else:
                    instructions = _('Press the %(letter)s key with your %(finger)s.') % { 'letter': letter, 'finger': finger }

                self.lessonbuffer.insert(self.lessonbuffer.get_end_iter(), instructions + '\n\n')

                if state & gtk.gdk.SHIFT_MASK:
                    shift_key = self.keyboard.find_key_by_label('shift')
                    pixbuf = self.keyboard.get_key_pixbuf(shift_key, scale=1)
                    self.lessonbuffer.insert_pixbuf(self.lessonbuffer.get_end_iter(), pixbuf)
                    self.lessonbuffer.insert(self.lessonbuffer.get_end_iter(), ' ')
                
                if state & gtk.gdk.MOD5_MASK:
                    altgr_key = self.keyboard.find_key_by_label('altgr')
                    pixbuf = self.keyboard.get_key_pixbuf(altgr_key, scale=1)
                    self.lessonbuffer.insert_pixbuf(self.lessonbuffer.get_end_iter(), pixbuf)
                    self.lessonbuffer.insert(self.lessonbuffer.get_end_iter(), ' ')

                pixbuf = self.keyboard.get_key_pixbuf(key, state, group, 1)
                self.lessonbuffer.insert_pixbuf(self.lessonbuffer.get_end_iter(), pixbuf)
            
            self.lessonbuffer.apply_tag_by_name('image',
                self.lessonbuffer.get_iter_at_mark(self.line_marks[0]),
                self.lessonbuffer.get_end_iter())
                   
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
        
        medals = self.lesson['medals']
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

                order = ' '.join([m['name'] for m in medals])
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
                self.activity.data['motd'] = 'newmedal'
                self.activity.data['medals'][lesson_name] = medal
                
                # Refresh the main screen given the new medal.
                self.activity.mainscreen.show_lesson(self.activity.mainscreen.lesson_index)
        
        # Generate results for the user.
        text = ''
        
        congrats = [
            _('Good job!'),
            _('Well done!'),
            _('Nice work!'),
            _('Way to go!')
        ]
        text += random.choice(congrats) + ' '
        
        if self.total_time > 0:
            text += _('You finished the lesson in %(time)d seconds, with %(errors)d errors.\n') % \
                { 'time': int(self.total_time), 'errors': self.incorrect_keys }
            text += _('Your words per minute (WPM) was %(wpm)d, and your accuracy was %(accuracy)d%%.\n\n') % \
                report
        else:
            text += _('You finished the lesson with %(errors)d errors.\n') % \
                { 'errors': self.incorrect_keys }
            text += _('Your accuracy was %(accuracy)d%%.\n\n') % \
                report
        
        if self.medal:
            # TODO: Play medal sound here.
            
            text += _('Congratulations!  You earned a %(type)s medal!') % medal
            
        else:
            # Comment on what the user needs to do better.
            need_wpm = report['wpm'] < medals[0]['wpm']
            need_accuracy = report['accuracy'] < medals[0]['accuracy']
            
            if need_accuracy and need_wpm:
                text += _('You need to practice this lesson more before moving on.')
                
            elif need_accuracy:
                text += _('You almost got a medal!  Next time, try not to make as many errors.')
                
            elif need_wpm:
                text += _('You almost got a medal!  Next time, try to type a little faster.')
            
        return text
        
    def end_lesson(self):
        self.activity.pop_screen()
        
        # Show the new medal if there was one.
        if self.medal:
            self.activity.push_screen(medalscreen.MedalScreen(self.medal, self.activity))

    def stop_cb(self, widget):
        self.activity.pop_screen()
