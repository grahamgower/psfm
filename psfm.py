#!/usr/bin/env python3

# Play Some Fucking Music, using XMMS2.
#
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

import os
import sys
import urllib.parse
from collections import OrderedDict

from tkinter import *
from tkinter import ttk

import xmmsclient
import xmmsclient.collections as xcoll

import tkconnector
from notebookx import NotebookX


XMMS_PATH = os.getenv("XMMS_PATH")
SOURCE_PREFS = ["server", "plugin/id3v2", "*"]
PSFM_COLUMNS = ('artist', 'album', 'tracknr', 'title', 'duration', 'song_id')
PSFM_DISP_COLUMNS = PSFM_COLUMNS[0:-1]

def mapvals(minfo):
    def ms2str(ms):
        secs = (ms//1000)%60
        mins = ms//(60*1000)
        hrs = ms//(3600*1000)
        tm = []
        if hrs:
            tm.append(str(hrs))
        tm.append(str(mins))
        tm.append("{:02}".format(secs))
        return ":".join(tm)

    for x in PSFM_COLUMNS:
        val = minfo.get(x, None)
        if x == 'title' and (val == None or val == ""):
            # Make up the title from the filename.
            url = minfo.get("url", "")
            title = os.path.basename(url)
            try:
                if title[-4] == ".":
                    title = title[:-4]
            except IndexError:
                pass
            title = urllib.parse.unquote_plus(title)
            title = title.replace("_", " ")
            yield title
        elif x == 'duration' and (val != None and val != ""):
            yield ms2str(val)
        else:
            yield "" if val is None else val

class SongList(ttk.Frame):
    """
    A ttk.TreeView that displays a list of songs (playlist or collection).
    """
    def __init__(self, parent, psfm, collname="Default", collection=None, is_searchlist=False):
        ttk.Frame.__init__(self, parent)
        self.grid(column=0, row=1, sticky=(N, S, E, W))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.psfm = psfm
        self.xmms = psfm.xmms
        self.collname = collname
        self.coll = collection
        self.is_searchlist = is_searchlist
        self.is_playlist = collection == None
        if self.is_playlist:
            self.namespace = "Playlists"
        else:
            self.namespace = "Collections"

        self.build_songlist()
        self.populate()


    def build_songlist(self):
        songlist = ttk.Treeview(self, columns=PSFM_COLUMNS,
                displaycolumns=PSFM_DISP_COLUMNS)
        sb = ttk.Scrollbar(self, orient=VERTICAL, command=songlist.yview)
        songlist['yscrollcommand'] = sb.set
        songlist.grid(column=0, row=0, sticky=(N, S, E, W))
        sb.grid(column=1, row=0, sticky=(N, S))

        songlist.column('#0', width=75, anchor=E, stretch=False)
        songlist.column('artist', width=200, anchor=W, stretch=False)
        songlist.heading('artist', text='Artist')
        songlist.column('album', width=200, anchor=W, stretch=False)
        songlist.heading('album', text='Album')
        songlist.column('tracknr', width=50, anchor=E, stretch=False)
        songlist.heading('tracknr', text='Track')
        songlist.column('title', width=500, anchor=W, stretch=True)
        songlist.heading('title', text='Title')
        songlist.column('duration', width=100, anchor='center', stretch=False)
        songlist.heading('duration', text='Time')

        songlist.bind("<Double-Button-1>", self.jump_to_song)

        songlist.tag_configure("current", background="yellow")
        self.current_song = None

        self.songlist = songlist

    def new_search(self, newcoll):
        if not self.is_searchlist:
            raise Exception("trying to do a search on a playlist/collection")

        self.coll = newcoll

        self.build_songlist()
        self.populate()


    def populate(self, newcoll=None):
        """
        Add all the songs to the treeview.
        """

        def update_song_info(res):
            if res.iserror():
                raise Exception(res.value())

            minfos = res.value()
            if len(minfos) == 0:
                return 

            if self.is_searchlist:
                # TODO: figure out why xmms doesn't send this in ASC order
                minfos = reversed(minfos)

            for pid, minfo in enumerate(minfos, 1):
                vals = list(mapvals(minfo))
                mid = minfo.get("song_id")
                self.mid2pid[mid] = pid
                self.songlist.item(pid, values=vals)

        def create_songlist_entries(res):
            if res.iserror():
                raise Exception(res.value())

            for pid in range(1, res.value()+1):
                self.songlist.insert('', 'end', iid=pid, text=pid)

            if self.is_playlist:
                self.after_idle(self.home)

            get_song_info()

        def get_song_info():
            fetch = {"type": "cluster-list",
                    "cluster-by": "id" if self.is_searchlist else "position",
                    "source-preference": SOURCE_PREFS,
                    "data": {
                        "type": "metadata",
                        "get": ["field", "value"],
                        "fields": ["artist", "album", "tracknr", "title", "duration", "url", "id"],
                        }
                    }
            self.xmms.coll_query(self.coll, fetch, update_song_info)

        if self.coll is None:
            res = self.xmms.coll_get(self.collname, self.namespace)
            res.wait()
            self.coll = res.value()

        self.mid2pid = {}

        # populate songlist
        self.xmms.coll_query(self.coll, {"type": "count"}, create_songlist_entries)

    def home(self):
        """
        Move the scrollbar to show the current song.
        """

        if not self.is_playlist:
            # collections don't have a current song
            return

        def set_ypos(res):
            if res.iserror():
                raise Exception(res.value())

            value = res.value()
            name = value["name"]
            if name != self.collname:
                return
            pos = value["position"]
            self.songlist.yview(pos)
            self.highlight_song(pos+1)

        self.xmms.playlist_current_pos(self.collname, set_ypos)

    def jump_to_song(self, event):
        tid = int(self.songlist.focus()) # Treeview id of highlighted song
        if self.is_searchlist:
            values = self.songlist.item(tid, "values")
            mid = int(values[-1])
            self.psfm.play_mid(mid)
        else:
            self.xmms.playlist_set_next(tid-1).wait()
            self.xmms.playback_tickle().wait()
            self.psfm.play()

    def jump_to_mid(self, mid):
        pid = self.mid2pid[mid]-1
        self.xmms.playlist_set_next(pid).wait()
        self.xmms.playback_tickle().wait()
        self.psfm.play()

    def highlight_song(self, pos):
        if self.current_song != None:
            self.songlist.item(self.current_song, tags=())

        if pos > 0:
            self.songlist.item(pos, tags=("current"))
            self.current_song = pos
        else:
            self.current_song = None

class PSFM():
    def __init__(self):
        root = Tk()
        root.title("Play Some Fucking Music")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.root = root

        mainframe = ttk.Frame(root)
        mainframe.grid(column=0, row=0, sticky=(N, S, E, W))
        self.mainframe = mainframe

        topframe = ttk.Frame(mainframe)
        topframe.grid(column=0, row=0, sticky=(E, W))
        self.topframe = topframe

        notebook = NotebookX(mainframe)
        notebook.grid(column=0, row=1, sticky=(N, S, E, W))
        notebook.bind("<<NotebookClosedTab>>", self.closed_tab)
        self.notebook = notebook

        self.build_topframe()
        self.build_statusbar()

        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(1, weight=1)

        self.xmms = xmmsclient.XMMS("PSFM")
        try:
            self.xmms.connect(XMMS_PATH)
        except IOError as e:
            print("Failed to connect: {}".format(e))
            sys.exit(1)

        self.connector = tkconnector.TkConnector(self.root, self.xmms)

        self.current_songlist = SongList(notebook, self)
        self.songlists = OrderedDict({"Default": self.current_songlist})
        notebook.add(self.current_songlist, text="Default")

        self.xmms.broadcast_playlist_current_pos(self.update_playlist_current_pos)
        self.xmms.playback_current_id(self.update_current_song)


    def build_topframe(self):
        controls = [
                ("home", self.home),
                ("-", None),
                ("prev", self.set_prev),
                ("next", self.set_next),
                ("-", None),
                ("play", self.play),
                ("pause", self.pause),
                ("stop", self.stop),
                ("-", None),
                ]

        padx = pady = 5

        i = 0
        for txt, cmd in controls:
            if txt == "-":
                s = ttk.Separator(self.topframe, orient=VERTICAL)
                s.grid(column=i, row=0, sticky=(N, S), padx=padx, pady=pady)
            else:
                b = ttk.Button(self.topframe, text=txt, command=cmd)
                b.grid(column=i, row=0, sticky=W, padx=padx, pady=pady)
            i += 1

        l = ttk.Label(self.topframe, text="search:")
        l.grid(column=i, row=0, sticky=E, padx=padx, pady=pady)
        i += 1

        self.searchbox = StringVar("")
        e = ttk.Entry(self.topframe, width=50, textvariable=self.searchbox)
        e.grid(column=i, row=0, sticky=E, padx=padx, pady=pady)
        e.bind("<KeyPress-Return>", self.search)
        e.bind("<KeyPress-KP_Enter>", self.search)
        e.focus_set()

    def build_statusbar(self):
        self.status = StringVar("")
        sb = ttk.Label(self.mainframe, textvariable=self.status,
                borderwidth=1, relief='sunken')
        sb.grid(column=0, row=2, sticky=(E, W))


    def update_song_descr(self, vals):
        v = [str(s) for s in vals[0:4] if s != ""]
        self.status.set(" - ".join(v))

    def update_current_song(self, res):
        mid = res.value()
        if mid == 0:
            # nothing is playing
            return

        def cb_medialib_get_info(res):
            if res.iserror():
                raise Except(res.value())
            minfo = res.value()
            minfo.sources = SOURCE_PREFS
            vals = list(mapvals(minfo))
            self.update_song_descr(vals)

        self.xmms.medialib_get_info(mid, cb_medialib_get_info)

    def update_playlist_current_pos(self, res):
        if res.iserror():
            raise Except(res.value())

        value = res.value()
        name = value["name"]
        try:
            sl = self.songlists[name]
        except KeyError:
            # that playlist isn't loaded
            return

        pos = value["position"]+1
        song_vals = sl.songlist.item(pos, "values")
        if len(song_vals) == len(sl.songlist["columns"]):
            self.update_song_descr(song_vals)
#        else:
#            print("current song not loaded in list")

        sl.highlight_song(pos)

    def play_mid(self, mid):
        sl = self.current_songlist
        sl.jump_to_mid(mid)

    def play(self):
        self.xmms.playback_start().wait()
        self.xmms.playback_current_id(self.update_current_song)

    def pause(self):
        self.xmms.playback_pause().wait()

    def stop(self):
        self.xmms.playback_stop().wait()

    def set_prev(self):
        self.xmms.playlist_set_next_rel(-1).wait()
        self.xmms.playback_tickle().wait()

    def set_next(self):
        self.xmms.playlist_set_next_rel(1).wait()
        self.xmms.playback_tickle().wait()

    def home(self):
        self.current_songlist.home()

    def search(self, event):
        query = self.searchbox.get()
        if query == "":
            return

        try:
            coll = xcoll.coll_parse(query)
        except ValueError as e:
            return

        sl = self.songlists.get("search", None)
        if sl is not None:
            sl.new_search(coll)
        else:
            sl = SongList(self.notebook, self, collection=coll, is_searchlist=True)
            self.songlists["search"] = sl
            tabid = self.notebook.index('end')
            self.notebook.insert('end', sl, text="search")
            self.notebook.select(tabid)

    def closed_tab(self, e):
        index = e.widget.index("@{},{}".format(e.x, e.y))

        if index == 0:
            # don't close the Default playlist
            return

        sl_name = list(self.songlists)[index]
        del self.songlists[sl_name]

        self.notebook.forget(index)


if __name__ == "__main__":
    app = PSFM()
#    app.root.attributes('-zoomed', True)
    app.root.mainloop()
