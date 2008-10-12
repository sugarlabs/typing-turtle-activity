#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk

# This is an example keyboard layout.
#
# The keyboard layout is described by the following data structure. The structure
# has three levels: Layout, Groups, and Keys.  A Layout contains a list of Groups,
# each of which contains a list of Keys.  Groups are intended to be a way to collect
# related keys (e.g. nearby each other on the keyboard with similar properties)
# together.
#
# Entirely new keyboard layouts can be created just by modifying the following values,
# without changing the code.
#
# Further, the property scheme allows for an expandable feature set with good support
# for backwards compatibility.
default_layout = {
    'layout-name': "default",

    'layout-width': 555,
    'layout-height': 300,

    'group-layout': 'horizontal',

    'key-width': 40,
    'key-height': 45,
    'key-gap': 5,

    'groups': [
	{
	    'group-name': "row0",
            'group-x': 10,
            'group-y': 7.5,
 
            'key-width': 100,
            'key-height': 30,
            'key-gap': 45,
    
	    'keys': [
		{'key-normal':"X",'key-shift':"X"}, 
		{'key-normal':"O",'key-shift':"O"}, 
		{'key-normal':"X",'key-shift':"X"}, 
		{'key-normal':"O",'key-shift':"O"}
	    ]
	},
	{
	    'group-name': "row1",
            'group-x': 10,
            'group-y': 50,

	    'keys': [
	     {'key-normal':"1",'key-shift':"!"}, 
	     {'key-normal':"2",'key-shift':"@"}, 
	     {'key-normal':"3",'key-shift':"#"}, 
	     {'key-normal':"4",'key-shift':"$"}, 
	     {'key-normal':"5",'key-shift':"%"}, 
	     {'key-normal':"6",'key-shift':"^"}, 
	     {'key-normal':"7",'key-shift':"&"}, 
	     {'key-normal':"8",'key-shift':"*"}, 
	     {'key-normal':"9",'key-shift':"("}, 
	     {'key-normal':"0",'key-shift':")"}, 
	     {'key-normal':"-",'key-shift':"_"}, 
	     {'key-normal':"=",'key-shift':"+"}
	    ]
	},
	{
	    'group-name': "row2",
            'group-x': 10,
            'group-y': 100,

	    'keys': [
	     {'key-normal':"q",'key-shift':"Q"}, 
	     {'key-normal':"w",'key-shift':"W"}, 
	     {'key-normal':"e",'key-shift':"E"}, 
	     {'key-normal':"r",'key-shift':"R"}, 
	     {'key-normal':"t",'key-shift':"T"}, 
	     {'key-normal':"y",'key-shift':"Y"}, 
	     {'key-normal':"u",'key-shift':"U"}, 
	     {'key-normal':"i",'key-shift':"I"}, 
	     {'key-normal':"o",'key-shift':"O"}, 
	     {'key-normal':"p",'key-shift':"P"}, 
	     {'key-normal':"[",'key-shift':"{"}, 
	     {'key-normal':"]",'key-shift':"}"}
	    ]
	},
	{
	    'group-name': "row3",
            'group-x': 10,
            'group-y': 150,

	    'keys': [
	     {'key-normal':"a",'key-shift':"A"}, 
	     {'key-normal':"s",'key-shift':"S"}, 
	     {'key-normal':"d",'key-shift':"D"}, 
	     {'key-normal':"f",'key-shift':"F"}, 
	     {'key-normal':"g",'key-shift':"G"}, 
	     {'key-normal':"h",'key-shift':"H"},
	     {'key-normal':"j",'key-shift':"J"}, 
	     {'key-normal':"k",'key-shift':"K"}, 
	     {'key-normal':"l",'key-shift':"L"}, 
	     {'key-normal':";",'key-shift':":"}, 
	     {'key-normal':"'",'key-shift':")"}, 
	     {'key-normal':"\"",'key-shift':"|"}
	    ]
	},
	{
	    'group-name': "row4",
            'group-x': 55,
            'group-y': 200,

	    'keys': [
	     {'key-normal':"z",'key-shift':"Z"}, 
	     {'key-normal':"x",'key-shift':"X"}, 
	     {'key-normal':"c",'key-shift':"C"}, 
	     {'key-normal':"v",'key-shift':"V"}, 
	     {'key-normal':"b",'key-shift':"B"}, 
	     {'key-normal':"n",'key-shift':"N"},
	     {'key-normal':"m",'key-shift':"M"}, 
	     {'key-normal':",",'key-shift':"<"}, 
	     {'key-normal':".",'key-shift':">"}, 
	     {'key-normal':"/",'key-shift':"?"}
	    ]
	},
	{
	    'group-name': "row5",
            'group-x': 55,
            'group-y': 250,

	    'keys': [
	     {'key-normal':"fn",'key-shift':"fn"}, 
	     {'key-normal':"HA",'key-shift':"HA"}, 
	     {'key-normal':"alt",'key-shift':"alt"}, 
	     {'key-normal':"space",'key-shift':"space", 'key-width':85}, 
	     {'key-normal':"alt gr",'key-shift':"alt gr"}, 
	     {'key-normal':"HA",'key-shift':"HA"}, 
	     {'key-normal':"<-",'key-shift':"<-"}, 
	     {'key-normal':"dn",'key-shift':"dn"}, 
	     {'key-normal':"->",'key-shift':"->"}
	    ]
	}
    ]
}

class Key:
    def __init__(self, props):
        self.props = props

        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

        self.screen_x = 0
        self.screen_y = 0
        self.screen_width = 0
        self.screen_height = 0

