#!/usr/bin/python
#
# Created by Michael Mandel <mim@mr-pc.org>
# Based on the seeqpod resolver by:
# Max Howell <max@methylblue.com> twitter.com/mxcl
# Licensed the same as Playdar

########################################################################
import sys
import simplejson as json
import urllib
import socket
from struct import unpack, pack

# Redirect stdout to stderr when starting pylab stuff so that error
# messages don't get mixed into the stream and mess it up.
stdout = sys.stdout
sys.stdout = sys.stderr

from model import Artist, Track
from gordon_db import get_full_mp3filename
import dse_difflib  as DL

# Restore stdout
sys.stdout = stdout

# Gordon resolver

matcher = DL.SequenceMatcher()

def resolve(artist_name, track_name):
    results = []
    matches = Artist.query.filter("(lower(artist.name) ~ ('%s'))" 
                                  % artist_name.lower())
    a_scores = [(a, fuzzy_match(artist_name, a.name)) for a in matches]
    a_scores = [(a, score) for a, score in a_scores if score > 0.6]
    results = []
    for artist, a_score in a_scores:
        t_scores = [(tr, fuzzy_match(track_name, tr.title)) 
                    for tr in artist.tracks]
        results.extend([track2dict(artist, tr, sc*a_score)
                        for tr, sc in t_scores if sc > 0.6])
    return results

def track2dict(artist, track, score):
    return {'artist': artist.name,
            'track': track.title,
            'album': track.album,
            'url': 'file://' + get_full_mp3filename(track.id),
            'duration': int(track.secs),
            'source': 'gordon',
            'score': score}

def fuzzy_match(query, match):
    matcher.set_seqs(query, match)
    return matcher.ratio()
#     # Try to determine if there is a match in order of fastest to
#     # slowest functions
#     for ratio in [matcher.real_quick_ratio, matcher.quick_ratio]:
#         r = ratio()
#         if r > 0.6: return r
#     return matcher.ratio()
   
###################################################################### functions
def print_json(o):
    s = json.dumps(o)
    sys.stdout.write(pack('!L', len(s)))
    sys.stdout.write(s)
    sys.stdout.flush()

def percent_encode(url):
    # Ha! Yeah, needs work
    return url.replace(' ', '%20')


def test():
    print "TESTING!!!"
    for t in resolve(u"weezer", u"buddy holly"):
        print t

def main():
    #test()
    ################################################################### settings
    print_json( {"_msgtype": "settings",
                 "name": "Gordon Resolver",
                 "targettime": 5000,      # millseconds
                 "weight": 75,            # Gordon results are pretty good
                 } )

    ################################################################## main loop
    while 1:
        length = sys.stdin.read(4)

        if not length:
            break;

        length = unpack('!L', length)[0]
        if not length:
            break
        # something probably went wrong, most likely we're out of sync
        # and are reading the 4 bytes length header in the middle of a
        # json string. We can't recover. Bail.
        if length > 4096 or length < 0:
            break
        if length > 0:
            msg = sys.stdin.read(length)
            try:
                request = json.loads(msg)
                # print request
                tracks = resolve(request['artist'], request['track'])
                if len(tracks) > 0:
                    response = { 'qid':request['qid'], 
                                 'results':tracks, 
                                 '_msgtype':'results' }
                    print_json(response)
            except:
                # safe to continue, skipping this msg, because at least
                # we consumed enough input so next iteration hits size header.
                pass

if __name__ == '__main__':
    main()
