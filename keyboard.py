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
#!/usr/bin/env python
# vi:sw=4 et 

import pygtk
pygtk.require('2.0')
import gtk
import rsvg
import os, glob, re
import pango
import json

# Tweaking variables.
HAND_YOFFSET = -15

# Unicode symbol for the paragraph key.
PARAGRAPH_CODE = u'\xb6'

# List of all key properties in the keyboard layout description.
#
# Keyboard Layouts use a property inheritance scheme similar to CSS (cascading style sheets):
# - Keys inherit properties from their groups, if not explicitly set.
# - Groups inherit properties from the layout.
# - The layout inherits properties from defaults values defined below.
#
# Therefore it is possible to set any property once in the Layout, and have
# it automatically filter down to all Keys, yet still be able to override it
# individually per key.
KEY_PROPS = [
    # Name of the layout.
    { 'name': 'layout-name',  'default': '' },

    # Source dimensions of the layout.  
    # This is the coordinate system that key sizes and coordinates are defined in.  
    # It can be any units, for example inches, millimeters, percentages, etc.  
    { 'name': 'layout-width',  'default': 100 },
    { 'name': 'layout-height', 'default': 100 },

    # Name of the group.
    { 'name': 'group-name', 'default': '' },

    # Position of group in layout coordinates.
    { 'name': 'group-x',  'default': 0 },
    { 'name': 'group-y',  'default': 0 },

    # Layout algorithm for the group.
    # Possibilities are: 'horizontal', 'vertical', 'custom'.
    { 'name': 'group-layout', 'default': 'custom' },

    # Position of key in layout coordinates.  Used by 'custom' layout algorithm.
    { 'name': 'key-x',  'default': 0 },
    { 'name': 'key-y',  'default': 0 },

    # Dimensions of a key in the layout coordinates.
    { 'name': 'key-width',  'default': 0 },
    { 'name': 'key-height', 'default': 0 },

    # Gap between keys. Used by 'horizontal' and 'verical' layout algorithms.
    { 'name': 'key-gap', 'default': 0 },

    # Keyboard scan code for this key.
    { 'name': 'key-scan', 'default': 0 },

    # Text label to be displayed on keys which do not generate keys.
    { 'name': 'key-label', 'default': '' },

    # Image filename showing a finger pressing this key.
    { 'name': 'key-hand-image', 'default': '' },

    # Which finger should be used to press the key.  
    # Options are [LR][TIMRP], so LM would mean the left middle finger.
    { 'name': 'key-finger', 'default': '' },

    # True if the key is currently pressed.
    { 'name': 'key-pressed', 'default': False },
]