class Keyboard(gtk.DrawingArea):
    """A GTK widget which provides an interactive visual keyboard, with support
       for data driven custom layouts."""

    # List of all possible properties in the keyboard layout description.
    #
    # Keyboard Layouts use a property inheritance scheme similar to CSS (cascading style sheets):
    # - Keys inherit properties from their groups, if not explicitly set.
    # - Groups similarly inherit properties from the layout.
    # - The layout inherits properties from defaults values defined below.
    #
    # Therefore it is possible to set any property once in the Layout, and have
    # it automatically filter down to all Keys, yet still be able to override it
    # individually per key.
    key_props = [
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

        # Character generated by the key, when no modifier keys are pressed.
        { 'name': 'key-normal', 'default': '' },

        # Character generated by the key with shift pressed.
        { 'name': 'key-shift', 'default': '' },
    ]

    def __init__(self):
        gtk.DrawingArea.__init__(self)

        # This array contains the current keyboard layout.
        self.keys = []

        self.pangolayout = self.create_pango_layout("")

        self.set_events(gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.POINTER_MOTION_HINT_MASK )

        self.connect("expose-event", self.expose_cb)

    def _build_key_list(self, layout):
        """Builds a list of Keys objects from a layout description.  
           Also fills in derived and inherited key properties.  
           The layout description can be discarded afterwards."""
        self.keys = []

        group_count = 0
        for g in layout['groups']:
            
            key_count = 0
            for k in g['keys']:

                # Create and fill out a unique property list for this key.
                props = k.copy()

                # Assign key and group index.
                props['key-index'] = key_count
                props['group-index'] = group_count

                # Inherit undefined properties from group, layout and
                # defaults, in that order.
                for p in Keyboard.key_props:
                    pname = p['name']
                    if not props.has_key(pname):
                        if g.has_key(pname):
                            props[pname] = g[pname]
                        elif layout.has_key(pname):
                            props[pname] = layout[pname]
                        else:
                            props[pname] = p['default']

                # Add to internal list.
                self.keys.append(Key(props))
                key_count += 1

            group_count += 1
  
    def _layout_keys(self):
        """Assigns positions and sizes to the individual keys."""
        # Note- We know self.keys is sorted by group, and by index within the group.
        # The layout algorithms depend on this order.
        x, y = None, None
        cur_group = None
        for k in self.keys:
            # Reset the working coordinates with each new group.
            if k.props['group-index'] != cur_group:
                cur_group = k.props['group-index']
                x = k.props['group-x']
                y = k.props['group-y']
           
            # Apply the current layout.               
            if k.props['group-layout'] == 'horizontal':
                k.x = x
                k.y = y
                k.width = k.props['key-width']
                k.height = k.props['key-height']
                
                x += k.props['key-width']
                x += k.props['key-gap']

            elif k.props['group-layout'] == 'vertical':
                k.x = x
                k.y = y
                k.width = k.props['key-width']
                k.height = k.props['key-height']
                
                y += k.props['key-height']
                y += k.props['key-gap']

            elif k.props['group-layout'] == 'custom':
                k.x = x + k.props['key-x']
                k.y = y + k.props['key-y']
                k.width = k.props['key-width']
                k.height = k.props['key-height']

            else:
                k.x = 0
                k.y = 0
                k.width = 0
                k.height = 0

    def set_layout(self, layout):
        """Sets the keyboard's layout from  a layout description."""
        self._build_key_list(layout)
        self._layout_keys()

    def _update_screen_layout(self):
        """Applies the screen scaling factor for the layout given the current 
           allocation.
           TODO - Preserve the layout's aspect ratio in this calculation."""
        bounds = self.get_allocation()
 
        for k in self.keys:
            # This calculates a ratio from layout coordinates to the DrawingArea's
            # dimensions.  This ratio allows the layout coordinates to be *anything* -
            # inches, millimeters, percentage, whatever.  They just have to be
            # relative to layout-width and layout-height.
            ratio_x = 100 * bounds.width / k.props['layout-width']
            ratio_y = 100 * bounds.height / k.props['layout-height']

            # Make sure the final coordinates are integers, for the drawing routines.
            k.screen_x = int(k.x * ratio_x / 100)
            k.screen_y = int(k.y * ratio_y / 100)
            k.screen_width = int(k.width * ratio_x / 100)
            k.screen_height = int(k.height * ratio_y / 100)

    def expose_cb(self, area, event):
        # Update layout given screen size.
        self._update_screen_layout()

        # Draw the keys.
        style = self.get_style()
        gc = style.fg_gc[gtk.STATE_NORMAL]

        for k in self.keys:
            # Outline rectangle.
            gc.set_clip_rectangle(gtk.gdk.Rectangle(k.screen_x-1, k.screen_y-1, k.screen_width+2, k.screen_height+2))
            self.window.draw_rectangle(gc, False, k.screen_x, k.screen_y, k.screen_width, k.screen_height)

            # Inner text.
            gc.set_clip_rectangle(gtk.gdk.Rectangle(k.screen_x+1, k.screen_y+1, k.screen_width-1, k.screen_height-1))
            self.pangolayout.set_text(k.props['key-normal'])
            self.window.draw_layout(gc, k.screen_x+5, k.screen_y+5, self.pangolayout)

        return True

if __name__ == "__main__":
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_title("keyboard widget")
    window.connect("destroy", lambda w: gtk.main_quit())

    k = Keyboard()
    k.set_layout(default_layout)
    k.show()

    window.add(k)
    window.show()

    gtk.main()
