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

import random, datetime
from gettext import gettext as _

import gobject, pygtk, gtk, pango, time, math

import medalscreen

KITE_SIZE = 300

class Rope:
    def __init__(self, start, end, num_segs):
        self.start = start
        self.end = end
        
        self.points = []
        for i in xrange(num_segs+1):
            t = float(i) / float(num_segs)
            p = (start[0] + (end[0] - start[0])*t, start[1] + (end[1] - start[1])*t)
            self.points.append(p)
        
        self.seg_length = math.sqrt((end[0]-start[0]) ** 2 + (end[1]-start[1]) ** 2) / float(num_segs)

        self.int_points = []
        
    def apply_gravity(self, force):
        for j in xrange(len(self.points)):
            p = self.points[j]
            self.points[j] = (p[0], p[1] + force)
        
    def tick(self, num_iterations):
        for i in xrange(num_iterations):
            for j in xrange(len(self.points)-1):
                p0 = self.points[j]
                p1 = self.points[j+1]
                
                l = math.sqrt((p1[0]-p0[0]) ** 2 + (p1[1]-p0[1]) ** 2)

                if l > 0:
                    d = (l - self.seg_length) * 0.5 / l

                    v = ((p1[0]-p0[0])*d, (p1[1]-p0[1])*d)
                    
                    
                    p0n = (p0[0] + v[0], p0[1] + v[1])
                    p1n = (p1[0] - v[0], p1[1] - v[1])
                    
                    self.points[j] = p0n
                    self.points[j+1] = p1n
            
            self.points[0] = (self.start[0], self.start[1])
            self.points[-1] = (self.end[0], self.end[1])

        self.int_points = [(int(p[0]), int(p[1])) for p in self.points]

    def queue_draw(self, area):
        minx = 1.0e32
        miny = 1.0e32
        maxx = -1.0e32
        maxy = -1.0e32
        for p in self.points:
            if p[0] < minx: minx = p[0]
            if p[0] > maxx: maxx = p[0]
            if p[1] < miny: miny = p[1]
            if p[1] > maxy: maxy = p[1]
        area.queue_draw_area(int(minx), int(miny), int(maxx-minx)+1, int(maxy-miny)+1)
        
    def draw(self, area, gc):
        #for i in xrange(len(self.points)-1):
        #    p0 = self.points[i]
        #    p1 = self.points[i+1]
        #    area.window.draw_line(gc, int(p0[0]), int(p0[1]), int(p1[0]), int(p1[1]))

        #if self.int_points:
        #    area.window.draw_lines(gc, self.int_points)

        # For some insane reason, filling a polygon is infinitely faster than
        # drawing lines using either of the above methods.
        # Plus this way we get a thicker line.
        r = [(p[0] - 1, p[1] - 1) for p in self.int_points]
        r.reverse()
        area.window.draw_polygon(gc, True, self.int_points + r)

