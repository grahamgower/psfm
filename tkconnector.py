# Copyright (c) 2014 Graham Gower <graham.gower@gmail.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from tkinter import READABLE, WRITABLE

class TkConnector:
    """XMMS2 event handling connector for Tk."""

    def __init__(self, tk, xmms):
        self.tk = tk
        self.xmms = xmms
        self.fd = xmms.get_fd()

        self.xmms.set_need_out_fun(self.need_out)
        self.tk.createfilehandler(self.fd, READABLE, self.handler)


    def need_out(self, unused):
        if self.xmms.want_ioout():
            self.tk.createfilehandler(self.fd, READABLE|WRITABLE, self.handler)
        else:
            self.tk.createfilehandler(self.fd, READABLE, self.handler)

    def handler(self, fd, rd_wr):
        if rd_wr&READABLE:
            return self.xmms.ioin()

        if rd_wr&WRITABLE:
            self.xmms.ioout()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.tk.deletefilehandler(self.fd)


if __name__ == "__main__":
    import os
    import sys
    import xmmsclient
    import tkinter

    xmms = xmmsclient.XMMS("TkConnector")
    try:
        xmms.connect(os.getenv("XMMS_PATH"))
    except IOerror as err:
        print("Connection failed:", err)
        sys.exit(1)

    root = tkinter.Tk()

    def print_mid(res):
        print("mid =", res.value())
        root.quit()

    TkConnector(root, xmms)
    xmms.playback_current_id(print_mid)
    root.mainloop()
