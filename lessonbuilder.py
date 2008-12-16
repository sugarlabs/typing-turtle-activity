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

import os, sys, random, json
from gettext import gettext as _

import keyboard

CONGRATS = [
    _('Well done!'),
    _('Good job.'),
    _('Awesome!'),
    _('Way to go!'),
    _('Wonderful!'),
    _('Nice work.'),
    _('You did it!'),
]

FINGERS = {
    'LP': _('left pinky'),
    'LR': _('left ring'),
    'LM': _('left middle'),
    'LI': _('left index'),
    'LT': _('left thumb'),
    'RP': _('right pinky'),
    'RR': _('right ring'),
    'RM': _('right middle'),
    'RI': _('right index'),
    'RT': _('right thumb'),
}

def make_all_triples(keys):
    text = ''
    for k in new_keys:
        text += k + k + ' ' + k + ' '
    return text

def make_all_doubles(keys):
    text = ''
    for k in new_keys:
        text += k + k + ' '
    return text

def make_random_triples(keys, count):
    text = ''
    for y in xrange(0, count):
        k = random.choice(keys)
        text += k + k + ' ' + k + ' '
    return text

def make_jumbles(keys, count, gap):
    text = ''
    for y in range(0, count):
        text += random.choice(keys)
        if y % gap == gap-1:
            text += ' '
    return text

def make_all_pairs(keys):
    text = ''
    for k1 in keys:
        for k2 in keys:
            text += k1 + k2 + ' '
        for k2 in keys:
            text += k2 + k1 + ' '
    return text

def make_random_pairs(required_keys, keys, count):
    text = ''
    for y in xrange(0, count):
        k1 = random.choice(required_keys)
        k2 = random.choice(keys)
        text += random.choice([k1 + k2, k2 + k1]) + ' '
    return text

def make_all_joined_pairs(keys1, keys2):
    text = ''
    for k1 in keys1:
        for k2 in keys2:
            text += k1 + k2 + ' '
        for k2 in keys2:
            text += k2 + k1 + ' '
    return text

def make_random_words(words, count):
    text = ''
    for x in range(0, count):
        text += random.choice(words) + ' '
    return text

def load_wordlist(path):
    try:
        words = open(path, 'r').readlines()
        words = [s.strip() for s in words]
        return words
    except:
        return []

def filter_wordlist(words, all_keys, req_keys, minlen, maxlen, bad_words):

    good_words = []

    for word in words:
        if len(word) < minlen or len(word) > maxlen:
            continue

        good = True

        for c in word:
            if all_keys.find(c) == -1:
                good = False
                break

        any_req = False
        for c in req_keys:
            if word.find(c) >= 0:
                any_req = True
                break
        if not any_req:
            good = False

        for bad in bad_words:
            if word == bad:
                good = False
                break

        if good:
            good_words.append(word)

    return good_words

def add_step(lesson, instructions, text):
    step = {}
    step['instructions'] = instructions
    step['text'] = text.strip() + '\n'
    lesson['steps'].append(step)

def build_lesson(
    name, description, 
    level, required_level, 
    new_keys, base_keys, 
    wordlist=None, badwordlist=None):

    words = load_wordlist(wordlist)
    bad_words = load_wordlist(badwordlist)

    kb = keyboard.Keyboard(None)
    kb.set_layout(keyboard.DEFAULT_LAYOUT)

    all_keys = new_keys + base_keys

    lesson = {}
    lesson['name'] = name
    lesson['description'] = description
    lesson['level'] = level
    lesson['requiredlevel'] = required_level
    lesson['steps'] = []

    keynames = ''
    for k in new_keys[:-2]:
        keynames += k + ', '
    keynames += new_keys[-2] + ' and ' + new_keys[-1]

    add_step(lesson,
        _('Welcome to the %(name)s lesson!\n\nIn this lesson, you will learn the %(keynames)s keys.  Press the Enter key when you are ready to begin!') \
            % { 'name': name, 'keynames': keynames },
        '\n')

    for key in new_keys:
        k = kb.find_key_by_letter(key)
        add_step(lesson,
            _('Press the %(name)s key using your %(finger)s finger.') \
                % { 'name': key, 'finger': FINGERS[k.props['key-finger']]},
            key)

    # Key patterns - useful or not?
    #add_step(lesson,
    #    _('Time to practice some simple key patterns.'),
    #    make_all_triples(new_keys) * 4)
    
    add_step(lesson,
        _('Good job!  Now, practice typing the keys you just learned.'),
        make_random_triples(new_keys, count=20))
    
    # Key patterns - useful or not?
    #add_step(lesson,
    #    _('Practice typing the keys you just learned.'),
    #    make_all_pairs(new_keys))
    
    add_step(lesson,
        _('Well done! Now let\'s put the keys together in pairs.\n\nBe careful to use the correct finger to press each key.  Look at the keyboard below if you need help remembering.'),
        make_random_pairs(new_keys, new_keys, count=50))
    
    add_step(lesson,
        _('You made it!  Now we are going to practice word jumbles.  You can speed up a little, but be careful to get all the keys right!'),
        make_jumbles(new_keys, count=100, gap=5))
    
    if base_keys != '':
        # Key patterns - useful or not?
        #add_step(lesson,
        #    _('Wonderful!  Now we are going to bring in the keys you already know. We\'ll start with pairs.\n\nPay attention to your posture, and always be sure to use the correct finger!'),
        #    make_all_joined_pairs(new_keys, all_keys))
    
        add_step(lesson,
            _('Wonderful!  Now we will add the keys you already know.  Let\'s start with pairs.\n\nPay attention to your posture, and always be sure to use the correct finger.'),
            make_random_pairs(new_keys, all_keys, count=200))
    
        add_step(lesson,
            _('Great job.  Now practice these jumbles, using all the keys you know.'),
            make_jumbles(all_keys, count=300, gap=5))

    if wordlist:
        good_words = filter_wordlist(words=words, 
            all_keys=all_keys, req_keys=new_keys, 
            minlen=2, maxlen=10, 
            bad_words=bad_words)

        add_step(lesson,
            _('You\'re almost finished!  It\'s time to learn to type real words, using the keys you have just learned.'),
            make_random_words(good_words, count=300))
    
    return lesson

