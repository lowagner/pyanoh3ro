# piece.py has classes to import/export midi files, convert them into pyano readable music
# as well as methods to make them easy to edit.
from metagame import *
import midi as MIDI # from python-midi vishnubob github, for easy reading/writing of midi files
#from midi import *
import config
import pickle, os
import operator # this is for sorting of the midi events

def gcd(a, b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:      
        a, b = b, a % b
    return a

def lcm(a, b):
    """Return lowest common multiple."""
    return a * b // gcd(a, b)

def getpiecesettings( piecedir ):
    settings = {} #
    try:
        piecesettingsfile = os.path.join( piecedir, "info.pkl" )
        with open(piecesettingsfile, 'rb') as handle:
            settings = pickle.loads( handle.read() )
    except IOError:
        Warn(" No info.pkl in the piece directory.  Please create one... ")
    
    # set some defaults
    # get the possible difficulties by the actual 
    descendingdirectorycontents = os.walk(piecedir).next()[2] # 2 = files only, not directories
    difficulties = []
    for f in descendingdirectorycontents:
        if f[-4:] == ".mid":
            difficulties.append( f[-5] )
    
    if not "BookmarkTicks" in settings:
        settings["BookmarkTicks"] = [] 
    if not "Metronome" in settings:
        settings["Metronome"] = config.METRONOMEdefault

    settings["AllowedDifficulties"] = difficulties

    settings["TempoPercent"] = 100
    settings["Difficulty"] = difficulties[0]
    if "AllowedPlayerTracks" in settings:
        settings["PlayerTrack"] = settings["AllowedPlayerTracks"][0]
    else:
        settings["PlayerTrack"] = config.DEFAULTplayertrack
    settings["Sandbox"] = config.SANDBOXplay 

    return settings

class PieceClass:

##  PIECE CLASS

    def __init__( self, piecedir, iomidi, piecesettings ):
        ''' the piece-class holds information about how to read and write a midi file,
        as well as play it in the PlayClass and edit it in the EditClass.  (For the latter,
        see the MetaPieceClass, which keeps track of a bunch of pieces for each difficulty.)'''
        self.piecedir = piecedir
        #print "Opening piece ", piecedir
        self.settings = piecesettings # these are mostly ignored in the Edit class, but
                                      # are very important for the play class.
        #print "piece settings = ", piecesettings
        self.allowedsettings = [ "Name", "Difficulty", "AllowedDifficulties",
                                 "PlayerStarts", "PlayerTrack", "BookmarkTicks",
                                 "Metronome", "Sandbox" ]

        split = os.path.split( piecedir ) # splits path into a base and the last directory
        self.settings["Name"] = split[-1] #  the last directory is the name of the piece
        
        if os.path.isfile( self.piecedir ) or not os.path.isdir( self.piecedir ):
            Error("Piece "+self.piecedir+" should be a directory...")
        
        self.infofile = os.path.join( self.piecedir, "info.pkl" )       

        self.loaddifficulty( iomidi, self.settings["Difficulty"] )

    def setdifficulty( self, difficulty ):
        self.settings["Difficulty"] = difficulty
        difficultystring = str( difficulty )
        self.midifile = os.path.join( self.piecedir, self.settings["Name"]+difficultystring+".mid" )

    def loaddifficulty( self, iomidi, difficulty ):
        self.setdifficulty( difficulty )

        print "attempting to load ", self.midifile

        #self.pattern = midi.Pattern( resolution=config.EDITresolution )
        # track independent things:
        # track independent things:
        self.timesignatures = [ ] # 
        self.tempos = [ ] # list of set-tempo events
        self.instruments = [ ] # list of instruments for each track
        self.channels = [ ] # list of channels for each track
        self.texts = [ ] # list of texts you can get.  first text (texts[track][0]) is track name.

        # track dependent guys:
        # track dependent guys:
        self.notes = [ ]  # list of lists:  notes[track#] = [ noteon, noteoff, end of track, etc. ]
        
        try:
            readpattern = MIDI.read_midifile( self.midifile )
            if len(readpattern) > 16:
                Error(" expecting only 16 tracks in PieceClass. ")
            
            # get our resolution to match up with EDITresolution
            if config.EDITresolution % readpattern.resolution:
                Warn(" midi file resolution does not evenly divide EDITresolution ")
                resolutionmultiplier = 1.0 * config.EDITresolution / readpattern.resolution 
            else:
                resolutionmultiplier = config.EDITresolution / readpattern.resolution 
            
            self.resolution = config.EDITresolution

            for i in range(len(readpattern)):
                absoluteticks = 0
                self.notes.append( [ ] )
                self.channels.append( i+1 )
                self.instruments.append( None ) # default to PIANO instrument
                # at the beginning of the texts list is the Track Name... default is nothing
                trackname = MIDI.TextMetaEvent(text="")
                trackname.absoluteticks = 0
                self.texts.append( [ trackname ] ) # default track name is nothing
                del trackname
                print "Track", i
                #print readpattern[i]
                for event in readpattern[i]:
                    event.tick *= resolutionmultiplier 
                    absoluteticks += event.tick # convert relative time to absolute time
                    event.tick = int(event.tick) # in case we were floating because of the Warning
                    if event.name == "Time Signature":
                        event.absoluteticks = int(absoluteticks) # absolute ticks for this event
                        self.timesignatures.append( event )
                    elif event.name == "Set Tempo":
                        event.absoluteticks = int(absoluteticks) # absolute ticks for this event
                        self.tempos.append( event )
                    elif ( event.name == "Note On"
                           or event.name == "Note Off" ): # add to "notes" 
                        event.absoluteticks = int(absoluteticks) # absolute ticks for this event
                        self.notes[i].append( event )
                    elif event.name == "Program Change":
                        self.instruments[i] = event.value
                        self.channels[i] = event.channel
                    elif event.name == "Control Change":
                        self.channels[i] = event.channel
                    elif event.name == "Track Name":
                        trackname = MIDI.TextMetaEvent(text=event.text)
                        # switch over to a Text meta event since track names can't get their
                        # absolute ticks modified... :(.  but we will change back when we 
                        # write the midi file.  we assume that all Tracknames sit at the
                        # beginning of the texts list.
                        trackname.absoluteticks = 0
                        self.texts[i][0] = trackname
                        del trackname
                    elif event.name == "Text":
                        event.absoluteticks = int(absoluteticks) # absolute ticks for this event
                        self.texts[i].append( event )
                    elif event.name == "End of Track":
                        pass
                    else:
                        print "unknown event", event,"on track", i

                self.setinstrument( iomidi, i, self.instruments[i] )

            # now we sort everything
            self.sorteverything()
            self.setdefaults()

        except IOError:
            Warn("Piece midi-file not found.")
            self.clear()

        self.numberoftracks = len(self.notes)

    def addtrack( self ):
        absoluteticks = 0
        self.notes.append( [ ] )
        self.channels.append( len(self.notes)+1 )
        self.instruments.append( None ) # default to PIANO instrument
        # at the beginning of the texts list is the Track Name... default is nothing
        trackname = MIDI.TextMetaEvent(text="")
        trackname.absoluteticks = 0
        self.texts.append( [ trackname ] ) # default track name is nothing
        self.numberoftracks += 1

    def setinstrument( self, iomidi, track, instrumindex ):
        if self.channels[track] == 9:
            print "enforcing drum-ness for track", track, "[ channel 9 ]"
        elif instrumindex == None:
            print "no instrument chosen for track", track
        else:
            print "channel for track", track, "is", self.channels[track]
            self.instruments[track] = instrumindex
            iomidi.setinstrument( self.channels[track], instrumindex )
    
    def setchannel( self, iomidi, track, channel ):
        if channel == 9:
            print "enforcing drum-ness for track", track, "[ channel 9 ]"
            self.instruments[track] = None
            self.channels[track] = channel
        else:
            self.channels[track] = channel
            print "channel for track", track, "is", channel
            iomidi.setinstrument( channel, self.instruments[track] )

##  PIECE CLASS
    def clear( self ):
        #self.pattern.append( midi.Track() )
        self.resolution = config.EDITresolution
        trackname = MIDI.TextMetaEvent(text="")
        trackname.absoluteticks = 0
        self.texts = [ [trackname] ]
        #del trackname
        self.notes = [ [ ] ]
        self.instruments = [ config.DEFAULTinstrument ] # default to PIANO instrument
        self.channels = [ 1 ] # default to channel 1...
        self.tempos = [ ] # list of set-tempo events
        self.timesignatures = [ ] # 

        self.setdefaults()

    def setdefaults( self ):
        # set some defaults (as given by MIDI, not by anything the user should change)
        if len(self.tempos) == 0:
            self.addtempoevent()
        if len(self.timesignatures) == 0:
            self.addtimesignatureevent()

        self.setcurrentticks( 0 )

    def setcurrentticks( self, absoluteticks ):
        self.loaduntilticks = absoluteticks # how far we've loaded in the piece 
                                            # (or how far we will load to)

        self.currenttimesignatureindex = 0
        self.currenttempoindex = 0

        self.currentnoteindex = [0]*len(self.notes) # reset the note indices, which keep track of
                                                    # which notes have been released via the next
                                                    # method, getnoteevents.


        self.currenttextsindex = [0]*len(self.texts) # reset the texts indices, which keep track of
                                                    # which texts have been released via the next
                                                    # method, getnoteevents.

        trackindex=0
        while trackindex < len(self.notes): # loop over the tracks
            noteindex = 0
            while noteindex < len(self.notes[trackindex]):
                # see if the note at the noteindex has an absolute tick value
                # where we want to be starting at
                if self.notes[trackindex][noteindex].absoluteticks >= self.loaduntilticks:
                    # if so, get the currentnoteindex up to where it needs to be
                    break
#                elif self.notes[trackindex][noteindex].absoluteticks > self.loaduntilticks:
#                    # if so, get the currentnoteindex up to where it needs to be
#                    noteindex += 1
#                    break
                else:
                    noteindex += 1

            self.currentnoteindex[ trackindex ] = noteindex

            textindex = 0
            while textindex < len(self.texts[trackindex]):
                # see if the text at the textindex has an absolute tick value
                # where we want to be starting at
                if self.texts[trackindex][textindex].absoluteticks >= self.loaduntilticks:
                    # if so, get the currenttextindex up to where it needs to be
                    break
#                elif self.texts[trackindex][textindex].absoluteticks > self.loaduntilticks:
#                    # if so, get the currenttextindex up to where it needs to be
#                    textindex += 1
#                    break
                else:
                    textindex += 1

            self.currenttextsindex[ trackindex ] = textindex
                
            trackindex += 1

        index = 0    
        while index < len(self.tempos):
            # see if the note at the noteindex has an absolute tick value
            # where we want to be starting at
            if self.tempos[index].absoluteticks >= self.loaduntilticks:
                # if so, get the current tempo index up to where it needs to be
                break
#            elif self.tempos[index].absoluteticks > self.loaduntilticks:
#                # if so, get the current tempo index up to where it needs to be
#                index += 1
#                break
            else:
                index += 1 
        self.currenttempoindex = index
        
        index = 0    
        while index < len(self.timesignatures):
            # see if the note at the noteindex has an absolute tick value
            # where we want to be starting at
            if self.timesignatures[index].absoluteticks >= self.loaduntilticks:
                # if so, this is where the current tempo index should be
                break
            else:
                index += 1
        self.currenttimesignatureindex = index


##  PIECE CLASS

    def primegetevents( self, tickrange ): 
        ''' call this, then all the note events, etc.'''
        self.loaduntilticks += tickrange

    def getnoteevents( self, trackindex = 0 ):  
        startindex = self.currentnoteindex[ trackindex ]
        while ( self.currentnoteindex[trackindex] < len(self.notes[trackindex]) and
                self.notes[trackindex][self.currentnoteindex[trackindex]].absoluteticks < self.loaduntilticks ):
            self.currentnoteindex[ trackindex ] += 1

        return self.notes[trackindex][startindex:self.currentnoteindex[trackindex]]

##  PIECE CLASS

    def addtempoevent( self, tempo=120, absoluteticks=0 ):
        t = MIDI.SetTempoEvent( bpm = tempo )
        t.absoluteticks = absoluteticks

        if len(self.tempos):
            if absoluteticks > self.tempos[-1].absoluteticks:
                self.tempos.append( t )
            else:
                i = 0
                while i < len(self.tempos):
                    if absoluteticks < self.tempos[i].absoluteticks:
                        self.tempos.insert(i, t)
                        break
                    elif absoluteticks == self.tempos[i].absoluteticks:
                        self.tempos[i] = t
                        break
                    else:
                        i += 1
        else:
            self.tempos.append( t )

    def addtimesignatureevent( self, num=4, absoluteticks=0 ):
        ts = MIDI.TimeSignatureEvent( numerator=num )
        ts.absoluteticks = absoluteticks

        if len(self.timesignatures):
            # if it's at the end of things
            if absoluteticks > self.timesignatures[-1].absoluteticks:
                self.timesignatures.append( ts )
            else: 
                # otherwise it's somewhere in the middle
                i = 0
                while i < len(self.timesignatures):
                    if absoluteticks < self.timesignatures[i].absoluteticks:
                        self.timesignatures.insert(i, ts)
                        break
                    elif absoluteticks == self.timesignatures[i].absoluteticks:
                        self.timesignatures[i] = ts
                        break
                    else:
                        i += 1
        else:
            self.timesignatures.append( ts )
    
    def removetimesignatureevent( self, absoluteticks ):
        if len(self.timesignatures):
            # otherwise it's somewhere in the middle
            i = 0
            while i < len(self.timesignatures):
                if absoluteticks == self.timesignatures[i].absoluteticks:
                    del self.timesignatures[i]
                    return 0
                i += 1
        return 1 
    
    def removetempoevent( self, absoluteticks ):
        if len(self.tempos):
            i = 0
            while i < len(self.tempos):
                if absoluteticks == self.tempos[i].absoluteticks:
                    del self.tempos[i]
                    return 0
                i += 1
        return 1 

##  PIECE CLASS
    def addmidinote( self, midinoteevent, trackindex = 0 ):
        if midinoteevent.absoluteticks >= 0:
            i = 0
            success = False
            while i < len(self.notes[trackindex]):
                if midinoteevent.absoluteticks < self.notes[trackindex][i].absoluteticks:
                    self.notes[trackindex].insert( i, midinoteevent )
                    success = True

                    break
                i += 1
            
            if not success:
                # this is a note after all others...
                self.notes[trackindex].append( midinoteevent )

    def addnote( self, midinote, velocity, absticks, duration, trackindex = 0 ):  
        ''' add a note to the track index track! '''
        # not sure what the tick is, but that's ok.  that all gets recalculated at the end anyway.

        if absticks >= 0:
            noteon = MIDI.NoteOnEvent( tick=0, velocity=velocity, pitch=midinote )
            noteon.absoluteticks = absticks
            noteoff = MIDI.NoteOffEvent( tick=0, velocity=0, pitch=midinote )
            noteoff.absoluteticks = absticks + duration

            # fix things for playing
            if absticks < self.loaduntilticks:
                self.currentnoteindex[trackindex] += 1
            if absticks+duration < self.loaduntilticks:
                self.currentnoteindex[trackindex] += 1

            i = 0
            success = False
            while i < len(self.notes[trackindex]):
                if absticks < self.notes[trackindex][i].absoluteticks:
                    self.notes[trackindex].insert( i, noteon )
                    success = True

                    break
                i += 1
            
            if not success:
                # this is a note after all others...
                self.notes[trackindex].append( noteon )
                # so it turns off after all others, too.
                self.notes[trackindex].append( noteoff )
            else:
                # this note was in the midst of everyone.
                i += 1
                success = False
                # try to find where the end note goes
                while i < len(self.notes[trackindex]):
                    if absticks+duration < self.notes[trackindex][i].absoluteticks:
                        self.notes[trackindex].insert( i, noteoff )
                        success = True
                        break
                        
                    i += 1

                if not success:
                    # it turns off after all other notes.
                    self.notes[trackindex].append( noteoff )
        else:
            print "WARNING:  tried to add note before beginning of piece."

    def selectnotes( self, tickrange, midirange=None, trackindex=0 ):  
        # grab on notes with absoluteticks >= tickrange[0] to < tickrange[1]
        #   and their corresponding off notes
        # as long as they have a pitch >= midirange[0] to <= midirange[1]
        if midirange == None:
            midirange = [0,128]

        selectednotes = []
        selectedmidinotes = []
        i = 0
        while i < len(self.notes[trackindex]):
            notei = self.notes[trackindex][i]
            if ( notei.name == "Note Off" ):
                # we'll only consider on notes to simplify things here
                pass
            elif ( notei.absoluteticks >= tickrange[1] ):
                break
                # all notes that are on after the tick range can be ignored.
            elif ( midirange[0] <= notei.pitch <= midirange[-1] ):
                # filter based on midirange 
                # it's an on note, so we go searching for it's off switch.
                onpitch = notei.pitch
                # get the off note with the right pitch
                j = i + 1
                while j < len(self.notes[trackindex]):
                    notej = self.notes[trackindex][j]
                    # search for the note off.
                    if ( notej.name == "Note Off" and notej.pitch == onpitch ):
                        # found it!
                        if ( notei.absoluteticks >= tickrange[0]
                        or notej.absoluteticks >= tickrange[0] ):
                            # on note starts after tickrange[0] (but before tickrange[1])
                            # both on and off notes are in the delete zone
                            selectednotes.append( [ onpitch,
                                notei.velocity,
                                notei.absoluteticks,
                                notej.absoluteticks
                                -notei.absoluteticks 
                            ] )
                            selectedmidinotes.append( notei )
                            selectedmidinotes.append( notej )
                        break
                    j += 1

            i += 1

        return selectednotes, selectedmidinotes

    def deletenotes( self, selectednotes, selectednotestrack=0 ):
        if len(selectednotes):
            ti = 0 # track note index
            si = 0 # selected note index
            searchon = True # whether searching for on (or off if False)
            while ( si < len(selectednotes) ):
                if ti >= len( self.notes[selectednotestrack] ) or ti < 0:
                    # hopefully don't have to loop around too much, but it's here if necessary.
                    ti = 0
                    
                tracknote = self.notes[selectednotestrack][ti]
                selnote = selectednotes[si]

                if searchon:
                    name = "Note On"
                    absticks = selnote[2]
                else:
                    name = "Note Off"
                    absticks = selnote[2] + selnote[3]

                if ( tracknote.pitch == selnote[0] and 
                     tracknote.name == name and
                     tracknote.absoluteticks == absticks ):
                    del self.notes[selectednotestrack][ti]

                    if not searchon: # if we were searching for an off
                        si += 1     # increment what note we're searching for
                        ti -= 5     # check back a few notes in the track
                    
                    # we were successful in finding the on or off, so switch now:
                    searchon = not searchon
                else:
                    ti += 1

        self.notes[selectednotestrack].sort(key=operator.attrgetter('absoluteticks'))
##  PIECE CLASS

    def carveoutregion( self, tickrange, midirange=None, trackindex=0 ):  
        # remove note sections that are in this region.
        # lots of different cases.  some notes are outside completely,
        # other notes are just inside from start or end,
        # some notes are completely inside,
        # and other notes exist before and after the region (need to be
        # cut in two).
        if midirange == None:
            midirange = [0,128]
        
        undeleted = [] # like the undead.  
        # some of them are full dead, others just partially.
        
        i = 0
        while i < len(self.notes[trackindex]):
            notei = self.notes[trackindex][i]
            if ( notei.name == "Note Off" ):
                # we'll only consider on notes to simplify things here
                pass
            elif ( notei.absoluteticks >= tickrange[1] ):
                break
                # all notes that are on after the tick range can be ignored.
            elif ( midirange[0] <= notei.pitch <= midirange[-1] ):
                # filter based on midirange 
                # it's an on note, so we go searching for it's off switch.
                onpitch = notei.pitch
                # get the off note with the right pitch
                j = i + 1
                while j < len(self.notes[trackindex]):
                    notej = self.notes[trackindex][j]
                    # search for the note off.
                    if ( notej.name == "Note Off" and notej.pitch == onpitch ):
                        # found it!
                        if notei.absoluteticks >= tickrange[0]:
                            # on note starts after tickrange[0]
                            if notej.absoluteticks <= tickrange[1]:
                                # both on and off notes are in the delete zone
                                undeleted.append( [ onpitch,
                                                    notei.velocity,
                                                    notei.absoluteticks,
                                                    notej.absoluteticks
                                                    -notei.absoluteticks ] )

                                # then delete both of them
                                del self.notes[trackindex][i]
                                i -= 1
                                # because we deleted one of them,...
                                del self.notes[trackindex][j-1] # need to minus one here
                            else:
                                # the off note is outside the delete zone, 
                                # so move up (to tickrange[1]) the on note.
                                
                                # grab what's carved out
                                undeleted.append( [ onpitch, notei.velocity,
                                    notei.absoluteticks,
                                    tickrange[1]-notei.absoluteticks
                                    -config.EDITnotespace ] ) # give it space, too
                                
                                # moving on note to tickrange[1]
                                notei.absoluteticks = tickrange[1]
                        else:
                            # on note happens before tickrange[0]
                            if notej.absoluteticks <= tickrange[0]:
                                # off note happens before tickrange[0], too. ignore
                                pass
                            elif notej.absoluteticks <= tickrange[1]:
                                # off note is in the range, move it up to tickrange[0]
                                # deleted note:
                                undeleted.append( [ onpitch, 
                                                    notei.velocity,  
                                                    tickrange[0], #starts at tickrange[0]
                                                    notej.absoluteticks - tickrange[0]  #duration of deleted note
                                                    - config.EDITnotespace
                                                  ] )
                                notej.absoluteticks = tickrange[0] - config.EDITnotespace
                            else:
                                # off note happens after the region.  this is interesting!
                                # we just deleted the whole region out of that note.
                                undeleted.append( [ onpitch, 
                                                    notei.velocity,  
                                                    tickrange[0], #starts at tickrange[0]
                                                    tickrange[1] - tickrange[0]  
                                                    - config.EDITnotespace
                                                  ] )
                                # instead of deleting notes, we need to add an off and on.
                                noteoff = MIDI.NoteOffEvent( tick=0, pitch=onpitch, 
                                    absoluteticks = tickrange[0]-config.EDITnotespace )
                                self.notes[trackindex].insert( i+1, noteoff )
                                del noteoff
                                noteon = MIDI.NoteOnEvent( tick=0, pitch=onpitch, 
                                    velocity=notei.velocity,
                                    absoluteticks = tickrange[1] )
                                self.notes[trackindex].insert( i+2, noteon )
                                del noteon
                                i += 2
                        break
                    j += 1

            i += 1
        
        self.notes[trackindex].sort(key=operator.attrgetter('absoluteticks'))
        return undeleted

##  PIECE CLASS

    def deletenextonnote( self, pitch, startingticks, track=0 ):
        ti = 0 # track note index
        while ti < len( self.notes[track] ): 
            tracknote = self.notes[track][ti]
            if ( tracknote.name == "Note On" 
            and tracknote.absoluteticks > startingticks
            and tracknote.pitch == pitch ):
                del self.notes[track][ti]
                return 0
            ti += 1
        return 1
    
    def deleteonnote( self, pitch, tickrange, track=0 ):
        ti = 0 # track note index
        while ti < len( self.notes[track] ): 
            tracknote = self.notes[track][ti]
            if ( tracknote.name == "Note On" 
            and tickrange[0] < tracknote.absoluteticks <= tickrange[-1]
            and tracknote.pitch == pitch ):
                del self.notes[track][ti]
                return 0
            ti += 1
        return 1

    def gettimesignatureevents( self ): 
        ''' this should be called immediately after getnoteevents''' 
        startindex = self.currenttimesignatureindex
        while ( self.currenttimesignatureindex < len(self.timesignatures) and
                self.timesignatures[self.currenttimesignatureindex].absoluteticks < self.loaduntilticks ):
            self.currenttimesignatureindex += 1
        
        return self.timesignatures[startindex:self.currenttimesignatureindex]
    
    def gettempoevents( self ): 
        ''' this should be called after getnoteevents and gettimesignatureevents'''
        startindex = self.currenttempoindex
        while ( self.currenttempoindex < len(self.tempos) and
                self.tempos[self.currenttempoindex].absoluteticks < self.loaduntilticks ):
            self.currenttempoindex += 1
        
        return self.tempos[startindex:self.currenttempoindex]

##  PIECE CLASS

    def gettextevents( self, trackindex = 0 ):
        startindex = self.currenttextsindex[ trackindex ]
        while ( self.currenttextsindex[trackindex] < len(self.texts[trackindex]) and
                self.texts[trackindex][self.currenttextsindex[trackindex]].absoluteticks < self.loaduntilticks ):
            self.currenttextsindex[ trackindex ] += 1

        return self.texts[trackindex][startindex:self.currenttextsindex[trackindex]]
        
    def addremovetextevent( self, text, absoluteticks=0, trackindex=0 ):
        ''' returns 1 if adding a text event (len(text)>0), 
        -1 if removing a text event (len(text)==0),
        and 0 if nothing happened (len(text)==0 and no matching text with absoluteticks) '''
        if absoluteticks == 0:
            # set the trackname if we're at the beginning of the piece
            self.texts[trackindex][0].text = text
            if len(text):
                return 1
            else:
                return -1
        elif len(text):
            # adding process
            miditext = MIDI.TextMetaEvent(text=text)
            # for some reason we need to put in the data by hand:
            miditext.data = [ ord(letter) for letter in text ]
            miditext.absoluteticks = absoluteticks

            if absoluteticks > self.texts[trackindex][-1].absoluteticks:
                self.texts[trackindex].append( miditext ) 
                return 1
            else:
                i = 0
                while i < len(self.texts[trackindex]):
                    if absoluteticks < self.texts[trackindex][i].absoluteticks:
                        self.texts[trackindex].insert(i, miditext)
                        return 1
                    elif absoluteticks == self.texts[trackindex][i].absoluteticks:
                        self.texts[trackindex][i] = miditext
                        return 1
                    else:
                        i += 1
        else:
            # removal process
            i = 0
            while i < len(self.texts[trackindex]):
                if absoluteticks == self.texts[trackindex][i].absoluteticks:
                    del self.texts[trackindex][i]
                    return -1
                else:
                    i += 1
        return 0

##  PIECE CLASS

    def sorteverything( self ):
        ''' sorts every note in each track, as well as tempo and time signatures '''
        for track in self.notes:
            track.sort(key=operator.attrgetter('absoluteticks'))
        for i in range(len(self.texts)):
            trackname = self.texts[i][0]
            tracktexts = self.texts[i][1:]
            tracktexts.sort(key=operator.attrgetter('absoluteticks'))
            self.texts[i] = [trackname] + tracktexts

        self.tempos.sort(key=operator.attrgetter('absoluteticks'))
        self.timesignatures.sort(key=operator.attrgetter('absoluteticks'))

    def writeinfo( self ):
        with open(self.infofile, 'wb') as handle:
            pickle.dump(self.settings, handle)
     
##  PIECE CLASS

    def writemidi( self, filedir="" ):
        # sort the events by absoluteticks
        # put all tempo, time signature data in track 0, as well as any instrument or track names

        # first grab the track name
        if self.texts[0][0].text != "":
            trackname = MIDI.TrackNameEvent(text=self.texts[0][0].text, tick=0)
            trackname.absoluteticks = 0
            # for some reason, the data doesn't get through via the text above.
            trackname.data = [ ]
            i = 0
            while i < len(self.texts[0][0].text):
                trackname.data.append( ord( self.texts[0][0].text[i] ) ) 
                i+= 1
            tracks = [[ trackname]] 
            del trackname # so that when we reuse this variable later it doesn't change the above
        else:
            tracks = [[]]
        # put all tempo, time signature data in track 0
        tracks[0] += self.texts[0][1:] + self.tempos+self.timesignatures+self.notes[0]
        # sort everything
        tracks[0].sort(key=operator.attrgetter('absoluteticks'))
#        print "saving track0"
#        print tracks[0]

        # then grab the instrument
        if self.channels[0] != 9 and self.instruments[0]:
            tracks[0].insert(0, MIDI.ProgramChangeEvent( value=self.instruments[0],
                            channel=self.channels[0]  ) )


        for i in range(1,len(self.notes)):
            # sort each track separately
            # first grab the track name
            if self.texts[i][0].text != "":
                trackname = MIDI.TrackNameEvent(text=self.texts[i][0].text, tick=0)
                # for some reason, the data doesn't get through via the text above.
                trackname.data = [ ]
                trackname.absoluteticks = 0
                j = 0
                while j < len(self.texts[i][0].text):
                    trackname.data.append( ord( self.texts[i][0].text[j] ) ) 
                    j += 1
                tracks.append( [ trackname ] )
                del trackname # so that when we reuse this variable later it doesn't change the above
            else:
                tracks.append( [] )
            # then grab the instrument
            tracks[i] += self.texts[i][1:] + self.notes[i] 
            tracks[i].sort(key=operator.attrgetter('absoluteticks'))
            if self.channels[i] != 9 and self.instruments[i]:
                tracks[i].insert(0, MIDI.ProgramChangeEvent( value=self.instruments[i],
                            channel=self.channels[i] ))

        # now that everything is sorted globally,
        # make sure that the local ticks are correct.
        tickdivisor = config.EDITresolution
        for i in range(len(tracks)):
            tracks[i].insert(0, MIDI.ControlChangeEvent( tick=0, channel=self.channels[i],
                                                        data=[7,127]) )
        for track in tracks:
            previouseventabsoluteticks = 0
            for event in track:
                try:
                    thiseventabsoluteticks = int(event.absoluteticks)
                except AttributeError:
                    thiseventabsoluteticks = 0
                # number of ticks between previous event and the current event
                tickmeoff = thiseventabsoluteticks - previouseventabsoluteticks
                event.tick = tickmeoff
                # check to see how small we can get the resolution
                tickdivisor = gcd( tickdivisor, tickmeoff )
                # set up the ticks for next event
                previouseventabsoluteticks = thiseventabsoluteticks
         
        if config.EDITresolution % tickdivisor:
            Error(" min RESOLUTION does not divide our EDITresolution.  something is funky ")

        # prep the new pattern for creating
        newpattern = MIDI.Pattern( resolution=config.EDITresolution/tickdivisor )
        for track in tracks:
            if tickdivisor > 1:
                for event in track:
                    # divide up the relative ticks
                    event.tick /= tickdivisor
                    # keep absolute ticks in the EDITresolution
            if track[-1].name != "End of Track":
                # add an end of track if it isn't there
                track.append( MIDI.EndOfTrackEvent( tick=config.EDITresolution/tickdivisor ) )
            newpattern.append( MIDI.Track(track) )
        
        if filedir == "":
            MIDI.write_midifile(self.midifile, newpattern)
        else:
            MIDI.write_midifile(filedir, newpattern)
        
##        # recreate the pattern # probably unnecessary
##        self.pattern = midi.Pattern( config.EDITresolution )
##        for track in tracks:
##            if tickdivisor > 1:
##                for event in track:
##                    event.tick *= tickdivisor
##            # add tracks to the pattern
##            self.pattern.apppend( track )

##  PIECE CLASS

    def gettimesignature( self, absoluteticks ):
        i = len(self.timesignatures) - 1 # start from the end of the song and work backwards
        while i >= 0:
            # the first time signature whose absolute-ticks is before the abs-ticks of interest 
            if self.timesignatures[i].absoluteticks <= absoluteticks:
                return self.timesignatures[i].numerator, i  # just the numerator, beats per measure
            else:
                i -= 1
        return 4, None # default beats per measure

##  PIECE CLASS

    def getfloormeasureticks( self, absoluteticks ): 
        lastchange = 0
        timesig = 4
        if len(self.timesignatures) > 0:
            i = len(self.timesignatures) - 1 # start from the end of the song and work backwards
            while i >= 0:
                # the first time signature whose absolute-ticks is before the abs-ticks of interest 
                if self.timesignatures[i].absoluteticks <= absoluteticks:
                    timesig = self.timesignatures[i].numerator # just the numerator, beats per measure
                    lastchange = self.timesignatures[i].absoluteticks
                    break
                else:
                    i -= 1

        #need first multiple past a certain number of measures past lastchange.
        relativeticks = absoluteticks - lastchange
        tickspermeasure = timesig * self.resolution # number of ticks in a measure
        relativemeasures = int( floor( 1.0*relativeticks / tickspermeasure ) )

        return lastchange + relativemeasures * tickspermeasure
        
    def gettempo( self, absoluteticks ):
        i = len(self.tempos) - 1 # start from the end of the song and work backwards
        while i >= 0:
            # the first time signature whose absolute-ticks is before the abs-ticks of interest 
            if self.tempos[i].absoluteticks <= absoluteticks:
                return self.tempos[i].bpm
            else:
                i -= 1
        return 120 # default tempo

        
##  END PIECE CLASS


#class MetaPieceClass:
#    def __init__( self, piecedir ):
#        # grab the piece directory
#        self.piecedir = piecedir
#        self.allowedsettings = [ "Name", 
#                                 "AllowedDifficulties" ]
#
#        split = os.path.split( piecedir ) # splits path into a base and the last directory
#        self.settings = {}
#        self.settings["Name"] = split[-1] #  the last directory is the name of the piece
#
#        # set all defaults...
#        self.settings["PlayerStarts"] = config.PLAYERstarts 
#        # PlayerStarts = true for solo piano pieces, or when the piano starts the piece.
#        #   otherwise it should be false when there is background music
#        self.settings["PlayerTrack"] = config.PLAYERtrack
#        self.settings["AllowedDifficulties"] = config.ALLOWEDdifficulties
#
#        if os.path.isfile( self.piecedir ):
#            Error("Piece "+self.piecedir+" is a file, and it should be a directory...")
#        if not os.path.isdir( self.piecedir ):
#            ## if the piece directory has not been created yet
#            os.makedirs( self.piecedir ) # create it.
#
#        # check for an info file
#        self.infofile = os.path.join( self.piecedir, "info.pkl" )
#        try:
#            with open(infofile, 'rb') as handle:
#                nondefaults = pickle.loads( handle.read() )
#            self.setstate( **nondefaults )
#        except IOError:
#            print "For "+self.piecedir+", info.pkl file does not exist.  Setting defaults."     
#            self.writeinfo()
#
#        # check for a midi file
#        self.midifilebase = os.path.join( self.piecedir, str(piecename) )
#        # all difficulties should be accessible via self.midifilebase + str(Difficulty) + ".mid"
#        self.pieces = {} # a set of midi patterns for each difficulty
#        for d in self.settings["AllowedDifficulties"]: 
#            piecesettings = {}
#            for key in self.settings:
#                piecesettings[key] = self.settings[key]
#            piecesettings["Difficulty"] = d
#            self.pieces[d] = PieceClass( self.piecedir, piecesettings )
#
#    def setstate( self, **kwargs ):
#        for key, value in kwargs.iteritems():
#            if key in self.allowedsettings:
#                self.settings[key] = value
#
#    def writeinfo( self ):
#        with open(self.infofile, 'wb') as handle:
#            pickle.dump(self.settings, handle)
#
#    def readmidi( self ):
#        pass
#
#    def writemidi( self ):
#        pass
#
#    def gettimesignature( self, measure, difficultyindex ):
#        i = len(self.timesignatures[difficultyindex]) - 1 # start from the end of the song and work backwards
#        while i >= 0:
#            # the first time signature whose measure is before the measure of interest 
#            if self.timesignatures[difficultyindex][i].measure < measure:
#                return self.timesignature[difficultyindex][i].data
#            else:
#                i -= 1
#
#    def getmeasure( self, absoluteticks ):
#        pass
#
#
#
if __name__ == "__main__":
    from iomidi import *
    IOmidi = MidiClass()
    piece = PieceClass("songs/Random/Polka/Fish Polka", 
                        IOmidi,
                        {"Difficulty" : 5, 
                         "Name" : "Fish Polka", 
                         "PlayerStarts" : True, 
                         "PlayerTrack" : 3 } )

    piece.writemidi( "fishy.mid" )
    #print piece.notes[5]
    

