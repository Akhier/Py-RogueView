import libtcodpy
from Panel import Panel


class Console:

    def __init__(self, screenwidth, screenheight,
                 title, font='terminal12x12_gs_ro.png',
                 fontflags=(libtcodpy.FONT_TYPE_GREYSCALE |
                            libtcodpy.FONT_LAYOUT_ASCII_INROW),
                 fullscreen=False, fps=60):
        self.screenwidth = screenwidth
        self.screenheight = screenheight
        self.set_font(font, fontflags)
        self.set_fps(fps)
        libtcodpy.console_init_root(screenwidth, screenheight,
                                    title, fullscreen)
        self.root_panel = Panel(0, 0, screenwidth, screenheight)

    def set_title(self, title):
        libtcodpy.console_set_window_title(title)

    def set_fps(self, fps):
        libtcodpy.sys_set_fps(fps)

    def set_font(self, font, fontflags):
        libtcodpy.console_set_custom_font(font, fontflags)

    @property
    def flush(self):
        libtcodpy.console_flush()

    @property
    def blit(self):
        self.root_panel.blit
        libtcodpy.console_blit(self.root_panel.body, 0, 0, self.screenwidth,
                               self.screenheight, 0, 0, 0)

    @property
    def is_window_closed(self):
        return libtcodpy.console_is_window_closed()
