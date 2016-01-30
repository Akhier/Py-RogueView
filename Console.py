import libtcodpy
from Panel import Panel


class Console:

    def __init__(self, screenwidth, screenheight,
                 title, font='terminal12x12_gs_ro.png',
                 fontflags=(libtcodpy.FONT_TYPE_GREYSCALE |
                            libtcodpy.FONT_LAYOUT_ASCII_INROW),
                 fullscreen=False):
        self.screenwidth = screenwidth
        self.screenheight = screenheight
        libtcodpy.console_set_custom_font(font, fontflags)
        libtcodpy.console_init_root(screenwidth, screenheight,
                                    title, fullscreen)
        self.root_panel = Panel(0, 0, screenwidth, screenheight)

    def set_title(self, title):
        libtcodpy.console_set_window_title(title)

    @property
    def flush(self):
        self.root_panel.blit
        libtcodpy.console_flush()

    @property
    def is_window_closed(self):
        return libtcodpy.console_is_window_closed()
