import libtcodpy
import random
from Console import Console
from Panel import Panel


test = Console(20, 20, 'test')
test.set_fps(10)
ptest = Panel(0, 0, 20, 20)
ptest.set_default_foreground(libtcodpy.light_gray)
pshade = Panel(-1, -1, 10, 10)
random.seed(222)
fade = 0.1

while not test.is_window_closed:
    for x in range(0, 20):
        for y in range(0, 20):
            if random.randint(0, 2):
                ptest.write(x, y, '.')
                if not random.randint(0, 5):
                    ptest.set_default_background(libtcodpy.red)
                elif not random.randint(0, 5):
                    ptest.set_default_background(libtcodpy.blue)
                elif not random.randint(0, 5):
                    ptest.set_default_background(libtcodpy.yellow)
                else:
                    ptest.set_default_background(libtcodpy.black)
            else:
                ptest.write(x, y, '#')
                if not random.randint(0, 3):
                    ptest.set_default_foreground(libtcodpy.red)
                elif not random.randint(0, 3):
                    ptest.set_default_foreground(libtcodpy.blue)
                elif not random.randint(0, 3):
                    ptest.set_default_foreground(libtcodpy.yellow)
                else:
                    ptest.set_default_foreground(libtcodpy.white)
    ptest.blit(ffade=fade)
    pshade.x += 1
    if pshade.x > 10:
        pshade.x = 0
    pshade.y += 1
    if pshade.y > 10:
        pshade.y = 0
    # pshade.blit(bfade=fade)
    fade += .1
    if fade > .9:
        fade = .1
    test.flush
    libtcodpy.console_wait_for_keypress(False)