def build_intro_lesson():
    lesson = {}
    lesson['name'] = _('Welcome to Typing Turtle!') 
    lesson['description'] = _('Click here to begin.') 
    lesson['level'] = 0
    lesson['requiredlevel'] = 0
    lesson['steps'] = []

    text = ''
    text += _('Hi there, welcome to Typing Turtle!  My name is Max the Turtle, ')
    text += _('and I\'m going to teach you how to type.\n\n')
    text += _('First, I will tell you the secret of fast typing.  Are you ready?\n\n')
    text += _('The secret is: Always use the correct finger to press each key!\n\n')
    text += _('Simple, right?  Now all you need to do is practice.')
    #show you how to use the activity.  The box you are ')
    text += _('reading right now is where the instructions will appear.  The ')
    text += _('picture of the keyboard below shows what your hands should be ')
    text += _('doing.  And the dials to the right, they show how quickly and ')
    text += _('accurately you are typing!\n\n')
    text += _('When you see a big picture of a key like the one below, that ')
    text += _('means you are supposed to press that key on the keyboard! ')
    text += _('Make sure you use the correct finger to type each key!')

    return lesson

def usage():
    print """
lessonbuilder.py v1.0 by Wade Brainerd <wadetb@gmail.com>
Generates automatic lesson content for Typing Turtle.

--help              Display this message.
--keys='...'        Keys to teach.  Required.
--base-keys='...'   Keys already taught prior to this lesson.
--name='...'        Lesson name.
--desc='...'        Lesson description.
--level=N           Level granted by the lesson.
--required-level=N  Level requirement for the lesson.
--wordlist=file     List of words to use, one per line.
--badwordlist=file  List of words *not* to use, one per line.
--output=file       Output file.
"""

if __name__ == "__main__":
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'x', 
            ['help', 'name=', 'desc=', 'level=', 'required-level=', 
             'keys=', 'base-keys=', 'wordlist=', 'badwordlist=',
             'output='])
    except:
        usage()
        sys.exit()

    name = 'Generated'
    desc = 'Default description'
    level = 0
    required_level = 0
    new_keys = None
    base_keys = ''
    wordlist = None
    badwordlist = None
    output = None

    for opt, arg in opts:
        if opt == '--help':
            usage()
            sys.exit()
        elif opt == '--name':
            name = arg
        elif opt == '--desc':
            desc = arg
        elif opt == '--level':
            level = int(arg)
        elif opt == '--required-level':
            required_level = int(arg)
        elif opt == '--keys':
            new_keys = arg
        elif opt == '--base-keys':
            base_keys = arg
        elif opt == '--wordlist':
            wordlist = arg
        elif opt == '--badwordlist':
            badwordlist = arg
        elif opt == '--output':
            output = arg

    if not new_keys:
        usage()
        sys.exit()

    lesson = build_lesson(
        name=name, description=desc, 
        level=level, required_level=required_level,
        new_keys=new_keys, base_keys=base_keys, 
        wordlist=wordlist, badwordlist=badwordlist)

    if output:
        import json
        text = json.write(lesson)
        open(output, 'w').write(text)
    else:
        import pprint
        pprint.pprint(lesson)

