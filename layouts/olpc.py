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


# This is the OLPC XO membrane keyboard layout.
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
