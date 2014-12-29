# iomidi.py - for nice midi input from a keyboard, and output via fluidsynth
import pygame
import pygame.midi
from mingus.midi import fluidsynth
import config

class MidiClass:
    def __init__( self ):
    # possible fluidsynth guys
##main_volume(channel, value)
##modulation(channel, value)
##pan(channel, value)

        if not fluidsynth.init( config.SOUNDfont, config.FLUIDSYNTHdriver ):
            sys.exit(" COULD NOT LOAD SOUNDFONT PianoMenu.sf2 ")
        # set instruments on each channel.  
        fluidsynth.set_instrument( config.PIANOchannel,    ## channel to set instrument on
                                   config.SOUNDfontPIANO ) ## instrument.  determined by sound font

        self.keysmod12 = [ "C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B" ]
        self.keyson = [ 0 ]*12  # denotes all keys on in an octave
        self.newnotesonlist = [ ]   # list of new [note,velocity] that player has hit
        self.newnotesofflist = [ ]  # list of new note that player has taken fingers off of
        #self.noteson = set()    # set of notes that the player currently has down 
        # commented out since it was crashing things to remove notes sometimes...
        self.pitchwheel = 64    # current value of the pitch wheel
        self.modwheel = 0       # current value of the mod wheel
        self.transientnotes = []
        pygame.midi.init()

    def playnote( self, midinote, notevel=100, duration=1, channel=0 ):
        ''' play a note, but only let it exist for a short period of time '''
        self.transientnotes.append( [ midinote, duration, channel ] )
        fluidsynth.play_Note( midinote, channel, notevel ) # 

    def startnote( self, midinote, notevel=100, channel=0 ):
        ''' start a note playing, usually from a midi input source. MUST END IT LATER. '''
        fluidsynth.play_Note( midinote, channel, notevel ) # 

    def endnote( self, midinote, channel=0 ):
        ''' the counterpart to starting a note.  this ends it. '''
        fluidsynth.stop_Note( midinote, channel ) # stop  note

    def clearall( self ):
        fluidsynth.stop_everything()

    def getallowedinputs(self):            
        allowedin = []
        allowedinnames = []
        for midi_id in range( pygame.midi.get_count() ):
            interface, name, input, output, opened = pygame.midi.get_device_info( midi_id )
            if input:
                allowedin.append( midi_id )
                allowedinnames.append( name )

        return allowedin, allowedinnames

    def setinstrument( self, channel, instrument ):
        fluidsynth.set_instrument( channel, instrument )
        print "setting channel", channel, "to instrument", instrument

    def setinput( self, midi_id ):
        try:
            del self.midiin
        except AttributeError:
            pass

        self.midiin = pygame.midi.Input( midi_id )

    def update( self, dt ):
        ## check if any midi events have happened
        if self.midiin.poll():
            midi_events = self.midiin.read(10) #not sure what 10 is for
            # convert them into regular pygame events.
            midi_evs = pygame.midi.midis2events(midi_events, self.midiin.device_id)

            for m_e in midi_evs:
                pygame.fastevent.post( m_e )
        
        i=0
        while i < len(self.transientnotes):
            self.transientnotes[i][1] -= dt
            if self.transientnotes[i][1] < 0:
                fluidsynth.stop_Note( self.transientnotes[i][0], self.transientnotes[i][2] ) # stop  note
                del self.transientnotes[i]
            else:
                i += 1
                
        ## we deal with the midi-converted-to-pygame events in the "process" method below

    def process( self, event ):
        if event.type in [pygame.midi.MIDIIN]:
            octave, numnote = divmod(event.data1, 12)
            #note = self.keysmod12[numnote]  # returns human readable C,D,E, etc.
            if event.status == 144: #key down
                velocity = event.data2
                self.keyson[numnote] += 1
                self.newnotesonlist.append( [event.data1, event.data2] ) #note and velocity
                #self.noteson.add( event.data1 )
            elif event.status == 128: #key up
                self.newnotesofflist.append( event.data1 ) #note and velocity
                if self.keyson[numnote] > 0:
                    self.keyson[numnote] -= 1
                #self.noteson.remove( event.data1 )
            elif event.status == 224: #pitch wheel
                self.pitchwheel = event.data2 # will sit at 64 for regular pitch, can go from 0 to 127
            elif event.status == 176: #mod wheel
                self.modwheel = event.data2 #somewhere between 0 and 127  
            ## this was a midi event
            return 1
        else:
            ## this was not a midi event
            return 0

    def newnoteson(self):
        newonlist = self.newnotesonlist
        self.newnotesonlist = [] #clear out these new on notes, assume they'll be taken care of
        return newonlist
    
    def newnotesoff(self):
        newofflist = self.newnotesofflist
        self.newnotesofflist = [] #clear out the off notes, assume they are taken care of
        return newofflist

    def quit(self):
        del self.midiin
        pygame.midi.quit()

