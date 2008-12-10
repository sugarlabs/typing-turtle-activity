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

def make_triple(keys):
    text = ''
    for k in new_keys:
        text += k + k + ' ' + k + ' '
    return text

def make_double(keys):
    text = ''
    for k in new_keys:
        text += k + k + ' '
    return text

def make_random_triple(keys, count):
    text = ''
    for y in xrange(0, count * len(keys)):
        k = random.choice(keys)
        text += k + k + ' ' + k + ' '
    return text

def make_random(keys, count, gap):
    text = ''
    for y in range(0, count * len(keys)):
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

def make_random_pair(keys, count):
    text = ''
    for y in xrange(0, count * len(keys)):
        k1 = random.choice(keys)
        k2 = random.choice(keys)
        text += k1 + k2 + ' '
    return text

def make_all_joined_pairs(keys1, keys2):
    text = ''
    for k1 in keys1:
        for k2 in keys2:
            text += k1 + k2 + ' '
        for k2 in keys2:
            text += k2 + k1 + ' '
    return text

def make_words(wordlist, count):
    text = ''
    for x in range(0, count):
        text += random.choice(wordlist) + ' '
    return text

def filter_wordlist(path, all_keys, req_keys, minlen, maxlen, badwordlist):
    wordlist = open(path, 'r').readlines()
    wordlist = [s.strip() for s in wordlist]

    if badwordlist:
        bad_words = open(badwordlist, 'r').readlines()
        bad_words = [s.strip() for s in badwordlist]
    else:
        bad_words = []

    good_words = []

    for word in wordlist:
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
    step['text'] = text
    lesson['steps'].append(step)

def build_lesson(
    name, description, 
    level, required_level, 
    new_keys, base_keys, 
    wordlist=None, badwordlist=None):

    all_keys = new_keys + base_keys

    lesson = {}
    lesson['name'] = name
    lesson['description'] = description
    lesson['level'] = level
    lesson['requiredlevel'] = required_level
    lesson['steps'] = []

    for key in new_keys:
        add_step(lesson,
            _('Press the %(name)s key with your %(finger)s.') \
                % { 'name': key, 'finger': 'finger' },
            key)
    
    add_step(lesson,
        _('Practice typing the keys you just learned.'),
        make_triple(new_keys) * 4)
    
    add_step(lesson,
        _('Practice typing the keys you just learned.'),
        make_random_triple(new_keys, count=5))
    
    add_step(lesson,
        _('Practice typing the keys you just learned.'),
        make_all_pairs(new_keys))
    
    add_step(lesson,
        _('Practice typing the keys you just learned.'),
        make_random_pair(new_keys, count=10))
    
    add_step(lesson,
        _('Practice typing the keys you just learned.'),
        make_random(new_keys, count=40, gap=5))
    
    if base_keys != '':
        add_step(lesson,
            _('Practice typing the keys you just learned.'),
            make_all_joined_pairs(new_keys, all_keys))
    
        add_step(lesson,
            _('Practice typing the keys you just learned.'),
            make_random_pair(all_keys, count=20))
    
        add_step(lesson,
            _('Practice typing the keys you just learned.'),
            make_random(all_keys, count=50, gap=5))

    if wordlist:
        good_words = filter_wordlist(path=wordlist, 
            all_keys=all_keys, req_keys=new_keys, 
            minlen=2, maxlen=10, 
            badwordlist=badwordlist)

        add_step(lesson,
            _('Practice typing these words.'),
            make_words(good_words, count=500))
    
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

    name = 'Generated lesson'
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
        name='Created Lesson', description='Lesson Description', 
        level=0, required_level=0,
        new_keys=new_keys, base_keys=base_keys, 
        wordlist=wordlist, badwordlist=badwordlist)

    if output:
        import json
        text = json.write(lesson)
        open(output, 'w').write(text)
    else:
        import pprint
        pprint.pprint(lesson)

