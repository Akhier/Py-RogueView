import libtcodpy


class Panel:

    def __init__(self, x, y, panelwidth, panelheight,
                 foreground=libtcodpy.white, background=libtcodpy.black,
                 border=False):
        self.x = x
        self.y = y
        self.panelwidth = panelwidth
        self.panelheight = panelheight
        self._panel = libtcodpy.console_new(self.panelwidth,
                                            self.panelheight)
        libtcodpy.console_set_default_foreground(self._panel, foreground)
        libtcodpy.console_set_default_background(self._panel, background)
        self.border = border
        if self.border:
            libtcodpy.console_print_frame(self._panel, 0, 0, panelwidth,
                                          panelheight)

    @property
    def clear(self):
        libtcodpy.console_clear(self._panel)
        if self.border:
            libtcodpy.console_print_frame(self._panel, 0, 0,
                                          self.panelwidth, self.panelheight)

    @property
    def x2(self):
        return self.x + self.panelwidth - 1

    @property
    def y2(self):
        return self.y + self.panelheight - 1

    def blit(self, x=0, y=0, w=False, h=False, dst=0,
             xdst=False, ydst=False, ffade=1.0, bfade=1.0):
        if not xdst:
            xdst = self.x
        if not ydst:
            ydst = self.y
        if not w:
            w = self.panelwidth
        if not h:
            h = self.panelheight
        libtcodpy.console_blit(self._panel, x, y, w, h, dst, xdst,
                               ydst, ffade, bfade)

    @property
    def body(self):
        return self._panel

    def set_default_foreground(self, fore):
        libtcodpy.console_set_default_foreground(self._panel, fore)

    def set_default_background(self, back):
        libtcodpy.console_set_default_background(self._panel, back)

    def write(self, x, y, txt, flag=libtcodpy.BKGND_NONE,
              align=libtcodpy.LEFT):
        libtcodpy.console_print_ex(self._panel, x, y, flag,
                                   align, txt)

    def write_ex(self, x, y, txt, fore, back):
        self.set_default_foreground(fore)
        self.set_default_background(back)
        self.write(x, y, txt)

    def write_wrap(self, x, y, w, h, txt):
        libtcodpy.console_print_rect(self._panel, x, y, w, h, txt)

    def write_wrap_ex(self, x, y, w, h, txt, align, flag=libtcodpy.BKGND_NONE):
        libtcodpy.console_print_rect_ex(self._panel, x, y, w, h,
                                        flag, align, txt)

    def rect(self, x, y, w, h, clear, flag=libtcodpy.BKGND_DEFAULT):
        libtcodpy.console_print_frame(self._panel, x, y, w, h, clear, flag)

    def color_rect(self, x, y, w, h, clear, flag=libtcodpy.BKGND_DEFAULT):
        libtcodpy.console_rect(0, x, y, w, h, clear, flag)

    def inside(self, X, Y):
        if X >= self.x and X <= self.x2 and Y >= self.y and Y <= self.y2:
            return True
        else:
            return False