# This is the OLPC XO-1 keyboard layout.
#
# The keyboard layout is described by the following data structure. The structure
# has three levels: Layout, Groups, and Keys.  A Layout contains a list of Groups,
# each of which contains a list of Keys.  Groups are intended to be a way to collect
# related keys (e.g. nearby each other on the keyboard with similar properties)
# together.
#
# Entirely new keyboard layouts can be created just by copying this structure and
# modifying the following values, without changing the code.
OLPC_LAYOUT = {
    'layout-name': "olpc",

    'layout-width': 775,
    'layout-height': 265,

    'group-layout': 'horizontal',

    'key-width': 45,
    'key-height': 45,
    'key-gap': 5,

    'groups': [
        {
            'group-name': "numbers",
            'group-x': 10,
            'group-y': 10,
            
            'keys': [
                {'key-scan':0x31,'key-finger':'LP','key-hand-image':'OLPC_Lhand_tilde.svg','key-width':35}, 
                {'key-scan':0x0a,'key-finger':'LP','key-hand-image':'OLPC_Lhand_1.svg'}, 
                {'key-scan':0x0b,'key-finger':'LR','key-hand-image':'OLPC_Lhand_2.svg'}, 
                {'key-scan':0x0c,'key-finger':'LM','key-hand-image':'OLPC_Lhand_3.svg'}, 
                {'key-scan':0x0d,'key-finger':'LI','key-hand-image':'OLPC_Lhand_4.svg'}, 
                {'key-scan':0x0e,'key-finger':'LI','key-hand-image':'OLPC_Lhand_5.svg'}, 
                {'key-scan':0x0f,'key-finger':'RI','key-hand-image':'OLPC_Rhand_6.svg'}, 
                {'key-scan':0x10,'key-finger':'RI','key-hand-image':'OLPC_Rhand_7.svg'}, 
                {'key-scan':0x11,'key-finger':'RM','key-hand-image':'OLPC_Rhand_8.svg'}, 
                {'key-scan':0x12,'key-finger':'RR','key-hand-image':'OLPC_Rhand_9.svg'}, 
                {'key-scan':0x13,'key-finger':'RP','key-hand-image':'OLPC_Rhand_0.svg'}, 
                {'key-scan':0x14,'key-finger':'RP','key-hand-image':'OLPC_Rhand_minus.svg'}, 
                {'key-scan':0x15,'key-finger':'RP','key-hand-image':'OLPC_Rhand_plus.svg','key-width':65},
                {'key-scan':0x16,'key-finger':'RP','key-label':"erase",'key-width':95}
            ]
        },
        {
            'group-name': "top",
            'group-x': 10,
            'group-y': 60,
            
            'keys': [
                {'key-scan':0x17,'key-finger':'LP','key-label':"tab"},
                {'key-scan':0x18,'key-finger':'LP','key-hand-image':'OLPC_Lhand_Q.svg'}, 
                {'key-scan':0x19,'key-finger':'LR','key-hand-image':'OLPC_Lhand_W.svg'}, 
                {'key-scan':0x1a,'key-finger':'LM','key-hand-image':'OLPC_Lhand_E.svg'}, 
                {'key-scan':0x1b,'key-finger':'LI','key-hand-image':'OLPC_Lhand_R.svg'}, 
                {'key-scan':0x1c,'key-finger':'LI','key-hand-image':'OLPC_Lhand_T.svg'}, 
                {'key-scan':0x1d,'key-finger':'RI','key-hand-image':'OLPC_Rhand_Y.svg'}, 
                {'key-scan':0x1e,'key-finger':'RI','key-hand-image':'OLPC_Rhand_U.svg'}, 
                {'key-scan':0x1f,'key-finger':'RM','key-hand-image':'OLPC_Rhand_I.svg'}, 
                {'key-scan':0x20,'key-finger':'RR','key-hand-image':'OLPC_Rhand_O.svg'}, 
                {'key-scan':0x21,'key-finger':'RP','key-hand-image':'OLPC_Rhand_P.svg'}, 
                {'key-scan':0x22,'key-finger':'RP','key-hand-image':'OLPC_Rhand_bracketL.svg'}, 
                {'key-scan':0x23,'key-finger':'RP','key-hand-image':'OLPC_Rhand_bracketR.svg','key-width':55},
                {'key-scan':0x24,'key-finger':'RP','key-hand-image':'OLPC_Rhand_ENTER.svg','key-label':"enter",'key-width':95,'key-height':95}
            ]
        },
        {
            'group-name': "home",
            'group-x': 10,
            'group-y': 110,
            
            'keys': [
                {'key-scan':0x25,'key-finger':'LP','key-label':"ctrl",'key-width':55},
                {'key-scan':0x26,'key-finger':'LP','key-hand-image':'OLPC_Lhand_A.svg'}, 
                {'key-scan':0x27,'key-finger':'LR','key-hand-image':'OLPC_Lhand_S.svg'}, 
                {'key-scan':0x28,'key-finger':'LM','key-hand-image':'OLPC_Lhand_D.svg'}, 
                {'key-scan':0x29,'key-finger':'LI','key-hand-image':'OLPC_Lhand_F.svg'}, 
                {'key-scan':0x2a,'key-finger':'LI','key-hand-image':'OLPC_Lhand_G.svg'}, 
                {'key-scan':0x2b,'key-finger':'RI','key-hand-image':'OLPC_Rhand_H.svg'},
                {'key-scan':0x2c,'key-finger':'RI','key-hand-image':'OLPC_Rhand_J.svg'}, 
                {'key-scan':0x2d,'key-finger':'RM','key-hand-image':'OLPC_Rhand_K.svg'}, 
                {'key-scan':0x2e,'key-finger':'RR','key-hand-image':'OLPC_Rhand_L.svg'}, 
                {'key-scan':0x2f,'key-finger':'RP','key-hand-image':'OLPC_Rhand_SEMICOLON.svg'}, 
                {'key-scan':0x30,'key-finger':'RP','key-hand-image':'OLPC_Rhand_APOSTROPHE.svg'}, 
                {'key-scan':0x33,'key-finger':'RP'}
            ]
        },
        {
            'group-name': "bottom",
            'group-x': 10,
            'group-y': 160,
            
            'keys': [
                {'key-scan':0x32,'key-finger':'LP','key-hand-image':'OLPC_Lhand_SHIFT.svg','key-label':"shift",'key-width':75},
                {'key-scan':0x34,'key-finger':'LP','key-hand-image':'OLPC_Lhand_Z.svg'}, 
                {'key-scan':0x35,'key-finger':'LR','key-hand-image':'OLPC_Lhand_X.svg'}, 
                {'key-scan':0x36,'key-finger':'LM','key-hand-image':'OLPC_Lhand_C.svg'}, 
                {'key-scan':0x37,'key-finger':'LI','key-hand-image':'OLPC_Lhand_V.svg'}, 
                {'key-scan':0x38,'key-finger':'LI','key-hand-image':'OLPC_Lhand_B.svg'}, 
                {'key-scan':0x39,'key-finger':'RI','key-hand-image':'OLPC_Rhand_N.svg'},
                {'key-scan':0x3a,'key-finger':'RI','key-hand-image':'OLPC_Rhand_M.svg'}, 
                {'key-scan':0x3b,'key-finger':'RM','key-hand-image':'OLPC_Rhand_COMMA.svg'}, 
                {'key-scan':0x3c,'key-finger':'RR','key-hand-image':'OLPC_Rhand_PERIOD.svg'}, 
                {'key-scan':0x3d,'key-finger':'RP','key-hand-image':'OLPC_Rhand_QUESTIONMARK.svg'},
                {'key-scan':0x3e,'key-finger':'RP','key-hand-image':'OLPC_Rhand_SHIFT.svg','key-label':"shift",'key-width':75},
                {'key-scan':0x6f,'key-finger':'RP','key-label':""}, # Up
                {'key-label':""}, # Language key
            ]
        },
        {
            'group-name': "space",
            'group-x': 10,
            'group-y': 210,
            
            'keys': [
                {'key-label':"fn",'key-width':35},
                {'key-label':"",'key-width':55}, # LHand
                {'key-scan':0x40,'key-label':"alt",'key-width':55}, # LAlt
                {'key-scan':0x41,'key-finger':'RT','key-hand-image':'OLPC_Rhand_SPACE.svg','key-width':325}, # Spacebar
                {'key-scan':0x6c,'key-label':"altgr",'key-width':55}, # AltGr
                {'key-label':"",'key-width':55}, # RHand
                {'key-scan':0x71,'key-label':""}, # Left 
                {'key-scan':0x74,'key-label':""}, # Down
                {'key-scan':0x72,'key-label':""}, # Right
            ]
        }
    ]
}

