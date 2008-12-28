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

import os, sys, random, json, locale, re
from gettext import gettext as _

# Set up remote debugging.
#import dbgp.client
#dbgp.client.brkOnExcept(host='192.168.1.104', port=12900)

# Import keyboard data.
import keyboard

# Set up localization.
locale.setlocale(locale.LC_ALL, '')

CONGRATS = [
    _('Well done!'),
    _('Good job.'),
    _('Awesome!'),
    _('Way to go!'),
    _('Wonderful!'),
    _('Nice work.'),
    _('You did it!'),
]

HINTS = [
    _('Be careful to use the correct finger to press each key.  Look at the keyboard below if you need help remembering.'),
    _('Try to type at the same speed, all the time.  As you get more comfortable you can increase the speed a little.')
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
    return text.strip()

def make_all_doubles(keys):
    text = ''
    for k in new_keys:
        text += k + k + ' '
    return text.strip()

def make_random_triples(keys, count):
    text = ''
    for y in xrange(0, count):
        k = random.choice(keys)
        text += k + k + ' ' + k + ' '
    return text.strip()

def make_random_doubles(keys, count):
    text = ''
    for y in xrange(0, count):
        k = random.choice(keys)
        text += k + k + ' '
    return text.strip()

def make_jumbles(keys, count, gap):
    text = ''
    for y in range(0, count):
        text += random.choice(keys)
        if y % gap == gap-1:
            text += ' '
    return text.strip()

def make_all_pairs(keys):
    text = ''
    for k1 in keys:
        for k2 in keys:
            text += k1 + k2 + ' '
        for k2 in keys:
            text += k2 + k1 + ' '
    return text.strip()

def make_random_pairs(required_keys, keys, count):
    text = ''
    for y in xrange(0, count):
        k1 = random.choice(required_keys)
        k2 = random.choice(keys)
        text += random.choice([k1 + k2, k2 + k1]) + ' '
    return text.strip()

def make_all_joined_pairs(keys1, keys2):
    text = ''
    for k1 in keys1:
        for k2 in keys2:
            text += k1 + k2 + ' '
        for k2 in keys2:
            text += k2 + k1 + ' '
    return text.strip()

RE_NONALPHA = re.compile('\W+', re.UNICODE)

def load_wordlist(path):
    try:
        text = open(path, 'r').read()
        
        # Split words by non-alpha characters.  This extracts all actual words,
        # minus punctuation.  Note- Could get messed up by hyphenation, leading
        # to fragments in the word list.
        words = RE_NONALPHA.split(text)
        
        return words
    
    except:
        return []

def get_pairs_from_wordlist(words):
    print 'Calculating common pairs...'

    # Construct char_map, a map for each character c0 in words, giving the frequency of each other
    # character c1 in words following c0.
    char_map = {}
    for word in words:
        for i in xrange(0, len(word)-1):
            c0 = word[i]
            c1 = word[i+1]
            
            c0_map = char_map.setdefault(c0, {})
            c1_value = c0_map.setdefault(c1, 0)
            c0_map[c1] = c1_value + 1

    #print char_map['j']
    
    # Convert to list of pairs with probability.    
    pairs = []
    for c0, c0_map in char_map.items():
        for c1, c1_value in c0_map.items():
            pairs.append((c0+c1, c1_value))

    # Sort by frequency.
    pairs.sort(cmp=lambda x,y: x[1] - y[1])
    
    # Normalize the weights.
    total = 0.0
    for p in pairs:
        total += p[1]
    pairs = [(p[0], p[1]/total) for p in pairs]

    return pairs

def filter_pairs(pairs, required_keys, keys):
    # Require at least one key from required_keys, and require that only
    # keys be present.
    good_pairs = []
    for p in pairs:
        str = p[0]
        if required_keys.find(str[0]) == -1 and required_keys.find(str[1]) == -1:
            continue
        if keys.find(str[0]) == -1 or keys.find(str[1]) == -1:
            continue
        good_pairs.append(p)
    
    # Re-normalize weights.
    total = 0.0
    for p in good_pairs:
        total += p[1]
    good_pairs = [(p[0], p[1]/total) for p in good_pairs]

    return good_pairs
    
def get_weighted_random_pair(pairs):
    # TODO: I'm currently ignoring the weighting because it's preventing keys from
    # ever appearing, for example j never appears in the home row lesson.
    return random.choice(pairs)
    #n = random.uniform(0, 1)
    #for p in pairs:
    #    if n < p[1]:
    #        break
    #    n -= p[1]
    #return p

def make_weighted_wordlist_pairs(pairs, required_keys, keys, count):
    good_pairs = filter_pairs(pairs, required_keys, keys)
    
    text = ''
    for y in xrange(0, count):
        p = get_weighted_random_pair(good_pairs)
        text += p[0] + ' '
    return text.strip()
    
def filter_wordlist(words, all_keys, req_keys, minlen, maxlen, bad_words):
    print 'Filtering word list...'

    # Uniquify words.
    # TODO: Build a frequency table as with the pairs.
    words = list(set(words))

    # Filter word list based on variety of contraints.
    good_words = []

    for word in words:
        if len(word) < minlen or len(word) > maxlen:
            continue
        
        good = True
        
        # Check for letters that are not supported.
        for c in word:
            if all_keys.find(c) == -1:
                good = False
                break
        
        # Make sure required letters are present.
        any_req = False
        for c in req_keys:
            if word.find(c) >= 0:
                any_req = True
                break
        if not any_req:
            good = False
        
        # Remove bad words.
        for bad in bad_words:
            if word == bad:
                good = False
                break
        
        if good:
            good_words.append(word)

    return good_words

def make_random_words(words, count):
    text = ''
    for x in range(0, count):
        text += random.choice(words) + ' '
    return text.strip()

def add_step(lesson, instructions, mode, text):
    print instructions
    print text
    step = {}
    step['instructions'] = instructions
    step['text'] = text
    step['mode'] = mode
    lesson['steps'].append(step)

def build_lesson(
    name, description, 
    level, required_level, 
    new_keys, base_keys, 
    words, bad_words):

    print "Building lesson '%s'..." % name

    all_keys = new_keys + base_keys

    good_words = filter_wordlist(words=words, 
        all_keys=all_keys, req_keys=new_keys, 
        minlen=2, maxlen=8, 
        bad_words=bad_words)
    
    pairs = get_pairs_from_wordlist(words)
        
    lesson = {}
    lesson['name'] = name
    lesson['description'] = description
    lesson['level'] = level
    lesson['requiredlevel'] = required_level
    lesson['medals'] = [
        { 'name': 'bronze', 'wpm': 5,  'accuracy': 60 },
        { 'name': 'silver', 'wpm': 10, 'accuracy': 75 },
        { 'name': 'gold',   'wpm': 20, 'accuracy': 90 }
    ]
    lesson['steps'] = []

    kb = keyboard.KeyboardData()
    kb.set_layout(keyboard.DEFAULT_LAYOUT)

    keynames = ''
    for k in new_keys[:-2]:
        keynames += k + ', '
    keynames += new_keys[-2] + ' and ' + new_keys[-1]

    add_step(lesson,
        _('Welcome to the %(name)s lesson!\n\nIn this lesson, you will learn the %(keynames)s keys.  Press the Enter key when you are ready to begin!') \
            % { 'name': name, 'keynames': keynames },
        'key', '\n')

    for key in new_keys:
        k = kb.find_key_by_letter(key)
        add_step(lesson,
            _('Press the %(name)s key using your %(finger)s finger.') \
                % { 'name': key, 'finger': FINGERS[k['key-finger']] },
            'key', key)

    add_step(lesson,
        _('Practice typing the keys you just learned.'),
        'text', make_random_doubles(new_keys, count=40))
    
    add_step(lesson,
        _('Keep practicing the new keys.'),
        'text', make_random_doubles(new_keys, count=40))
    
    add_step(lesson,
        _('Now put the keys together into pairs.'),
        'text', make_weighted_wordlist_pairs(pairs, new_keys, new_keys, count=50))
    
    add_step(lesson,
        _('Keep practicing key pairs.'),
        'text', make_weighted_wordlist_pairs(pairs, new_keys, new_keys, count=50))
    
    if base_keys != '':
        add_step(lesson,
            _('Now practice all the keys you know.'),
            'text', make_weighted_wordlist_pairs(pairs, new_keys, all_keys, count=50))
    
        add_step(lesson,
            _('Almost done.  Keep practicing all the keys you know.'),
            'text', make_weighted_wordlist_pairs(pairs, new_keys, all_keys, count=50))

    else:
        add_step(lesson,
            _('Almost done.  Keep practicing key pairs.'),
            'text', make_weighted_wordlist_pairs(pairs, new_keys, new_keys, count=100))

    add_step(lesson,
        _('Time to type real words.'),
        'text', make_random_words(good_words, count=100))
    
    add_step(lesson,
        _('Keep practicing these words.'),
        'text', make_random_words(good_words, count=100))
    
    add_step(lesson,
        _('Almost finished. Try to type as quickly and accurately as you can!'),
        'text', make_random_words(good_words, count=200))
    
    text = '$report'
    add_step(lesson, text, 'key', '\n')

    return lesson

def write_lesson(filename, lesson):
    code = locale.getlocale(locale.LC_ALL)[0]
    text = json.write(lesson)
    open(os.path.join('lessons', code, filename), 'w').write(text)   

def build_intro_lesson():
    lesson = {}
    lesson['name'] = _('Welcome') 
    lesson['description'] = _('Click here to begin your typing adventure.') 
    lesson['level'] = 1
    lesson['requiredlevel'] = 0
    lesson['report'] = 'simple'
    lesson['medals'] = [
        { 'name': 'bronze', 'wpm': 0, 'accuracy': 10 },
        { 'name': 'silver', 'wpm': 0, 'accuracy': 70 },
        { 'name': 'gold', 'wpm': 0, 'accuracy': 100 }
    ]
    lesson['steps'] = []
    
    text = ''
    text += _('Hi, welcome to Typing Turtle!  My name is Max the turtle, ')
    text += _('and I\'ll to teach you how to type.\n\n')
    text += _('First, I will tell you the secret of fast typing... ')
    text += _('Always use the correct finger to press each key!\n\n')
    text += _('If you learn which finger presses each key, and keep practicing, you will be typing like a pro before you know it!\n\n')
    text += _('Now, place your hands on the keyboard just like the picture below.\n')
    text += _('When you\'re ready, press the space bar with your thumb!')
    add_step(lesson, text, 'key', ' ')

    text = ''
    text += _('Good job!  You correctly typed your first key.  When typing, the space bar is ')
    text += _('used to insert spaces between words.\n\n')
    text += _('Press the space bar again with your thumb.')
    add_step(lesson, text, 'key', ' ')
    
    text = ''
    text += _('Now I\'ll teach you the second key, enter.  ')
    text += _('That\'s the big square key near your right pinky finger.\n\n')
    text += _('Without moving any other fingers, reach your pinky over and press ')
    text += _('Enter.\nCheck the picture below if you need a hint!')
    add_step(lesson, text, 'key', '\n')
    
    text = ''
    text += _('Great!  When typing, the enter key is used to begin a new line.\n\n')
    text += _('Press the enter key again with your right pinky.')
    add_step(lesson, text, 'key', '\n')
    
    text = ''
    text += _('Wonderful!  Now I\'m going to tell you a little more about Typing Turtle.\n\n')
    text += _('The box you are reading is where instructions will appear.  The keyboard ')
    text += _('picture below shows what your hands should be doing.  The numbers ')
    text += _('up top show how quickly and accurately you are typing.\n\n')
    text += _('When you see a big picture of a key like this one, you are supposed to ')
    text += _('press that key on the keyboard.\nRemember, always use the correct finger to ')
    text += _('type each key!')
    add_step(lesson, text, 'key', ' ')

    text = '$report'
    add_step(lesson, text, 'key', '\n')

    return lesson

def make_default_lesson_set(words, bad_words):
    write_lesson(
        'intro.lesson',
        build_intro_lesson())

    lesson = build_lesson(
        name=_('The Home Row'),
        description=_('This lesson teaches you the first a, s, d, f, g, h, j, k and l keys \nin the middle of the keyboard.\nThese keys are called the Home Row.'), 
        level=2, required_level=1,
        new_keys=_('asdfghjkl'), base_keys='', 
        words=words, bad_words=bad_words)
    write_lesson('homerow.lesson', lesson)
    
    lesson = build_lesson(
        name=_('The Top Row'),
        description=_('This lesson teaches you the q, w, e, r, t, y, u, i, o and p keys \non the top row of the keyboard.'), 
        level=3, required_level=2,
        new_keys='qwertyuiop', base_keys='asdfghjkl', 
        words=words, bad_words=bad_words)
    write_lesson('toprow.lesson', lesson)

    lesson = build_lesson(
        name=_('The Bottom Row'),
        description=_('This lesson teaches you the z, x, c, v, b, n and m keys \non the bottom row of the keyboard.'), 
        level=4, required_level=3,
        new_keys='zxcvbnm', base_keys='asdfghjklqwertyuiop', 
        words=words, bad_words=bad_words)
    write_lesson('bottomrow.lesson', lesson)
    
if __name__ == "__main__":
    import optparse
    parser = optparse.OptionParser("usage: %prog [options]")
    parser.add_option("--make-all-lessons", dest="make_all_lessons", action="store_true",
                      help="Automatically generate a complete lesson set.")
    parser.add_option("--output", dest="output", metavar="FILE",
                      help="Output file.")
    parser.add_option("--keys", dest="keys", metavar="KEYS", default='',
                      help="Keys to teach.")
    parser.add_option("--base-keys", dest="base_keys", metavar="KEYS",
                      help="Keys already taught prior to this lesson.")
    parser.add_option("--name", dest="name", default="Generated",
                      help="Lesson name.")
    parser.add_option("--desc", dest="desc", default="Default description.",
                      help="Lesson description.")
    parser.add_option("--level", dest="level", type="int", metavar="LEVEL", default=0,
                      help="Level granted by this lesson.")
    parser.add_option("--req-level", dest="required_level", type="int", metavar="LEVEL", default=0,
                      help="Level requirement for this lesson.")
    parser.add_option("--wordlist", dest="wordlist", metavar="FILE",
                      help="Text file containing words to use.")
    parser.add_option("--badwordlist", dest="badwordlist", metavar="FILE",
                      help="Text file containing words *not* to use.")
    
    (options, args) = parser.parse_args()
    
    if not options.make_all_lessons and not options.keys:
        parser.error('no keys given')

    if not options.wordlist:
        parser.error('no wordlist file given')
        
    words = load_wordlist(options.wordlist)

    bad_words = []
    if options.badwordlist:
        bad_words = load_wordlist(options.badwordlist)

    if options.make_all_lessons:
        make_default_lesson_set(words=words, bad_words=bad_words)
        sys.exit()

    else:
        lesson = build_lesson(
            name=options.name, description=options.desc, 
            level=options.level, required_level=options.required_level,
            new_keys=options.keys, base_keys=options.base_keys, 
            words=words, bad_words=bad_words)
    
        if output:
            text = json.write(lesson)
            open(output, 'w').write(text)
        else:
            import pprint
            pprint.pprint(lesson)

