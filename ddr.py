# this is the meta-gameplay for both the play and edit classes.
# 
# ddrstyle  :   notes fly from top of screen to bottom onto piano keyboard
#           :   hit the note when it hits the keyboard to get the points
#
from metagame import *
from backdrops import *
from iomidi import *
from piece import *
import config
#
from collections import deque # this is for fast popping of lists from the left

def divisors(n):
    # get all the divisors of the number n.
    # thanks to Ben Ruijl on 
    # http://stackoverflow.com/questions/12421969/finding-all-divisors-of-a-number-optimization

    # first factorize n
    factors = []
    # only use the first few primes to factorize
    for p in [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61]:
        if p*p > n: break
        i = 0
        while n % p == 0:
            n //= p
            i+=1
        if i > 0:
            factors.append((p, i));
    if n > 1: factors.append((n, 1))
    
    # now that we have factors
    div = [1]
    for (p, r) in factors:
        div = [d * p**e for d in div for e in range(r + 1)]

    # sort divisors from smallest to largest
    div.sort()
    return div


class DDRClass( GameChunkClass ):
    def __init__( self, piecedir, midi, 
                    piecesettings = { 
                        "TempoPercent" : 100, "Difficulty" : 0,
                        "Sandbox" : config.SANDBOXplay,
                        "PlayerStarts" : config.PLAYERstarts,
                        "PlayerTrack" : 0,
                        "Metronome" : config.METRONOMEdefault } ):
        ''' the DDR class interfaces between a piece and the visuals onscreen. '''
        self.backdrop = ColorOscillatingBackDropClass()
        self.alerttext = ""
        self.alerttimer = 0
        self.previousabsoluteticks = 0

        # the majority of the work happens in this next KeyboardAndMusicVisualsClass...
        # that is at the bottom of this ddr file.  This is how we visualize the
        # music notes, measure bars, etc., and make them fly around and stuff.
        # it holds the visuals:
        self.keymusic = KeyboardAndMusicVisualsClass()  
        self.keymusic.metronome = piecesettings["Metronome"]

        # the DDRClass essentially interfaces between the piece and the visuals.
        self.piece = PieceClass( piecedir, midi, piecesettings )

        self.currenttrack = piecesettings["PlayerTrack"]
        # the piece represents everything in midi ticks.
        # but the visuals don't know about ticks and what not, only pixels.
        # so we need conversion factors...
        self.resolution = self.piece.resolution
        self.tempomultiplier = 1.0*piecesettings["TempoPercent"]/100
        self.sandbox = piecesettings["Sandbox"]
        self.noisytracks = set(range( self.piece.numberoftracks ))
        self.bookmarkticks = []


        # next we setup the time grid, with allowed durations.
        # for example, with a X/4 (e.g. 6/4, 3/4, 4/4) time signature, the quarter note gets the beat.
        # here we find what durations our beat note (e.g. the quarter note) can divide into:
        self.allowedbeatdivisors = divisors( self.resolution ) # default is 5040, lots of resolution!

        # resolution = # ticks per beat.  1 tick is the smallest unit of time in a midi file,
        # but exactly how long it is in seconds depends on the tempo and the resolution.
        # MIDI uses microseconds to get from a Tempo in bpm (beats per minute) to a unit of time per beat.
        # 1 tick * (1,000,000 microseconds/sec) * (60 sec/min) / (Tempo [bpm]) / Resolution [ticks/beat]
        # = 60,000,000/(Tempo*Resolution) microseconds,
        # or equivalently, there are precisely
        # 60,000,000/(Tempo*Resolution) microseconds / tick.

        # now trim the allowed durations so that we can't get super duper small in our time grid.
        i=1 # don't need to start at i=0,  allowedbeatdivisors[0] = 1.
        while i < len( self.allowedbeatdivisors ):
            if self.allowedbeatdivisors[i] > 16: # default is 16.  
                del self.allowedbeatdivisors[i:] # only allow durations up to MAXbeatDIVISOR
                # if MAXbeatDIVISOR = 16 and the quarter note gets the beat, 
                # this means 64th notes are the smallest notes allowed.  
                # But that's only if the EDITresolution divides equally into 16 pieces.
                break
            else:
                i += 1

        # duration of the time grid increment (the current note length)
        self.readnotecode("n")
        # the above sets self.notecode:
        #self.notecode = "n"    # 1n 2n 3n, ..., n/1, n/2, n/3, ...  "note" (beat)
                                # 1m 2m 3m, ..., m/1, m/2, m/3, ...  "measure"
        self.currentnoteoffset = 0
                                    
        # essentially we load notes by their range of absoluteticks.
        # we load in a full screen at a time
        # except when resetting everything, when we load in an extra screen to be safe.
        self.currentabsoluteticks = 0
        self.setcurrentticksandload(0)
        
        self.play = False # default to not immediately playing.  fixed in derivative classes
        self.selectednotes = []

    def readnotecode( self, notecode ):
        # try to find the note duration based on the notecode
        # and some other stuff.
        notecode = notecode.replace(" ","") # remove all white space
        nindex = notecode.find("n")
        notemultiplier = 1
        notedivider = 1
        notebase = "n"          # default to one beat
        warning = False
        if nindex >= 0:
            # "n" is in notecode:
            if len(notecode) > 1:
                if nindex > 0:
                    try:
                        notemultiplier = int( notecode[:nindex] )
                    except:
                        warning = True
                print "note mult = ", notemultiplier
                divideindex = notecode.find("/")
                if divideindex < 0:
                    # no divider
                    pass
                elif divideindex > nindex:
                    try:
                        notedivider = int( notecode[divideindex+1:] )
                    except:
                        warning = True
                else:
                    warning = True
            else:
                # this is default.
                # notecode = "n" -> notebase = "n", notemultiplier, notedivider = 1
                pass
        else:
            # "n" is NOT in notecode.
            mindex = notecode.find("m")
            if mindex >= 0:
                # "m" is in notecode
                notebase = "m" #
                if len(notecode) > 1:
                    if mindex > 0:
                        try:
                            notemultiplier = int( notecode[:mindex] )
                        except:
                            warning = True
                    divideindex = notecode.find("/")
                    if divideindex < 0:
                        # no divider
                        pass
                    elif divideindex > mindex:
                        try:
                            notedivider = int( notecode[divideindex+1:] )
                        except:
                            warning = True
                    else:
                        warning = True
            else:
                # "m" is not in notecode.
                warning = True
        
        if not warning:
            self.notecode = notecode
            self.notemultiplier = notemultiplier
            self.notedivider = notedivider
            self.notebase = notebase
            # return true if it was a valid note code
            return 1
        else:
            return 0

    def getticks( self, timesignature ):
        notebaseduration = self.resolution  # default to quarter note (i.e. one beat)
        if self.notebase == "m":                # a measure needs timesignature multiplied:
            notebaseduration *= timesignature

        noteticks = 1.0*self.notemultiplier * notebaseduration / self.notedivider

        if self.currentnoteoffset:
            noteoffset = noteticks / 2
        else:
            noteoffset = 0

        return noteticks, noteoffset

    def resetticks( self ):
        self.lastloadedtimesignature = self.currenttimesignature
        self.lastloadednoteticks, self.lastloadednoteoffset = self.getticks( self.lastloadedtimesignature )
        self.currentnoteticks = self.lastloadednoteticks

