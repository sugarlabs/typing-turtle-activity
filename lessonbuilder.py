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

import os, sys, random, simplejson, locale, re, optparse
from gettext import gettext as _

# For modifier constants.
import gtk

# Set up remote debugging.
#import dbgp.client
#dbgp.client.brkOnExcept(host='192.168.1.104', port=12900)

# Import keyboard data.
import keyboard

def error(s):
    print "lessonbuilder: ERROR: ", s 
    print "The lesson could not be generated, exiting.\n\n"
    sys.exit(1)

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

def make_jumbles(required_keys, keys, count, width):
    text = ''
    for y in range(0, count):
        # Alternating between required and non-required.  Is this too challenging to type?
        for x in range(0, width/2):
            text += random.choice(required_keys)
            text += random.choice(keys)
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

RE_WHITESPACE = re.compile('\s+', re.UNICODE)

def load_wordlist(path):
    try:
        text = unicode(open(path, 'r').read())
        
        # Split words by whitespace characters.
        # This preserves partial punctuation in some words, which is
        # intentional since we want to teach punctuation in its natural
        # form.
        words = RE_WHITESPACE.split(text)
        
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

    # Convert to list of pairs with probability.    
    pairs = []
    for c0, c0_map in char_map.items():
        for c1, c1_value in c0_map.items():
            pairs.append((c0+c1, c1_value))

    # Sort by frequency.
    #pairs.sort(cmp=lambda x,y: x[1] - y[1])
    
    # Normalize the weights.
    #total = 0.0
    #for p in pairs:
    #    total += p[1]
    #pairs = [(p[0], p[1]/total) for p in pairs]

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
    # TODO: I'm currently ignoring the weighting because it's preventing certain keys 
    # from ever appearing due to their unpopularity, for example j never appears in the 
    # home row lesson.
    return random.choice(pairs)
    #n = random.uniform(0, 1)
    #for p in pairs:
    #    if n < p[1]:
    #        break
    #    n -= p[1]
    #return p

def make_weighted_wordlist_pairs(pairs, required_keys, keys, count):
    good_pairs = filter_pairs(pairs, required_keys, keys)
    
    if len(good_pairs) == 0:
        return make_random_pairs(required_keys, keys, count)
        
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

    unknown_re = re.compile('[^'+re.escape(all_keys)+']')
    req_re = re.compile('['+re.escape(req_keys)+']')

    for word in words:
        if len(word) < minlen or len(word) > maxlen:
            continue
        
        # Check for letters that are not supported.
        if unknown_re.search(word):
            continue 
        
        # Make sure at least one required letter is present.
        if not req_re.search(word):
            continue

        # Remove bad words.
        if word in bad_words:
            continue
        
        good_words.append(word)

    return good_words

def make_random_words(words, required_keys, keys, count):
    text = ''
    for x in range(0, count):
        text += random.choice(words) + ' '
    return text.strip()

def make_step(instructions, mode, text):
    step = {}
    step['instructions'] = instructions
    step['text'] = text
    step['mode'] = mode
    return step

def build_game_words(
    new_keys, base_keys, 
    words, bad_words):

    all_keys = new_keys + base_keys

    good_words = filter_wordlist(words=words, 
        all_keys=all_keys, req_keys=new_keys, 
        minlen=2, maxlen=8, 
        bad_words=bad_words)

    random.shuffle(good_words)
    
    return good_words[:200]

