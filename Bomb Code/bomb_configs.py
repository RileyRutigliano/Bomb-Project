#################################
# CSC 102 Defuse the Bomb Project
# Configuration file
# Team: The Atomic Bomb (Libby Divers and Riley Rutigliano)
#################################

# constants
DEBUG = True        # debug mode?
RPi = True           # is this running on the RPi?
ANIMATE = True       # animate the LCD text?
SHOW_BUTTONS = True # show the Pause and Quit buttons on the main LCD GUI?
COUNTDOWN = 360      # the initial bomb countdown value (seconds)
NUM_STRIKES = 5      # the total strikes allowed before the bomb "explodes"
NUM_PHASES = 4       # the total number of initial active bomb phases
WINNER_IMAGE = "./winner.png"
LOSER_IMAGE = "./loser.png"
DEFUSED_AUDIO = "./defused.mp3"
STRIKE_AUDIO = "./strike.mp3"
WINNER_AUDIO = "./winner.mp3"
LOSER_AUDIO = "./loser.mp3"

# imports
from random import randint, shuffle, choice
from string import ascii_uppercase
if (RPi):
    import board
    from adafruit_ht16k33.segments import Seg7x4
    from digitalio import DigitalInOut, Direction, Pull
    from adafruit_matrixkeypad import Matrix_Keypad

#################################
# setup the electronic components
#################################
# 7-segment display
# 4 pins: 5V(+), GND(-), SDA, SCL
#         ----------7SEG---------
if (RPi):
    i2c = board.I2C()
    component_7seg = Seg7x4(i2c)
    # set the 7-segment display brightness (0 -> dimmest; 1 -> brightest)
    component_7seg.brightness = 0.5

# keypad
# 8 pins: 10, 9, 11, 5, 6, 13, 19, NA
#         -----------KEYPAD----------
if (RPi):
    # the pins
    keypad_cols = [DigitalInOut(i) for i in (board.D10, board.D9, board.D11)]
    keypad_rows = [DigitalInOut(i) for i in (board.D5, board.D6, board.D13, board.D19)]
    # the keys
    keypad_keys = ((1, 2, 3), (4, 5, 6), (7, 8, 9), ("*", 0, "#"))

    component_keypad = Matrix_Keypad(keypad_rows, keypad_cols, keypad_keys)

# jumper wires
# 10 pins: 14, 15, 18, 23, 24, 3V3, 3V3, 3V3, 3V3, 3V3
#          -------JUMP1------  ---------JUMP2---------
# the jumper wire pins
if (RPi):
    # the pins
    component_wires = [DigitalInOut(i) for i in (board.D14, board.D15, board.D18, board.D23, board.D24)]
    for pin in component_wires:
        # pins are input and pulled down
        pin.direction = Direction.INPUT
        pin.pull = Pull.DOWN

# pushbutton
# 6 pins: 4, 17, 27, 22, 3V3, 3V3
#         -BUT1- -BUT2-  --BUT3--
if (RPi):
    # the state pin (state pin is input and pulled down)
    component_button_state = DigitalInOut(board.D4)
    component_button_state.direction = Direction.INPUT
    component_button_state.pull = Pull.DOWN
    # the RGB pins
    component_button_RGB = [DigitalInOut(i) for i in (board.D17, board.D27, board.D22)]
    for pin in component_button_RGB:
        # RGB pins are output
        pin.direction = Direction.OUTPUT
        pin.value = True

# toggle switches
# 3x3 pins: 12, 16, 20, 21, 3V3, 3V3, 3V3, 3V3, GND, GND, GND, GND
#           -TOG1-  -TOG2-  --TOG3--  --TOG4--  --TOG5--  --TOG6--
if (RPi):
    # the pins
    component_toggles = [DigitalInOut(i) for i in (board.D12, board.D16, board.D20, board.D21)]
    for pin in component_toggles:
        # pins are input and pulled down
        pin.direction = Direction.INPUT
        pin.pull = Pull.DOWN

