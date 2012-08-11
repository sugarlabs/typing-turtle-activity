#!/usr/bin/env python
# vi: sw=4 et
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
from gi.repository import GObject
from gi.repository import Pango

# Import Sugar UI modules.
import sugar3.activity.activity
import sugar3.graphics.style
import sugar3.graphics.icon

# Import lessonbuilder functions.
import lessonbuilder

class EditLessonScreen(Gtk.VBox):
    def __init__(self, activity, lesson):
        GObject.GObject.__init__(self)
        self.set_border_width(10)

        self.activity = activity
        self.lesson = lesson

        self.in_build = False
        
        # Add the header.
        title = Gtk.Label()
        title.set_markup("<span size='20000'><b>" + _("Edit a Lesson") + "</b></span>")
        title.set_alignment(1.0, 0.0)
        
        stoplabel = Gtk.Label(label=_('Go Back'))
        stopbtn = Gtk.Button()
        stopbtn.add(stoplabel)
        stopbtn.connect('clicked', self.stop_clicked_cb)
               
        titlebox = Gtk.HBox()
        titlebox.pack_start(stopbtn, False, False, 10)
        titlebox.pack_end(title, False, False, 10)

        self.vp = Gtk.Viewport()

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scroll.add(self.vp)

        self.pack_start(titlebox, False, False, 10)
        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
        self.pack_start(self.scroll, True, True, 0)

        self.build()
        
        self.show_all()

    def build_generate(self):
        generatebox = Gtk.VBox()
        generatebox.set_spacing(5)

        newlabel = Gtk.Label(label=_('New keys'))
        knownlabel = Gtk.Label(label=_('Known keys'))
        lengthlabel = Gtk.Label(label=_('Length'))
        
        generatebox.newkeysent = Gtk.Entry()
        generatebox.newkeysent.set_width_chars(8)
        generatebox.knownkeysent = Gtk.Entry()
        generatebox.knownkeysent.set_width_chars(15)
        generatebox.lengthent = Gtk.Entry()
        generatebox.lengthent.set_width_chars(5)
        generatebox.lengthent.set_text('60')
        
        oklabel = Gtk.Label()
        oklabel.set_markup(_('Generate!'))
        okbtn = Gtk.Button()
        okbtn.add(oklabel)
        okbtn.connect('clicked', self.generate_ok_clicked_cb, generatebox)
        okbtn.set_alignment(0.5, 0.5)

        box = Gtk.HBox()
        box.set_spacing(10)
        box.pack_start(newlabel, False, True, 0)
        box.pack_start(generatebox.newkeysent, False, True, 0)
        box.pack_start(knownlabel, False, True, 0)
        box.pack_start(generatebox.knownkeysent, False, True, 0)
        box.pack_start(lengthlabel, False, True, 0)
        box.pack_start(generatebox.lengthent, False, True, 0)
        box.pack_end(okbtn, False, True, 0)
        box.show_all()
        
        wordslabel = Gtk.Label()
        wordslabel.set_markup(_('Edit Word List'))
        wordsbtn = Gtk.Button()
        wordsbtn.add(wordslabel)
        wordsbtn.connect('clicked', self.generate_words_clicked_cb)
        wordsbtn.set_alignment(0.5, 0.5)

        generatebox.pack_start(box, True, True, 0)
        generatebox.pack_start(wordsbtn, expand=False, fill=False, padding=0)
        
        return generatebox

    def build_step(self, step, idx):
        stepbox = Gtk.VBox()
        stepbox.set_spacing(5)

        steplabel = Gtk.Label()
        steplabel.set_markup("<span size='x-large' weight='bold'>" + (_('Step #%d') % (idx+1)) + "</span>")
        steplabel.set_alignment(0.0, 0.5)
        steplabel.set_padding(10, 0)

        # Build the step type combo box.
        stepbox.typecombo = Gtk.ComboBoxText()
        stepbox.typecombo.append_text(_('Keys'))
        stepbox.typecombo.append_text(_('Words'))

        steptype = step.get('mode', 'text') 
        if steptype == 'key':
            stepbox.typecombo.set_active(0)
        elif steptype == 'text': 
            stepbox.typecombo.set_active(1)
        
        # Build the tool buttons.
        delstepbtn = Gtk.Button()
        delstepbtn.add(sugar3.graphics.icon.Icon(icon_name='list-remove'))
        delstepbtn.connect('clicked', self.del_step_clicked_cb, idx)
        addstepbtn = Gtk.Button()
        addstepbtn.add(sugar3.graphics.icon.Icon(icon_name='list-add'))
        addstepbtn.connect('clicked', self.add_step_clicked_cb, idx)
        moveupbtn = Gtk.Button()
        moveupbtn.add(sugar3.graphics.icon.Icon(icon_name='go-up'))
        moveupbtn.connect('clicked', self.move_step_up_clicked_cb, idx)
        movedownbtn = Gtk.Button()
        movedownbtn.add(sugar3.graphics.icon.Icon(icon_name='go-down'))
        movedownbtn.connect('clicked', self.move_step_down_clicked_cb, idx)

        if idx == 0:
            moveupbtn.set_sensitive(False)
        if idx == len(self.lesson['steps']) - 1:
            movedownbtn.set_sensitive(False)

        btnbox = Gtk.HBox()
        btnbox.pack_start(steplabel, False, False, 0)
        btnbox.pack_start(stepbox.typecombo, expand=False,
                          fill=False, padding=10)
        btnbox.pack_end(addstepbtn, False, False, 0)
        btnbox.pack_end(delstepbtn, False, False, 0)
        btnbox.pack_end(moveupbtn, False, False, 0)
        btnbox.pack_end(movedownbtn, False, False, 0)

        # Build the instructions entry.
        instlabel = Gtk.Label()
        instlabel.set_markup("<span size='large' weight='bold'>" + _('Instructions') + "</span>")
        instlabel.set_alignment(0.0, 0.5)
        instlabel.set_padding(20, 0)

        self.labelsizegroup.add_widget(instlabel)

        stepbox.insttext = Gtk.TextView()
        stepbox.insttext.set_buffer(Gtk.TextBuffer())
        stepbox.insttext.props.wrap_mode = Gtk.WrapMode.WORD
        stepbox.insttext.modify_font(Pango.FontDescription('Monospace'))
        instscroll = Gtk.ScrolledWindow()
        instscroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        instscroll.add(stepbox.insttext)
        instscroll.set_size_request(-1, 75)
        stepbox.insttext.get_buffer().set_text(step['instructions'])

        instbox = Gtk.HBox()
        instbox.pack_start(instlabel, False, False, 0)
        instbox.pack_start(instscroll, True, True, 0)

        # Build the text entry.
        textlabel = Gtk.Label()
        textlabel.set_markup("<span size='large' weight='bold'>" + _('Text') + "</span>")
        textlabel.set_alignment(0.0, 0.5)
        textlabel.set_padding(20, 0)

        self.labelsizegroup.add_widget(textlabel)

        stepbox.texttext = Gtk.TextView()
        stepbox.texttext.set_buffer(Gtk.TextBuffer())
        stepbox.texttext.props.wrap_mode = Gtk.WrapMode.WORD
        stepbox.texttext.modify_font(Pango.FontDescription('monospace'))
        textscroll = Gtk.ScrolledWindow()
        textscroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        textscroll.add(stepbox.texttext)
        textscroll.set_size_request(-1, 100)
        stepbox.texttext.get_buffer().set_text(step['text'])

        textbox = Gtk.HBox()
        textbox.pack_start(textlabel, False, True, 0)
        textbox.pack_start(textscroll, True, True, 0)

        sizegroup = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)
        sizegroup.add_widget(instlabel)
        sizegroup.add_widget(textlabel)    

        stepbox.pack_start(btnbox, False, True, 0)
        stepbox.pack_start(instbox, False, True, 0)
        stepbox.pack_start(textbox, False, True, 0)
        
        return stepbox

    def build_medal(self, medal, name):
        box = Gtk.HBox()

        label = Gtk.Label()
        label.set_markup("<span size='large' weight='bold'>" + name + "</span>")
        label.set_alignment(0.0, 0.5)
        label.set_padding(20, 0)

        self.labelsizegroup.add_widget(label)
        
        box.pack_start(label, False, False, 0)

        if self.lesson['type'] == 'normal':
            acclabel = Gtk.Label(label=_('Accuracy'))
            wpmlabel = Gtk.Label(label=_('WPM'))
            
            box.accent = Gtk.Entry()
            box.wpment = Gtk.Entry()

            box.accent.set_text(str(medal['accuracy']))
            box.wpment.set_text(str(medal['wpm']))
        
            box.pack_start(acclabel, False, False, 10)
            box.pack_start(box.accent, False, False, 0)
            box.pack_start(wpmlabel, False, False, 10)
            box.pack_start(box.wpment, False, False, 0)
        
        elif self.lesson['type'] == 'balloon':
            scorelabel = Gtk.Label(label=_('Score'))
            
            box.scoreent = Gtk.Entry()
            box.scoreent.set_text(str(medal['score']))
        
            box.pack_start(scorelabel, False, False, 10)
            box.pack_start(box.scoreent, False, False, 0)
            
        return box
      
    def build(self):
        self.in_build = True
        
        self.vbox = Gtk.VBox()
        self.vbox.set_border_width(20)
        self.vbox.set_spacing(5)
        
        self.labelsizegroup = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)

        # Lesson details widgets.
        detailslabel = Gtk.Label()
        detailslabel.set_markup("<span size='x-large'><b>" + _('Lesson Details') + "</b></span>")
        detailslabel.set_alignment(0.0, 0.5)
        detailslabel.set_padding(10, 0)

        namelabel = Gtk.Label()
        namelabel.set_markup("<span size='large' weight='bold'>" + _('Name') + "</span>")
        namelabel.set_alignment(0.0, 0.5)
        namelabel.set_padding(20, 0)

        self.nameent = Gtk.Entry()
        self.nameent.set_text(self.lesson['name'])

        namebox = Gtk.HBox()
        namebox.pack_start(namelabel, False, True, 0)
        namebox.pack_start(self.nameent, True, True, 0)
        
        typelabel = Gtk.Label()
        typelabel.set_markup("<span size='large' weight='bold'>" + _('Type') + "</span>")
        typelabel.set_alignment(0.0, 0.5)
        typelabel.set_padding(20, 0)

        self.textradio = Gtk.RadioButton(None, _('Normal Lesson'))
        self.textradio.connect('toggled', self.type_toggled_cb)
        
        self.balloonradio = Gtk.RadioButton(self.textradio, _('Balloon Game'))
        self.balloonradio.connect('toggled', self.type_toggled_cb)
        
        self.textradio.set_active(self.lesson['type'] == 'normal')
        self.balloonradio.set_active(self.lesson['type'] == 'balloon')        

        typebox = Gtk.HBox()
        typebox.pack_start(typelabel, False, True, 0)
        typebox.pack_start(self.textradio, False, True, 0)
        typebox.pack_start(self.balloonradio, False, True, 0)
        
        desclabel = Gtk.Label()
        desclabel.set_markup("<span size='large' weight='bold'>" + _('Description') + "</span>")
        desclabel.set_alignment(0.0, 0.5)
        desclabel.set_padding(20, 0)

        self.desctext = Gtk.TextView()
        self.desctext.set_buffer(Gtk.TextBuffer())
        self.desctext.props.wrap_mode = Gtk.WrapMode.WORD
        descscroll = Gtk.ScrolledWindow()
        descscroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        descscroll.add(self.desctext)
        descscroll.set_size_request(-1, 75)
        self.desctext.get_buffer().set_text(self.lesson['description'])

        descbox = Gtk.HBox()
        descbox.pack_start(desclabel, False, True, 0)
        descbox.pack_start(descscroll, True, True, 0)

        # Build the options.
        optslabel = Gtk.Label()
        optslabel.set_markup("<span size='large' weight='bold'>" + _('Options') + "</span>")
        optslabel.set_alignment(0.0, 0.5)
        optslabel.set_padding(20, 0)

        self.mistakescheck = Gtk.CheckButton(_('Allow Mistakes'))
        self.mistakescheck.set_active(self.lesson.get('options', {}).get('mistakes', True))
        self.backspacecheck = Gtk.CheckButton(_('Allow Backspace'))
        self.backspacecheck.set_active(self.lesson.get('options', {}).get('backspace', True))

        optsbox = Gtk.HBox()
        optsbox.pack_start(optslabel, False, True, 0)
        optsbox.pack_start(self.backspacecheck, False, True, 0)
        optsbox.pack_start(self.mistakescheck, False, True, 0)
            
        self.labelsizegroup.add_widget(namelabel)
        self.labelsizegroup.add_widget(typelabel)    
        self.labelsizegroup.add_widget(desclabel)    
        self.labelsizegroup.add_widget(optslabel)    
  
        self.vbox.pack_start(detailslabel, False, True, 0)
        self.vbox.pack_start(namebox, False, True, 0)
        self.vbox.pack_start(typebox, False, True, 0)
        self.vbox.pack_start(descbox, False, True, 0)
        self.vbox.pack_start(optsbox, False, True, 0)

        # Build the generator.
        generatelabel = Gtk.Label()
        generatelabel.set_markup("<span size='x-large'><b>" + _('Automatic Lesson Generator') + "</b></span>")
        generatelabel.set_alignment(0.0, 0.5)
        generatelabel.set_padding(10, 0)

        generatebox = self.build_generate()
        self.vbox.pack_start(generatelabel, expand=False,
                             fill=False, padding=10)
        self.vbox.pack_start(generatebox, False, True, 0)
        
        self.has_normal_widgets = False
        self.has_balloon_widgets = False
        
        # Steps or words widgets.
        if self.lesson['type'] == 'normal':
            self.has_normal_widgets = True
            
            if not self.lesson.has_key('steps') or len(self.lesson['steps']) == 0:
                step = { 'instructions': '', 'text': '' }
                self.lesson['steps'] = [ step ]              
                  
            self.stepboxes = []
            
            for step in self.lesson['steps']:
                stepbox = self.build_step(step, len(self.stepboxes))
                self.stepboxes.append(stepbox)
                
                self.vbox.pack_start(stepbox, False, True, 0)
                
        if self.lesson['type'] == 'balloon':
            self.has_balloon_widgets = True

            if not self.lesson.has_key('words') or len(self.lesson['words']) == 0:
                self.lesson['words'] = []
            
            textlabel = Gtk.Label()
            textlabel.set_markup("<span size='large' weight='bold'>" + _('Words') + "</span>")
            textlabel.set_alignment(0.0, 0.5)
            textlabel.set_padding(20, 0)

            self.labelsizegroup.add_widget(textlabel)

            self.wordstext = Gtk.TextView()
            self.wordstext.set_buffer(Gtk.TextBuffer())
            self.wordstext.props.wrap_mode = Gtk.WrapMode.WORD
            self.wordstext.modify_font(Pango.FontDescription('Monospace'))
            textscroll = Gtk.ScrolledWindow()
            textscroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            textscroll.add(self.wordstext)
            textscroll.set_size_request(-1, 200)
            self.wordstext.get_buffer().set_text(' '.join(self.lesson['words']))
    
            textbox = Gtk.HBox()
            textbox.pack_start(textlabel, False, True, 0)
            textbox.pack_start(textscroll, True, True, 0)
            
            self.vbox.pack_start(textbox, False, True, 0)

        # Medal requirements widgets.
        medalslabel = Gtk.Label()
        medalslabel.set_markup("<span size='x-large'><b>" + _('Medal Requirements') + "</b></span>")
        medalslabel.set_alignment(0.0, 0.5)
        medalslabel.set_padding(10, 0)

        self.vbox.pack_start(medalslabel, expand=False,
                             fill=False, padding=10)
        
        self.medalboxes = []
        self.medalboxes.append(self.build_medal(self.lesson['medals'][0], _('Bronze')))
        self.medalboxes.append(self.build_medal(self.lesson['medals'][1], _('Silver')))
        self.medalboxes.append(self.build_medal(self.lesson['medals'][2], _('Gold')))
        
        self.vbox.pack_start(self.medalboxes[0], False, True, 0)
        self.vbox.pack_start(self.medalboxes[1], False, True, 0)
        self.vbox.pack_start(self.medalboxes[2], False, True, 0)

        self.vbox.show_all()
        
        self.in_build = False
        
        # Remove any existing controls.
        if self.vp.get_child():
            self.vp.remove(self.vp.get_child())
        
        self.vp.add(self.vbox)
    
    def stop_clicked_cb(self, btn):
        self.save()
        
        self.activity.pop_screen()
    
    def save(self):
        self.lesson['name'] = self.nameent.get_text()
        
        buf = self.desctext.get_buffer()
        self.lesson['description'] = buf.get_text(buf.get_start_iter(),
                                                  buf.get_end_iter(), False)
        
        if not self.lesson.has_key('options'):
            self.lesson['options'] = {}
        self.lesson['options']['mistakes'] = self.mistakescheck.get_active()
        self.lesson['options']['backspace'] = self.backspacecheck.get_active()
        
        if self.textradio.get_active():
            self.lesson['type'] = 'normal'
       
            if self.has_normal_widgets:
                steps = []
                
                for sb in self.stepboxes:
                    step = {}
                    
                    buf = sb.insttext.get_buffer()
                    step['instructions'] = buf.get_text(buf.get_start_iter(),
                                                        buf.get_end_iter(),
                                                        False)
                    
                    buf = sb.texttext.get_buffer()
                    step['text'] = buf.get_text(buf.get_start_iter(),
                                                buf.get_end_iter(), False)
                    
                    if sb.typecombo.get_active() == 0:
                        step['mode'] = 'key'
                    elif sb.typecombo.get_active() == 1:
                        step['mode'] = 'text'
                    
                    steps.append(step)
                
                self.lesson['steps'] = steps
    
                for i in range(0, 3):
                    self.lesson['medals'][i]['accuracy'] = int(self.medalboxes[i].accent.get_text())                
                    self.lesson['medals'][i]['wpm'] = int(self.medalboxes[i].wpment.get_text())
                    
        if self.balloonradio.get_active():
            self.lesson['type'] = 'balloon'

            if self.has_balloon_widgets:
                buf = self.wordstext.get_buffer()
                text = buf.get_text(buf.get_start_iter(),
                                    buf.get_end_iter(), False)
                self.lesson['words'] = text.split(' ')
                
                for i in range(0, 3):
                    self.lesson['medals'][i]['score'] = int(self.medalboxes[i].scoreent.get_text())                

    def add_step_clicked_cb(self, btn, index):
        self.save()

        step = { 'instructions': '', 'text': '' }
        self.lesson['steps'].insert(index, step)
        
        self.build()
    
    def del_step_clicked_cb(self, btn, index):
        self.save()

        self.lesson['steps'].pop(index)
        
        self.build()
    
    def move_step_up_clicked_cb(self, btn, index):
        if index > 0:
            self.save()

            step = self.lesson['steps'].pop(index)
            self.lesson['steps'].insert(index-1, step)
            
            self.build()
    
    def move_step_down_clicked_cb(self, btn, index):
        if index < len(self.lesson['steps']) - 1:
            self.save()

            step = self.lesson['steps'].pop(index)
            self.lesson['steps'].insert(index+1, step)
            
            self.build()

    def type_toggled_cb(self, btn):
        # Prevent infinite recursion
        if self.in_build:
            return
        
        self.save()
        self.build()
        
    def get_wordlist(self):
        if len(self.activity.wordlist):
            return self.activity.wordlist
        
        # Load the myspell dictionary.
        # TODO: Find a better way to determine its location.
        code = locale.getdefaultlocale()[0] or 'en_US'
        return lessonbuilder.load_wordlist('/usr/share/myspell/%s.dic' % code)

    def generate_ok_clicked_cb(self, btn, box):
        self.save()

        new_keys = box.newkeysent.get_text()
        known_keys = box.knownkeysent.get_text()
        length = int(box.lengthent.get_text())
        
        try:
            words = self.get_wordlist()

            if self.lesson['type'] == 'normal':
                self.lesson['steps'] = lessonbuilder.build_key_steps(length, new_keys, known_keys, words, [])
            
            if self.lesson['type'] == 'balloon':
                self.lesson['words'] = lessonbuilder.build_game_words(length, new_keys, known_keys, words, [])                
                
        except Exception, e:
            logging.error('Unable to generate lesson: ' + str(e))

        self.build()

    def generate_words_clicked_cb(self, btn):
        self.activity.push_screen(WordListScreen(self.activity))