def build_key_steps(
    count, new_keys, base_keys, 
    words, bad_words):

    CONGRATS = [
        _('Well done!'),
        _('Good job.'),
        _('Awesome!'),
        _('Way to go!'),
        _('Wonderful!'),
        _('Nice work.'),
        _('You did it!'),
    ]

    def get_congrats():
        return random.choice(CONGRATS) + ' '

    HINTS = [
        _('Be careful to use the correct finger to press each key.  Look at the keyboard below if you need help remembering.'),
        _('Try to type at the same speed, all the time.  As you get more comfortable you can increase the speed a little.')
    ]

    def get_hint():
        return random.choice(HINTS)

    FINGERS = {
        'LP': _('left little'),
        'LR': _('left ring'),
        'LM': _('left middle'),
        'LI': _('left index'),
        'LT': _('left thumb'),
        'RP': _('right little'),
        'RR': _('right ring'),
        'RM': _('right middle'),
        'RI': _('right index'),
        'RT': _('right thumb'),
    }

    all_keys = new_keys + base_keys

    good_words = filter_wordlist(words=words, 
        all_keys=all_keys, req_keys=new_keys, 
        minlen=2, maxlen=8, 
        bad_words=bad_words)
    
    pairs = get_pairs_from_wordlist(good_words)
        
    steps = []

    kb = keyboard.KeyboardData()

    # Attempt to load a letter map for the current locale.
    code = locale.getdefaultlocale()[0]
    try:
        kb.load_letter_map('lessons/%s/%s.key' % (code, code))
    except:
        kb.load_letter_map('lessons/en_US/en_US.key')

    kb.set_layout(keyboard.OLPC_LAYOUT)

    keynames = new_keys[0]
    if len(new_keys) >= 2:
        for k in new_keys[1:-1]:
            keynames += ', ' + k
        keynames += _(' and %s keys') % new_keys[-1]
    else:
        keynames += _(' key')

    steps.append(make_step(
        _('In this lesson, you will learn the %(keynames)s.\n\nPress the ENTER key when you are ready to begin!') \
            % { 'keynames': keynames },
        'key', '\n'))

    for letter in new_keys:
        key, state, group = kb.get_key_state_group_for_letter(letter)

        if not key:
            error("There is no key combination in the current keymap for the '%s' letter. " % letter + \
                  "Are you sure the keymap is set correctly?\n")

        try:
            finger = FINGERS[key['key-finger']]
        except:
            error("The '%s' letter (scan code %x) does not have a finger assigned." % (letter, key['key-scan']))

        if state == gtk.gdk.SHIFT_MASK:
            # Choose the finger to press the SHIFT key with.
            if key['key-finger'][0] == 'R':
                shift_finger = FINGERS['LP']
            else:
                shift_finger = FINGERS['RP']

            instructions = _('Press and hold the SHIFT key with your %(finger)s finger, ') % { 'finger': shift_finger }
            instructions += _('then press the %(letter)s key with your %(finger)s finger.') % { 'letter': letter, 'finger': finger }

        elif state == gtk.gdk.MOD5_MASK:
            instructions = _('Press and hold the ALTGR key, ') 
            instructions += _('then press the %(letter)s key with your %(finger)s finger.') % { 'letter': letter, 'finger': finger }

        elif state == gtk.gdk.SHIFT_MASK | gtk.gdk.MOD5_MASK:
            instructions = _('Press and hold the ALTGR and SHIFT keys, ')
            instructions += _('then press the %(letter)s key with your %(finger)s finger.') % { 'letter': letter, 'finger': finger }

        else:
            instructions = _('Press the %(letter)s key with your %(finger)s finger.') % { 'letter': letter, 'finger': finger }

        steps.append(make_step(instructions, 'key', letter))

    steps.append(make_step(
        get_congrats() + _('Practice typing the keys you just learned.'),
        'text', make_random_doubles(new_keys, count)))
    
    steps.append(make_step(
        get_congrats() + _('Now put the keys together into pairs.'),
        'text', make_weighted_wordlist_pairs(pairs, new_keys, all_keys, count)))
    
    if len(good_words) == 0:
        steps.append(make_step(
            get_congrats() + _('Time to type jumbles.'),
            'text', make_jumbles(new_keys, all_keys, count, 5)))
        
    else:
        steps.append(make_step(
            get_congrats() + _('Time to type real words.'),
            'text', make_random_words(good_words, new_keys, all_keys, count)))
    
    text = '$report'
    steps.append(make_step(text, 'key', ' '))

    return steps 

