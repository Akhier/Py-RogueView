import libtcodpy


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

    def set_title(self, title):
        libtcodpy.console_set_window_title(title)

    def set_fps(self, fps):
        libtcodpy.sys_set_fps(fps)

    def set_font(self, font, fontflags):
        libtcodpy.console_set_custom_font(font, fontflags)

    def blit(self, src, x=0, y=0, w=False, h=False, xdst=0,
             ydst=0, ffade=1.0, bfade=1.0):
        if not w:
            w = self.screenwidth
        if not h:
            h = self.screenheight
        libtcodpy.console_blit(src, x, y, w, h, 0, xdst, ydst, ffade, bfade)

    @property
    def flush(self):
        libtcodpy.console_flush()

    @property
    def is_window_closed(self):
        return libtcodpy.console_is_window_closed()

    @property
    def clear(self):
        libtcodpy.console_clear(0)

    @property
    def x2(self):
        return self.x + self.panelwidth - 1

    @property
    def y2(self):
        return self.y + self.panelheight - 1

    def set_default_foreground(self, fore):
        libtcodpy.console_set_default_foreground(0, fore)

    def set_default_background(self, back):
        libtcodpy.console_set_default_background(0, back)

    def write(self, x, y, txt, flag=libtcodpy.BKGND_NONE,
              align=libtcodpy.LEFT):
        libtcodpy.console_print_ex(0, x, y, flag, align, txt)

    def write_ex(self, x, y, txt, fore, back):
        self.set_default_foreground(fore)
        self.set_default_background(back)
        self.write(x, y, txt)

    def write_wrap(self, x, y, w, h, txt):
        libtcodpy.console_print_rect(0, x, y, w, h, txt)

    def write_wrap_ex(self, x, y, w, h, txt, align, flag=libtcodpy.BKGND_NONE):
        libtcodpy.console_print_rect_ex(0, x, y, w, h, flag, align, txt)

    def rect(self, x, y, w, h, clear, flag=libtcodpy.BKGND_DEFAULT):
        libtcodpy.console_print_frame(0, x, y, w, h, clear, flag)

    def color_rect(self, x, y, w, h, clear, flag=libtcodpy.BKGND_DEFAULT):
        libtcodpy.console_rect(0, x, y, w, h, clear, flag)
