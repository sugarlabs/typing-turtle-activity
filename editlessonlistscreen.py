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
import json
from gi.repository import Gtk
from gi.repository import GObject

# Import Sugar UI modules.
import sugar3.activity.activity
import sugar3.graphics.style
import sugar3.graphics.alert
import sugar3.mime
import sugar3.datastore.datastore
from sugar3.graphics.objectchooser import ObjectChooser

# Import activity modules.
import editlessonscreen

class EditLessonListScreen(Gtk.VBox):
    def __init__(self, activity, lessons):
        GObject.GObject.__init__(self)

        self.activity = activity
        self.lessons = lessons

        # Add the header.
        title = Gtk.Label()
        title.set_markup("<span size='20000'><b>" + _("Edit Lessons") + "</b></span>")
        title.set_alignment(1.0, 0.0)
        
        stoplabel = Gtk.Label(label=_('Go Back'))
        stopbtn = Gtk.Button()
        stopbtn.add(stoplabel)
        stopbtn.connect('clicked', self.stop_clicked_cb)
       
        titlebox = Gtk.HBox()
        titlebox.pack_start(stopbtn, False, False, 10)
        titlebox.pack_end(title, False, False, 10)

        # Add the lesson list.
        self.treeview = Gtk.TreeView()
        self.treeview.set_rules_hint(True)
        self.treeview.set_enable_search(False)

        # Note that the only thing we store in our liststore is the lesson id.
        # All the actual data is in the lessons list.
        self.liststore = Gtk.ListStore(GObject.TYPE_INT)
        self.treeview.set_model(self.liststore)

        # Construct the columns.
        renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_('Name'), renderer)
        col.set_cell_data_func(renderer, self.name_render_cb) 
        self.treeview.append_column(col)

        renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_('Description'), renderer)
        col.set_cell_data_func(renderer, self.description_render_cb) 
        col.set_expand(True)
        self.treeview.append_column(col)

        renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_('Type'), renderer)
        col.set_cell_data_func(renderer, self.type_render_cb) 
        col.set_expand(False)
        self.treeview.append_column(col)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.treeview)

        importlabel = Gtk.Label(label=_('Import Lessons from Journal'))
        self.importbtn = Gtk.Button()
        self.importbtn.add(importlabel)
        self.importbtn.connect('clicked', self.import_clicked_cb)
        
        exportlabel = Gtk.Label(label=_('Export Lessons to Journal'))
        self.exportbtn = Gtk.Button()
        self.exportbtn.add(exportlabel)
        self.exportbtn.connect('clicked', self.export_clicked_cb)
        
        exportlabel = Gtk.Label(label=_('Save Lessons to Activity'))
        self.defaultsbtn = Gtk.Button()
        self.defaultsbtn.add(exportlabel)
        self.defaultsbtn.connect('clicked', self.set_default_clicked_cb)
        
        self.addbtn = Gtk.Button()
        self.addbtn.add(sugar3.graphics.icon.Icon(icon_name='list-add'))
        self.addbtn.connect('clicked', self.add_lesson_clicked_cb)
        self.delbtn = Gtk.Button()
        self.delbtn.add(sugar3.graphics.icon.Icon(icon_name='list-remove'))
        self.delbtn.connect('clicked', self.del_lesson_clicked_cb)
        self.delbtn.set_sensitive(False)
        self.moveupbtn = Gtk.Button()
        self.moveupbtn.add(sugar3.graphics.icon.Icon(icon_name='go-up'))
        self.moveupbtn.connect('clicked', self.move_lesson_up_clicked_cb)
        self.moveupbtn.set_sensitive(False)
        self.movedownbtn = Gtk.Button()
        self.movedownbtn.add(sugar3.graphics.icon.Icon(icon_name='go-down'))
        self.movedownbtn.connect('clicked', self.move_lesson_down_clicked_cb)
        self.movedownbtn.set_sensitive(False)

        btnbox = Gtk.HBox()
        btnbox.pack_start(self.importbtn, False, False, 10)
        btnbox.pack_start(self.exportbtn, False, False, 0)
        btnbox.pack_start(self.defaultsbtn, False, False, 10)
        btnbox.pack_end(self.addbtn, False, False, 0)
        btnbox.pack_end(self.delbtn, False, False, 0)
        btnbox.pack_end(self.moveupbtn, False, False, 0)
        btnbox.pack_end(self.movedownbtn, False, False, 0)

        self.pack_start(titlebox, False, False, 10)
        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
        self.pack_start(scroll, True, True, 10)
        self.pack_start(btnbox, False, False, 10)

        # README: I had to move these two lines here because the
        # signal was emitted before all the widget are created
        self.treeview.connect('cursor-changed', self.lesson_selected_cb)
        self.treeview.connect('row-activated', self.lesson_activated_cb)

        self.build()

        self.show_all()
    
    def build(self):
        # Fill the lesson list.
        self.liststore.clear()
        for t in range(0, len(self.lessons)):
            self.liststore.append((0,))
    
    def name_render_cb(self, column, cell_renderer, model, iter, data):
        id = model.get_path(iter).get_indices()[0]
        t = self.lessons[id]
        cell_renderer.set_property('text', t['name'])
    
    def description_render_cb(self, column, cell_renderer, model, iter, data):
        id = model.get_path(iter).get_indices()[0]
        t = self.lessons[id]
        cell_renderer.set_property('text', t['description'])

    def type_render_cb(self, column, cell_renderer, model, iter, data):
        id = model.get_path(iter).get_indices()[0]
        t = self.lessons[id]
        if t['type'] == 'normal':
            cell_renderer.set_property('text', _('Text'))
        if t['type'] == 'balloon':
            cell_renderer.set_property('text', _('Balloon Game'))

    def stop_clicked_cb(self, btn):
        # Assign lesson order.
        num = 0
        for l in self.lessons:
            l['order'] = num
            num = num + 1
        
        # Refresh the main screen given the new lesson data.
        if self.activity.mainscreen.lesson_index >= len(self.lessons):
            self.activity.mainscreen.lesson_index = len(self.lessons) - 1
        self.activity.mainscreen.show_lesson(self.activity.mainscreen.lesson_index)
        
        self.activity.pop_screen()
    
    def add_lesson_clicked_cb(self, btn):
        lesson = {}
        lesson['name'] = ''
        lesson['description'] = ''
        lesson['type'] = 'normal'
        lesson['steps'] = [ { 'mode':'text', 'instructions':'', 'text':'' } ]
        lesson['medals'] = [ 
            { 'name': 'bronze', 'wpm': 15, 'accuracy': 70, 'score': 3000 },
            { 'name': 'silver', 'wpm': 20, 'accuracy': 80, 'score': 4500 },
            { 'name': 'gold',   'wpm': 25, 'accuracy': 90, 'score': 6000 },
        ]
        self.lessons.append(lesson)
        self.activity.push_screen(editlessonscreen.EditLessonScreen(self.activity, lesson))
        self.liststore.append()

    def del_lesson_clicked_cb(self, btn):
        if len(self.lessons) > 1:
            path, focus_column = self.treeview.get_cursor()

            if path:
                msg = sugar3.graphics.alert.ConfirmationAlert()
                msg.props.title = _('Delete Lesson?')
                msg.props.msg = _('Deleting the lesson will erase the lesson content.')
        
                def alert_response_cb(alert, response_id, self, path):
                    self.activity.remove_alert(alert)
                    if response_id is Gtk.ResponseType.OK:
                        id = path.get_indices()[0]
                        self.lessons.pop(id)
                        del self.liststore[path]
                        self.treeview.get_selection().select_path(id)
                        self.treeview.grab_focus()
                        self.update_sensitivity()

                msg.connect('response', alert_response_cb, self, path)
                
                self.activity.add_alert(msg)
                msg.show_all()

    def move_lesson_up_clicked_cb(self, btn):
        path, focus_column = self.treeview.get_cursor()
        if path:
            id = path.get_indices()[0]
            if id > 0:
                lesson = self.lessons.pop(id)
                self.lessons.insert(id - 1, lesson)
                self.liststore.swap(self.liststore.get_iter(id), self.liststore.get_iter(id - 1))
                self.treeview.get_selection().select_path(id - 1)
                self.treeview.grab_focus()
                self.update_sensitivity()

    def move_lesson_down_clicked_cb(self, btn):
        path, focus_column = self.treeview.get_cursor()
        if path:
            id = path.get_indices()[0]
            if id < len(self.lessons) - 1:
                lesson = self.lessons.pop(id)
                self.lessons.insert(id + 1, lesson)
                self.liststore.swap(self.liststore.get_iter(id), self.liststore.get_iter(id + 1))
                self.treeview.get_selection().select_path(id + 1)
                self.treeview.grab_focus()
                self.update_sensitivity()

    def lesson_selected_cb(self, treeview):
        self.update_sensitivity()

    def lesson_activated_cb(self, treeview, path, column):
        path, focus_column = self.treeview.get_cursor()
        id = path.get_indices()[0]
        lesson = self.lessons[id]
        self.activity.push_screen(editlessonscreen.EditLessonScreen(self.activity, lesson))

    def enter(self):
        self.update_sensitivity()

    def update_sensitivity(self):
        path, focus_column = self.treeview.get_cursor()
        if path:
            self.delbtn.set_sensitive(True)

            id = path.get_indices()[0]
            if id > 0:
                self.moveupbtn.set_sensitive(True)
            else:
                self.moveupbtn.set_sensitive(False)

            if id < len(self.lessons) - 1:
                self.movedownbtn.set_sensitive(True)
            else:
                self.movedownbtn.set_sensitive(False)
        else:
            self.delbtn.set_sensitive(False)
            self.moveupbtn.set_sensitive(False)
            self.movedownbtn.set_sensitive(False)

        # Don't allow to remove the last one
        if len(self.lessons) == 1:
            self.delbtn.set_sensitive(False)
        
    def import_clicked_cb(self, btn):
        chooser = ObjectChooser(parent=self,
                                what_filter='text/x-typing-turtle-lessons')

        jobject = None
        if chooser.run() == Gtk.ResponseType.ACCEPT:
            jobject = chooser.get_selected_object()

        if jobject and jobject.file_path:
            fd = open(jobject.file_path, 'r')
            
            try:
                data = json.loads(fd.read())
                
                # Replace lessons without destroying the object.
                while len(self.lessons):
                    self.lessons.pop()
                for l in data['lessons']:
                    self.lessons.append(l)
                self.build()
            
            finally:
                fd.close()
    
    def export_clicked_cb(self, btn):
        # Create the new journal entry
        fileObject = sugar3.datastore.datastore.create()

        meta = self.activity.metadata
        fileObject.metadata['title'] = meta['title'] + _(' (Exported Lessons)')
        fileObject.metadata['title_set_by_user'] = meta['title_set_by_user']
        fileObject.metadata['mime_type'] = 'text/x-typing-turtle-lessons'
        fileObject.metadata['icon-color'] = meta['icon-color']
        fileObject.file_path = os.path.join(self.activity.get_activity_root(), 'instance', '%i' % time.time())
        
        fd = open(fileObject.file_path, 'w')
        
        try:
            data = { 'lessons': self.lessons }
            fd.write(json.dumps(data))
            
        finally:
            fd.close()
        
        sugar3.datastore.datastore.write(fileObject, transfer_ownership=True)
        fileObject.destroy()
        del fileObject

    def set_default_clicked_cb(self, btn):
        code = locale.getdefaultlocale()[0] or 'en_US'
        path = sugar3.activity.activity.get_bundle_path() + '/lessons/%s.lessons' % code
        
        fd = open(path, 'w')
        
        try:
            data = { 'lessons': self.lessons }
            fd.write(json.dumps(data))
            
        finally:
            fd.close()
            