def build_intro_steps():
    steps = []

    text = ''
    text += _('Hihowahyah!  Ready to learn the secret of fast typing?\n')
    text += _('Always use the correct finger to press each key!\n\n')
    text += _('Now, place your hands on the keyboard just like the picture below.\n')
    text += _('When you\'re ready, press the SPACE bar with your thumb!')
    steps.append(make_step(text, 'key', ' '))

    text = ''
    text += _('Good job!  The SPACE bar is used to insert spaces between words.\n\n')
    text += _('Press the SPACE bar again with your thumb.')
    steps.append(make_step(text, 'key', ' '))
    
    text = ''
    text += _('Now I\'ll teach you the second key, ENTER.  ')
    text += _('That\'s the big square key near your right little finger.\n\n')
    text += _('Now, reach your little finger over and press ENTER.')
    steps.append(make_step(text, 'key', '\n'))
    
    text = ''
    text += _('Great!  When typing, the ENTER key is used to begin a new line.\n\n')
    text += _('Press the ENTER key again with your right little finger.')
    steps.append(make_step(text, 'key', '\n'))
    
    text = ''
    text = '$report'
    steps.append(make_step(text, 'key', '\n'))

    return steps 

def build_text_step(path):
    steps = []

    instructions = _('Copy out the following text.')

    try:
        text = unicode(open(path, 'r').read())
    except:
        text = ''

    steps.append(make_step(instructions, 'text', text))

    return steps

