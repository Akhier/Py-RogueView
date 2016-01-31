import libtcodpy


class Panel:

    def __init__(self, x, y, panelwidth, panelheight,
                 foreground=libtcodpy.white, background=libtcodpy.black,
                 border=False):
        self.x = x
        self.y = y
        self.panelwidth = panelwidth
        self.panelheight = panelheight
        self.children = []
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
    def blit(self):
        if self.children:
            for child in self.children:
                child.blit
                libtcodpy.console_blit(child.body, 0, 0, child.panelwidth,
                                       child.panelheight, self._panel,
                                       child.x, child.y)

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

    def add_child(self, panel):
        self.children.append(panel)
