#!/usr/bin/python

# Copyright (C) 2010 Michael Mandel
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

"""Basic script to search playdar for a track and get the url."""

import sys
import simplejson as json
import urllib
import time

base_url = 'http://localhost:60210'
wait_time = 2

def main():
    artist, track = sys.argv[1:3]
    # '/api/?method=resolve&artist=weezer&track=buddy%20holly'
    res = get_json("%s/api" % base_url, 
                   {"artist":artist, "track":track, "method":"resolve"})
    qid = res["qid"]

    # Wait a little for results
    time.sleep(wait_time)

    # '/api/?method=get_results&qid=386C50C9-9F9E-4633-B9AE-33EB41E31312'
    res = get_json("%s/api" % base_url, {"method":"get_results","qid":qid})
    
    if len(res["results"]) > 0:
        print res["results"][0]
        sid = res["results"][0]["sid"]

        # '/sid/E042363C-075C-43AA-8BC2-CC3C18CA0008'
        print "%s/sid/%s" % (base_url, sid)

    
def get_json(url, params):
    """Make a request at a url with a dictionary of parameters.  

    Return a dictionary parsed from a json response.
    """
    p_enc = urllib.urlencode(params)
    full_url = '%s/?%s' % (url, p_enc)
    print full_url
    f = urllib.urlopen(full_url)
    return json.loads(f.read())


if __name__=='__main__':
    main()