def main():
    parser = optparse.OptionParser("usage: %prog [options]")

    parser.add_option("--title", dest="name", default="Generated",
                      help="Lesson title.")
    parser.add_option("--desc", dest="desc", default="Default description.",
                      help="Lesson description.  Use \\n to break lines.")
    parser.add_option("--order", dest="order", type="int", metavar="N", default=0,
                      help="Order of this lesson in the index.")
    parser.add_option("--seed", dest="seed", type="int", metavar="N", default=0x12345678,
                      help="Random seed.")
    parser.add_option("--locale", dest="locale",
                      help="Lesson locale (overrides system setting).")
    parser.add_option("--keys", dest="keys", metavar="KEYS", default='',
                      help="Keys to teach.")
    parser.add_option("--base-keys", dest="base_keys", metavar="KEYS", default='',
                      help="Keys already taught prior to this lesson.")
    parser.add_option("--length", dest="length", type="int", metavar="N", default=60,
                      help="Length of the lesson.  Default 60.")
    parser.add_option("--wordlist", dest="wordlist", metavar="FILE",
                      help="Text file containing words to use.")
    parser.add_option("--badwordlist", dest="badwordlist", metavar="FILE",
                      help="Text file containing words *not* to use.")
    parser.add_option("--text-file", dest="text_file", metavar="FILE",
                      help="Text file containing the lesson text.")
    parser.add_option("--game", dest="game", metavar="TYPE", default='balloon',
                      help="Type of game to use.  Currently just 'balloon'.")
    parser.add_option("--output", dest="output", metavar="FILE",
                      help="Output file (*.lesson).")

    type_group = optparse.OptionGroup(parser, 
        'Lesson Types', 
        'You must pass a lesson type to control the kind of lesson created.')
    type_group.add_option("--intro-lesson", dest="make_intro_lesson", action="store_true",
                      help="Generate the introductory lesson.")
    type_group.add_option("--text-lesson", dest="make_text_lesson", action="store_true",
                      help="Generate a lesson from a text source such as a paragraph.")
    type_group.add_option("--key-lesson", dest="make_key_lesson", action="store_true",
                      help="Generate a lesson to teach a specific set of keys.")
    type_group.add_option("--game-lesson", dest="make_game_lesson", action="store_true",
                      help="Generate a lesson which plays a game.")
    parser.add_option_group(type_group)

    medal_group = optparse.OptionGroup(parser, 
        'Medal Requirements', 
        'Pass these arguments to set medal requirements.')
    medal_group.add_option("--bronze-wpm", dest="bronze_wpm", type="int", metavar="N", default=15,
                      help="Words per minute for a Bronze medal.  Default 15.")
    medal_group.add_option("--silver-wpm", dest="silver_wpm", type="int", metavar="N", default=20,
                      help="Words per minute for a Silver medal.  Default 20.")
    medal_group.add_option("--gold-wpm", dest="gold_wpm", type="int", metavar="N", default=25,
                      help="Words per minute for a Gold medal.  Default 25.")
    medal_group.add_option("--bronze-acc", dest="bronze_accuracy", type="int", metavar="N", default=70,
                      help="Accuracy for a Bronze medal.  Default 70.")
    medal_group.add_option("--silver-acc", dest="silver_accuracy", type="int", metavar="N", default=80,
                      help="Accuracy for a Silver medal.  Default 80.")
    medal_group.add_option("--gold-acc", dest="gold_accuracy", type="int", metavar="N", default=90,
                      help="Accuracy for a Gold medal.  Default 90.")
    medal_group.add_option("--bronze-score", dest="bronze_score", type="int", metavar="N", default=3000,
                      help="Game score for a Bronze medal.  Default 3000.")
    medal_group.add_option("--silver-score", dest="silver_score", type="int", metavar="N", default=4500,
                      help="Game score  for a Silver medal.  Default 4500.")
    medal_group.add_option("--gold-score", dest="gold_score", type="int", metavar="N", default=6000,
                      help="Game score for a Gold medal.  Default 6000.")
    parser.add_option_group(medal_group)

    (options, args) = parser.parse_args()

    if not (options.make_intro_lesson or options.make_key_lesson or options.make_game_lesson):
        parser.error('no lesson type given')

    if not options.output:
        parser.error('no output file given')
    
    # Set up localization.
    if options.locale:
        locale.setlocale(locale.LC_ALL, options.locale)
    else:
        locale.setlocale(locale.LC_ALL, '')

    words = load_wordlist(options.wordlist)
    
    bad_words = []
    if options.badwordlist:
        bad_words = load_wordlist(options.badwordlist)

    # Convert string arguments to Unicode.
    options.name = unicode(options.name)
    options.keys = unicode(options.keys)
    options.base_keys = unicode(options.base_keys)
    options.desc = unicode(options.desc.replace('\\n', '\n'))
    
    random.seed(options.seed)

    print "Building lesson '%s'..." % options.name

    lesson = {}
    lesson['name'] = options.name
    lesson['description'] = options.desc
    lesson['order'] = options.order

    lesson['medals'] = [ 
        { 'name': 'bronze', 'wpm': options.bronze_wpm, 'accuracy': options.bronze_accuracy, 'score': options.bronze_score },
        { 'name': 'silver', 'wpm': options.silver_wpm, 'accuracy': options.silver_accuracy, 'score': options.silver_score },
        { 'name': 'gold',   'wpm': options.gold_wpm,   'accuracy': options.gold_accuracy,   'score': options.gold_score },
    ]

    if options.make_intro_lesson:
        lesson['type'] = 'normal' 
        lesson['steps'] = build_intro_steps()
    
    elif options.make_key_lesson:        
        if not options.wordlist:
            parser.error('no wordlist file given')
        
        lesson['type'] = 'normal' 
        lesson['steps'] = build_key_steps(
            count=options.length, new_keys=options.keys, base_keys=options.base_keys, 
            words=words, bad_words=bad_words)

    elif options.make_text_lesson:
        lesson['type'] = 'normal'
        lesson['steps'] = build_text_step(options.text_file)

    elif options.make_game_lesson:
        if not options.wordlist:
            parser.error('no wordlist file given')
        
        lesson['type'] = options.game
        lesson['length'] = options.length
        lesson['words'] = build_game_words(
            new_keys=options.keys, base_keys=options.base_keys, 
            words=words, bad_words=bad_words)

    text = simplejson.dumps(lesson, ensure_ascii=False, sort_keys=True, indent=4)

    open(options.output, 'w').write(text)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "Ctrl-C detected, aborting."
        sys.exit(1)