###########
# functions
###########
# generates the bomb's serial number
#  it should be made up of alphaneumeric characters, and include at least 3 digits and 3 letters
#  the sum of the digits should be in the range 1..15 to set the toggles target
#  the first three letters should be distinct and in the range 0..4 such that A=0, B=1, etc, to match the jumper wires
#  the last letter should be outside of the range
def genSerial():
    # set the digits (used in the toggle switches phase)
    serial_digits = []
    toggle_value = randint(1, 15)
    # the sum of the digits is the toggle value
    while (len(serial_digits) < 3 or toggle_value - sum(serial_digits) > 0):
        d = randint(0, min(9, toggle_value - sum(serial_digits)))
        serial_digits.append(d)
        
    # set the letters (used in the jumper wires phase)
    jumper_indexes = [ 0 ] * 5
    while (sum(jumper_indexes) < 3):
        jumper_indexes[randint(0, len(jumper_indexes) - 1)] = 1
    jumper_value = int("".join([ str(n) for n in jumper_indexes ]), 2)
    # the letters indicate which jumper wires must be "cut"
    jumper_letters = [ chr(i + 65) for i, n in enumerate(jumper_indexes) if n == 1 ]
    
    # form the serial number
    serial = [ str(d) for d in serial_digits ] + jumper_letters #choice(list(letterlist)) #
    # and shuffle it
    shuffle(serial)
    # finally, add a final letter (F..Z)
    serial += [ choice([ chr(n) for n in range(70, 91) ]) ]
    # and make the serial number a string
    serial = "".join(serial)

    return serial, toggle_value, jumper_value



# generates the keypad combination from a keyword and rotation key
def genKeypadCombination():
    # encrypts a keyword using a rotation cipher
    def encrypt(keyword, rot):
        cipher = ""

        # encrypt each letter of the keyword using rot
        for c in keyword:
            cipher += chr((ord(c) - 65 + rot) % 26 + 65)

        return cipher

    # returns the keypad digits that correspond to the passphrase
    def digits(passphrase):
        combination = ""
        keys = [ None, None, "ABC", "DEF", "GHI", "JKL", "MNO", "PRS", "TUV", "WXY" ]

        # process each character of the keyword
        for c in passphrase:
            for i, k in enumerate(keys):
                if (k and c in k):
                    # map each character to its digit equivalent
                    combination += str(i)

        return combination

    # the list of riddles and matching answers
    keywords = { "What goes all the way around the world but stays in a corner?": "STAMP",\
                 "What has four fingers and a thumb, but isn’t alive?": "GLOVE",\
                 "What gets wet when drying": "TOWEL",\
                 "David's father has three sons: Snap, Crackle, and ___.": "DAVID",\
                 "What has 13 hearts, but no other organs?": "CARDS",\
                 "What has hands, but can't clap?": "CLOCK",\
                 "What word looks the same upside down and backwards?": "SWIMS",\
                 "What gets bigger when more is taken away?": "HOLES",\
                 "What word is always spelled wrong?": "WRONG",\
                 "I have no legs but never walk, but I always run. What am I?": "RIVER"}

    # the rotation cipher key
    rot = randint(1, 25)

    # pick a keyword and matching passphrase
    keyword,passphrase = choice(list(keywords.items()))

    #get combination
    combination = digits(passphrase)

    return keyword, combination, passphrase, rot #, cipher_keyword

def wirecombo():
    # the list of keywords and matching number correspondant
    wireword = { "coal": 1,\
                 "iron": 2,\
                 "coal and iron": 3,\
                 "plum": 4,\
                 "coal and plum": 5,\
                 "iron and plum": 6,\
                 "coal, iron, and plum": 7,\
                 "sky": 8,\
                 "coal and sky": 9,\
                 "iron and sky": 10,\
                 "coal, iron, and sky": 11,\
                 "plum and sky": 12,\
                 "coal, plum, and sky": 13,\
                 "iron, plum, and sky": 14,\
                 "coal, iron, plum, and sky": 15,\
                 "snow": 16,\
                 "coal and snow": 17,\
                 "iron and snow": 18,\
                 "coal, iron, and snow": 19,\
                 "plum and snow": 20,\
                 "coal, pl.um, and snow": 21,\
                 "iron, plum, and snow": 22,\
                 "coal, iron, plum, and snow": 23,\
                 "sky and snow": 24,\
                 "coal, sky, and snow": 5,\
                 "iron, sky, and snow": 26,\
                 "coal iron, sky, and snow": 27,\
                 "plum, sky, and snow": 28,\
                 "coal, plum, sky, and snow": 29,\
                 "iron, plum, sky, and snow": 30}

    key,passphrase = choice(list(wireword.items()))   
 
    wires_target = passphrase
    
    return key, passphrase    

