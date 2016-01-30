import libtcodpy
from Console import Console
from Panel import Panel


if __name__ == '__main__':
    test = Console(20, 20, 'test')
    testpanel = Panel(5, 5, 10, 10, border=True)
    test.root_panel.add_child(testpanel)
    while not test.is_window_closed:
        test.flush
        libtcodpy.console_wait_for_keypress(True)
