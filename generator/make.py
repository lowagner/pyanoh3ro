#!/usr/bin/python
import midi

Tempo = 60 # beats (quarter-notes) per minute
Resolution = 300
# resolution is the # of ticks for a single quarter note (or beat)

import sys
if len(sys.argv) < 2:
    sys.exit("Add key (e.g. C, or C#, or Db).")

key = sys.argv[1]

if key == "C":
    start = 60
elif key == "C#" or key == "Db":
    start = 61
elif key == "D":
    start = 62
elif key == "D#" or key == "Eb":
    start = 63
elif key == "E":
    start = 64
elif key == "F":
    start = 65
elif key == "F#" or key == "Gb":
    start = 66
elif key == "G":
    start = 67
elif key == "G#" or key == "Ab":
    start = 68
elif key == "A":
    start = 69
elif key == "A#" or key == "Bb":
    start = 70
elif key == "B":
    start = 71
else:
    sys.exit(" The key of "+key+" is NOT RECOGNIZED ")


if len(sys.argv) == 3:
    scale = sys.argv[2]
else:
    scale = "major"

if scale == "major":
    noteset = [0, 2, 4, 5, 7, 9, 11, 12]
elif scale == "chromatic":
    noteset = range(13)
else:
    sys.exit(" The ", scale, " scale is NOT YET RECOGNIZED ")

if len(sys.argv) == 4:
    hands = int( sys.argv[3] )
else:
    hands = 1

if not (hands == 1 or hands == 2):
    sys.exit(" Need to have only 1 or 2 hands;", hands," is ??? ")

print "key is ",key, scale,", which starts on midi note ",start

# midi = time in microseconds.
# so for a tempo of 120 beats / minute:
# 60 seconds/minute * (1,000,000 microseconds/second) / ( 120 beats / minute) 
# = 500,000 microseconds / beat
# Now the resolution converts ticks to time:  resolution = ticks / beat
# 500,000 microseconds/beat / ( 1000 ticks/beat)
# = 500 microseconds / tick

# Instantiate a MIDI Pattern (contains a list of tracks)
pattern = midi.Pattern(resolution=Resolution)
# Instantiate a MIDI Track (contains a list of MIDI events)
track = midi.Track()
# Append the track to the pattern
pattern.append(track)
# set the tempo:
track.append( midi.SetTempoEvent(tick=0, bpm=Tempo) )

scalelen = len(noteset)
for i in range(2*scalelen-1):
    currentindex = scalelen-abs(i-scalelen+1)-1
    currentnote = start+noteset[currentindex]
    # Instantiate a MIDI note on event, append it to the track
    track.append( midi.NoteOnEvent(tick=0, velocity=100, pitch=currentnote) )
    if hands == 2:
        track.append( midi.NoteOnEvent(tick=0, velocity=100, pitch=currentnote-12) )
    
    # Instantiate a MIDI note off event, append it to the track
    track.append( midi.NoteOffEvent(tick=Resolution, pitch=currentnote) )
    if hands == 2:
        track.append( midi.NoteOffEvent(tick=0, pitch=currentnote-12) )

# Add the end of track event, append it to the track, wait a full beat before killing
eot = midi.EndOfTrackEvent(tick=Resolution)

track.append(eot)
# Print out the pattern
print pattern
# Save the pattern to disk
midi.write_midifile(key+".mid", pattern)
