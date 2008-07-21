#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
from Key import *

class keyboard:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_default_size(800,350)
        window.set_title("keyboard widget")
        window.connect("destroy", lambda w: gtk.main_quit())
        self.area = gtk.DrawingArea()
        self.area.set_size_request(800, 350)
        self.pangolayout = self.area.create_pango_layout("")
        self.layout = gtk.Layout(None,None)
        self.layout.set_size(800,350)
        self.layout.put(self.area,10,10)
        window.add(self.layout)
        self.area.set_events(gtk.gdk.POINTER_MOTION_MASK |
                             gtk.gdk.POINTER_MOTION_HINT_MASK )
        bounds = window.get_allocation()
        self.area.connect("expose-event", self.area_expose_cb)
        self.area.show()
        self.layout.show()
        window.show()

    def area_expose_cb(self, area, event):
        self.style = self.area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        bounds = area.get_allocation()
        Xdim = bounds[2] - bounds[0]
        Ydim = bounds[3] - bounds[1]
        col = 10
        key_width = int(Xdim / 18)
        key_height = int(Ydim / 7)
        key_gap = int(key_width / 5)
        row_gap = int(key_height / 5)
        row_level_0 = 70
        row_level_1 = 100
        row_level_2 = row_level_1 + key_height + row_gap
        row_level_3 = row_level_2 + key_height + row_gap
        row_level_4 = row_level_3 + key_height + row_gap
        row_level_5 = row_level_4 + key_height + row_gap
        keys = []
        #Row 1
        row1 = [("1","!"),("2","@"),("3","#"),("4","$"),("5","%"),("6","^"),("7","&"),("8","*"),("9","("),("0",")"),("-","_"),("=","+")]
        row2 = [("q","Q"),("w","W"),("e","E"),("r","R"),("t","T"),("y","Y"),("u","U"),("i","I"),("o","O"),("p","P"),("[","{"),("]","}")]        
        row3 = [("a","A"),("s","S"),("d","D"),("f","F"),("g","G"),("h","H"),("j","J"),("k","K"),("l","L"),(";",":"),("'",")"),("\"","|")]
        row4 = [("z","Z"),("x","X"),("c","C"),("v","V"),("b","B"),("n","N"),("m","M"),(",","<"),(".",">"),("/","?")]
        myCol = col
        keys.append(Key(("`","~"),(myCol,row_level_1,(key_width-key_gap),key_height)))
        myCol += (key_width)
        for text in row1:
            keys.append(Key(text,(myCol,row_level_1,key_width,key_height)))
            myCol += (key_width + key_gap)
        keys.append(Key(("erase","erase"),(myCol,row_level_1,key_width*2,key_height)))
        
        #Row 2
        myCol = col
        keys.append(Key(("<-","<-"),(myCol,row_level_2,key_width,key_height)))
        myCol += (key_width + key_gap)
        for text in row2:
            keys.append(Key(text,(myCol,row_level_2,key_width,key_height)))
            myCol += (key_width + key_gap)
        
        #Row 3
        myCol = col
        keys.append(Key(("ctrl","ctrl"),(myCol,row_level_3,key_width+key_gap,key_height)))
        myCol += (key_width + key_gap + key_gap)
        for text in row3:
            keys.append(Key(text,(myCol,row_level_3,key_width,key_height)))
            myCol += (key_width + key_gap)

        #Row 4
        myCol = col
        keys.append(Key(("shift","shift"),(myCol,row_level_4,key_width*2,key_height)))
        myCol += (2*key_width + key_gap)
        for text in row4:
            keys.append(Key(text,(myCol,row_level_4,key_width,key_height)))
            myCol += (key_width + key_gap)

        for i in range(0,51):
            self.draw_key(keys[i])
        return True

    def draw_key(self, key):
        self.area.window.draw_rectangle(self.gc, False, key.specs[0], key.specs[1], key.specs[2], key.specs[3])
        self.pangolayout.set_text(key.text[0])
        self.area.window.draw_layout(self.gc, key.specs[0]+5, key.specs[1]+5, self.pangolayout)
        return



def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    keyboard()
    main()