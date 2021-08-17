# Copyright (c) 2021, LE GOFF Vincent
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""Main window of Campi, using the Blind User Interface.."""

import aiohttp
from bui import Window, start

from campi.feed import Feed
from campi.settings import Settings

class MainWindow(Window):

    """Campi's main window."""

    def on_init_stories(self):
        self.session = aiohttp.ClientSession()

    async def on_init_feeds(self, widget):
        """Attempt to load the list of feeds from the user settings and display it."""
        self.settings = Settings.load_from_filesystem()

        # Add rows in the feeds table accordingly.
        for feed in self.settings.feeds:
            self.add_feed(feed)

        widget.selected = 0

    async def on_select_feeds(self, widget):
        """The selection has changed in the feeds table."""
        row = widget.selected
        feed = self.settings.feed_hashes[row.hash]

        # If the feed isn't fully loaded from filesystem yet, do it now.
        if not feed.loaded:
            await feed.load_stories_from_filesystem()

        await feed.load_stories_from_link(self.session)
        self.update_stories(feed)
        row.title = f"{feed.title} ({feed.unread})"

    async def on_add_feed(self, widget):
        dialog = await self.pop_dialog("""
                <dialog title="Add a new feed">
                  <text x=2 y=2 id=link>Enter the feed's link (URL):</text>
                  <button x=1 y=5 set_true>Add</button>
                  <button x=4 y=5 set_false>Cancel</button>
                </dialog>
        """)
        if dialog:
            link = dialog["link"].value

            # Test the link.
            feed = await Feed.test_feed(self.session, self.settings, link)
            if feed:
                self.settings.save()
                self.add_feed(feed, select=True)
            else:
                await self.pop_alert("Invalid link",
                        f"The specified link ({link}) doesn't seem to "
                        "lead to a valid RSS feed.")

    def add_feed(self, feed: "Feed", select: bool = False):
        """Add a new feed, select the new row if select is True."""
        table = self["feeds"]
        table.add_row(f"{feed.title} ({feed.unread})", feed.description, feed.hash)
        if select:
            table.selected = table.rows[-1]

    def update_stories(self, feed: "Feed"):
        """Update the stories for the specified feed."""
        table = self["stories"]
        table.rows = [
                (f"{story.status_text} {story.title}", story.ago, story.category, story.hash)
                for story in feed.stories
        ]

    async def on_press_return_in_stories(self, widget):
        """The user pressed RETURN on a story."""
        row = widget.selected
        story = self.settings.story_hashes[row.hash]
        await story.open_in_browser()
        row.title = f"{story.status_text} {story.title}"

    async def on_press_left_in_stories(self, widget):
        """The user presses CTRL + = on the list of stories."""
        row = widget.selected
        story = self.settings.story_hashes[row.hash]
        await story.decrease_note()
        row.title = f"{story.status_text} {story.title}"
        self["feeds"].selected.title = f"{story.feed.title} ({story.feed.unread})"

    async def on_press_right_in_stories(self, widget):
        """The user presses right arrow on the list of stories."""
        row = widget.selected
        story = self.settings.story_hashes[row.hash]
        await story.increase_note()
        row.title = f"{story.status_text} {story.title}"
        self["feeds"].selected.title = f"{story.feed.title} ({story.feed.unread})"


def run():
    """Start the BUI server."""
    start(MainWindow)

if __name__ == "__main__":
    run()
