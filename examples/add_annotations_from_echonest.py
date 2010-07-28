#!/usr/bin/env python 
"""Adds information returned by the Echo Nest analysis as gordon annotations.

This script processes all tracks in the gordon database.

Depends on pyechonest, available from http://code.google.com/p/pyechonest/
"""
import os

import gordon
import pyechonest
import pyechonest.config
import pyechonest.track

pyechonest.config.ECHO_NEST_API_KEY = os.environ['ECHO_NEST_API_KEY']


def process_track(track):
    print 'Processing %s' % track

    entrack = pyechonest.track.track_from_filename(track.fn_audio)
    
    for name in ('sections', 'bars', 'beats'):
        events = getattr(entrack, name)
        htkannotation = echonest_events_to_htk_annotation(events)
        add_annotation(track, 'echonest:%s' % name, htkannotation, 'htk')

    for name in ('analyzer_version', 'id', 'key', 'key_confidence', 'loudness',
                 'tempo', 'tempo_confidence', 'time_signature',
                 'time_signature_confidence'):
        value = getattr(entrack, name)
        add_annotation(track, 'echonest:%s' % name, value, 'text')
    gordon.commit()

def add_annotation(track, name, value, type):
    try:
        if value == track.annotation_dict[name]:
            print ('Annotation %s already exists in track %s, skipping'
                   % (name, track))
            return
    except KeyError:
        track.annotations.append(gordon.Annotation(name=unicode(name), value=unicode(value)))

def echonest_events_to_htk_annotation(events, min_confidence=-1):
    htkannotation = []
    for n, event in enumerate(x for x in events
                              if x['confidence'] > min_confidence):
        starttime = event['start']
        endtime = starttime + event['duration']
        label = event['confidence']
        htkannotation.append('%f\t%f\t%s' % (starttime, endtime, label))
    return '\n'.join(htkannotation)

def main():
    tracks = gordon.Track.query.all()
    for track in tracks:
        process_track(track)

if __name__ == "__main__":
    main()
