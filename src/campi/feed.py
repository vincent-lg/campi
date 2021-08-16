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

"""Class to retrieve a feed object."""

from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

import aiofiles
import aiohttp
from aiohttp import ClientSession
import dateutil.parser
from defusedxml.ElementTree import fromstring, ParseError
import yaml

from campi.story import Story

class Feed:

    """A feed with a unique hash."""

    def __init__(self, settings: "Settings", title: str,
            description: str, link: str, hash: Optional[str] = None):
        self.settings = settings
        self.title = title
        self.description = description
        self.link = link
        self.stories = []
        self.loaded = False

        if hash is None: # Determine the hash for this feed.
            while (new_hash := str(uuid4())) in settings.feed_hashes:
                # This loop shouldn't run too long in theory, uuid4()
                # has a very high chance of returning a new hash that
                # is not used by any other feed.
                continue
            hash = new_hash
        self.hash = hash
        settings.feed_hashes[hash] = self

    def __repr__(self):
        return f"<Feed {self.title} ({self.link}, hash={self.hash})"

    @property
    def unread(self) -> int:
        """Return the number of unread stories."""
        return len([story for story in self.stories if story.unread])

    async def load_stories_from_filesystem(self):
        """Load the list of stories from the file system and populate the list of stories."""
        feed_file = self.settings.directory / f"feed_{self.hash}.yml"
        if not feed_file.exists():
            feed_file.touch()

        async with aiofiles.open(str(feed_file), "r", encoding="utf-8") as file:
            content = await file.read()

        loaded_stories = yaml.safe_load(content)
        stories = []

        if isinstance(loaded_stories, list):
            for story_def in loaded_stories:
                title = story_def.get("title", "unknown")
                published = story_def.get("published", "unknown")
                category = story_def.get("category", "unknown")
                link = story_def.get("link", "")
                unread = story_def.get("unread", True)
                note = story_def.get("note", "0")
                hash = story_def.get("hash", "unknown")
                self.add_story_if_needed(title, published, category, link, unread, note, hash)

        self.loaded = True

    async def load_stories_from_link(self,
            session: Optional[ClientSession] = None):
        """Attempt to load the stories from the provided link."""
        session = session or aiohttp.ClientSession()

        async with session.get(self.link) as response:
            if response.status == 200: # No problem has occurred.
                text = await response.text()

                # Read the XML entry.
                try:
                    parsed = fromstring(text)
                except ParseError:
                    pass
                else:
                    await self.update_from_XML(parsed)

        await self.save()

    async def update_from_XML(self, parsed):
        """Parse a XML tree and try to update this feed."""
        if (titles := list(parsed.iter("title"))):
            # We assume the first title is the feed's.
            self.title = titles[0].text

        if (descriptions := list(parsed.iter("description"))):
            # We assume the first description is the feed's.
            self.description = descriptions[0].text

        # We browse the list of items, creating stories.
        for item in parsed.iter("item"):
            # An item might be a story, we need some additional information.

            # Parse the title.
            if (element := item.find("title")) is not None:
                title = element.text
            else:
                title = "unknown"

            # Parse the publication date.
            if (element := item.find("pubDate")) is not None:
                published = element.text
            elif (element := item.find("submitted")) is not None:
                published = element.text
            else:
                published = datetime.now()

            # Try to convert the date if necessary.
            if isinstance(published, str):
                published = dateutil.parser.parse(published)

            # Parse the category.
            if (element := item.find("category")) is not None:
                category = element.text
            else:
                category = "unknown"

            # Parse the link.
            if (element := item.find("link")) is not None:
                link = element.text
            else:
                link = ""

            self.add_story_if_needed(title, published, category, link)

        await self.save()

    async def save(self):
        """Save the feed on the file system, along with its stories."""
        feed_file = self.settings.directory / f"feed_{self.hash}.yml"
        if not feed_file.exists():
            feed_file.touch()

        stories = [{
                "title": story.title,
                "published": story.published,
                "category": story.category,
                "link": story.link,
                "unread": story.unread,
                "note": story.note,
                "hash": story.hash,
                } for story in self.stories]

        async with aiofiles.open(str(feed_file), "w", encoding="utf-8") as file:
            await file.write(yaml.dump(stories, sort_keys=False,
                    allow_unicode=True))

    def add_story_if_needed(self, title: str, published: datetime,
            category: str, link: str, unread: bool = True, note: int = 0,
            hash: Optional[str] = None):
        """Add a story, if it's not already present."""
        if title.lower() in [st.title.lower() for st in self.stories]:
            return

        if link.lower() in [st.link.lower() for st in self.stories]:
            return

        story = Story(self.settings, self, title, published, category, link, hash)
        story.unread = unread
        story.note = note
        self.stories.append(story)
        self.stories.sort(key=lambda st: st.published, reverse=True)

    @classmethod
    async def test_feed(cls, session: ClientSession, settings: "Settings",
            link: str) -> "Feed":
        """Test a feed and add it if valid."""
        async with session.get(link) as response:
            if response.status == 200: # No problem has occurred.
                text = await response.text()

                # Read the XML entry.
                try:
                    parsed = fromstring(text)
                except ParseError:
                    pass
                else:
                    feed = cls(settings, "unknown", "unknown", link)
                    await feed.update_from_XML(parsed)
                    settings.feeds.append(feed)
                    return feed