class KiteGame(gtk.VBox):
    def __init__(self, lesson, activity):
        gtk.VBox.__init__(self)
        
        self.lesson = lesson
        self.activity = activity
        
        # Build title bar.
        title = gtk.Label()
        title.set_markup("<span size='x-large'><b>" + lesson['name'] + "</b></span>")
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
        self.area.connect("expose-event", self.expose_cb)

        # Connect keyboard grabbing and releasing callbacks.        
        self.area.connect('realize', self.realize_cb)
        self.area.connect('unrealize', self.unrealize_cb)

        self.pack_start(hbox, False, False, 10)
        self.pack_start(self.area, True, True)
        
        self.show_all()
        
        # Initialize the game data.
        self.text = ''
        for i in range(0, self.lesson['length']):
            if i > 0: self.text += ' '
            self.text += random.choice(self.lesson['words'])

        self.key_hist = []

        self.kitex = None 
        self.kitey = None 

        self.wpm = 0

        self.score = 0

        self.medal = None
        self.finished = False

        self.rope = None

        self.draw_queued = False
        
        # Start the animation loop running.        
        self.update_timer = gobject.timeout_add(20, self.tick, priority=gobject.PRIORITY_HIGH_IDLE+30)
    
    def realize_cb(self, widget):
        self.activity.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.key_press_cb_id = self.activity.connect('key-press-event', self.key_cb)
        
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

                # Show the new medal if there was one.
                if self.medal:
                    self.activity.push_screen(medalscreen.MedalScreen(self.medal, self.activity))

        else:
            # Automatically consume spaces when the next correct letter is typed.
            correct = False
            if self.text[0] == ' ' and len(self.text) > 1 and key == unicode(self.text[1]):
                self.text = self.text[1:]
                correct = True
            elif key == unicode(self.text[0]):
                correct = True

            if correct:
                self.text = self.text[1:]
                self.queue_draw_text()
                self.add_score(10)
                if len(self.text) == 0:
                    self.finish_game()

            else:
                self.add_score(-10)

            self.key_hist.insert(0, (time.time(), correct))
            self.key_hist = self.key_hist[:10]

        return False
    
    def tick(self):
        if self.finished:
            return

        if not self.draw_queued:
            self.queue_draw_kite()

        # Calculate average WPM using the key press history.
        correct_keys = 0
        total_keys = 0 

        t = time.time()
        avg_key_time = 0
        for h in self.key_hist[2:]:
            if time.time() - h[0] > 10.0:
                break
            if h[1]: 
                correct_keys += 1
                avg_key_time += t - h[0]
                t = h[0]
            total_keys += 1

        if correct_keys > 0:
            avg_key_time = avg_key_time / float(correct_keys)
            
        if avg_key_time > 0:
            wpm = 12.0 / avg_key_time 
        else:
            wpm = 0

        wpm = self.wpm * 0.9 + wpm * 0.1
        if int(wpm) != int(self.wpm):
            self.queue_draw_score()
        self.wpm = wpm

        progress = float(total_keys) / 20.0

        # Height is a factor of words per minute.
        oldkitey = self.kitey
        newkitey = (self.bounds.height - KITE_SIZE/2) * (1.0 - (progress * (wpm / 30.0)))
        if self.kitey is None:
            self.kitey = newkitey
        else:
            self.kitey += (newkitey - self.kitey) * 0.1
            self.kitey += (self.kitey - oldkitey) * 0.5

        # Movement across the screen is a factor of accuracy with a tiny bit of WPM.
        if total_keys > 0:
            acc = progress * float(correct_keys) / total_keys
        else:
            acc = 0

        oldkitex = self.kitex
        newkitex = self.bounds.width*0.5 + acc*self.bounds.width*0.3 + wpm*0.5
        if self.kitex is None:
            self.kitex = newkitex
        else:
            self.kitex += (newkitex - self.kitex) * 0.05
            self.kitex += (self.kitex - oldkitex) * 0.1

        # Update the rope.
        if self.rope is None:
            self.rope = Rope((self.kitex, self.kitey), (self.bounds.width*0.35, self.bounds.height*0.8), 5)
        self.rope.start = (self.kitex, self.kitey)
        self.rope.apply_gravity(5.0)
        self.rope.tick(1)
        
        # Draw new kite.
        if not self.draw_queued:
            self.queue_draw_kite()
            self.draw_queued = True

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
        gc.foreground = self.area.get_colormap().alloc_color(0,0,0)

        title = _('You finished!') + '\n'
        layout = self.area.create_pango_layout(title)
        layout.set_font_description(pango.FontDescription('Serif Bold 16'))    
        size = layout.get_size()
        tx = x+w/2-(size[0]/pango.SCALE)/2
        ty = y + 100
        self.area.window.draw_layout(gc, tx, ty, layout)

        report = ''
        report += _('Your score was %(score)d.') % { 'score': self.score } + '\n'
        if self.medal:
            report += _('You earned a %(type)s medal!') % self.medal + '\n'
        report += '\n'
        report += _('Press the ENTER key to continue.')
    
        layout = self.area.create_pango_layout(report)
        layout.set_font_description(pango.FontDescription('Times 12'))    
        size = layout.get_size()
        tx = x+w/2-(size[0]/pango.SCALE)/2
        ty = y + 200
        self.area.window.draw_layout(gc, tx, ty, layout)

    def finish_game(self):
        self.finished = True

        # Add to the lesson history.
        report = { 
            'lesson': self.lesson['name'],
            'score': self.score,
        }
        self.activity.add_history(report)

        # Show the medal screen, if one should be given.
        got_medal = None
        
        medals = self.lesson['medals']
        for medal in medals:
            if self.score >= medal['score']:
                got_medal = medal['name']
        
        if got_medal:
            # Award the medal.
            medal = {
                'lesson': self.lesson['name'],
                'type': got_medal,
                'date': datetime.date.today().strftime('%B %d, %Y'),
                'nick': self.activity.owner.props.nick,
                'score': self.score
            }
            self.medal = medal

            # Compare this medal with any existing medals for this lesson.
            # Only record the best one.
            add_medal = True
            if self.activity.data['medals'].has_key(self.lesson['name']):
                old_medal = self.activity.data['medals'][self.lesson['name']]

                order = ' '.join([m['name'] for m in medals])
                add_idx = order.index(medal['type'])
                old_idx = order.index(old_medal['type']) 

                if add_idx < old_idx:
                    add_medal = False
                elif add_idx == old_idx:
                    if medal['score'] < old_medal['score']:
                        add_medal = False
            
            if add_medal:
                self.activity.data['motd'] = 'newmedal'
                self.activity.data['medals'][self.lesson['name']] = medal
                
                # Refresh the main screen given the new medal.
                self.activity.mainscreen.show_lesson(self.activity.mainscreen.lesson_index)

        self.queue_draw()

    def queue_draw_kite(self):
        if self.kitey is None:
            return

        x = int(self.kitex)
        y = int(self.kitey) - KITE_SIZE/2
        if y < 0:
            y = 0

        self.area.queue_draw_area(
            x-KITE_SIZE/2, y,
            KITE_SIZE, KITE_SIZE)

        if self.rope:
            self.rope.queue_draw(self.area)
        
    def draw_kite(self, gc):
        if self.kitey is None or self.kitex is None:
            return

        color = (65535, 0 ,0)
 
        p0 = (int(self.kitex), int(self.kitey-KITE_SIZE*0.3))
        p1 = (int(self.kitex+KITE_SIZE*0.3), int(self.kitey))
        p2 = (int(self.kitex), int(self.kitey+KITE_SIZE*0.5))
        p3 = (int(self.kitex-KITE_SIZE*0.3), int(self.kitey))
        pts = [ p0, p1, p2, p3 ]

        gc.foreground = self.area.get_colormap().alloc_color(color[0],color[1],color[2])
        self.area.window.draw_polygon(gc, True, pts)
        
        if self.rope:
            gc.foreground = self.area.get_colormap().alloc_color(0,0,0)
            self.rope.draw(self.area, gc)
    
    def add_score(self, num):
        self.score += num
        self.queue_draw_score()

    def get_score_text(self):
        return _("SCORE: %d") % self.score + "\n" + \
               _("WPM: %d") % int(self.wpm)

    def queue_draw_score(self):
        layout = self.area.create_pango_layout('')
        layout.set_markup("<span size='large'>" + self.get_score_text() + "</span>")
        size = layout.get_size()
        x = self.bounds.width-20-size[0]/pango.SCALE
        y = 20
        self.area.queue_draw_area(x, y, size[0], size[1])

    def draw_score(self, gc):
        layout = self.area.create_pango_layout('')
        layout.set_markup("<span size='large'>" + self.get_score_text() + "</span>")
        size = layout.get_size()
        x = self.bounds.width-20-size[0]/pango.SCALE
        y = 20
        self.area.window.draw_layout(gc, x, y, layout)

    def draw_instructions(self, gc):
        gc.foreground = self.area.get_colormap().alloc_color(0,0,0)

        layout = self.area.create_pango_layout('')
        layout.set_markup("<span size='x-large' weight='bold'>" + _('Type the words smoothly to fly the kite!') + "</span>")
        size = layout.get_size()
        x = (self.bounds.width - size[0]/pango.SCALE)/2
        y = 40 - size[1]/pango.SCALE 
        self.area.window.draw_layout(gc, x, y, layout)

    def queue_draw_text(self):
        layout = self.area.create_pango_layout('')
        layout.set_markup("<span size='x-large'>" + self.text[:50] + "</span>")
        size = layout.get_size()
        x = 0
        y = int(self.bounds.height*0.25 - size[1]/pango.SCALE) 
        self.area.queue_draw_area(
            x, y, self.bounds.width, self.bounds.height)

    def draw_text(self, gc):
        layout = self.area.create_pango_layout('')
        layout.set_markup("<span size='x-large'>" + self.text[:50] + "</span>")
        size = layout.get_size()
        x = int(self.bounds.width*0.25)
        y = int(self.bounds.height*0.25 - size[1]/pango.SCALE) 

        gc.foreground = self.area.get_colormap().alloc_color(65535,65535,65535)
        self.area.window.draw_rectangle(gc, True, 0, y, self.bounds.width, size[1]/pango.SCALE+10)

        gc.foreground = self.area.get_colormap().alloc_color(0,0,0)
        self.area.window.draw_layout(gc, x, y+5, layout)

        self.area.window.draw_line(gc, 0, y, self.bounds.width, y)
        self.area.window.draw_line(gc, 0, y+size[1]/pango.SCALE+10, self.bounds.width, y+size[1]/pango.SCALE+10)

    def draw(self):
        self.bounds = self.area.get_allocation()
        self.draw_queued = False

        gc = self.area.window.new_gc()
        
        gc.foreground = self.area.get_colormap().alloc_color(60000,60000,65535)
        self.area.window.draw_rectangle(gc, True, 0, 0, self.bounds.width, self.bounds.height)

        if self.finished:
            self.draw_results(gc)

        else:
            self.draw_instructions(gc)
            self.draw_kite(gc)
            self.draw_text(gc)
            self.draw_score(gc)

    def expose_cb(self, area, event):
        self.draw()

