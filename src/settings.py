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

"""Class to retrieve settings for the user."""

from pathlib import Path
from typing import List

import yaml

from feed import Feed

class Settings:

    """An object to contain user settings."""

    def __init__(self, feeds: List[Feed]):
        self.feeds = feeds

        # Hashes
        self.feed_hashes = {}
        self.story_hashes = {}

    @classmethod
    def load_from_filesystem(cls) -> "Settings":
        """Load the settings from the file system."""
        directory = Path("settings")
        if not directory.exists():
            directory.mkdir()

        feed_file = directory / "feeds.yml"
        if not feed_file.exists():
            feed_file.touch()

        with feed_file.open("r", encoding="utf-8") as file:
            content = file.read()

        loaded_feeds = yaml.safe_load(content)
        settings = cls([])
        feeds = []
        if isinstance(loaded_feeds, list):
            for feed_def in loaded_feeds:
                title = feed_def.get("title", "unknown")
                description = feed_def.get("description", "unknown")
                link = feed_def.get("link", "unknown")
                hash = feed_def.get("hash", "unknown")
                feeds.append(Feed(settings, title, description, link, hash))

        settings.feeds = feeds
        return settings

    def save(self):
        """Save the setting file."""
        directory = Path("settings")
        if not directory.exists():
            directory.mkdir()

        feed_file = directory / "feeds.yml"
        feeds = [{
                "title": feed.title,
                "description": feed.description,
                "link": feed.link,
                "hash": feed.hash,
                } for feed in self.feeds]

        with feed_file.open("w", encoding="utf-8") as file:
            file.write(yaml.dump(feeds, sort_keys=False,
                    allow_unicode=True))
