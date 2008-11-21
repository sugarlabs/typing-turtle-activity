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
from sugar.graphics import *

# Import activity modules.
import lessonscreen, medalscreen

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
        
        lessons.sort(lambda x, y: x['level'] - y['level'])
        
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
            
            hbox.button = btn
            hbox.medalbutton = medalbtn
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
            # Disable the lesson button unless available.
            lesson_available = self.activity.data['level'] >= l.lesson['requiredlevel']
            l.button.set_sensitive(lesson_available)
            l.medalbutton.set_sensitive(lesson_available)
            
            # Update the medal image.
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
        self.activity.push_screen(lessonscreen.LessonScreen(widget.lesson, self.activity))
    
    def medal_clicked_cb(self, widget):
        if self.activity.data['medals'].has_key(widget.lesson['name']):
            medal = self.activity.data['medals'][widget.lesson['name']]
            self.activity.push_screen(medalscreen.MedalScreen(medal, self.activity))
