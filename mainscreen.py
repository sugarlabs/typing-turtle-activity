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
import logging, os, math, time, copy, json, locale, datetime, random, re, glob
from gettext import gettext as _

# Import PyGTK.
import gobject, pygtk, gtk, pango

# Import Sugar UI modules.
import sugar.activity.activity
from sugar.graphics import *

# Import activity modules.
import lessonscreen, medalscreen

class TitleScene(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)

        bundle = sugar.activity.activity.get_bundle_path()
        self.backgroundpixbuf = gtk.gdk.pixbuf_new_from_file(bundle + '/images/main-background.png')
        
        self.set_size_request(self.backgroundpixbuf.get_width(), self.backgroundpixbuf.get_height())
        
        self.connect("expose-event", self.expose_cb)
        
        self.title_original = _('Typing Turtle')
        self.title_src = self.title_original
        self.title_text = ''
        self.title_counter = 50
        
        gobject.timeout_add(10, self.timer_cb)

    def expose_cb(self, area, event):
        bounds = self.get_allocation()
        
        gc = self.get_style().fg_gc[gtk.STATE_NORMAL]
        
        self.window.draw_pixbuf(
            gc, self.backgroundpixbuf, 
            event.area.x, event.area.y, 
            event.area.x, event.area.y, event.area.width, event.area.height)
        
        # Animated Typing Turtle title.
        pc = self.create_pango_context()
        
        layout = self.create_pango_layout('')
        layout.set_font_description(pango.FontDescription('Times 60'))
        
        layout.set_text(self.title_original)
        original_size = layout.get_size()
        
        x = (bounds.width-original_size[0]/pango.SCALE)/2
        y = 10

        layout.set_text(self.title_text)        
        self.window.draw_layout(gc, x, y, layout)

    def timer_cb(self):
        self.title_counter -= 1
        if self.title_counter == 0:
            if len(self.title_src) > 0:
                self.title_text += self.title_src[0]
                self.title_src = self.title_src[1:]
                self.queue_draw()
            
            self.title_counter = random.randint(1, 5)
            
        return True
    
class MainScreen(gtk.VBox):
    def __init__(self, activity):
        gtk.VBox.__init__(self)
        
        self.activity = activity
        
        # Build background.
        self.titlescene = TitleScene()
        
        # Build lessons list.
        self.lessonbox = gtk.HBox()
        
        nexticon = sugar.graphics.icon.Icon(icon_name='go-next')
        self.nextlessonbtn = gtk.Button()
        self.nextlessonbtn.add(nexticon)
        self.nextlessonbtn.connect('clicked', self.next_lesson_clicked_cb)
        
        previcon = sugar.graphics.icon.Icon(icon_name='go-previous')
        self.prevlessonbtn = gtk.Button()
        self.prevlessonbtn.add(previcon)
        self.prevlessonbtn.connect('clicked', self.prev_lesson_clicked_cb)
        
        bundle_path = sugar.activity.activity.get_bundle_path() 
        code = locale.getlocale(locale.LC_ALL)[0]
        path = bundle_path + '/lessons/' + code
        
        # Find all .lesson files in ./lessons/en_US/ for example.
        self.lessons = []
        for f in glob.iglob(path + '/*.lesson'):
            fd = open(f, 'r')
            try:
                lesson = json.read(fd.read())
                self.lessons.append(lesson)
            finally:
                fd.close()
        
        self.lessons.sort(lambda x, y: x['level'] - y['level'])
        
        lessonscrollbox = gtk.HBox()
        lessonscrollbox.set_spacing(10)
        lessonscrollbox.pack_start(self.prevlessonbtn, False)
        lessonscrollbox.pack_start(self.lessonbox)
        lessonscrollbox.pack_start(self.nextlessonbtn, False)
        
        self.pack_start(self.titlescene, False, True, 10)
        self.pack_start(lessonscrollbox, True)
        
        self.show_highest_available_lesson()
    
    def show_highest_available_lesson(self):
        highest_index = 0
        for index in xrange(0, len(self.lessons)):
            if self.lessons[index]['requiredlevel'] <= self.activity.data['level']:
                highest_index = max(highest_index, index)
        print "showing lesson %d" % highest_index
        self.show_lesson(highest_index)
    
    def show_lesson(self, index):
        # Clear all widgets in the lesson box.
        for w in self.lessonbox:
            self.lessonbox.remove(w)
        
        self.prevlessonbtn.set_sensitive(index > 0)
        self.nextlessonbtn.set_sensitive(index < len(self.lessons)-1)
        
        lesson = self.lessons[index]

        self.lesson_index = index
        self.visible_lesson = lesson
        
        # Create the lesson button.
        label = gtk.Label()
        label.set_alignment(0.0, 0.25)
        label.set_markup("<span size='15000'><b>" + lesson['name'] + "</b></span>\n" + 
                         "<span size='10000'>" + lesson['description'] + "</span>")
        
        lessonbtn = gtk.Button()
        lessonbtn.add(label)
        lessonbtn.connect('clicked', self.lesson_clicked_cb)
        
        # Create the medal image.
        medalimage = gtk.Image()
        
        medal_type = 'none'
        if self.activity.data['medals'].has_key(lesson['name']):
            medal_type = self.activity.data['medals'][lesson['name']]['type']
        
        bundle = sugar.activity.activity.get_bundle_path()
        images = {
            'none':   bundle+'/images/no-medal.jpg',
            'bronze': bundle+'/images/bronze-medal.jpg',
            'silver': bundle+'/images/silver-medal.jpg',
            'gold':   bundle+'/images/gold-medal.jpg'
        }
        medalimage.set_from_file(images[medal_type])
        
        medalbtn = gtk.Button()
        medalbtn.add(medalimage)
        medalbtn.connect('clicked', self.medal_clicked_cb)
        
        # Disable the buttons unless available.
        lesson_available = self.activity.data['level'] >= lesson['requiredlevel']
        lessonbtn.set_sensitive(lesson_available)
        medalbtn.set_sensitive(lesson_available)
        
        self.lessonbox.pack_start(lessonbtn, True)
        self.lessonbox.pack_start(medalbtn, False)

        self.lessonbox.show_all()
    
    def next_lesson_clicked_cb(self, widget):
        self.show_lesson(self.lesson_index+1)
    
    def prev_lesson_clicked_cb(self, widget):
        self.show_lesson(self.lesson_index-1)
    
    def lesson_clicked_cb(self, widget):
        self.activity.push_screen(lessonscreen.LessonScreen(self.visible_lesson, self.activity))
    
    def medal_clicked_cb(self, widget):
        if self.activity.data['medals'].has_key(self.visible_lesson['name']):
            medal = self.activity.data['medals'][self.visible_lesson['name']]
            self.activity.push_screen(medalscreen.MedalScreen(medal, self.activity))