#### DDR CLASS

    def tickstosecs( self, duration ):
        # convert a duration (in ticks) to seconds
        return duration * 1.0 / ( self.currenttempo * self.tempomultiplier)
    
    def roundtonoteticks( self, absoluteticks, gobackwards = 0 ):
        # HELP:  USE "getticks("timesig") at the absoluteticks
        ts, tsindex = self.piece.gettimesignature( absoluteticks )
        noteticks, noteoffset = self.getticks( ts )
        if absoluteticks < noteoffset:
            return noteoffset

        lastmeasure = self.piece.getfloormeasureticks( absoluteticks - noteoffset ) + noteoffset

        relativeticks = absoluteticks - lastmeasure
        relativedivs = int( round( 1.0*relativeticks / noteticks ) ) - gobackwards
        # need first multiple past a certain number of measures past lastchange.
        possibleticks = lastmeasure + relativedivs * noteticks

        if len(self.piece.timesignatures) > 1:
            if ( ( tsindex > 0 
                and possibleticks < self.piece.timesignatures[tsindex].absoluteticks )
            or ( tsindex < len(self.piece.timesignatures)-1 
                and possibleticks >= self.piece.timesignatures[tsindex+1].absoluteticks )
            ):
                return self.roundtonoteticks( possibleticks )
        
        return possibleticks

    def setcurrenttimesignature( self, timesig ):
        if timesig != self.currenttimesignature:
            self.currenttimesignature = timesig

    def setcurrentticksandload( self, absoluteticks ):
        ''' this method erases all current notes and sets the current position to absoluteticks'''
        if absoluteticks < 0:
            absoluteticks = 0
        # clear everything
        self.keymusic.clearallmusic()
        self.readynotes = []
        for i in range(len(self.piece.notes)):
            self.readynotes.append( deque([]) )
        # previously:  self.readynotes = [deque([])]*len(self.piece.notes)
        # this was bad, they all were copies of the same deque.

        self.clearmidi = True
        # grab tempo and time signatures...
        self.currenttempo = self.piece.gettempo( absoluteticks )
        self.currenttimesignature, tsindex = self.piece.gettimesignature( absoluteticks )
        # grab the tick durations
        self.resetticks()
        # find last measure location, to put into load
        self.lastloadedmeasureticks = self.piece.getfloormeasureticks( absoluteticks )
        # minor bars that cross the screen
        self.lastloadedbarticks = self.lastloadednoteoffset
        
        # get how we get to the pixel coordinates
        self.pixelspertick = ( 1.0*config.PIXELSperbeat / 
            (0.6*self.lastloadednoteticks + 0.4*self.resolution) /
            (0.8 + 0.2*self.tempomultiplier)
        )      
        # and back, how many ticks we need to load based on how big the screen is:
        self.tickrange = int( 2 * config.DEFAULTresolution[1] / self.pixelspertick ) 
        
        # reset absoluteticks in DDR and in piece
        self.currentabsoluteticks = absoluteticks  
        self.piece.setcurrentticks( absoluteticks )

        # here we load in a screen height's worth 
        self.loadeduntil = absoluteticks # the ticks we have loaded up to.  currently nothing past absoluteticks
        self.loadmusic()
        # here we load in another screen height's worth, as a buffer.
        self.loadmusic()
    
    def loadmusic( self ):
        ''' this method adds notes that are up to be looked at... '''
        # get all notes from the piece in a certain range, for the player track
        # load them into the background / visuals, etc.

        # keep track of how much we load in this section
        self.loadeduntil += self.tickrange

        # start with notes:
        # prime the piece for getting events
        self.piece.primegetevents( self.tickrange )

        # get notes from each track
        for i in range(len(self.piece.notes)): 
            events = self.piece.getnoteevents( i )           
            if i == self.currenttrack:
                for note in events:
                    reltickpixels = (note.absoluteticks-self.currentabsoluteticks) * self.pixelspertick
                    if note.name == "Note On":
                        self.keymusic.addnote( note.pitch, note.velocity, reltickpixels ) 

                        self.readynotes[i].append( [ note.pitch, note.velocity, note.absoluteticks ] )

                    elif note.name == "Note Off":
                        self.keymusic.addnote( note.pitch, 0, reltickpixels ) 
                        self.readynotes[i].append( [ note.pitch, 0, note.absoluteticks ] )

            else:
                # get the non-player notes ready for playing
                for note in events:
                    if note.name == "Note On":
                        self.readynotes[i].append( [ note.pitch, note.velocity, note.absoluteticks ] )
                    elif note.name == "Note Off":
                        self.readynotes[i].append( [ note.pitch, 0, note.absoluteticks ] )

        # then get on with our measures.  
        # of ticks in a measure:
        tickspermeasure = self.lastloadedtimesignature*self.resolution
        
        if tickspermeasure  % self.lastloadednoteticks == 0:
            # note divisions equally divide measure
            nextbigbar = self.lastloadedmeasureticks
            nextsmallbar = self.lastloadedbarticks

            while nextbigbar < self.loadeduntil or nextsmallbar < self.loadeduntil:
                if abs(nextbigbar - nextsmallbar) < 2:
                    # both a measurebar and a tickbar should be placed.
                    # but only place a measurebar.
                    nextsmallbar = nextbigbar   # reset small bar if it's getting out of sync.
                    if nextbigbar >= self.currentabsoluteticks:
                        self.keymusic.addmeasurebar( 
                            (nextbigbar-self.currentabsoluteticks)*self.pixelspertick 
                        )
                    # but increment both:
                    nextsmallbar += self.lastloadednoteticks
                    nextbigbar += tickspermeasure
                elif nextbigbar < nextsmallbar:
                    # a measure bar should be placed next.
                    if nextbigbar >= self.currentabsoluteticks:
                        self.keymusic.addmeasurebar( 
                            (nextbigbar-self.currentabsoluteticks)*self.pixelspertick 
                        )
                    nextbigbar += tickspermeasure
                else:
                    # a tick bar should be placed next:
                    if nextsmallbar >= self.currentabsoluteticks:
                        self.keymusic.addmeasurebar( 
                            (nextsmallbar-self.currentabsoluteticks)*self.pixelspertick,
                            True    # for placing a minor bar
                        )
                    nextsmallbar += self.lastloadednoteticks
        else:
            # note divisions DO NOT equally divide measure
            nextbigbar = self.lastloadedmeasureticks
            nextsmallbar = self.loadeduntil
            while nextbigbar < self.loadeduntil:
                if nextbigbar >= self.currentabsoluteticks:
                    self.keymusic.addmeasurebar( 
                        (nextbigbar-self.currentabsoluteticks)*self.pixelspertick 
                    )
                nextbigbar += tickspermeasure

        # now do time signatures
        events = self.piece.gettimesignatureevents()
        if len(events) > 0: 
            for event in events:
                # we just got a time-signature event
                newtimesig = event.numerator
                newtickspermeasure = newtimesig*self.resolution
                timesigpix = (event.absoluteticks-self.currentabsoluteticks) * self.pixelspertick 
                # add in time signature to keymusic no matter what. 
                self.keymusic.addtimesignature( timesigpix, newtimesig )

                # clear everything if the new numerator is different than the old one
                if tickspermeasure != newtickspermeasure:
                    tickspermeasure = newtickspermeasure

                    self.lastloadedtimesignature = newtimesig
                    # update note offset and note duration:
                    self.lastloadednoteticks, self.lastloadednoteoffset = self.getticks( newtimesig )
                    
                    #and clear measure bars after that point:
                    self.keymusic.clearmeasurebarsafter( timesigpix )

                    # and reset the lastmeasure to that point so we will add those measures
                    # reload measurebars after that point
                    # new division markers at...

                    if tickspermeasure % self.lastloadednoteticks == 0:
                        # note divisions equally divide measure
                        nextbigbar = event.absoluteticks
                        nextsmallbar = nextbigbar + self.lastloadednoteoffset
                        while nextbigbar < self.loadeduntil or nextsmallbar < self.loadeduntil:
                            if abs(nextbigbar - nextsmallbar) < 2:
                                # both a measurebar and a tickbar should be placed.
                                # but only place a measurebar.
                                nextsmallbar = nextbigbar   # reset small bar if it's getting out of sync.
                                if nextbigbar >= self.currentabsoluteticks:
                                    self.keymusic.addmeasurebar( 
                                        (nextbigbar-self.currentabsoluteticks)*self.pixelspertick 
                                    )
                                # but increment both:
                                nextsmallbar += self.lastloadednoteticks
                                nextbigbar += tickspermeasure
                            elif nextbigbar < nextsmallbar:
                                # a measure bar should be placed next.
                                if nextbigbar >= self.currentabsoluteticks:
                                    self.keymusic.addmeasurebar( 
                                        (nextbigbar-self.currentabsoluteticks)*self.pixelspertick 
                                    )
                                nextbigbar += tickspermeasure
                            else:
                                # a tick bar should be placed next:
                                if nextsmallbar >= self.currentabsoluteticks:
                                    self.keymusic.addmeasurebar( 
                                        (nextsmallbar-self.currentabsoluteticks)*self.pixelspertick,
                                        True    # for placing a minor bar
                                    )
                                nextsmallbar += self.lastloadednoteticks
                    else:
                        # note divisions DO NOT equally divide measure
                        nextbigbar = self.lastloadedmeasureticks
                        nextsmallbar = self.loadeduntil
                        while nextbigbar < self.loadeduntil:
                            if nextbigbar >= self.currentabsoluteticks:
                                self.keymusic.addmeasurebar( 
                                    (nextbigbar-self.currentabsoluteticks)*self.pixelspertick 
                                )
                            nextbigbar += tickspermeasure
                    
        self.lastloadedmeasureticks = nextbigbar 
        self.lastloadedbarticks = nextsmallbar 

        # now get tempo events
        events = self.piece.gettempoevents()
        for event in events:
            # we just got a tempo event
            self.keymusic.addtempo( (event.absoluteticks-self.currentabsoluteticks) *
                                    self.pixelspertick, self.tempomultiplier*event.bpm )

        # now get any text events
        events = self.piece.gettextevents( self.currenttrack )
        for event in events:
            # we just got a text event
            self.keymusic.addtext( (event.absoluteticks-self.currentabsoluteticks) *
                                                  self.pixelspertick, event.text )

    def scoochforward( self, bigscooch = False ):
        if bigscooch:
            beats = 4.0
        else:
            beats = 1.0
        self.setcurrentticksandload( 
            self.roundtonoteticks( beats*self.currentnoteticks+self.currentabsoluteticks )
        )
        
    def scoochbackward( self, bigscooch = False ):
        if bigscooch:
            beats = 4.0
        else:
            beats = 1.0
        self.setcurrentticksandload( 
            self.roundtonoteticks( -beats*self.currentnoteticks+self.currentabsoluteticks )
        )

    def update( self, dt, midi ):
        self.backdrop.update( dt )
        self.keymusic.update( dt )

        if self.clearmidi:
            midi.clearall()
            self.clearmidi = False

        if self.alerttext:
            # if there is a message,
            if self.alerttimer > 0:
                # count down
                self.alerttimer -= dt
            else:
                # shut it off...
                self.alerttext = ""

        if self.play:
            # grab current piece stuff
            self.currenttimesignature, tsindex = self.piece.gettimesignature( self.currentabsoluteticks )
            self.currenttempo = self.piece.gettempo( self.currentabsoluteticks )
            # send notes flying down.
            # dt is in milliseconds.  tempo = beats per minute.  measure displacement in ticks.
            # ticks = [ticksperbeat] * [beats per minute] * (1 minute / 60,000 milliseconds) * dt
            tickchange = dt * self.resolution * self.tempomultiplier * self.currenttempo / 60000
            self.keymusic.displaceallmusic( tickchange * self.pixelspertick )
            self.currentabsoluteticks += tickchange
            
            # check if any notes should be played (or hit by player, in play-mode)
            for i in range(len(self.readynotes)):
                track = self.readynotes[i]
                # if the first note has its absolute ticks less than the current absolute ticks...
                # track is a list of notes, each note is [ pitch, velocity, absoluteticks ]
                while len(track) and (track[0][-1] <= self.currentabsoluteticks):
                    soundme = track.popleft()
                    if i in self.noisytracks:
                        if soundme[1]: # if there is velocity...
                            midi.startnote( soundme[0], soundme[1], self.piece.channels[i] )  
                        else:
                            midi.endnote( soundme[0], self.piece.channels[i] )  
            
            # get notes that are still coming
            if self.currentabsoluteticks > self.loadeduntil-self.tickrange: # stay two steps ahead
                self.loadmusic()
        else:
            pass

    def process( self, event, midi ):
        if event.type == pygame.KEYDOWN:
            if event.key == 27: # escape key
                return { "gamestate" : 0, "printme" : "ESCAPE FROM DDR MODE" }
            elif self.commonnav( event, midi ): # check for common navigations
                return {}
            elif self.commongrid( event, midi ): # check for common navigations
                return {}
                
        return {}

    def getlastmeasureticks( self ):
        if len(self.piece.notes[self.currenttrack]):
            lastnoteticks = self.piece.notes[self.currenttrack][-1].absoluteticks
            return self.piece.getfloormeasureticks( lastnoteticks )
        else:
            return 0
    
    def commonnav( self, event, midi ):
        if event.key == pygame.K_w:
            self.setalert("playing track "+str(self.currenttrack))
            print "ready ", self.readynotes
            print "selecting ", self.selectednotes
        elif event.key == pygame.K_h or event.key == pygame.K_LEFT: # press left 
            if pygame.key.get_mods() & pygame.KMOD_SHIFT: # if the shift key is held down
                self.keymusic.scoochkeyboard( -6 ) 
            else:
                self.keymusic.scoochkeyboard( -1 )              
            return 1
        elif event.key == pygame.K_l or event.key == pygame.K_RIGHT: # press right
            if pygame.key.get_mods() & pygame.KMOD_SHIFT: # if the shift key is held down
                self.keymusic.scoochkeyboard( 6 ) 
            else:
                self.keymusic.scoochkeyboard( 1 ) 
            return 1

        # other events are only allowed in sandbox mode
        elif self.sandbox:
            if event.key == pygame.K_SPACE: 
                midi.clearall()
                self.play = not self.play
                if not self.play:
                    self.setcurrentticksandload( 
                        self.currentnoteticks * int(round(1.0*self.currentabsoluteticks / self.currentnoteticks) )
                    )
                    
                return 1
            elif event.key == pygame.K_g: # press key g
                self.currentnoteoffset = 0
                if (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    if len(self.piece.notes[self.currenttrack]):
                        lastmeasureticks = self.getlastmeasureticks()
                        if self.currentabsoluteticks != 0 and self.currentabsoluteticks != lastmeasureticks:
                            self.previousabsoluteticks = self.currentabsoluteticks
                        self.setcurrentticksandload( lastmeasureticks )
                        self.setalert("At end of piece.")
                    else:
                        if self.currentabsoluteticks != 0:
                            self.previousabsoluteticks = self.currentabsoluteticks
                        self.setcurrentticksandload( 0 )
                        self.setalert("No notes yet, going to beginning.")
                else:
                    if len(self.piece.notes[self.currenttrack]):
                        lastmeasureticks = self.getlastmeasureticks()
                        if self.currentabsoluteticks != 0 and self.currentabsoluteticks != lastmeasureticks:
                            self.previousabsoluteticks = self.currentabsoluteticks
                    else:
                        if self.currentabsoluteticks != 0:
                            self.previousabsoluteticks = self.currentabsoluteticks
                    self.setcurrentticksandload( 0 )
                    self.setalert("At beginning of piece.")
                self.play = False
                return 1
            elif event.key == pygame.K_j or event.key == pygame.K_DOWN: # press down
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    return 0
                self.scoochbackward(pygame.key.get_mods() & pygame.KMOD_SHIFT) 
                return 1
            elif event.key == pygame.K_k or event.key == pygame.K_UP: # press up
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    return 0
                self.scoochforward(pygame.key.get_mods() & pygame.KMOD_SHIFT) 
                return 1
            elif event.key == pygame.K_PAGEUP:
                self.setcurrentticksandload( self.currentabsoluteticks+ 
                            int((pygame.display.get_surface().get_height())*(1-config.WHITEKEYfraction)/self.pixelspertick) )
                self.setalert("Page up")
                return 1
            elif event.key == pygame.K_PAGEDOWN:
                self.setcurrentticksandload( max(0,self.currentabsoluteticks-
                            int((pygame.display.get_surface().get_height())*(1-config.WHITEKEYfraction)/self.pixelspertick) ) )
                self.setalert("Page down")
                return 1
            elif event.key == pygame.K_HOME:
                self.keymusic.centeredmidinote = 9
                self.setalert("At lowest (piano) key")
                return 1
            elif event.key == pygame.K_END:
                self.keymusic.centeredmidinote = 96
                self.setalert("At highest (piano) key")
                return 1
            elif event.key == pygame.K_COMMA: # press comma (<)
                self.tempomultiplier *= 100
                if (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    self.tempomultiplier -= 10
                else:
                    self.tempomultiplier -= 1
                 
                if self.tempomultiplier < 10:
                    self.tempomultiplier = 10

                self.setalert("Speed to "+str(int(self.tempomultiplier))+"%")
                self.tempomultiplier *= 1.0 / 100
                return 1
            elif event.key == pygame.K_PERIOD: # press period (>)
                self.tempomultiplier *= 100
                if (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    self.tempomultiplier += 10
                else:
                    self.tempomultiplier += 1
                 
                if self.tempomultiplier > 300:
                    self.tempomultiplier = 300

                self.setalert("Speed to "+str(int(self.tempomultiplier))+"%")
                self.tempomultiplier *= 1.0 / 100
                return 1
            elif event.key == pygame.K_c:   
                # add a click track
                if (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    # if shift is pressed
                    if abs(self.keymusic.clicksounds[1].get_volume()/config.CLICKTRACKvolume - 1) < 0.1:
                        self.setalert("Upping clicktrack volume")
                        self.keymusic.clicksounds[0].set_volume( min(1, 10*config.CLICKTRACKvolume*1.1 ) )
                        self.keymusic.clicksounds[1].set_volume( min(1, 10*config.CLICKTRACKvolume ) )
                    else:
                        self.setalert("Lowering clicktrack volume")
                        self.keymusic.clicksounds[0].set_volume( min(1, config.CLICKTRACKvolume*1.1 ) )
                        self.keymusic.clicksounds[1].set_volume( min(1, config.CLICKTRACKvolume ) )
                            
                    self.keymusic.metronome = True
                else:
                    self.keymusic.metronome = not self.keymusic.metronome
                    self.setalert("Click track "+("on" if self.keymusic.metronome else "off"))
                return 1
            elif event.key == pygame.K_BACKQUOTE:
                if self.currentabsoluteticks != self.previousabsoluteticks:
                    lastmeasureticks = self.getlastmeasureticks()
                    initial = self.currentabsoluteticks
                    self.setcurrentticksandload( self.previousabsoluteticks )
                    if initial != 0 and initial != lastmeasureticks:
                        self.previousabsoluteticks = initial 
                    self.setalert("Back to last jump point.")
                else:
                    self.setalert("At previous jump point.")

            elif event.key == pygame.K_b:
                if (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    try:
                        self.bookmarkticks.remove( self.currentabsoluteticks )
                        self.setalert("Bookmark removed.")
                    except ValueError:
                        self.bookmarkticks.append(self.currentabsoluteticks)
                        self.setalert("Bookmark added.  (Use b|B to jump between bookmarks.)")

                elif len(self.bookmarkticks) == 0:
                    self.setalert("No bookmarks.  Add one with ctrl+b")
                
                elif len(self.bookmarkticks) == 1:
                    nextticks = self.bookmarkticks[0] 
                    previous = self.currentabsoluteticks
                    if self.currentabsoluteticks != nextticks:
                        self.setcurrentticksandload( nextticks )
                        self.previousabsoluteticks = previous
                    self.setalert("At only bookmark.  Add more (or delete this one) with ctrl+b.")
                else:
                    if (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        # proceed backwards through bookmarks
                        nextticks = None
                        if self.currentabsoluteticks == self.bookmarkticks[0]:
                            nextticks = self.bookmarkticks[-1]
                            self.setalert("Looped back to last bookmark.")
                        else:
                            i = len(self.bookmarkticks)-2
                            while i >= 0:
                                if self.currentabsoluteticks == self.bookmarkticks[i+1]:
                                    nextticks = self.bookmarkticks[i]
                                    self.setalert("Back to bookmark "+str(i)+".")
                                    break
                                i -= 1
                            if nextticks == None:
                                nextticks = self.bookmarkticks[-1]
                                self.setalert("At last bookmark.")

                        self.previousabsoluteticks = self.currentabsoluteticks
                        self.setcurrentticksandload( nextticks )            
    
                    else:
                        # proceed forwards through bookmarks
                        nextticks = None
                        if self.currentabsoluteticks == self.bookmarkticks[-1]:
                            nextticks = self.bookmarkticks[0]
                            self.setalert("Looped back to bookmark 0.")
                        else:
                            for i in range(len(self.bookmarkticks)-1):
                                if self.currentabsoluteticks == self.bookmarkticks[i]:
                                    nextticks = self.bookmarkticks[i+1]
                                    self.setalert("Advanced to bookmark "+str(i+1)+".")
                                    break
                            if nextticks == None:
                                nextticks = self.bookmarkticks[0]
                                self.setalert("At bookmark 0.")

                        self.previousabsoluteticks = self.currentabsoluteticks
                        self.setcurrentticksandload( nextticks )            
                return 1

        return 0 

    def commongrid( self, event, midi ):
        # if we have numeric input, change the note duration
        if event.key >= 48 and event.key < 58: # numbers 1 (ascii 49) through 9 (ascii 57)
            # number 1 = longest note duration, 2 = shorter note, ...
            self.currentnoteoffset = 0
            notecode = "n"
            if event.key == 48: # 0
                notecode = "n/8"
            elif event.key <= 54: # 1 through 6
                notecode = "m/"+str(event.key-48)
            else:   
                # ascii 55 = 7, and 9 = ascii 57.  
                notecode = "n/"+str(2**(event.key-55))
                
            self.readnotecode( notecode )
            self.setcurrentticksandload( self.currentabsoluteticks )
            self.setalert( "Note grid set to "+self.notecode )
            return 1
        elif event.key == 45: # - ???   HELP may need to switch with 61.
            if self.notebase == "m":
                # decrease note duration from measure base unit
                if self.notemultiplier > 1:
                    # clean up the notation:
                    if self.notedivider > 1:
                        notecode = str(self.notemultiplier-1)+"m/"+str(self.notedivider)
                    else:
                        notecode = str(self.notemultiplier-1)+"m"
                elif self.notedivider > 8:  # completely arbitrary when to switch
                    notecode = "n"          # over to quarter notes.
                else:
                    notecode = "m/"+str(self.notedivider+1)
            else:
                # decrease note duration from beat base unit
                if self.notemultiplier > 1:
                    # clean up the notation:
                    if self.notedivider > 1:
                        notecode = str(self.notemultiplier-1)+"n/"+str(self.notedivider)
                    else:
                        notecode = str(self.notemultiplier-1)+"n"
                elif self.notedivider >= 15:
                    # this is the smallest unit
                    notecode = "n/16"
                else:
                    notecode = "n/"+str(self.notedivider+1)
                    
            self.readnotecode( notecode )
            self.setcurrentticksandload( self.currentabsoluteticks )
            self.setalert( "Note grid set to "+self.notecode )
            return 1
        elif event.key == 61: # + ???
            if self.notebase == "m":
                # increase note duration from measure base unit
                if self.notedivider > 1:  
                    if self.notemultiplier > 1:
                        notecode = str(self.notemultiplier)+"m/"+str(self.notedivider-1)
                    else:
                        notecode = "m/"+str(self.notedivider-1)
                elif self.notemultiplier >= 3:   # completely arbitrary.
                    notecode = "4m"   # don't go above notes that are 4 measures long
                else:
                    notecode = str(self.notemultiplier+1)+"m"
            else:
                # increase note duration from beat base unit
                if self.notedivider > 1:  
                    if self.notemultiplier > 1:
                        notecode = str(self.notemultiplier)+"n/"+str(self.notedivider-1)
                    else:
                        notecode = "n/"+str(self.notedivider-1)
                elif self.notemultiplier >= 8:   # completely arbitrary.
                    notecode = "m"   # switch over to measures when note gets too big.
                else:
                    notecode = str(self.notemultiplier+1)+"n"
            self.readnotecode( notecode )
            self.setcurrentticksandload( self.currentabsoluteticks )
            self.setalert( "Note grid set to "+self.notecode )
            return 1
        return 0 

    def processmidi( self, midi ):
        newnotes = midi.newnoteson()
        lastnote = -1
        for note in newnotes:
            midi.startnote( note[0], note[1], self.piece.channels[self.currenttrack] ) #start note[0] with velocity note[1]
            # also light up the appropriate key on the background
            self.keymusic.brightenkey( note[0], note[1] ) 
            lastnote = note[0]  # grab just the midi note, not the velocity
            
        newnotes = midi.newnotesoff()
        for note in newnotes:
            midi.endnote( note, self.piece.channels[self.currenttrack] ) # stop note note

        return {}

    def draw( self, screen ):
        #backdrop screen
        self.backdrop.draw( screen )
        #draw keyboard and music
        self.keymusic.draw( screen )
        if self.alerttext:
            self.alertbox.top = 10
            self.alertbox.right = screen.get_width() - 10
            
            screen.blit( self.alert, self.alertbox ) 

    def setalert( self, string, time = 5000 ):
        self.alerttext = string
        self.alerttimer = time
        fontandsize = pygame.font.SysFont(config.FONT, 20*config.FONTSIZEmultiplier )
        self.alert = fontandsize.render( self.alerttext, 1, (255,255,255) )
        self.alertbox = self.alert.get_rect()

# end DDR class

class FlyingMusicElement( GameElementClass ):
    def __init__( self, reltickpixels ):
        self.reltickpixels = reltickpixels
    def draw( self, screen, topofkeys ):
        pass
    def displace( self, displacement ):
        self.reltickpixels -= displacement
        if self.reltickpixels < 0:
            return 1 # delete me
        else:
            return 0 # don't delete me

class MeasureBar( FlyingMusicElement ):
    def __init__( self, reltickpixels, otherdivider = False ):
        FlyingMusicElement.__init__( self, reltickpixels )
        if otherdivider:
            self.color = config.DIVIDERcolor 
            self.linewidth = 1
        else:
            self.color = config.MEASUREcolor
            self.linewidth = 3

    def draw( self, screen, topofkeys ):
        y = topofkeys - self.reltickpixels
        if y > 0:
            rightx = screen.get_width()
            pygame.draw.line( screen, self.color, (0,y), (rightx,y), self.linewidth )

    def displace( self, displacement ):
        self.reltickpixels -= displacement
        if self.reltickpixels < -self.linewidth:
            return 1 # delete me
        else:
            return 0

class FlyingText( FlyingMusicElement ):
    def __init__( self, reltickpixels, text, fontsize=20 ):
        self.font = 'monospace'
        self.fontcolor = (250,210,250)
        self.fontsize = fontsize * config.FONTSIZEmultiplier
        self.text = str(text)
        self.reltickpixels = reltickpixels
        self.fractionx = 0.4
        
        fontandsize = pygame.font.SysFont( self.font, self.fontsize)
        self.label = fontandsize.render( self.text, 1, self.fontcolor )
        self.labelbox = self.label.get_rect()

    def draw( self, screen, topofkeys ):
        y = topofkeys - self.reltickpixels
        if y > 0:
            self.labelbox.bottom = y
            self.labelbox.right = (screen.get_width())*self.fractionx
            screen.blit( self.label, self.labelbox )

    def displace( self, displacement ):
        self.reltickpixels -= displacement
        if self.reltickpixels < -self.labelbox.height:
            # tempo disappears after it pops below the keys
            return 1 # delete me
        else:
            return 0

class FlyingTempo( FlyingText ):
    def __init__( self, reltickpixels, bpm ):
        FlyingText.__init__( self, reltickpixels, format("%.1f")%(bpm), 35 )

    def draw( self, screen, topofkeys ):
        # draw on left side of screen
        y = topofkeys - self.reltickpixels
        if y > 0:
            self.labelbox.bottom = y
            self.labelbox.left = 10
            screen.blit( self.label, self.labelbox )

class FlyingTimeSignature( FlyingText ):
    def __init__( self, reltickpixels, numerator ):
        FlyingText.__init__( self, reltickpixels, str(int(numerator)), 40 )
    
    def draw( self, screen, topofkeys ):
        # draw on right side of screen
        y = topofkeys - self.reltickpixels
        if y > 0:
            self.labelbox.bottom = y
            self.labelbox.right = screen.get_width() - 10
            screen.blit( self.label, self.labelbox )

class BottomPianoKeyClass( PianoKeyClass ):
    ''' this class has methods for dealing with notes on/off '''
    def __init__( self, **kwargs ):
        ''' this key is centered at x and anchored on the bottom by y '''
        PianoKeyClass.__init__( self, **kwargs )
        self.notes = deque([])
        self.notewidth =  config.NOTEwidth

    def draw( self, screen, y ):
        keypos = Rect(0,0,self.width,self.length)
        keypos.centerx = self.x
        keypos.bottom = y 
        
        if len(self.notes) > 0:
            screenheight = screen.get_height() # y position relative to the key
            lastnoteheight = screenheight
            if self.white:
                linercolor = ( 140, 140, 140 )
            else:
                linercolor = ( 20, 20, 20 )

            i = 0
            while i < len(self.notes):
                # draw the note
                #note.draw( screen, self.x, pos.top, self.fillcoloron, linercolor )
                #def draw( self, screen, x, miny, fillcolor, outlinecolor ):
                notepos = Rect(0,0,self.notewidth,screenheight)
                notepos.centerx = self.x        
                try:
                    notepos.height = self.notes[i+1][1] - self.notes[i][1]
                except IndexError:
                    pass
                notepos.bottom = keypos.top - self.notes[i][1]

                if notepos.bottom > 0: 
                    # only draw if it's onscreen
                    noteoutline = Rect( notepos.left-2, notepos.top-2, notepos.width+4, notepos.height+4)
                    pygame.draw.rect( screen, linercolor, noteoutline ) #draw outline
                    # draw color based on velocity
                    notevelfrac = 1.0*self.notes[i][0]/128
                    grau = (1-notevelfrac)*120 # more gray if it is a softly played note
                    # more colorful if it is hit hard:
                    notecolor = (   int( notevelfrac*self.fillcoloron[0] + grau ), 
                                    int( notevelfrac*self.fillcoloron[1] + grau ),
                                    int( notevelfrac*self.fillcoloron[2] + grau )   )
                    pygame.draw.rect( screen, notecolor, notepos ) #draw filled 

                # check how far down it is
                if self.notes[i][1] < lastnoteheight:
                    lastnoteheight = self.notes[i][1]

                # increment two, because we took care of OFF notes in the "try" part.
                i += 2
            # draw a line connecting the lowest note to the keyboard
            if lastnoteheight > 0 and lastnoteheight < screenheight:
                linewidth = 2 + 200.0/(lastnoteheight+10)
                liner = Rect(0,0,linewidth,lastnoteheight)
                liner.centerx = self.x
                liner.bottom = keypos.top
                pygame.draw.rect( screen, linercolor, liner ) #draw filled

        pygame.draw.rect( screen, self.fillcolor, keypos ) #draw filled
            
    def addnote( self, velocity, reltickspixels ):
        ''' this note could be on (velocity>0) or off (velocity=0), with ticks
        relative to the top of the keyboard, but measured in pixels.'''
        if len(self.notes) > 0:
            self.notes.append( [velocity, reltickspixels] )
        else:
            if velocity:
                self.notes.append( [velocity, reltickspixels] )
            else:
                self.notes.append( [100, 0] )  # add a dummy on-note
                self.notes.append( [0, reltickspixels] ) # and set the off-note here
    
    def clearallnotes( self ):
        self.notes = deque([])

    def displacenotes( self, displacement ):
        ''' displace all notes, HERE measured in pixels.'''
        if len(self.notes):
            if self.notes[0][0] == 0: # hack to get a note in if velocity is off for first note
                self.notes.appendleft([100,0])

        i=0
        while i < len( self.notes ):
            # move any "on notes" down
            if self.notes[i][1] > 0:
                self.notes[i][1] -= displacement #
            else:
                self.notes[i][1] = 0 #

            try:
                # try to move any "off notes" down.
                self.notes[i+1][1] -= displacement
                if self.notes[i+1][1] < 0:
                    # if the off note has gotten lower then zero,
                    # then delete both the on and the off note.
                    del self.notes[i] # delete i and i+1
                    del self.notes[i] # delete i and i+1
                else:
                    i += 2
            except IndexError:
                # this happens if we have an "on" note but no "off" note on screen.
                # we want to keep the on note, and wait for an off note to appear.
                i += 1 # as long as we increment some amount, we'll pass out of the loop


# this used to be BOTTOMPIANO class.
class KeyboardAndMusicVisualsClass( GameElementClass ):
#### CLASS KEYBOARDANDMUSIC
    def __init__( self, **kwargs ):
        self.allowedchanges = [ "redmean", "redamp", "redfrequency", "redphase",
                                "greenmean", "greenamp", "greenfrequency", "greenphase",
                                "bluemean", "blueamp", "bluefrequency", "bluephase" ]
        ## make 88 keys
        self.keys = []
        # horizontal lines, like measure bars, etc., as well as tempo and time signature changes
        self.measures = []
        self.tempos = []
        self.timesignatures = []
        self.texts = [ ]
        
        self.metronome = True
        self.clicksounds = [ pygame.mixer.Sound( 
                                os.path.join( "resources", "measureclick.ogg" )
                             ),
                             pygame.mixer.Sound( 
                                os.path.join( "resources", "barclick.ogg" )
                             ) ]
        self.clicksounds[0].set_volume( min(1, config.CLICKTRACKvolume*1.1 ) )
        self.clicksounds[1].set_volume( min(1, config.CLICKTRACKvolume ) )

        self.cursorpixels = 0 # how far above the piano to display the cursor
        self.selectanchor = 0 # where the select anchor is, if it is set.  if set, [ midinote, relpixels ]
        self.cursorcolor = config.CURSORcolor # cursor color

        self.defaulthalfwidth = config.KEYwidth / 2 # default half-width of white keys
        self.k = 0.005  # spring constant
        self.incrementnotedistance = []
        startingi = 9 #lowest octave starts with A
        self.effectivekeyhalfwidths = []
        endingi = 12 # all octaves, besides the highest, go to 12
        for octaves in range(9): # 9 octaves, but the first and last are only partial
            if octaves == 8:
                endingi = 1 # only one key in the last octave
            for i in range(startingi, endingi):
                ## make the on colors of the keys a rainbow
                if i in [ 0, 2, 4, 5, 7, 9, 11 ]:  
                    #white keys
                    self.effectivekeyhalfwidths.append( self.defaulthalfwidth )
                    self.keys.append( BottomPianoKeyClass( fillcoloroff=(200,200,200), length=130,
                                            fillcoloron=config.rainbow[i], width=20 ) )
                else: 
                    #black keys
                    self.effectivekeyhalfwidths.append( 0 )
                    self.keys.append( BottomPianoKeyClass( fillcoloroff=(20,20,20), length=80,
                                            fillcoloron=config.rainbow[i], white=False,
                                            width=15) )

            startingi = 0 # all the rest of the octaves start with C
        # lowest A has index 0, which is midinote 9
        # lowest C has index 3

        self.centeredmidinote = 60.0  # center it around middle C to begin with.

#### CLASS KEYBOARDANDMUSIC
    def setstate( self, **kwargs ):
        for key, value in kwargs.iteritems():
            if key in self.allowedchanges: 
                setattr( self, key, value )
            else:
                Warn("in BottomPianoBackDropClass:setstate - key "+ key +" is protected!!") 

#### CLASS KEYBOARDANDMUSIC
    def update( self, dt ):
        for i in range(len(self.effectivekeyhalfwidths)):
            if self.effectivekeyhalfwidths[i] > 0:
                dx = self.effectivekeyhalfwidths[i] - self.defaulthalfwidth
                self.effectivekeyhalfwidths[i] -=  self.k * dt * dx
        for key in self.keys:
            key.update(dt)

#### CLASS KEYBOARDANDMUSIC
    def draw( self, screen ):
        screenwidth, screenheight = screen.get_size()
        # here we draw the measures and what not
        # need to reference the white key
        whitekeylength = config.WHITEKEYfraction*screenheight
        blackkeylength = config.BLACKKEYwhitefraction*whitekeylength

        keytop = screenheight - whitekeylength
        for meas in self.measures:
            meas.draw( screen, keytop )
        
        for text in self.texts:
            text.draw( screen, keytop )
        
        for tempo in self.tempos:
            tempo.draw( screen, keytop )
        
        for timesig in self.timesignatures:
            timesig.draw( screen, keytop )

                

        # the following is everything we need to draw the keys... pianos are complicated!
#        whitekeylength = 0.13*screenheight # these were originally defined here.
#        blackkeylength = 0.7*whitekeylength # now they are defined above!
        screencenterx = 0.5*screenwidth
        
        blackkeyy = screenheight-(whitekeylength - blackkeylength) # y position of the black keys
                                                                   # measured from bottom of note.

        centerkeyindexNONINT = self.centeredmidinote - 9 # but this is not necessarily an integer
        centerkeyindex0 = int( centerkeyindexNONINT )
        eta = centerkeyindexNONINT - centerkeyindex0 # non-integer part of the centermidinote
        
        # figure out which key index to center on...
        if eta > 0.5:
            self.cursorkeyindex = centerkeyindex0 + 1
        else:
            self.cursorkeyindex = centerkeyindex0

        keyindexmin = centerkeyindex0 # will work this down to see which keys need to be drawn
        keyindexmax = centerkeyindex0 # will work this up to see which keys need to be drawn
        if (centerkeyindex0 < 0):  # centering lower than low A
            Error(" Attempting to center the BottomBackGroundPiano on a note below low A!!")
        
        if (centerkeyindex0 > 87): # centering on high C or higher
            Error(" Attempting to center the BottomBackGroundPiano on a note higher than high C!!")
        # here we try to center in between centerkeyindex0 and centerkeyindex0+1

        self.keys[centerkeyindex0].x = screencenterx 
        if eta:
            self.keys[centerkeyindex0].x -= eta*(self.effectivekeyhalfwidths[centerkeyindex0]+
                                               self.effectivekeyhalfwidths[centerkeyindex0+1]) 
                                        
            
        #work our way down to see which keys are visible
        currentx = self.keys[centerkeyindex0].x - self.effectivekeyhalfwidths[centerkeyindex0]
        while keyindexmin > 0 and currentx > - self.effectivekeyhalfwidths[keyindexmin]: # 0 is the minimum allowed keyindex
            keyindexmin -= 1   # but if it was at 1, this will send it to zero.
            # next part determines some width issues for black vs. white keys
            # white keys move "currentx" but black keys do not
            halfwidth = self.effectivekeyhalfwidths[keyindexmin]
            currentx -= halfwidth
            self.keys[keyindexmin].x = currentx
            currentx -= halfwidth
            
        currentx = self.keys[centerkeyindex0].x + self.effectivekeyhalfwidths[centerkeyindex0]
        #now work our way up to see which keys are visible
        while keyindexmax < 87 and currentx < screenwidth + self.effectivekeyhalfwidths[keyindexmax]: 
            # 87 is the max allowed keyindex, or whichever one is not off the screen
            keyindexmax += 1    # but this will send it to 87 if it was at 86.
            # next part determines some width issues for black vs. white keys
            # white keys move "currentx" but black keys do not
            halfwidth = self.effectivekeyhalfwidths[keyindexmax]
            currentx += halfwidth
            self.keys[keyindexmax].x = currentx
            currentx += halfwidth
        try: 
            # this is necessary for the case when we need to draw an extra white key before drawing
            # a black key.
            self.keys[keyindexmax+1].x = screenwidth + 1000
        except IndexError:
            pass

        # now start drawing the keyboard
        if self.cursorpixels:
            if self.keys[self.cursorkeyindex].white:
                cursorrect = Rect(0, 0, 1.5*self.effectivekeyhalfwidths[self.cursorkeyindex],
                                        self.cursorpixels )
            else:
                cursorrect = Rect(0, 0, 0.68*(self.effectivekeyhalfwidths[self.cursorkeyindex-1]
                                             +self.effectivekeyhalfwidths[self.cursorkeyindex+1]),
                                        self.cursorpixels )
            cursorrect.centerx = self.keys[self.cursorkeyindex].x
            cursorrect.bottom = screenheight - whitekeylength
            # we will draw the cursor after we draw the selector background

            if self.selectanchor:
                # selectanchor has position [ midinote, farthest-reach-in-rexels ]
                if self.selectanchor[0] > 127 or self.selectanchor[0] < 0:
                    # if we said to select midi note 128 (or -1), that means we select them all.
                    if self.selectanchor[1] >= self.cursorpixels:
                        # the mark is higher than the current cursor rexels
                        selectorrect = Rect(0,0, screenwidth, self.selectanchor[1]+self.cursorpixels)
                    else:
                        selectorrect = Rect(0,0, screenwidth, self.cursorpixels)

                else:
                    selindex = self.selectanchor[0]-9

                    if self.keys[selindex].white:
                        selectorrect = Rect(0, 0, 1.5*self.effectivekeyhalfwidths[selindex],
                                                self.cursorpixels )
                    else:
                        selectorrect = Rect(0, 0, 0.68*(self.effectivekeyhalfwidths[selindex-1]
                                                     +self.effectivekeyhalfwidths[selindex+1]),
                                                self.cursorpixels )
                    # now figure out the placement.  get the left/right side of things.
                    selectorrect.centerx = self.keys[selindex].x 
                    # now get the height figured out.
                    if self.selectanchor[1] >= self.cursorpixels:
                        # the mark is higher than the current cursor rexels
                        selectorrect.top = cursorrect.top - self.selectanchor[1]
                    else:
                        selectorrect.bottom = cursorrect.bottom

                    selectorrect.union_ip( cursorrect )
            
                selectorrect.bottom = cursorrect.bottom
                pygame.draw.rect( screen, (0.5*self.cursorcolor[0],
                                           0.5*self.cursorcolor[1],
                                           0.5*self.cursorcolor[2]), selectorrect )

            pygame.draw.rect( screen, self.cursorcolor, cursorrect )
                

        #  start at the bottom and draw them all
        keyindex = keyindexmin         
        while keyindex <= keyindexmax:
            if self.keys[keyindex].white:
                self.keys[keyindex].setstate( length=whitekeylength,
                                              width=1.5*self.effectivekeyhalfwidths[keyindex] )
                self.keys[keyindex].draw( screen, screenheight ) 
                keyindex += 1
            else: # black key
                # first draw the white key above it
                self.keys[keyindex+1].setstate( length=whitekeylength,
                                                width=1.5*self.effectivekeyhalfwidths[keyindex+1] )
                self.keys[keyindex+1].draw( screen, screenheight ) 
                # then draw the black key
                self.keys[keyindex].setstate( length=blackkeylength, 
                                              width=0.68*(self.effectivekeyhalfwidths[keyindex+1]+
                                                     self.effectivekeyhalfwidths[keyindex-1]) )
                self.keys[keyindex].draw( screen, blackkeyy ) 
                # BUT NOW INCREMENT BY TWO
                keyindex += 2

#### CLASS KEYBOARDANDMUSIC
    def addnote( self, midinote, velocity, startlocation ):
        ''' a note has a beginning and a duration, measured in ticks. 
        startlocation is PIXELS relative to the keyboard 
        (0 = just above keyboard, time to get hit by player)'''
#        self.resolution = 100 # ticks per beat, set by the piece
#        self.pixelsperbeat = 200 # given as a config
#        self.pixelspertick = 1.0 * self.pixelsperbeat / self.resolution # pixels/beat / (ticks/beat)
        
        keyindex =  (midinote-9)
        if keyindex >= 0 and keyindex <= 87:
            # if you are trying to add an off note before we have any on notes...
#            if velocity == 0 and len(self.keys[keyindex].notes) == 0:
#                # then add an "on" at the origin...
#                self.keys[ keyindex ].addnote( 100, 0 )
#            # then add the off later.  or just add the on if it's an on note
            self.keys[ keyindex ].addnote( velocity, startlocation )
                
            # if the velocity is zero and the length of the notes is zero, we are
            # attempting to add an off note before any on notes!

#        for note in self.keys[ keyindex ].notes:
#            print " midi ", midinote, ":  note0 = ",note[0], "; note1 = ",note[1]
    
    def clearallmusic( self ):
        for key in self.keys:
            key.clearallnotes()
        
        # remove all the objects that are flying around
        self.measures = [ ]
        self.tempos = [ ]
        self.timesignatures = [ ]
        self.texts = [ ]

    def addmeasurebar( self, reltickpixels, otherdivider=False ): 
        self.measures.append( MeasureBar( reltickpixels, otherdivider ) )

    def addtempo( self, reltickpixels, bpm ): 
        self.tempos.append( FlyingTempo( reltickpixels, bpm ) )
    
    def addtimesignature( self, reltickpixels, numerator ): 
        self.timesignatures.append( FlyingTimeSignature( reltickpixels, numerator ) )
    
    def addtext( self, reltickpixels, text ): 
        self.texts.append( FlyingText( reltickpixels, text ) )
        if len(self.texts) > 1:
            if abs(self.texts[-1].reltickpixels - self.texts[-2].reltickpixels) < 10:
                self.texts[-1].fractionx = 0.3
                self.texts[-2].fractionx = 0.7

    def clearmeasurebarsafter( self, reltickpixels ): 
        i = len(self.measures) - 1
        while i >= 0:
            if self.measures[i].reltickpixels >= reltickpixels :
                del self.measures[i]
            i -= 1

    def displaceallmusic( self, displacement ):
        ''' displace all notes by some amount in pixels.  positive displacement moves everything down. '''
        for key in self.keys:
            key.displacenotes( displacement )

        # do measures
        i = 0
        while i < len(self.measures):
            if self.measures[i].displace( displacement ):
                # if the flying musical element signals us to remove it
                
                # first play a metronome sound, if necessary
                if self.metronome:
                    if self.measures[i].linewidth > 1:
                        self.clicksounds[0].play()
                    else:
                        self.clicksounds[1].play()
                    
                # then delete it
                del self.measures[i]
            else:
                # otherwise increment and move on!
                i += 1

        # then do tempos 
        i = 0
        while i < len(self.tempos):
            if self.tempos[i].displace( displacement ):
                # if the flying musical element signals us to remove it
                # delete it
                del self.tempos[i]
            else:
                # otherwise increment and move on!
                i += 1
        
        # then do timesignatures
        i = 0
        while i < len(self.timesignatures):
            if self.timesignatures[i].displace( displacement ):
                # if the flying musical element signals us to remove it
                # delete it
                del self.timesignatures[i]
            else:
                # otherwise increment and move on!
                i += 1
        
        # then do texts
        i = 0
        while i < len(self.texts):
            if self.texts[i].displace( displacement ):
                # if the flying musical element signals us to remove it
                # delete it
                del self.texts[i]
            else:
                # otherwise increment and move on!
                i += 1
    
#### CLASS KEYBOARDANDMUSIC
    def hitrandomkey( self, midi, midioctave=5, notevel=100 ): # midioctave = 5 is middle C
        randompiano = int( random()*12 )
        self.setstate( redphase=randomphase(), 
                       greenphase=randomphase(), 
                       bluephase=randomphase() )
        ## and play it with midi:
        self.hitkey( midi, randompiano + midioctave*12, notevel )


#### CLASS KEYBOARDANDMUSIC
    def brightenkey( self, midinote = 60, notevel = 100 ): # midinote = 60 is middle C
        # make the key flash on
        keyindex =  (midinote-9)
        if keyindex >= 0 and keyindex <= 87:
            self.keys[ keyindex ].setstate( on=notevel )
            self.centeredmidinote += 0.01*(midinote - self.centeredmidinote)
            if self.effectivekeyhalfwidths[ keyindex ] > 0:
                self.effectivekeyhalfwidths[ keyindex ] += 2
            else:
                try:
                    self.effectivekeyhalfwidths[ keyindex+1 ] += 1
                    self.effectivekeyhalfwidths[ keyindex-1 ] += 1
                except IndexError:
                    pass
            ## and play it with midi:
        else:
            Warn(" Attempted to play strange note "+str(midinote)+" in BottomPiano... ")

#### CLASS KEYBOARDANDMUSIC
    def hitkey( self, midi, midinote = 60, notevel = 100, 
                duration=1, channel=0, playsound=True ): # midinote = 60 is middle C
        # make the key flash on
        self.brightenkey( midinote, notevel )
        if playsound:
            midi.playnote( midinote, notevel, duration, channel )
    
    def scoochkeyboard( self, leftright ):
        self.centeredmidinote += leftright
        if self.centeredmidinote < 9:
            self.centeredmidinote = 9
        elif self.centeredmidinote > 96:
            self.centeredmidinote = 96

    def setcursorheight( self, pixels = 0 ):
        self.cursorpixels = pixels
            
    def setselectanchor( self, pixels = 0 ):
        # if zero, then it won't print anything.
        # otherwise, you should use [ midinote, rexel ]
        # where rexel is the pixel distance from the bottom of the keyboard.
        self.selectanchor = pixels
        
#### END CLASS KEYBOARDANDMUSIC

