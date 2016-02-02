import libtcodpy
from Console import Console
from Panel import Panel


def handle_keys():
    global working, key, xbox, ybox

    if key.vk == libtcodpy.KEY_UP or key.vk == libtcodpy.KEY_KP8:
        move_cursor(0, -1)
    elif key.vk == libtcodpy.KEY_DOWN or key.vk == libtcodpy.KEY_KP2:
        move_cursor(0, 1)
    elif key.vk == libtcodpy.KEY_LEFT or key.vk == libtcodpy.KEY_KP4:
        move_cursor(-1, 0)
    elif key.vk == libtcodpy.KEY_RIGHT or key.vk == libtcodpy.KEY_KP6:
        move_cursor(1, 0)
    elif key.vk == libtcodpy.KEY_HOME or key.vk == libtcodpy.KEY_KP7:
        move_cursor(-1, -1)
    elif key.vk == libtcodpy.KEY_PAGEUP or key.vk == libtcodpy.KEY_KP9:
        move_cursor(1, -1)
    elif key.vk == libtcodpy.KEY_END or key.vk == libtcodpy.KEY_KP1:
        move_cursor(-1, 1)
    elif key.vk == libtcodpy.KEY_PAGEDOWN or key.vk == libtcodpy.KEY_KP3:
        move_cursor(1, 1)
    elif key.vk == libtcodpy.KEY_BACKSPACE:
        if boxlist:
            boxlist.pop()
        working = False
    elif key.vk == libtcodpy.KEY_ENTER:
        if working:
            working = False
        else:
            working = True
            xbox = cursor.x
            ybox = cursor.y
            boxlist.append(Panel(cursor.x, cursor.y, 1, 1, border=True))
    elif key.vk == libtcodpy.KEY_KP5:
        pass


def move_cursor(x, y):
    if x + cursor.x < 0 or x + cursor.x >= 80:
        x = 0
    if y + cursor.y < 0 or y + cursor.y >= 50:
        y = 0
    cursor.x += x
    cursor.y += y
    if working:
        if cursor.x < xbox:
            px = cursor.x
            pw = xbox - cursor.x + 1
        else:
            px = xbox
            pw = cursor.x - xbox + 1
        if cursor.y < ybox:
            py = cursor.y
            ph = ybox - cursor.y + 1
        else:
            py = ybox
            ph = cursor.y - ybox + 1
        boxlist[-1] = Panel(px, py, pw, ph, border=True)


test = Console(80, 50, 'test')
test3 = Panel(0, 0, 80, 50)
test3.write(0, 0, '1234567891111111111222222222233333333334444444444' +
            '5555555555666666666677777777778')
test3.write(0, 1, '         0123456789012345678901234567890123456789' +
            '0123456789012345678901234567890')
test3.write_wrap(0, 0, 2, 50, '1 2 3 4 5 6 7 8 9 1011121314151617181' +
                 '92021222324252627282930313233343536373839404142434' +
                 '4454647484950')
cursor = Panel(0, 0, 1, 1)
cursor.write(0, 0, '@')
boxlist = []
xbox = 0
ybox = 0
working = False
mouse = libtcodpy.Mouse()
key = libtcodpy.Key()
while not test.is_window_closed:
    libtcodpy.sys_check_for_event(libtcodpy.EVENT_KEY_PRESS |
                                  libtcodpy.EVENT_MOUSE,
                                  key, mouse)
    handle_keys()
    test.clear
    test3.blit()
    for p in boxlist:
        p.blit()
    cursor.blit()
    test.flush
