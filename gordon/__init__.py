# Copyright (C) 2010 Douglas Eck
#
# This file is part of Gordon.
#
# Gordon is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Gordon is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gordon.  If not, see <http://www.gnu.org/licenses/>.

"""Gordon Music Database

This package gives convenient access to a large music collection via a
simple API based on SQLAlchemy.

Example
-------
>>> tracks = gordon.Track.query.filter_by(artist='The Beatles')
>>> print tracks.count()
>>> x, fs, svals = tracks[0].audio()

See Also
--------
gordon.db.config : database configuration
gordon.db.audio_intake : add new music to the database
gordon.db.mbrainz_resolver : resolve database metadata against MusicBrainz
gordon.web : TurboGears web interface to the database
"""

__version__ = ""

from db import *
