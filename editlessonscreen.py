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
import logging, os, math, time, copy, json, locale, datetime, random, re
from gettext import gettext as _

# Import PyGTK.
import gobject, pygtk, gtk, pango

# Import Sugar UI modules.
import sugar.activity.activity
import sugar.graphics.style

class EditLessonScreen(gtk.VBox):
    def add_step_cb(w):
        pass

    def make_step(self):
        stepbox = gtk.VBox()

        stepbox.pack_start(gtk.HSeparator())

        delstepbtn = gtk.Button()
        delstepbtn.add(gtk.Label('Delete'))

        addstepbtn = gtk.Button()
        addstepbtn.add(gtk.Label('Add'))

        moveupbtn = gtk.Button()
        moveupbtn.add(gtk.Label('Move Up'))

        movedownbtn = gtk.Button()
        movedownbtn.add(gtk.Label('Move Down'))

        btnbox = gtk.HBox()
        btnbox.pack_start(gtk.Label('Step'))
        btnbox.pack_end(addstepbtn, False, False)
        btnbox.pack_end(delstepbtn, False, False)
        btnbox.pack_end(moveupbtn, False, False)
        btnbox.pack_end(movedownbtn, False, False)

        stepbox.pack_start(btnbox)

        stepbox.pack_start(gtk.Label(_('Instructions')))
        inst_text = gtk.TextView(gtk.TextBuffer())
        inst_text.props.wrap_mode = gtk.WRAP_WORD
        inst_scroll = gtk.ScrolledWindow()
        inst_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        inst_scroll.add(inst_text)
        inst_scroll.set_size_request(-1, 100)
        stepbox.pack_start(inst_scroll)

        stepbox.pack_start(gtk.Label(_('Text')))
        text_text = gtk.TextView(gtk.TextBuffer())
        text_text.props.wrap_mode = gtk.WRAP_WORD
        text_scroll = gtk.ScrolledWindow()
        text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        text_scroll.add(text_text)
        text_scroll.set_size_request(-1, 200)
        stepbox.pack_start(text_scroll)

        return stepbox

    def make_lesson(self, lesson):
        table = gtk.Table(8, 2)

        table.attach(gtk.Label(_('Name')), 0, 1, 0, 1)
        nameent = gtk.Entry()
        table.attach(nameent, 1, 2, 0, 1)

        table.attach(gtk.Label(_('Description')), 0, 1, 1, 2)
        descent = gtk.Entry()
        table.attach(descent, 1, 2, 1, 2)

        table.attach(gtk.Label(_('Type')), 0, 1, 2, 3)
        type_drop = gtk.combo_box_new_text()
        type_drop.append_text(_('Text'))
        type_drop.append_text(_('Game'))
        table.attach(type_drop, 1, 2, 2, 3)

        vbox = gtk.VBox()
        vbox.pack_start(table, False, False)

        vbox.pack_start(self.make_step_widgets())
        vbox.pack_start(self.make_step_widgets())

        vp = gtk.Viewport()
        vp.add(vbox)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.add(vp)



    def __init__(self, activity):
        gtk.VBox.__init__(self)

        # Build the lesson editor.
        self.pack_start(scroll)

        self.show_all()