def togglescombo():
    # the combos for the toggles with the corresponding combo
    letterlist = { "A": 1,\
                   "B": 2,\
                   "AB": 3,\
                   "C": 4,\
                   "AC": 5,\
                   "BC": 6,\
                   "ABC": 7,\
                   "D": 8,\
                   "AD": 9,\
                   "BD": 10,\
                   "ABD": 11,\
                   "CD": 12,\
                   "ACD": 13,\
                   "BCD": 14,\
                   "ABCD": 15}
    letter, answer = choice(list(letterlist.items()))
    
    toggles_target = answer
    
    return letter, answer
    


###############################
# generate the bomb's specifics
###############################
# generate the bomb's serial number (which also gets us the toggle and jumper target values)
#  serial: the bomb's serial number
#  toggles_target: the toggles phase defuse value
#  wires_target: the wires phase defuse value
serial, toggles_target, jumper_value = genSerial() #wires_target

key, wires_target = wirecombo()

letter, toggles_target = togglescombo()
# generate the combination for the keypad phase
#  keyword: the plaintext keyword for the lookup table
#  cipher_keyword: the encrypted keyword for the lookup table
#  rot: the key to decrypt the keyword
#  keypad_target: the keypad phase defuse value (combination)
#  passphrase: the target plaintext passphrase
keyword, keypad_target, passphrase, rot = genKeypadCombination() #, cipher_keyword

# generate the color of the pushbutton (which determines how to defuse the phase)
button_color = choice(["R", "G", "B"])
# appropriately set the target
button_target = None

# G is the second to last digit in the serial number
if (button_color == "G"):
    button_target = [ n for n in serial if n.isdigit() ][-2]
# B is the third numeric digit in the serial number
elif (button_color == "B"):
    button_target = [ n for n in serial if n.isdigit() ][2]   
# R is the first even numeric digit in the serial number
elif (button_color == "R"):
    # collect all digits in the serial number
    serial_digits = [n for n in serial if n.isdigit() ]
    even_serials = []
    # collect and add all numbers that can be divided by 2 with no remainders (even) to the even list
    for number in serial_digits:
        if int(number) % 2 == 0:
            even_serials.append(number)
            # if there is no even number auto diffuse
            if even_serials[0] == "":
                self._defused = True
            else:
                button_target = even_serials[0] #else, set target to first in the list
            

if (DEBUG):
    print(f"Serial number: {letter}-{serial}")
    print(f"Toggles target: {bin(toggles_target)[2:].zfill(4)}/{toggles_target}")
    print(f"Wires target: {bin(wires_target)[2:].zfill(5)}/{wires_target}")
    print(f"Keypad target: {keypad_target}/{passphrase}/{keyword}/(key={key})") #{cipher_keyword}
    print(f"Button target: {button_target}")

# set the bomb's LCD bootup text
#{cipher_keyword}
boot_text = f"Booting...\n\x00\x00"\
            f"*Kernel v3.1.4-159 loaded.\n"\
            f"Initializing subsystems...\n\x00"\
            f"*System model: 102BOMBv4.2\n"\
            f"*Serial number: {letter}-{serial}\n"\
            f"Encrypting keypad...\n\x00"\
            f"*Keyword: {keyword}\n"\
            f"*Key: {key}\n"\
            f"*{''.join(ascii_uppercase)}\n"\
            f"*{''.join([str(n % 10) for n in range(26)])}\n"\
            f"Rendering phases...\x00"