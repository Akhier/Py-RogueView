import libtcodpy


class Panel:

    def __init__(self, x, y, panelwidth, panelheight,
                 foreground=libtcodpy.white, border=False):
        self.x = x
        self.y = y
        self.panelwidth = panelwidth
        self.panelheight = panelheight
        self.children = []
        self._panel = libtcodpy.console_new(self.panelwidth,
                                            self.panelheight)
        libtcodpy.console_set_default_foreground(self._panel, foreground)
        self.border = border
        if self.border:
            libtcodpy.console_print_frame(self._panel, 0, 0, panelwidth,
                                          panelheight)

    @property
    def clear(self):
        self._panel.clear()
        if self.border:
            libtcodpy.console_print_frame(self._panel, 0, 0,
                                          self.panelwidth, self.panelheight)

    def write(self, x, y, txt):
        libtcodpy.console_print_ex(self._panel, x, y, libtcodpy.BKGND_NONE,
                                   libtcodpy.LEFT, txt)

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

    def add_child(self, panel):
        self.children.append(panel)
