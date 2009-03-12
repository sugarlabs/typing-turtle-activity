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

import sys
import keyboard

import gtk

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.set_title("keyboard widget")
window.connect("destroy", lambda w: gtk.main_quit())
window.show_all()
window.realize()

image = keyboard.KeyboardImages(800,400)
image.load_images()

k = keyboard.KeyboardWidget(image, window, poll_keys=True)
try:
    k.load_letter_map(sys.argv[1])
except:
    pass
k.set_layout(keyboard.OLPC_LAYOUT)

savebtn = gtk.Button()
savebtn.add(gtk.Label('Save Keys'))
savebtn.connect('clicked', lambda w: k.save_letter_map(sys.argv[1]))

quitbtn = gtk.Button()
quitbtn.add(gtk.Label('Quit'))
quitbtn.connect('clicked', lambda w: gtk.main_quit())

hbox = gtk.HBox()
hbox.pack_start(savebtn)
hbox.pack_start(quitbtn)

vbox = gtk.VBox()
vbox.pack_start(k)
vbox.pack_start(hbox)

window.add(vbox)
window.show_all()

gtk.main()

