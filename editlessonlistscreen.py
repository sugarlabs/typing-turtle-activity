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

# Import activity modules.
import editlessonscreen

class EditLessonListScreen(gtk.VBox):
    def __init__(self, activity, lessons):
        gtk.VBox.__init__(self)

        self.activity = activity
        self.lessons = lessons

        # Add the header.
        title = gtk.Label()
        title.set_markup("<span size='20000'><b>" + _("Edit Lessons") + "</b></span>")
        title.set_alignment(1.0, 0.0)
        
        stoplabel = gtk.Label(_('Go Back'))
        stopbtn = gtk.Button()
        stopbtn.add(stoplabel)
        stopbtn.connect('clicked', self.stop_clicked_cb)
       
        titlebox = gtk.HBox()
        titlebox.pack_start(stopbtn, False, False, 10)
        titlebox.pack_end(title, False, False, 10)

        # Add the lesson list.
        self.treeview = gtk.TreeView()
        self.treeview.set_rules_hint(True)
        self.treeview.set_enable_search(False)

        self.treeview.connect('cursor-changed', self.lesson_selected_cb)
        self.treeview.connect('row-activated', self.lesson_activated_cb)

        # Note that the only thing we store in our liststore is the lesson id.
        # All the actual data is in the lessons list.
        self.liststore = gtk.ListStore(gobject.TYPE_INT)
        self.treeview.set_model(self.liststore)

        # Construct the columns.
        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Name'), renderer)
        col.set_cell_data_func(renderer, self.name_render_cb) 
        self.treeview.append_column(col)

        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Description'), renderer)
        col.set_cell_data_func(renderer, self.description_render_cb) 
        col.set_expand(True)
        self.treeview.append_column(col)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.add(self.treeview)

        addlabel = gtk.Label()
        addlabel.set_markup(_('Add Lesson'))
        addlessonbtn = gtk.Button()
        addlessonbtn.add(addlabel)
        addlessonbtn.connect('clicked', self.add_lesson_clicked_cb)

        editlabel = gtk.Label()
        editlabel.set_markup('<span size="x-large"><b>'+_('Edit Lesson')+'</b></span>')
        self.editlessonbtn = gtk.Button()
        self.editlessonbtn.add(editlabel)
        self.editlessonbtn.connect('clicked', self.edit_lesson_clicked_cb)
        self.editlessonbtn.set_sensitive(False)

        dellabel = gtk.Label()
        dellabel.set_markup(_('Delete Lesson'))
        self.dellessonbtn = gtk.Button()
        self.dellessonbtn.add(dellabel)
        self.dellessonbtn.connect('clicked', self.del_lesson_clicked_cb)
        self.dellessonbtn.set_sensitive(False)

        buttonbox = gtk.HBox()
        buttonbox.pack_start(addlessonbtn, True, False, 10)
        buttonbox.pack_start(self.editlessonbtn, True, False, 10)
        buttonbox.pack_start(self.dellessonbtn, True, False, 10)

        self.pack_start(titlebox, False, False, 10)
        self.pack_start(gtk.HSeparator(), False, False, 0)
        self.pack_start(scroll, True, True, 10)
        self.pack_start(buttonbox, False, False, 10)

        self.build()

        self.show_all()
    
    def build(self):
        # Fill the lesson list.
        self.liststore.clear()
        for t in range(0, len(self.lessons)-1):
            self.liststore.append((t,))
    
    def name_render_cb(self, column, cell_renderer, model, iter):
        id = model.get_value(iter, 0)
        t = self.lessons[id]
        cell_renderer.set_property('text', t['name'])
    
    def description_render_cb(self, column, cell_renderer, model, iter):
        id = model.get_value(iter, 0)
        t = self.lessons[id]
        cell_renderer.set_property('text', t['description'])

    def stop_clicked_cb(self, btn):
        # Refresh the main screen given the new lesson data.
        self.activity.mainscreen.show_lesson(self.activity.mainscreen.lesson_index)
        
        self.activity.pop_screen()
    
    def add_lesson_clicked_cb(self, btn):
        lesson = { 'name':'', 'description':'', 'type':'normal', 'steps':[ { 'instructions':'', 'text':'' } ] }
        self.lessons.append(lesson)
        self.activity.push_screen(editlessonscreen.EditLessonScreen(self.activity, lesson))
        self.build()

    def del_lesson_clicked_cb(self, btn):
        path = self.treeview.get_cursor()[0]
        if path:
            model = self.liststore
            iter = model.get_iter(path)
            id = model.get_value(iter, 0)
            self.lessons.pop(id)
            self.build()

    def edit_lesson_clicked_cb(self, btn):
        path = self.treeview.get_cursor()[0]
        if path:
            model = self.liststore
            iter = model.get_iter(path)
            id = model.get_value(iter, 0)
            lesson = self.lessons[id]
            self.activity.push_screen(editlessonscreen.EditLessonScreen(self.activity, lesson))
        
    def lesson_selected_cb(self, treeview):
        path = treeview.get_cursor()[0]
        if path:
            self.editlessonbtn.set_sensitive(True)
            self.dellessonbtn.set_sensitive(True)
        else:
            self.editlessonbtn.set_sensitive(False)
            self.dellessonbtn.set_sensitive(False)

    def lesson_activated_cb(self, treeview, path, column):
        model = treeview.get_model()
        id = model.get_value(model.get_iter(path), 0)
        lesson = self.lessons[id]
        self.activity.push_screen(editlessonscreen.EditLessonScreen(self.activity, lesson))


