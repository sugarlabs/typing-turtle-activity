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

# Import PyGTK.
import gobject, pygtk, gtk, pango

# Import Sugar UI modules.
import sugar.activity.activity
import sugar.graphics.style
import sugar.graphics.icon

# Import lessonbuilder functions.
import lessonbuilder

class EditLessonScreen(gtk.VBox):
    def __init__(self, activity, lesson):
        gtk.VBox.__init__(self)
        self.set_border_width(10)

        self.activity = activity
        self.lesson = lesson

        self.in_build = False
        
        # Add the header.
        title = gtk.Label()
        title.set_markup("<span size='20000'><b>" + _("Edit a Lesson") + "</b></span>")
        title.set_alignment(1.0, 0.0)
        
        stoplabel = gtk.Label(_('Go Back'))
        stopbtn = gtk.Button()
        stopbtn.add(stoplabel)
        stopbtn.connect('clicked', self.stop_clicked_cb)
               
        titlebox = gtk.HBox()
        titlebox.pack_start(stopbtn, False, False, 10)
        titlebox.pack_end(title, False, False, 10)

        self.vp = gtk.Viewport()

        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll.add(self.vp)

        self.pack_start(titlebox, False, False, 10)
        self.pack_start(gtk.HSeparator(), False, False, 0)
        self.pack_start(self.scroll, True, True, 0)

        self.build()
        
        self.show_all()

    def build_generate(self):
        generatebox = gtk.VBox()
        generatebox.set_spacing(5)

        newlabel = gtk.Label(_('New keys'))       
        knownlabel = gtk.Label(_('Known keys'))
        lengthlabel = gtk.Label(_('Length'))       
        
        generatebox.newkeysent = gtk.Entry()
        generatebox.newkeysent.set_width_chars(8)
        generatebox.knownkeysent = gtk.Entry()
        generatebox.knownkeysent.set_width_chars(15)
        generatebox.lengthent = gtk.Entry()
        generatebox.lengthent.set_width_chars(5)
        generatebox.lengthent.set_text('60')
        
        oklabel = gtk.Label()
        oklabel.set_markup(_('Generate!'))
        okbtn = gtk.Button()
        okbtn.add(oklabel)
        okbtn.connect('clicked', self.generate_ok_clicked_cb, generatebox)
        okbtn.set_alignment(0.5, 0.5)

        box = gtk.HBox()
        box.set_spacing(10)
        box.pack_start(newlabel, expand=False)
        box.pack_start(generatebox.newkeysent, expand=False)
        box.pack_start(knownlabel, expand=False)
        box.pack_start(generatebox.knownkeysent, expand=False)
        box.pack_start(lengthlabel, expand=False)
        box.pack_start(generatebox.lengthent, expand=False)
        box.pack_end(okbtn, expand=False)
        box.show_all()
        
        wordslabel = gtk.Label()
        wordslabel.set_markup(_('Edit Word List'))
        wordsbtn = gtk.Button()
        wordsbtn.add(wordslabel)
        wordsbtn.connect('clicked', self.generate_words_clicked_cb)
        wordsbtn.set_alignment(0.5, 0.5)

        generatebox.pack_start(box)
        generatebox.pack_start(wordsbtn, expand=False, fill=False)               
        
        return generatebox

    def build_step(self, step, idx):
        stepbox = gtk.VBox()
        stepbox.set_spacing(5)

        steplabel = gtk.Label()
        steplabel.set_markup("<span size='x-large' weight='bold'>" + (_('Step #%d') % (idx+1)) + "</span>")
        steplabel.set_alignment(0.0, 0.5)
        steplabel.set_padding(10, 0)

        # Build the step type combo box.
        stepbox.typecombo = gtk.combo_box_new_text()
        stepbox.typecombo.append_text(_('Keys'))
        stepbox.typecombo.append_text(_('Words'))

        steptype = step.get('mode', 'text') 
        if steptype == 'key':
            stepbox.typecombo.set_active(0)
        elif steptype == 'text': 
            stepbox.typecombo.set_active(1)
        
        # Build the tool buttons.
        delstepbtn = gtk.Button()
        delstepbtn.add(sugar.graphics.icon.Icon(icon_name='list-remove'))
        delstepbtn.connect('clicked', self.del_step_clicked_cb, idx)
        addstepbtn = gtk.Button()
        addstepbtn.add(sugar.graphics.icon.Icon(icon_name='list-add'))
        addstepbtn.connect('clicked', self.add_step_clicked_cb, idx)
        moveupbtn = gtk.Button()
        moveupbtn.add(sugar.graphics.icon.Icon(icon_name='go-up'))
        moveupbtn.connect('clicked', self.move_step_up_clicked_cb, idx)
        movedownbtn = gtk.Button()
        movedownbtn.add(sugar.graphics.icon.Icon(icon_name='go-down'))
        movedownbtn.connect('clicked', self.move_step_down_clicked_cb, idx)

        if idx == 0:
            moveupbtn.set_sensitive(False)
        if idx == len(self.lesson['steps']) - 1:
            movedownbtn.set_sensitive(False)

        btnbox = gtk.HBox()
        btnbox.pack_start(steplabel, False, False)
        btnbox.pack_start(stepbox.typecombo, expand=False, padding=10)
        btnbox.pack_end(addstepbtn, False, False)
        btnbox.pack_end(delstepbtn, False, False)
        btnbox.pack_end(moveupbtn, False, False)
        btnbox.pack_end(movedownbtn, False, False)

        # Build the instructions entry.
        instlabel = gtk.Label()
        instlabel.set_markup("<span size='large' weight='bold'>" + _('Instructions') + "</span>")
        instlabel.set_alignment(0.0, 0.5)
        instlabel.set_padding(20, 0)

        self.labelsizegroup.add_widget(instlabel)

        stepbox.insttext = gtk.TextView(gtk.TextBuffer())
        stepbox.insttext.props.wrap_mode = gtk.WRAP_WORD
        stepbox.insttext.modify_font(pango.FontDescription('Monospace'))
        instscroll = gtk.ScrolledWindow()
        instscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        instscroll.add(stepbox.insttext)
        instscroll.set_size_request(-1, 75)
        stepbox.insttext.get_buffer().set_text(step['instructions'])

        instbox = gtk.HBox()
        instbox.pack_start(instlabel, False, False)
        instbox.pack_start(instscroll, True, True)

        # Build the text entry.
        textlabel = gtk.Label()
        textlabel.set_markup("<span size='large' weight='bold'>" + _('Text') + "</span>")
        textlabel.set_alignment(0.0, 0.5)
        textlabel.set_padding(20, 0)

        self.labelsizegroup.add_widget(textlabel)

        stepbox.texttext = gtk.TextView(gtk.TextBuffer())
        stepbox.texttext.props.wrap_mode = gtk.WRAP_WORD
        stepbox.texttext.modify_font(pango.FontDescription('monospace'))
        textscroll = gtk.ScrolledWindow()
        textscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textscroll.add(stepbox.texttext)
        textscroll.set_size_request(-1, 100)
        stepbox.texttext.get_buffer().set_text(step['text'])

        textbox = gtk.HBox()
        textbox.pack_start(textlabel, expand=False)
        textbox.pack_start(textscroll)

        sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)   
        sizegroup.add_widget(instlabel)
        sizegroup.add_widget(textlabel)    

        stepbox.pack_start(btnbox, expand=False)
        stepbox.pack_start(instbox, expand=False)
        stepbox.pack_start(textbox, expand=False)
        
        return stepbox

    def build_medal(self, medal, name):
        box = gtk.HBox()

        label = gtk.Label()
        label.set_markup("<span size='large' weight='bold'>" + name + "</span>")
        label.set_alignment(0.0, 0.5)
        label.set_padding(20, 0)

        self.labelsizegroup.add_widget(label)
        
        box.pack_start(label, False, False)

        if self.lesson['type'] == 'normal':
            acclabel = gtk.Label(_('Accuracy'))       
            wpmlabel = gtk.Label(_('WPM'))
            
            box.accent = gtk.Entry()
            box.wpment = gtk.Entry()

            box.accent.set_text(str(medal['accuracy']))
            box.wpment.set_text(str(medal['wpm']))
        
            box.pack_start(acclabel, False, False, 10)
            box.pack_start(box.accent, False, False)
            box.pack_start(wpmlabel, False, False, 10)
            box.pack_start(box.wpment, False, False)
        
        elif self.lesson['type'] == 'balloon' or \
             self.lesson['type'] == 'kite':
            scorelabel = gtk.Label(_('Score'))
            
            box.scoreent = gtk.Entry()
            box.scoreent.set_text(str(medal['score']))
        
            box.pack_start(scorelabel, False, False, 10)
            box.pack_start(box.scoreent, False, False)
            
        return box
      
    def build(self):
        self.in_build = True
        
        self.vbox = gtk.VBox()
        self.vbox.set_border_width(20)
        self.vbox.set_spacing(5)
        
        self.labelsizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)   

        # Lesson details widgets.
        detailslabel = gtk.Label()
        detailslabel.set_markup("<span size='x-large'><b>" + _('Lesson Details') + "</b></span>")
        detailslabel.set_alignment(0.0, 0.5)
        detailslabel.set_padding(10, 0)

        namelabel = gtk.Label()
        namelabel.set_markup("<span size='large' weight='bold'>" + _('Name') + "</span>")
        namelabel.set_alignment(0.0, 0.5)
        namelabel.set_padding(20, 0)

        self.nameent = gtk.Entry()
        self.nameent.set_text(self.lesson['name'])

        namebox = gtk.HBox()
        namebox.pack_start(namelabel, expand=False)
        namebox.pack_start(self.nameent)
        
        typelabel = gtk.Label()
        typelabel.set_markup("<span size='large' weight='bold'>" + _('Type') + "</span>")
        typelabel.set_alignment(0.0, 0.5)
        typelabel.set_padding(20, 0)

        self.textradio = gtk.RadioButton(None, _('Normal Lesson'))
        self.textradio.connect('toggled', self.type_toggled_cb)
        
        self.balloonradio = gtk.RadioButton(self.textradio, _('Balloon Game'))
        self.balloonradio.connect('toggled', self.type_toggled_cb)
        
        self.kiteradio = gtk.RadioButton(self.textradio, _('Kite Game'))
        self.kiteradio.connect('toggled', self.type_toggled_cb)
        
        self.textradio.set_active(self.lesson['type'] == 'normal')
        self.balloonradio.set_active(self.lesson['type'] == 'balloon')        
        self.kiteradio.set_active(self.lesson['type'] == 'kite')        

        typebox = gtk.HBox()
        typebox.pack_start(typelabel, expand=False)
        typebox.pack_start(self.textradio, expand=False)
        typebox.pack_start(self.balloonradio, expand=False)
        typebox.pack_start(self.kiteradio, expand=False)
        
        desclabel = gtk.Label()
        desclabel.set_markup("<span size='large' weight='bold'>" + _('Description') + "</span>")
        desclabel.set_alignment(0.0, 0.5)
        desclabel.set_padding(20, 0)

        self.desctext = gtk.TextView(gtk.TextBuffer())
        self.desctext.props.wrap_mode = gtk.WRAP_WORD
        descscroll = gtk.ScrolledWindow()
        descscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        descscroll.add(self.desctext)
        descscroll.set_size_request(-1, 75)
        self.desctext.get_buffer().set_text(self.lesson['description'])

        descbox = gtk.HBox()
        descbox.pack_start(desclabel, expand=False)
        descbox.pack_start(descscroll)

        # Build the options.
        optslabel = gtk.Label()
        optslabel.set_markup("<span size='large' weight='bold'>" + _('Options') + "</span>")
        optslabel.set_alignment(0.0, 0.5)
        optslabel.set_padding(20, 0)

        self.mistakescheck = gtk.CheckButton(_('Allow Mistakes'))
        self.mistakescheck.set_active(self.lesson.get('options', {}).get('mistakes', True))
        self.backspacecheck = gtk.CheckButton(_('Allow Backspace'))
        self.backspacecheck.set_active(self.lesson.get('options', {}).get('backspace', True))

        optsbox = gtk.HBox()
        optsbox.pack_start(optslabel, expand=False)
        optsbox.pack_start(self.backspacecheck, expand=False)
        optsbox.pack_start(self.mistakescheck, expand=False)
            
        self.labelsizegroup.add_widget(namelabel)
        self.labelsizegroup.add_widget(typelabel)    
        self.labelsizegroup.add_widget(desclabel)    
        self.labelsizegroup.add_widget(optslabel)    
  
        self.vbox.pack_start(detailslabel, expand=False)        
        self.vbox.pack_start(namebox, expand=False)
        self.vbox.pack_start(typebox, expand=False)
        self.vbox.pack_start(descbox, expand=False)
        self.vbox.pack_start(optsbox, expand=False)

        # Build the generator.
        generatelabel = gtk.Label()
        generatelabel.set_markup("<span size='x-large'><b>" + _('Automatic Lesson Generator') + "</b></span>")
        generatelabel.set_alignment(0.0, 0.5)
        generatelabel.set_padding(10, 0)

        generatebox = self.build_generate()
        self.vbox.pack_start(generatelabel, expand=False, padding=10)      
        self.vbox.pack_start(generatebox, expand=False)       
        
        self.has_normal_widgets = False
        self.has_game_widgets = False
        
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
                
                self.vbox.pack_start(stepbox, expand=False)
                
        if self.lesson['type'] == 'balloon' or \
           self.lesson['type'] == 'kite':
            self.has_game_widgets = True

            if not self.lesson.has_key('words') or len(self.lesson['words']) == 0:
                self.lesson['words'] = []
            
            textlabel = gtk.Label()
            textlabel.set_markup("<span size='large' weight='bold'>" + _('Words') + "</span>")
            textlabel.set_alignment(0.0, 0.5)
            textlabel.set_padding(20, 0)

            self.labelsizegroup.add_widget(textlabel)

            self.wordstext = gtk.TextView(gtk.TextBuffer())
            self.wordstext.props.wrap_mode = gtk.WRAP_WORD
            self.wordstext.modify_font(pango.FontDescription('Monospace'))
            textscroll = gtk.ScrolledWindow()
            textscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            textscroll.add(self.wordstext)
            textscroll.set_size_request(-1, 200)
            self.wordstext.get_buffer().set_text(' '.join(self.lesson['words']))
    
            textbox = gtk.HBox()
            textbox.pack_start(textlabel, expand=False)
            textbox.pack_start(textscroll)
            
            self.vbox.pack_start(textbox, expand=False)

        # Medal requirements widgets.
        medalslabel = gtk.Label()
        medalslabel.set_markup("<span size='x-large'><b>" + _('Medal Requirements') + "</b></span>")
        medalslabel.set_alignment(0.0, 0.5)
        medalslabel.set_padding(10, 0)

        self.vbox.pack_start(medalslabel, expand=False, padding=10)
        
        self.medalboxes = []
        self.medalboxes.append(self.build_medal(self.lesson['medals'][0], _('Bronze')))
        self.medalboxes.append(self.build_medal(self.lesson['medals'][1], _('Silver')))
        self.medalboxes.append(self.build_medal(self.lesson['medals'][2], _('Gold')))
        
        self.vbox.pack_start(self.medalboxes[0], expand=False)
        self.vbox.pack_start(self.medalboxes[1], expand=False)
        self.vbox.pack_start(self.medalboxes[2], expand=False)

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
        self.lesson['description'] = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
        
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
                    step['instructions'] = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
                    
                    buf = sb.texttext.get_buffer()
                    step['text'] = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
                    
                    if sb.typecombo.get_active() == 0:
                        step['mode'] = 'key'
                    elif sb.typecombo.get_active() == 1:
                        step['mode'] = 'text'
                    
                    steps.append(step)
                
                self.lesson['steps'] = steps
    
        if self.balloonradio.get_active():
            self.lesson['type'] = 'balloon'

        if self.kiteradio.get_active():
            self.lesson['type'] = 'kite'

        if self.has_game_widgets:
            buf = self.wordstext.get_buffer()
            text = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
            self.lesson['words'] = text.split(' ')
            
            for i in range(0, 3):
                self.lesson['medals'][i]['score'] = int(self.medalboxes[i].scoreent.get_text())                

        else:
            for i in range(0, 3):
                self.lesson['medals'][i]['accuracy'] = int(self.medalboxes[i].accent.get_text())                
                self.lesson['medals'][i]['wpm'] = int(self.medalboxes[i].wpment.get_text())
                    

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

