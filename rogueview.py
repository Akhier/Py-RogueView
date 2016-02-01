import libtcodpy
from Console import Console
from Panel import Panel


if __name__ == '__main__':
    test = Console(20, 20, 'test')
    test1 = Panel(5, 5, 10, 10, border=True)
    test1.write(1, 1, 'test1')
    test2 = Panel(7, 7, 10, 10, border=True, foreground=libtcodpy.yellow)
    test2.write(1, 1, 'test2')
    while not test.is_window_closed:
        test.clear
        test1.blit()
        test2.blit()
        test.flush
        if test2.x < 15:
            test2.x += 1
            test2.y += 1
        else:
            test2.x = -5
            test2.y = -5
        libtcodpy.console_wait_for_keypress(True)