class KeyboardImages:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.images = {}

    def load_images(self):
        for filename in glob.iglob('images/OLPC_*.svg'):
            image = gtk.gdk.pixbuf_new_from_file_at_scale(filename, self.width, self.height, False)
            name = os.path.basename(filename)
            self.images[name] = image

class KeyboardData:
    def __init__(self): 
        # This array contains the current keyboard layout.
        self.keys = None
        self.key_scan_map = None
        
        self.letter_map = {} 
        
        # Access the current GTK keymap.
        self.keymap = gtk.gdk.keymap_get_default()

    def set_layout(self, layout): 
        self._build_key_list(layout)
        self._layout_keys()

    def _build_key_list(self, layout):
        """Builds a list of Keys objects from a layout description.  
           Also fills in derived and inherited key properties.  
           The layout description can be discarded afterwards."""
        self.keys = []
        self.key_scan_map = {}
        
        group_count = 0
        for g in layout['groups']:
            
            key_count = 0
            for k in g['keys']:
                
                # Create and fill out a unique property list for this key.
                key = k.copy()
                
                # Assign key and group index.
                key['key-index'] = key_count
                key['group-index'] = group_count
                
                # Inherit undefined properties from group, layout and
                # defaults, in that order.
                for p in KEY_PROPS:
                    pname = p['name']
                    if not key.has_key(pname):
                        if g.has_key(pname):
                            key[pname] = g[pname]
                        elif layout.has_key(pname):
                            key[pname] = layout[pname]
                        else:
                            key[pname] = p['default']
                
                # Add to internal list.
                self.keys.append(key)
                key_count += 1
           
                # Add to scan code mapping table.
                if key['key-scan']:
                    self.key_scan_map[key['key-scan']] = key

            group_count += 1

    def _layout_keys(self):
        """Assigns positions and sizes to the individual keys."""
        # Note- We know self.keys is sorted by group, and by index within the group.
        # The layout algorithms depend on this order.
        x, y = None, None
        cur_group = None
        for k in self.keys:
            # Reset the working coordinates with each new group.
            if k['group-index'] != cur_group:
                cur_group = k['group-index']
                x = k['group-x']
                y = k['group-y']
           
            # Apply the current layout.               
            if k['group-layout'] == 'horizontal':
                k['key-x'] = x
                k['key-y'] = y
                
                x += k['key-width']
                x += k['key-gap']
            
            elif k['group-layout'] == 'vertical':
                k['key-x'] = x
                k['key-y'] = y
                
                y += k['key-height']
                y += k['key-gap']
            
            else: # k['group-layout'] == 'custom' or unsupported
                pass

    def load_letter_map(self, filename):
        self.letter_map = json.loads(open(filename, 'r').read())

    def save_letter_map(self, filename):
        text = json.dumps(self.letter_map, ensure_ascii=False, sort_keys=True, indent=4)
        f = open(filename, 'w')
        f.write(text)
        f.close()

    def format_key_sig(self, scan, state, group):
        sig = 'scan%d' % scan
        if state & gtk.gdk.SHIFT_MASK:
            sig += ' shift'
        if state & gtk.gdk.MOD5_MASK:
            sig += ' altgr'
        if group != 0:
            sig += ' group%d' % group
        return sig

    KEY_SIG_RE = re.compile(r'scan(?P<scan>\d+) ?(?P<shift>shift)? ?(?P<altgr>altgr)?( group)?(?P<group>\d+)?')

    def parse_key_sig(self, sig):
        m = KeyboardData.KEY_SIG_RE.match(sig)

        state = 0
        if m.group('shift'):
            state |= gtk.gdk.SHIFT_MASK
        if m.group('altgr'):
            state |= gtk.gdk.MOD5_MASK

        scan = int(m.group('scan'))

        group = 0
        if m.group('group'):
            group = int(m.group('group'))
        
        return scan, state, group

    def find_key_by_label(self, label):
        for k in self.keys:
            if k['key-label'] == label:
                return k
        return None

    def get_key_state_group_for_letter(self, letter):
        """Returns a (key, modifier_state) which when pressed will generate letter."""
        # Special processing for the enter key.
        if letter == '\n' or letter == PARAGRAPH_CODE:
            return self.find_key_by_label('enter'), 0, 0

		# Look up the key in the letter map.
        for sig, l in self.letter_map.items():
            if l == letter:
                scan, state, group = self.parse_key_sig(sig)
                for k in self.keys:
                    if k['key-scan'] == scan:
                        return k, state, group

        return None, None, None

