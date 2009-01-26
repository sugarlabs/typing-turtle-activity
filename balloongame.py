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

import random
from gettext import gettext as _

import gobject, pygtk, gtk, pango

# Each 'stage' contains a certain number of balloons as well as
# parameters about them.
BALLOON_STAGES = [
    { 'count': 10, 'delay': 80 },
    { 'count': 20, 'delay': 60 },
    { 'count': 70, 'delay': 40 },
]

class Balloon:
    def __init__(self, x, y, vx, vy, word):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.word = word
        self.size = 100

class BalloonGame(gtk.VBox):
    def __init__(self, lesson, activity):
        gtk.VBox.__init__(self)
        
        self.lesson = lesson
        self.activity = activity
        
        # Build title bar.
        title = gtk.Label()
        title.set_markup("<span size='20000'><b>" + lesson['name'] + "</b></span>")
        title.set_alignment(1.0, 0.0)
        
        stoplabel = gtk.Label(_('Go Back'))
        stopbtn =  gtk.Button()
        stopbtn.add(stoplabel)
        stopbtn.connect('clicked', self.stop_cb)
        
        hbox = gtk.HBox()
        hbox.pack_start(stopbtn, False, False, 10)
        hbox.pack_end(title, False, False, 10)
        
        # Build the game drawing area.
        self.area = gtk.DrawingArea()
        self.area.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#ffffff'))
        self.area.connect("expose-event", self.expose_cb)

        # Connect keyboard grabbing and releasing callbacks.        
        self.area.connect('realize', self.realize_cb)
        self.area.connect('unrealize', self.unrealize_cb)

        self.pack_start(hbox, False, False, 10)
        self.pack_start(self.area, True, True)
        
        self.show_all()
        
        # Initialize the game data.
        self.balloons = []

        self.score = 0
        self.spawn_delay = 10

        self.stage_idx = 0
        self.stage = BALLOON_STAGES[self.stage_idx]
        self.count_left = self.stage['count']

        self.finished = False

        # Start the animation loop running.        
        self.update_timer = gobject.timeout_add(20, self.tick, priority=gobject.PRIORITY_HIGH_IDLE+30)
    
    def realize_cb(self, widget):
        self.activity.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.key_press_cb_id = self.activity.connect('key-press-event', self.key_cb)

        # Clear the mouse cursor. 
        #pixmap = gtk.gdk.Pixmap(widget.window, 10, 10)
        #color = gtk.gdk.Color()
        #cursor = gtk.gdk.Cursor(pixmap, pixmap, color, color, 5, 5)
        #widget.window.set_cursor(cursor)
        
    def unrealize_cb(self, widget):
        self.activity.disconnect(self.key_press_cb_id)
    
    def stop_cb(self, widget):
        # Stop the animation loop.
        if self.update_timer:
            gobject.source_remove(self.update_timer)
        
        self.activity.pop_screen()

    def key_cb(self, widget, event):
        # Ignore hotkeys.
        if event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.MOD1_MASK):
            return False

        # Extract information about the key pressed.
        key = gtk.gdk.keyval_to_unicode(event.keyval)
        if key != 0: key = unichr(key)

        if self.finished:
            key_name = gtk.gdk.keyval_name(event.keyval)
            if key_name == 'Return':
                self.activity.pop_screen()

        else:
            for b in self.balloons:
                if b.word[0] == key:
                    b.word = b.word[1:]
                    self.add_score(10)

                    # Pop the balloon if it's been typed.
                    if len(b.word) == 0:
                        self.balloons.remove(b)
                        self.add_score(100)

                    self.queue_draw_balloon(b)

                    break
        
        return False
    
    def update_balloon(self, b):
        self.queue_draw_balloon(b)
        
        b.x += b.vx
        b.y += b.vy 

        if b.x < 100 or b.x >= self.bounds.width - 100:
            b.vx = -b.vx

        if b.y < -100:
            self.balloons.remove(b)

        self.queue_draw_balloon(b)
    
    def tick(self):
        if self.finished:
            return

        self.bounds = self.area.get_allocation()
            
        for b in self.balloons:
            self.update_balloon(b)

        self.spawn_delay -= 1
        if self.spawn_delay <= 0:
            self.count_left -= 1

            if self.count_left <= 0:
                self.stage_idx += 1

                if self.stage_idx < len(BALLOON_STAGES):
                    self.stage = BALLOON_STAGES[self.stage_idx]
                    self.count_left = self.stage['count']

            else:
                word = random.choice(self.lesson['words'])

                x = random.randint(100, self.bounds.width - 100)
                y = self.bounds.height + 100

                vx = random.uniform(-2, 2)
                vy = -3 #random.uniform(-5, -3)

                b = Balloon(x, y, vx, vy, word)
                self.balloons.append(b)

                delay = self.stage['delay']
                self.spawn_delay = random.randint(delay-20, delay+20)

        if len(self.balloons) == 0 and self.stage_idx >= len(BALLOON_STAGES):
            self.finished = True
            self.queue_draw()
 
        return True

    def draw_results(self, gc):
        # Draw background.
        w = self.bounds.width - 400
        h = self.bounds.height - 200
        x = self.bounds.width/2 - w/2
        y = self.bounds.height/2 - h/2

        gc.foreground = self.area.get_colormap().alloc_color(50000,50000,50000)
        self.area.window.draw_rectangle(gc, True, x, y, w, h)
        gc.foreground = self.area.get_colormap().alloc_color(0,0,0)
        self.area.window.draw_rectangle(gc, False, x, y, w, h)

        # Draw text
        report = _('You finished the game!')
        report += '\n\n'
        report += _('Your score was %(score)d.') % { 'score': self.score }
        report += '\n\n'
        report += _('Press the ENTER key to continue.')
    
        gc.foreground = self.area.get_colormap().alloc_color(0,0,0)
        layout = self.area.create_pango_layout(report)
        layout.set_font_description(pango.FontDescription('Times 14'))    
        size = layout.get_size()
        tx = x+w/2-(size[0]/pango.SCALE)/2
        ty = y+h/2-(size[1]/pango.SCALE)/2
        self.area.window.draw_layout(gc, tx, ty, layout)

    def queue_draw_balloon(self, b):
        x1 = int(b.x - b.size/2)
        y1 = int(b.y - b.size/2)
        x2 = int(b.x + b.size/2)
        y2 = int(b.y + b.size/2)
        self.queue_draw_area(x1, y1, x2, y2)

    def draw_balloon(self, gc, b):
        x = int(b.x)
        y = int(b.y)
        
        # Draw the balloon.
        gc.foreground = self.area.get_colormap().alloc_color(65535,0,0)
        self.area.window.draw_arc(gc, True, x-b.size/2, y-b.size/2, b.size, b.size, 0, 360*64)
    
        # Draw the text.
        gc.foreground = self.area.get_colormap().alloc_color(0,0,0)
        layout = self.area.create_pango_layout(b.word)
        size = layout.get_size()
        tx = x-(size[0]/pango.SCALE)/2
        ty = y-(size[1]/pango.SCALE)/2
        self.area.window.draw_layout(gc, tx, ty, layout)
    
    def add_score(self, num):
        self.score += num
        self.queue_draw_score()

    def queue_draw_score(self):
        layout = self.area.create_pango_layout(_('SCORE: %d') % self.score)
        layout.set_font_description(pango.FontDescription('Times 14'))    
        size = layout.get_size()
        x = self.bounds.width-20-size[0]/pango.SCALE
        y = 20
        self.queue_draw_area(x, y, x+size[0], y+size[1])

    def draw_score(self, gc):
        layout = self.area.create_pango_layout(_('SCORE: %d') % self.score)
        layout.set_font_description(pango.FontDescription('Times 14'))    
        size = layout.get_size()
        x = self.bounds.width-20-size[0]/pango.SCALE
        y = 20
        self.area.window.draw_layout(gc, x, y, layout)

    def draw_instructions(self, gc):
        # Draw instructions.
        gc.foreground = self.area.get_colormap().alloc_color(0,0,0)

        layout = self.area.create_pango_layout(_('Type the words to pop the balloons!'))
        layout.set_font_description(pango.FontDescription('Times 14'))    
        size = layout.get_size()
        x = (self.bounds.width - size[0]/pango.SCALE)/2
        y = self.bounds.height-20 - size[1]/pango.SCALE 
        self.area.window.draw_layout(gc, x, y, layout)

    def draw(self):
        self.bounds = self.area.get_allocation()

        gc = self.area.window.new_gc()
        
        # Draw background.
        gc.foreground = self.area.get_colormap().alloc_color(65535,65535,65535)
        self.area.window.draw_rectangle(gc, True, 0, 0, self.bounds.width, self.bounds.height)

        # Draw the balloons.
        for b in self.balloons:
            self.draw_balloon(gc, b)

        if self.finished:
            self.draw_results(gc)

        else:
            self.draw_instructions(gc)

            self.draw_score(gc)

    def expose_cb(self, area, event):
        self.draw()