class WordListScreen(gtk.VBox):
    def __init__(self, activity):
        gtk.VBox.__init__(self)
        self.set_border_width(10)

        self.activity = activity
        
        # Add the header.
        title = gtk.Label()
        title.set_markup("<span size='20000'><b>" + _("Edit Word List") + "</b></span>")
        title.set_alignment(1.0, 0.0)
        
        stoplabel = gtk.Label(_('Go Back'))
        stopbtn = gtk.Button()
        stopbtn.add(stoplabel)
        stopbtn.connect('clicked', self.stop_clicked_cb)
       
        titlebox = gtk.HBox()
        titlebox.pack_start(stopbtn, False, False, 10)
        titlebox.pack_end(title, False, False, 10)

        subtitle = gtk.Label()
        subtitle.set_markup("<span size='10000'>" + _("Type or paste words here, for the Automatic Lesson Generator.  If empty, the dictionary will be used.") + "</span>")
        subtitle.set_alignment(1.0, 0.0)

        self.wordlisttext = gtk.TextView(gtk.TextBuffer())
        self.wordlisttext.props.wrap_mode = gtk.WRAP_WORD
        wordlistscroll = gtk.ScrolledWindow()
        wordlistscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        wordlistscroll.add(self.wordlisttext)
        wordlistscroll.set_size_request(-1, 75)
        self.wordlisttext.get_buffer().set_text(' '.join(self.activity.wordlist))

        self.pack_start(titlebox, expand=False)
        self.pack_start(subtitle, expand=False)
        self.pack_start(gtk.HSeparator(), expand=False)
        self.pack_start(wordlistscroll)
        
        self.show_all()

    def stop_clicked_cb(self, btn):
        buf = self.wordlisttext.get_buffer()
        wordstext = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
        self.activity.wordlist = wordstext.split()
        
        self.activity.pop_screen()
