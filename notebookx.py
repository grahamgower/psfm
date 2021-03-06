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

try:
    # python 3.x
    from tkinter import PhotoImage, ttk
except ImportError:
    # python 2.x
    from Tkinter import PhotoImage
    import ttk

# 12x12 gifs, base64 encoded.
img_data = [
"""
R0lGODlhDAAMAIABAAAAAP8AACH5BAEKAAEALAAAAAAMAAwAAAIXjI+pCYD9YGgu0sromlpdeXSd
AXLbeRYAOw==
""",
"""
R0lGODlhDAAMAKEAAP8AAP////8AAP8AACH5BAEKAAIALAAAAAAMAAwAAAIXhI+pGYH9IGgu0sro
mlpdeXSdAXLbeRYAOw==
""",
]

class NotebookX(ttk.Notebook):
    """
    ttk.Notebook with close buttons on the tabs, to resemble firefox.

    See http://paste.tclers.tk/896
    """

    def __init__(self, *args, **kwargs):

        # Careful not to let images get garbage collected;
        # they just become invisible with no error.
        self.im0 = PhotoImage("img_x", data=img_data[0])
        self.im1 = PhotoImage("img_x_red", data=img_data[1])

        style = ttk.Style()

        style.element_create("close", "image", "img_x",
            ("active", "alternate", "!disabled", "img_x_red"),
            border=10, sticky='')

        style.layout("NotebookX", [("NotebookX.client", {"sticky": "nswe"})])
        style.layout("NotebookX.Tab",
            [("NotebookX.tab", {"sticky": "nswe", "children":
                [("NotebookX.padding", {"side": "top", "sticky": "nswe",
                    "children":
                    [("NotebookX.focus", {"side": "top", "sticky": "nswe",
                        "children":
                        [("NotebookX.label", {"side": "left", "sticky": ''}),
                         ("NotebookX.close", {"side": "left", "sticky": ''})]
                    })]
                })]
            })]
        )

        ttk.Notebook.__init__(self, *args, style="NotebookX", **kwargs)
        self.bind("<ButtonPress-1>", self.button_press)
        self.bind("<Motion>", self.motion)

    def button_press(self, e):
        ident = e.widget.identify(e.x, e.y)
        if ident.endswith("close"):
            e.widget.event_generate("<<NotebookClosedTab>>", x=e.x, y=e.y)

    def motion(self, e):
        ident = e.widget.identify(e.x, e.y)
        if ident.endswith("close"):
            e.widget.state(["alternate"])
        else:
            e.widget.state(["!alternate"])

