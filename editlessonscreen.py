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

class EditLessonScreen(gtk.VBox):
    def __init__(self, activity, lesson):
        gtk.VBox.__init__(self)
        self.set_border_width(10)

        self.activity = activity
        self.lesson = lesson

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

        help = gtk.Label()
        help.set_padding(10, 0)
        help.set_alignment(1.0, 0.5)
        help.set_markup(
            _("Choose the lesson that you wish to modify.  If you wish to add a new lesson, ") +
            _("or delete an existing lesson, use the buttons at the bottom.")
            )

        self.vp = gtk.Viewport()

        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll.add(self.vp)

        self.pack_start(titlebox, False, False, 10)
        self.pack_start(help, False, False, 10)
        self.pack_start(gtk.HSeparator(), False, False, 0)
        self.pack_start(self.scroll, True, True, 0)

        self.build()
        
        self.show_all()

    def build_step(self, step, idx):
        stepbox = gtk.VBox()

        steplabel = gtk.Label()
        steplabel.set_markup("<span size='x-large' weight='bold'>" + (_('Step #%d') % (idx+1)) + "</span>")
        steplabel.set_alignment(0.0, 0.5)
        steplabel.set_padding(10, 0)

        generatelabel = gtk.Label()
        generatelabel.set_markup(_('Generate'))
        generatebtn = gtk.Button()
        generatebtn.add(generatelabel)
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

        btnbox = gtk.HBox()
        btnbox.pack_start(steplabel, False, False)
        btnbox.pack_end(addstepbtn, False, False)
        btnbox.pack_end(delstepbtn, False, False)
        btnbox.pack_end(moveupbtn, False, False)
        btnbox.pack_end(movedownbtn, False, False)
        btnbox.pack_end(generatebtn, False, False)

        instlabel = gtk.Label()
        instlabel.set_markup("<span size='large' weight='bold'>" + _('Instructions') + "</span>")
        instlabel.set_alignment(0.0, 0.5)
        instlabel.set_padding(20, 0)

        stepbox.insttext = gtk.TextView(gtk.TextBuffer())
        stepbox.insttext.props.wrap_mode = gtk.WRAP_WORD
        instscroll = gtk.ScrolledWindow()
        instscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        instscroll.add(stepbox.insttext)
        instscroll.set_size_request(-1, 75)
        stepbox.insttext.get_buffer().set_text(step['instructions'])

        instbox = gtk.HBox()
        instbox.pack_start(instlabel, False, False)
        instbox.pack_start(instscroll, True, True)

        textlabel = gtk.Label()
        textlabel.set_markup("<span size='large' weight='bold'>" + _('Text') + "</span>")
        textlabel.set_alignment(0.0, 0.5)
        textlabel.set_padding(20, 0)

        stepbox.texttext = gtk.TextView(gtk.TextBuffer())
        stepbox.texttext.props.wrap_mode = gtk.WRAP_WORD
        textscroll = gtk.ScrolledWindow()
        textscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textscroll.add(stepbox.texttext)
        textscroll.set_size_request(-1, 100)
        stepbox.texttext.get_buffer().set_text(step['text'])

        textbox = gtk.HBox()
        textbox.pack_start(textlabel, False, False)
        textbox.pack_start(textscroll, True, True)

        sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)   
        sizegroup.add_widget(instlabel)
        sizegroup.add_widget(textlabel)    

        stepbox.pack_start(btnbox, False, False, 10)
        stepbox.pack_start(instbox, False, False, 10)
        stepbox.pack_start(textbox, False, False, 10)
        
        return stepbox

    def build(self):
        # Add the editing controls.
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
        namebox.pack_start(namelabel, False, False)
        namebox.pack_start(self.nameent, True, True)
        
        typelabel = gtk.Label()
        typelabel.set_markup("<span size='large' weight='bold'>" + _('Type') + "</span>")
        typelabel.set_alignment(0.0, 0.5)
        typelabel.set_padding(20, 0)

        self.textradio = gtk.RadioButton(None, _('Normal Lesson'))
        self.balloonradio = gtk.RadioButton(self.textradio, _('Balloon Game'))
        
        self.textradio.set_active(self.lesson['type'] == 'normal')
        self.balloonradio.set_active(self.lesson['type'] == 'balloon')        

        typebox = gtk.HBox()
        typebox.pack_start(typelabel, False, False)
        typebox.pack_start(self.textradio, False, False)
        typebox.pack_start(self.balloonradio, False, False)
        
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
        descbox.pack_start(desclabel, False, False)
        descbox.pack_start(descscroll, True, True)

        sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)   
        sizegroup.add_widget(namelabel)
        sizegroup.add_widget(typelabel)    
        sizegroup.add_widget(desclabel)    

        self.vbox = gtk.VBox()
        self.vbox.set_border_width(20)
        self.vbox.pack_start(detailslabel, False, False, 10)        
        self.vbox.pack_start(namebox, False, False, 10)
        self.vbox.pack_start(typebox, False, False, 10)
        self.vbox.pack_start(descbox, False, False, 10)
        self.vbox.pack_start(gtk.HSeparator(), False, False, 0)
        
        if self.lesson['type'] == 'normal':
            self.stepboxes = []
            
            for step in self.lesson['steps']:
                stepbox = self.build_step(step, len(self.stepboxes))
                self.stepboxes.append(stepbox)
                
                self.vbox.pack_start(stepbox, False, False, 0)
                
        if self.lesson['type'] == 'balloon':
            textlabel = gtk.Label()
            textlabel.set_markup("<span size='large' weight='bold'>" + _('Words') + "</span>")
            textlabel.set_alignment(0.0, 0.5)
            textlabel.set_padding(20, 0)

            self.wordstext = gtk.TextView(gtk.TextBuffer())
            self.wordstext.props.wrap_mode = gtk.WRAP_WORD
            textscroll = gtk.ScrolledWindow()
            textscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            textscroll.add(self.wordstext)
            textscroll.set_size_request(-1, 200)
            self.wordstext.get_buffer().set_text(' '.join(self.lesson['words']))
    
            textbox = gtk.HBox()
            textbox.pack_start(textlabel, False, False)
            textbox.pack_start(textscroll, True, True)
            
            self.vbox.pack_start(textbox, False, False, 10)

        self.vbox.show_all()
        
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
        
        if self.textradio.get_active():
            self.lesson['type'] = 'normal'
       
            steps = []
            for sb in self.stepboxes:
                step = {}
                
                buf = sb.insttext.get_buffer()
                step['instructions'] = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
                
                buf = sb.texttext.get_buffer()
                step['text'] = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
                
                steps.append(step)
                
            self.lesson['steps'] = steps

        if self.balloonradio.get_active():
            self.lesson['type'] = 'balloon'
            
            buf = self.wordstext.get_buffer()
            text = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
            self.lesson['words'] = text.split(' ')

    def add_step_clicked_cb(self, btn, index):
        step = { 'instructions': '', 'text': '' }
        self.lesson['steps'].insert(index, step)
        self.build()
    
    def del_step_clicked_cb(self, btn, index):
        self.lesson['steps'].pop(index)
        self.build()
    
    def move_step_up_clicked_cb(self, btn, index):
        if index > 0:
            step = self.lesson['steps'].pop(index)
            self.lesson['steps'].insert(index-1, step)
            self.build()
    
    def move_step_down_clicked_cb(self, btn, index):
        if index < len(self.lesson['steps']) - 1:
            step = self.lesson['steps'].pop(index)
            self.lesson['steps'].insert(index+1, step)
            self.build()

