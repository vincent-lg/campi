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

"""Class to retrieve a story object."""

from datetime import datetime, timezone
import os
from typing import Optional
from uuid import uuid4

class Story:

    """A story with a unique hash."""

    def __init__(self, settings: "Settings", feed: "Feed", title: str,
            published: datetime, category: str, link: str,
            hash: Optional[str] = None):
        self.settings = settings
        self.feed = feed
        self.title = title
        self.published = published
        self.link = link
        self.category = category
        self.unread = True
        self.note = 0

        if hash is None: # Determine the hash for this story.
            while (new_hash := str(uuid4())) in settings.story_hashes:
                # This loop shouldn't run too long in theory, uuid4()
                # has a very high chance of returning a new hash that
                # is not used by any other story.
                continue
            hash = new_hash
        self.hash = hash
        settings.story_hashes[hash] = self

    def __repr__(self):
        return f"<Story {self.name} (published {self.ago}, hash={self.hash})"

    @property
    def ago(self) -> str:
        """Return an English version of how long the story was published."""
        utc_dt = datetime.now(timezone.utc)
        now = utc_dt.astimezone()
        try:
            # Try comparing aware times first.
            delta = (now - self.published)
        except TypeError:
            now = datetime.now()
            delta = (now - self.published)

        seconds = delta.total_seconds()
        if seconds < 5:
            return "a few seconds ago"
        elif seconds < 60:
            return "less than a minute ago"
        elif seconds < 60 * 60:
            return f"{int(seconds // 60)} minutes ago"
        elif seconds < 60 * 60 * 24:
            return f"{int(seconds // 60 // 60)} hours ago"
        elif seconds < 60 * 60 * 24 * 2:
            return f"a day ago"
        else:
            return f"{int(seconds // 60 // 60 // 24)} days ago"

    @property
    def note_as_symbol(self) -> str:
        """Return the note as a symbol, 0 or + multiplied."""
        note = self.note
        if note < 0:
            allowed = max(note, -3)
            return '-' * (allowed * -1)
        elif note > 0:
            allowed = min(note, 3)
            return '+' * allowed

        return '0'

    @property
    def status_text(self) -> str:
        """Return the statys as text."""
        if self.unread:
            return "U"

        return self.note_as_symbol

    @property
    def next_unread(self):
        """Return the next unread story in the feed or None."""
        try:
            index = self.feed.stories.index(self)
        except IndexError:
            return

        # Filter unread stories.
        stories = (story for story in self.feed.stories[index + 1:]
                if story.unread)
        return next(stories, None)

    async def open_in_browser(self):
        """Open this story in a browser."""
        os.startfile(self.link)

        if self.unread:
            self.unread = False
            await self.feed.save()

    async def decrease_note(self):
        """Decrease the note."""
        self.unread = False
        if self.note > -2:
            self.note -= 1
            await self.feed.save()

    async def increase_note(self):
        """Increase the note."""
        self.unread = False
        if self.note < 3:
            self.note += 1
            await self.feed.save()