class KeyboardWidget(KeyboardData, gtk.DrawingArea):
    """A GTK widget which implements an interactive visual keyboard, with support
       for custom data driven layouts."""

    def __init__(self, image, root_window, poll_keys=False):
        KeyboardData.__init__(self)
        gtk.DrawingArea.__init__(self)
        
        self.image = image
        self.root_window = root_window
        
        # Match the image cache in dimensions.
        self.set_size_request(image.width, image.height)

        self.connect("expose-event", self._expose_cb)
        
        # Active language group and modifier state.
        # See http://www.pygtk.org/docs/pygtk/class-gdkkeymap.html for more
        # information about key group and state.
        self.active_group = 0
        self.active_state = 0

        self.keymap.connect("keys-changed", self._keys_changed_cb)
        
        self.hilite_letter = None
        
        self.draw_hands = False
        
        self.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#d0d0d0'))

        # Connect keyboard grabbing and releasing callbacks.        
        if poll_keys:
            self.connect('realize', self._realize_cb)
            self.connect('unrealize', self._unrealize_cb)

    def _realize_cb(self, widget):
        # Setup keyboard event snooping in the root window.
        self.root_window.add_events(gtk.gdk.KEY_PRESS_MASK | gtk.gdk.KEY_RELEASE_MASK)
        self.key_press_cb_id = self.root_window.connect('key-press-event', self.key_press_release_cb)
        self.key_release_cb_id = self.root_window.connect('key-release-event', self.key_press_release_cb)

    def _unrealize_cb(self, widget):
        self.root_window.disconnect(self.key_press_cb_id)
        self.root_window.disconnect(self.key_release_cb_id)

    def set_layout(self, layout):
        """Sets the keyboard's layout from  a layout description."""
        KeyboardData.set_layout(self, layout)

        # Scale the keyboard to match the images.
        width_scale = float(self.image.width) / self.keys[0]['layout-width']
        height_scale = float(self.image.height) / self.keys[0]['layout-height']
        for k in self.keys:
            k['key-x'] = int(k['key-x'] * width_scale)
            k['key-y'] = int(k['key-y'] * height_scale)
            k['key-width'] = int(k['key-width'] * width_scale)
            k['key-height'] = int(k['key-height'] * height_scale)

        self._make_all_key_images()

    def _make_key_images(self, key):
        key['key-images'] = {}
        for group in [0, 1]:
            for state in [0, gtk.gdk.SHIFT_MASK, gtk.gdk.MOD5_MASK, gtk.gdk.SHIFT_MASK|gtk.gdk.MOD5_MASK]:
                key['key-images'][(state, group)] = self.get_key_image(key, state, group)

    def _make_all_key_images(self):
        for key in self.keys:
            self._make_key_images(key)

    def _draw_key(self, k, draw, gc, for_pixmap, w=0, h=0):
        x1 = 0 
        y1 = 0
        x2 = w
        y2 = h

        # Outline rounded box.
        gc.foreground = self.get_colormap().alloc_color(int(0.4*65536),int(0.7*65536),int(0.4*65536))
        
        corner = 5
        points = [
            (x1 + corner, y1), 
            (x2 - corner, y1),
            (x2, y1 + corner),
            (x2, y2 - corner),
            (x2 - corner, y2),
            (x1 + corner, y2),
            (x1, y2 - corner),
            (x1, y1 + corner)
        ]
        draw.draw_polygon(gc, True, points)
        
        # Inner text.
        gc.foreground = self.get_colormap().alloc_color(int(1.0*65536),int(1.0*65536),int(1.0*65536))

        text = ''
        if k['key-label']:
            text = k['key-label']

        else:
            sig = self.format_key_sig(k['key-scan'], self.active_state, self.active_group)
            if self.letter_map.has_key(sig):
                text = self.letter_map[sig]
        
        try:
            layout = self.create_pango_layout(unicode(text))
            draw.draw_layout(gc, x1+8, y2-28, layout)
        except:
            pass

    def _expose_hands(self, gc):
        lhand_image = self.image.images['OLPC_Lhand_HOMEROW.svg']
        rhand_image = self.image.images['OLPC_Rhand_HOMEROW.svg']

        if self.hilite_letter:
            key, state, group = self.get_key_state_group_for_letter(self.hilite_letter) 
            if key:
                handle = self.image.images[key['key-hand-image']]
                finger = key['key-finger']

                # Assign the key image to the correct side.
                if finger and handle:
                    if finger[0] == 'L':
                        lhand_image = handle
                    else:
                        rhand_image = handle

                # Put the other hand on the SHIFT key if needed.
                if state & gtk.gdk.SHIFT_MASK:
                    if finger[0] == 'L':
                        rhand_image = self.image.images['OLPC_Rhand_SHIFT.svg']
                    else:
                        lhand_image = self.image.images['OLPC_Lhand_SHIFT.svg']

                # TODO: Do something about ALTGR.

        bounds = self.get_allocation()
        screen_x = int(bounds.width-self.image.width)/2
        screen_y = int(bounds.height-self.image.height)/2

        self.window.draw_pixbuf(gc, lhand_image, 0, 0, screen_x, screen_y + HAND_YOFFSET)
        self.window.draw_pixbuf(gc, rhand_image, 0, 0, screen_x, screen_y + HAND_YOFFSET)

    def _expose_cb(self, area, event):
        gc = self.window.new_gc()
        
        bounds = self.get_allocation()
        screen_x = int(bounds.width-self.image.width)/2
        screen_y = int(bounds.height-self.image.height)/2

        # Draw the keys.
        for k in self.keys:
            x1 = k['key-x'] + screen_x
            y1 = k['key-y'] + screen_y
            x2 = x1 + k['key-width']
            y2 = y1 + k['key-height']

            # Index cached key images by state and group.
            state = self.active_state & (gtk.gdk.SHIFT_MASK|gtk.gdk.MOD5_MASK)
            index = (state, self.active_group)
            image = k['key-images'].get(index)

            if image:
                self.window.draw_image(gc, image, 0, 0, x1, y1, x2-x1, y2-y1) 
        
        # Draw overlay images.
        if self.draw_hands:
            self._expose_hands(gc)
        
        return True

    def key_press_release_cb(self, widget, event):
        key = self.key_scan_map.get(event.hardware_keycode)
        if key:
            key['key-pressed'] = event.type == gtk.gdk.KEY_PRESS

        # Hack to get the current modifier state - which will not be represented by the event.
        state = gtk.gdk.device_get_core_pointer().get_state(self.window)[1]

        if self.active_group != event.group or self.active_state != state:
            self.active_group = event.group
            self.active_state = state

            self.queue_draw()

        if event.string:
            sig = self.format_key_sig(event.hardware_keycode, event.state, event.group)
            if not self.letter_map.has_key(sig):
                self.letter_map[sig] = event.string
                self._make_key_images(key)
                self.queue_draw()

        return False

    def _keys_changed_cb(self, keymap):
        self._make_key_images()

    def clear_hilite(self):
        self.hilite_letter = None
        self.queue_draw()

    def set_hilite_letter(self, letter):
        self.hilite_letter = letter
        self.queue_draw()

    def set_draw_hands(self, enable):
        self.draw_hands = enable
        self.queue_draw()

    def get_key_pixbuf(self, key, state=0, group=0, scale=1):
        w = int(key['key-width'] * scale)
        h = int(key['key-height'] * scale)
        
        old_state, old_group = self.active_state, self.active_group
        self.active_state, self.active_group = state, group
        
        pixmap = gtk.gdk.Pixmap(self.root_window.window, w, h)
        gc = pixmap.new_gc()
        
        gc.foreground = self.get_colormap().alloc_color('#d0d0d0')
        pixmap.draw_rectangle(gc, True, 0, 0, w, h)

        self._draw_key(key, pixmap, gc, True, w, h)
        
        pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
        pb.get_from_drawable(pixmap, self.root_window.window.get_colormap(), 0, 0, 0, 0,w, h)
        
        self.active_state, self.active_group = old_state, old_group

        return pb

    def get_key_image(self, key, state=0, group=0, scale=1):
        w = int(key['key-width'] * scale)
        h = int(key['key-height'] * scale)
        
        old_state, old_group = self.active_state, self.active_group
        self.active_state, self.active_group = state, group
        
        pixmap = gtk.gdk.Pixmap(self.root_window.window, w, h)
        gc = pixmap.new_gc()
        
        gc.foreground = self.get_colormap().alloc_color('#d0d0d0')
        pixmap.draw_rectangle(gc, True, 0, 0, w, h)

        self._draw_key(key, pixmap, gc, True, w, h)
        
        image = pixmap.get_image(0, 0, w, h)
        
        self.active_state, self.active_group = old_state, old_group

        return image
    