class WordListScreen(Gtk.VBox):
    def __init__(self, activity):
        GObject.GObject.__init__(self)
        self.set_border_width(10)

        self.activity = activity
        
        # Add the header.
        title = Gtk.Label()
        title.set_markup("<span size='20000'><b>" + _("Edit Word List") + "</b></span>")
        title.set_alignment(1.0, 0.0)
        
        stoplabel = Gtk.Label(label=_('Go Back'))
        stopbtn = Gtk.Button()
        stopbtn.add(stoplabel)
        stopbtn.connect('clicked', self.stop_clicked_cb)
       
        titlebox = Gtk.HBox()
        titlebox.pack_start(stopbtn, False, False, 10)
        titlebox.pack_end(title, False, False, 10)

        subtitle = Gtk.Label()
        subtitle.set_markup("<span size='10000'>" + _("Type or paste words here, for the Automatic Lesson Generator.  If empty, the dictionary will be used.") + "</span>")
        subtitle.set_alignment(1.0, 0.0)

        self.wordlisttext = Gtk.TextView()
        self.wordlisttext.set_buffer(Gtk.TextBuffer())
        self.wordlisttext.props.wrap_mode = Gtk.WrapMode.WORD
        wordlistscroll = Gtk.ScrolledWindow()
        wordlistscroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        wordlistscroll.add(self.wordlisttext)
        wordlistscroll.set_size_request(-1, 75)
        self.wordlisttext.get_buffer().set_text(' '.join(self.activity.wordlist))

        self.pack_start(titlebox, False, True, 0)
        self.pack_start(subtitle, False, True, 0)
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, expand=False, fill=False, padding=0)
        self.pack_start(wordlistscroll, True, True, 0)
        
        self.show_all()

    def stop_clicked_cb(self, btn):
        buf = self.wordlisttext.get_buffer()
        wordstext = buf.get_text(buf.get_start_iter(),
                                 buf.get_end_iter(), False)
        self.activity.wordlist = wordstext.split()
        
        self.activity.pop_screen()
