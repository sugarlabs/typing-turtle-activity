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
import logging, os, math, time, copy, locale, datetime, random, re, glob
from gettext import gettext as _
from port import json

# Import PyGTK.
import gobject, pygtk, gtk, pango

# Import Sugar UI modules.
import sugar.activity.activity
from sugar.graphics import *

# Import activity modules.
import lessonscreen, medalscreen
import balloongame
import titlescene
import keyboard

# Temporary SVGs of medals from Wikimedia Commons.
# See the links below for licensing information.
# http://commons.wikimedia.org/wiki/File:Gold_medal_world_centered.svg
# http://commons.wikimedia.org/wiki/File:Silver_medal_world_centered.svg
# http://commons.wikimedia.org/wiki/File:Bronze_medal_world_centered.svg

class MainScreen(gtk.VBox):
    def __init__(self, activity):
        gtk.VBox.__init__(self)
        
        self.activity = activity
        
        # Build background.
        self.titlescene = titlescene.TitleScene()
        
        # Build lessons list.
        self.lessonbox = gtk.HBox()
        
        #nexticon = sugar.graphics.icon.Icon(icon_name='go-next')
        #self.nextlessonbtn.add(nexticon)
        nextlabel = gtk.Label()
        nextlabel.set_markup("<span size='large'>" + _('Next') + "</span>")

        self.nextlessonbtn = gtk.Button()
        self.nextlessonbtn.add(nextlabel)
        self.nextlessonbtn.connect('clicked', self.next_lesson_clicked_cb)
        
        #previcon = sugar.graphics.icon.Icon(icon_name='go-previous')
        #self.prevlessonbtn.add(previcon)
        prevlabel = gtk.Label()
        prevlabel.set_markup("<span size='large'>" + _('Previous') + "</span>")

        self.prevlessonbtn = gtk.Button()
        self.prevlessonbtn.add(prevlabel)
        self.prevlessonbtn.connect('clicked', self.prev_lesson_clicked_cb)
        
        lessonlabel = gtk.Label()
        lessonlabel.set_markup("<span size='x-large' weight='bold'>" + _('Start Lesson') + "</span>")
        
        lessonbtn = gtk.Button()
        lessonbtn.add(lessonlabel)
        lessonbtn.connect('clicked', self.lesson_clicked_cb)
        lessonbtn.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#60b060'))
        
        # Load lessons for this language.
        code = locale.getdefaultlocale()[0] or 'en_US'
        lessons_path = os.path.join(sugar.activity.activity.get_bundle_path(), 'lessons')
        lessons_file = os.path.join(lessons_path, code + '.lessons')
        if os.path.isfile(lessons_file):
            self.load_lessons(lessons_file)
        else:
            code = code[0:2]
            lessons_file = os.path.join(lessons_path, code + '.lessons')
            if os.path.isfile(lessons_file):
                self.load_lessons(lessons_file)
            else:
                # Fallback to en_US lessons if none found.
                self.load_lessons('lessons/en_US.lessons')

        # We cannot run without lessons.
        if not len(self.lessons):
            sys.exit(1)

        # Sort by the 'order' field.
        self.lessons.sort(lambda x, y: x.get('order', 0) - y.get('order', 0))

        # Load all the keyboard images.
        width = int(gtk.gdk.screen_width())
        height = int(gtk.gdk.screen_height()*0.3)
        self.keyboard_images = keyboard.KeyboardImages(width, height)
        self.keyboard_images.load_images()
        
        navbox = gtk.HBox()
        navbox.set_spacing(10)
        navbox.pack_start(self.prevlessonbtn, True)
        navbox.pack_start(lessonbtn, True)
        navbox.pack_start(self.nextlessonbtn, True)
        
        lessonbox = gtk.VBox()
        lessonbox.set_spacing(10)
        lessonbox.pack_start(navbox, False)
        lessonbox.pack_start(self.lessonbox)
        
        self.pack_start(self.titlescene, False, True, 10)
        self.pack_start(lessonbox, True)
        
        self.show_next_lesson()

    def enter(self):
        self.activity.editorbtn.set_sensitive(True)
    
    def leave(self):
        self.activity.editorbtn.set_sensitive(False)
    
    def load_lessons(self, path):
        fd = open(path, 'r')
        try:
            data = json.loads(fd.read())
            self.lessons = data['lessons']
        finally:
            fd.close()

    def get_next_lesson(self):
        """Returns the index of the first lesson without a medal."""
        index = len(self.lessons)-1
        for i in xrange(0, len(self.lessons)):
            if self.lessons[i]['order'] >= 0 and \
               not self.activity.data['medals'].has_key(self.lessons[i]['name']):
                index = min(index, i)
        return index
    
    def show_next_lesson(self):
        """Displays the first lesson which the user can activate that does not yet have a medal."""
        self.show_lesson(self.get_next_lesson())
    
    def show_lesson(self, index):
        # Clear all widgets in the lesson box.
        for w in self.lessonbox:
            self.lessonbox.remove(w)
        
        self.prevlessonbtn.set_sensitive(index > 0)
        self.nextlessonbtn.set_sensitive(index < len(self.lessons)-1)
        
        lesson = self.lessons[index]
        
        self.lesson_index = index
        self.visible_lesson = lesson

        medal_type = 'none'
        if self.activity.data['medals'].has_key(lesson['name']):
            medal_type = self.activity.data['medals'][lesson['name']]['type']
        
        # Create the lesson button.
        namelabel = gtk.Label()
        namelabel.set_alignment(0.5, 0.5)
        namelabel.set_markup("<span size='x-large' weight='bold'>" + lesson['name'] + "</span>")
        desclabel = gtk.Label()
        desclabel.set_alignment(0.5, 0.5)
        desclabel.set_markup("<span size='large' color='#606060'>" + lesson['description'] + "</span>")
        
        if medal_type != 'none':
            hint = _('You earned a medal in this lesson!  Advance to the next one\nby clicking the Next button.')
        else:
            hint = ''
                
        #hintlabel = gtk.Label()
        #hintlabel.set_alignment(0.0, 0.8)
        #hintlabel.set_markup("<span size='8000' color='#606020'>" + hint + "</span>")
        
        labelbox = gtk.VBox()
        labelbox.set_spacing(10)
        labelbox.set_border_width(20)
        labelbox.pack_start(namelabel, False)
        labelbox.pack_start(desclabel, False)
        #labelbox.pack_start(hintlabel)

        # Create the medal image.
        images = {
            'none':   'images/no-medal.svg',
            'bronze': 'images/bronze-medal.svg',
            'silver': 'images/silver-medal.svg',
            'gold':   'images/gold-medal.svg'
        }

        medal_size = int(2.0 * sugar.graphics.style.GRID_CELL_SIZE)
        medalpixbuf = gtk.gdk.pixbuf_new_from_file(images[medal_type])
        medalpixbuf = medalpixbuf.scale_simple(medal_size, medal_size, gtk.gdk.INTERP_BILINEAR)
        
        medalimage = gtk.Image()
        medalimage.set_from_pixbuf(medalpixbuf)
        
        names = {
            'none':   _('No Medal Yet'),
            'bronze': _('Bronze Medal'),
            'silver': _('Silver Medal'),
            'gold':   _('Gold Medal'),
        }
        medallabel = gtk.Label(names[medal_type])
        
        medalbox = gtk.VBox()
        medalbox.pack_start(medalimage)
        medalbox.pack_start(medallabel)
        
        medalbtn = gtk.Button()
        medalbtn.add(medalbox)
        medalbtn.connect('clicked', self.medal_clicked_cb)
        
        # Hilite the button in the direction of the first unmedaled lesson.
        next_index = self.get_next_lesson()
        if next_index > self.lesson_index and index < len(self.lessons)-1:
            self.nextlessonbtn.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#ff8080'))
        else:
            self.nextlessonbtn.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#40a040'))
        if next_index < self.lesson_index and index > 0:
            self.prevlessonbtn.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#ff8080'))
        else:
            self.prevlessonbtn.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#40a040'))
        
        self.lessonbox.pack_start(labelbox, True)
        if medal_type != 'none':
            self.lessonbox.pack_start(medalbtn, False)

        self.lessonbox.show_all()
    
    def next_lesson_clicked_cb(self, widget):
        self.show_lesson(self.lesson_index+1)
    
    def prev_lesson_clicked_cb(self, widget):
        self.show_lesson(self.lesson_index-1)
    
    def lesson_clicked_cb(self, widget):
        if self.visible_lesson['type'] == 'balloon':
            reload(balloongame)
            self.activity.push_screen(balloongame.BalloonGame(self.visible_lesson, self.activity))
        else:
            reload(lessonscreen)
            self.activity.push_screen(lessonscreen.LessonScreen(self.visible_lesson, self.keyboard_images, self.activity))
    
    def medal_clicked_cb(self, widget):
        if self.activity.data['medals'].has_key(self.visible_lesson['name']):
            medal = self.activity.data['medals'][self.visible_lesson['name']]
            self.activity.push_screen(medalscreen.MedalScreen(medal, self.activity))
