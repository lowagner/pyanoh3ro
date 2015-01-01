from metagame import *
from ddr import *
from cmd import *
from iomidi import *
from piece import *
import pygame
import midi as MIDI # from python-midi vishnubob github, for easy reading/writing of midi files
import config
from collections import deque # this is for fast popping of lists from the left
import itertools
import mingus.core.chords as CHORDS
import mingus.core.notes as NOTES

class EditClass( DDRClass ): # inherit from the DDRClass
#### EDIT CLASS
    def __init__( self, piecedir, midi, piecesettings = { 
            "TempoPercent" : 100, "Difficulty" : 0,
            "BookmarkTicks" : [],
            "AllowedDifficulties" : [ 0 ],
            "Sandbox" : config.SANDBOXplay,
            "PlayerStarts" : config.PLAYERstarts,
            "PlayerTrack" : 0,
            "Metronome" : config.METRONOMEdefault } ):
        DDRClass.__init__( self, piecedir, midi, piecesettings )
        self.noteson = {} # notes on that we will eventually turn off.
        self.sandbox = 1 # no matter what, in EDIT mode you should allow sandbox maneuvering
        self.currentvelocity = 100 # default note velocity.
        self.currenttrack = 0
        self.noteclipboard = [] # for copy pasting
    
        # set the default state of the editor
        self.allowedchanges = [ 'state' ]
        self.state = -1 # start uninitialized
        #self.EXITstate = 0 # 
        self.NAVIGATIONstate = 1 # default state after pressing escape.  for copy/pasting, etc.  
        self.SELECTstate = 2 # visual block/line type stuff
        self.COMMANDstate = 3 # after pressing escape, then colon (:).  vim-like command mode
        self.INSERTstate = 4 # after pressing i,I, a,A, you can insert notes on the keyboard
        self.CHORDstate = 5 

        self.commandlist = deque([], config.COMMANDhistory) # only allow the deck to get so big...
        self.commandlistindex = -1
        self.commandfont = config.FONT
        self.commandfontcolor = (255,255,255)
        self.commandfontsize = int(24*config.FONTSIZEmultiplier)
        self.commandbackcolor = (0, 0, 0)
        self.helperfontcolor = (255,255,255)
        self.helperfontsize = int(18*config.FONTSIZEmultiplier)
        self.helperbackcolor = (0, 0, 0)
        self.statenames = { self.NAVIGATIONstate : "Navigation",
                            self.SELECTstate : "Select",
                            self.COMMANDstate : "Command",
                            self.INSERTstate : "Insert",
                            self.CHORDstate : "Chord" }
        self.helper = { 
            self.NAVIGATIONstate : [ 0, #start line
                 [ " ctrl+j|k   scroll this helper list down|up",
                   "   ctrl+/   search this helper list",
                   " ctrl+n|N   repeat search forward|backward",
                   "",
                   "  h|j|k|l   move left|down|up|right",
                   "  H|J|K|L   move left|down|up|right faster",
                   "      g|G   go to beginning|end of piece",
                   "    SPACE   start/stop piece playing",
                   "",
                   "ESC|/|:|;   go to command mode",
                   "        i   go to insert mode",
                   "        a   insert mode:  rolls on input",
                   "        c   toggle click track (metronome)",
                   "        C   toggle click track volume loud/soft",
                   "",
                   "1-9|0|-|+   change time grid duration",
                   "      o|O   offset time grid forward|backward",
                   "        q   quick add note at cursor",
                   "        Q   add note at cursor and advance",
                   "      [|]   lower|raise volume at cursor",
                   "shift+[|]   quickly decrease|increase volume",
                   "    ENTER   play note at cursor",
                   "shift+ENT   play existing chord on line",
                   "",
                   "      v|V   activate/deactivate visual block|line",
                   "   ctrl+v   swap cursor/anchor of visual block",
                   " ctrl+h|l   swap cursor/anchor key position",
                   "",
                   "        y   yank (copy) notes with any overlap",
                   "        p   paste relative to cursor",
                   "        d   delete* notes with any overlap",
                   "        x   carve* note overlap only",
                   "            *both d and x copy the deleted notes",
                   "      X|D   carve|delete but without copying.",
                   "        P   paste and remove notes from underlying region",
                   "   ctrl+p   swap:  paste but copy existing notes",
                   "        m   merge notes under cursor",
                   "        M   merge with next note",
                   "      e|E   extend notes by half|full grid duration",
                   "      s|S   shorten notes by half|quarter",
                   "",
                   "  PgUp|Dn   move up|down by one screen",
                   " HOME|END   move all the way left|right",
                   "        `   back to last non-trivial jump point",
                   "   ctrl+b   add/delete bookmark here",
                   "      b|B   cycle forward|backward through bookmarks",
                   "shift+SPACE start looping from a bookmark to the next",
                    ]
               ],
            self.SELECTstate : [ 0, #start line
                 [ "ctrl+j|k    scroll this helper list down|up",
                   " h|j|k|l    move left|down|up|right" ]
               ],
            self.COMMANDstate : [ 0, #start line
                 [ "ctrl+j|k    scroll this helper list down|up",
                   "  ESCAPE    go back to navigation mode",
                   " up|down    navigate command history",
                   " PgUp|Dn    earliest|clear command",
                   " ",
                   "Type in and press enter to execute:",
                   "  q|quit    quit PyanoH3ro",
                   "s|save|w    save piece",
                   "  return    return to main menu ",
                   "  reload    reloads the piece from save file",
                   "   clear    clears the piece",
                   "",
                   "    Nm/D    set time grid to N/D times measure length ",
                   "    Nn/D    set grid to N/D times quarter note length ",
                   "",
                   "     t X    set current tempo to X (10 to 300, in bpm)",
                   "    ts X    set time signature to X (beats per measure)",
                   "     a X    add annotation with text X here",
                   "r t|ts|a    remove (t)empo|(ts) time signature|(a)nnotation",
                   "       X    go to line X",
                   "",
                   "     e X    edit track X",
                   "     i X    change track instrument to X",
                   "            X can be a number (0 to 127), or a name",
                   "     v X    set quick-input velocity to X (0 to 127)",
                   ]
               ],
            self.INSERTstate : [ 0, #start line
                 [ "ctrl+j|k    scroll this helper list down|up",
                   "  ESCAPE    go to navigation mode",
                   "   /|:|;    go to command mode",
                   "   SPACE    start/stop piano rolling",
                   "",
                   "Use keys from NAVIGATION mode to navigate,",
                   "change the time grid, and more.",
                   "",
                   " Play your dang MIDI keyboard! "
                   ]
               ],
            self.CHORDstate : [ 0, #start line
                 [ "ctrl+j|k    scroll this helper list down|up",
                   "",
                   "Type in and press enter to add chord:",
                   "       C    C major in selected region",
                   "      C7    C7 major in selected region",
                   "      C9    C9 major in selected region",
                   "      Am    A minor chord",
                   "and so on, with many other keys and combos.",
                   "     C;/    C major arpeggio going up",
                   "     C;\    C major arpeggio going down",
                   "    C;\/    C major arpeggio down and up",
                   "    C;/\    C major arpeggio up and down",
                   "and also with other keys."
                   ]
               ],
            }

        # this helper guy gives information on what the heck you're doing
        self.helperlines = [] # current list of text to be written to the screen
        self.lasthelpsearched = ""
        self.helperlinemax = max(1, config.HELPERLINEmax)

        self.setstate( state=self.NAVIGATIONstate )

        # the following variables modify the above editing states:
        self.insertmode = 0    # -1 = Ghost insert, 0 = friendly insert, 1 = aggressive insert
                               # it depends on what the self.state is, what insertmode does.
        self.waitforkeytoplay = 0

        # for grabbing information...
        self.commander = CommandClass( self.docommand, "cmd" )
        self.chordcommander = CommandClass( self.addquickchordinselection, "quick chord" )
        
        self.preemptor = None
        self.preemptingfor = { 
            "search help" : CommandClass( self.searchhelp, "search help" )
        }

        self.anchor = 0 #will go to [ midinote, anchorposition ]
        #self.trackticks = [ 0 for t in self.piece.notes ]

    def addtrack( self ):
        #self.trackticks.append(0)
        self.piece.addtrack()
        self.noisytracks.add( len(self.piece.notes)-1 )

    def setstate( self, **kwargs ):
        for key, value in kwargs.iteritems():
            if key in self.allowedchanges:
                setattr( self, key, value )
                if key == "state":
                    self.setalert("Now in "+self.statenames[value])
                    self.sethelperlines( value )
            else:
                Warn("in EditClass:setstate - key "+ key +" is protected!!") 

    def update( self, dt, midi ):
        DDRClass.update( self, dt, midi )

    def process( self, event, midi ):
        '''here we provide methods for changing things.
        we don't process midi input here; rather we allow for midi output
        when we want to, say on pressing some non-midi device it makes a noise.'''

        if self.preemptor:
            if len(self.preemptor.process( event, midi )):
                self.preemptor = None
            return {}

        elif self.metanav( event, midi ):
            return {}

        elif self.state == self.NAVIGATIONstate:
            return self.navprocess( event, midi )
        
        elif self.state == self.INSERTstate:
            return self.insprocess( event, midi )
        
        elif self.state == self.COMMANDstate:
            return self.commander.process( event, midi )

        elif self.state == self.CHORDstate:
            return self.chordcommander.process( event, midi )

        else:
            Error(" UNKNOWN state in EditClass.process( self, event, midi ) ")
        return {}

    def navprocess( self, event, midi ):
        # NAVIGATION STATE:  after hitting escape, we get to this mode.
        if event.type == pygame.KEYDOWN:
            if ( event.key == 27 ):
                if self.anchor:
                    self.anchor = 0
                else:
                    self.setstate( state=self.COMMANDstate ) 
            elif ( event.key == pygame.K_SLASH
                or event.key == pygame.K_SEMICOLON or event.key == pygame.K_COLON ):
                self.setstate( state=self.COMMANDstate  )
            elif event.key == pygame.K_o:
                # set tick offset
                # SUGGEST:  don't allow note-offset if note does not divide measure...
                self.currentnoteoffset = ( self.currentnoteoffset + self.currentnoteticks // 2 ) % self.currentnoteticks
                self.setcurrentticksandload( 
                    self.roundtonoteticks( self.currentabsoluteticks, 
                        pygame.key.get_mods() & pygame.KMOD_SHIFT 
                    ) 
                )
            elif event.key == pygame.K_i or event.key == pygame.K_a:
                # insert mode.  i = insert at current position, a = set insert, get playing ready
                if event.key == pygame.K_a:
                    self.waitforkeytoplay = 1
                # common to both
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.insertmode = 1 # aggressive insert
                else:
                    self.insertmode = 0 # friendly insert
                self.setstate( state=self.INSERTstate )

            elif event.key == pygame.K_q:
                # quick insert.  add note at cursor
                if self.anchor:
                    self.setstate( state=self.CHORDstate ) 
                    self.setalert("Choose shorthand chord") 
                else:
                    self.addnoteatcursor( midi )
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.setcurrentticksandload( self.currentabsoluteticks + self.currentnoteticks )
                # NEED NEW FUNCTIONALITY FOR SELECTIONS.
            elif event.key == pygame.K_d:
                self.deletecursorselection( pygame.key.get_mods() & pygame.KMOD_SHIFT )
            
            elif event.key == pygame.K_x:
                self.carvecursorselection( pygame.key.get_mods() & pygame.KMOD_SHIFT )
            
            elif event.key == pygame.K_m:
                self.mergecursorselection( pygame.key.get_mods() & pygame.KMOD_SHIFT )
            
            elif event.key == pygame.K_y:
                # yank (copy)
                self.copycursorselection()
            
            elif event.key == pygame.K_p:
                # paste
                self.pastenoteclipboard( pygame.key.get_mods() & pygame.KMOD_SHIFT,
                    pygame.key.get_mods() & pygame.KMOD_CTRL )
            
            elif event.key == pygame.K_s:
                self.shortencursorselection( pygame.key.get_mods() & pygame.KMOD_SHIFT )
            
            elif event.key == pygame.K_e:
                self.extendcursorselection( pygame.key.get_mods() & pygame.KMOD_SHIFT )

            elif event.key == pygame.K_LEFTBRACKET:
                # lower volume of notes under cursor
                self.changevelocityatcursorselection( midi, -1, pygame.key.get_mods() & pygame.KMOD_SHIFT )
            elif event.key == pygame.K_RIGHTBRACKET:
                # raise volume of notes under cursor
                self.changevelocityatcursorselection( midi,  1, pygame.key.get_mods() & pygame.KMOD_SHIFT )

            elif event.key == pygame.K_v:
                if self.play:
                    currentticks = self.roundtonoteticks( self.currentabsoluteticks )
                else:
                    currentticks = self.currentabsoluteticks

                if self.anchor:
                    # we already have a selection going.
                    if self.anchor[0] != -1 and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        # we have a selection, but it wasn't full line, but now we want to make it full line.
                        self.anchor[0] = -1
                    elif (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        # switch anchor and cursor
                        switch = [ self.anchor[0], self.anchor[1] ]
                        if switch[0] == -1:
                            # if anchor was holding the entire row...
                            # keep the cursor where it is:
                            switch[0] = self.keymusic.cursorkeyindex + config.LOWESTnote   
                            # make sure that it will now, too:
                            self.anchor = [ -1, currentticks ]
                        else:
                            self.anchor = [ self.keymusic.cursorkeyindex + config.LOWESTnote, 
                                            currentticks ]
                        self.keymusic.centeredmidinote = switch[0]
                        self.setcurrentticksandload( switch[1] )
                        self.play = False
                        if config.SMALLalerts:
                            self.setalert("Cursor/visual anchor swapped.")
                        else:
                            self.setalert("Cursor and visual block anchor swapped.")

                    else:
                        # otherwise we hit V again, and we probably want to escape selection mode.
                        self.anchor = 0
                else:
                    # select mode here we come!

                    midinote = -1
                    if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        # if the shift key is not on, pick the note specifically
                        midinote = self.keymusic.cursorkeyindex + config.LOWESTnote   
                    
                    self.anchor = [ midinote, currentticks ]
            
            elif event.key == pygame.K_RETURN:
                # play selected notes
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    # play the entire line if shift is pressed
                    currentticks = self.roundtonoteticks( self.currentabsoluteticks )
                    if self.anchor:
                        originalanchor0 = self.anchor[0]
                        self.anchor[0] = -1
                    else:
                        originalanchor0 = None
                        self.anchor = [ -1, currentticks ]

                    # check if there were selected notes
                    self.selectcursorselection()
                    if self.selectednotes:
                        for note in self.selectednotes:
                            # hit the key:
                            self.keymusic.hitkey( midi, note[0], 
                                note[1], self.tickstosecs(note[2]),
                                self.piece.channels[self.currenttrack], True 
                            )
                    else:
                        if self.anchor[1] != currentticks:
                            self.setalert("No notes to play in these rows.")
                        else:
                            self.setalert("No notes to play in this row")

                    if originalanchor0 == None:
                        self.anchor = 0
                    else:
                        self.anchor = [ originalanchor0, self.anchor[1] ]
                else:
                    # no notes were selected
                    self.keymusic.hitkey( midi, self.keymusic.cursorkeyindex + config.LOWESTnote,
                        100,    # velocity
                        1,      # duration
                        self.piece.channels[self.currenttrack], 
                        True  # play sound
                    )

            elif ( pygame.key.get_mods() & pygame.KMOD_CTRL
            and (event.key == pygame.K_h or event.key == pygame.K_l ) ):
                if self.anchor and self.anchor[0] != -1:
                    swap0 = self.anchor[0]
                    self.anchor[0] = self.keymusic.cursorkeyindex + config.LOWESTnote
                    self.keymusic.centeredmidinote = swap0
                    if config.SMALLalerts:
                        self.setalert("Swapping cursor/visual anchor key")
                    else:
                        self.setalert("Swapping cursor and visual anchor key position")
            elif self.commonnav( event, midi ):
#                if self.anchor and self.previousabsoluteticks != self.currentabsoluteticks:
#                    if ( self.previousabsoluteticks >= self.anchor[1] and
#                         self.currentabsoluteticks < self.anchor[1] ):
#                        # if had an anchor and now are moving below it,
#                        # reset the anchor to be at a height of...
#                        self.anchor[1] += self.currentnoteticks
#                        # so that it continues to capture the line it was originally on.
#                    elif ( self.previousabsoluteticks < self.anchor[1] and
#                         self.currentabsoluteticks >= self.anchor[1] ):
#                        # if had an anchor and now are moving above it,
#                        # reset the anchor to be at a height of...
#                        self.anchor[1] -= self.currentnoteticks
#                        # so that it continues to capture the line it was originally on.
                        
                return {}
            elif self.commongrid( event, midi ):
                return {}

        ## gamechunk must return a dictionary after processing events.
        ## if you don't want anything to happen, pass an empty dict:
        return {}

    def insprocess( self, event, midi ):
        # INSERT STATE.  From Navigation mode, we can get to INSERT mode by pressing the following keys:
        # NOT YET IMPLEMENTED:
        #   While holding down piano keys, if you move up/down (k/l or arrow keys),
        #   the duration of the note is extended.
        # method 2:
        # Hit keys [ASDFG, QWERTY] (white keys, black keys), which appear over the key on the screen.
        # They appear over different keys, depending on where your cursor is, left/right-speaking.
        if event.type == pygame.KEYDOWN:
            if event.key == 27:
                self.setstate( state=self.NAVIGATIONstate  )
            elif (event.key == pygame.K_SLASH
                   or event.key == pygame.K_SEMICOLON or event.key == pygame.K_COLON ):
                self.setstate( state=self.COMMANDstate  ) 
            elif (event.key == pygame.K_i):
                self.waitforkeytoplay = 1 - self.waitforkeytoplay
                if self.waitforkeytoplay:
                    if config.SMALLalerts:
                        self.setalert( "Piano rolls on input" )
                    else:
                        self.setalert( "Pressing a key will start notes-a-rolling" )
                else:
                    self.setalert( "Piano static on input" )
            elif (event.key == pygame.K_i):
                self.insertmode = 1 - self.insertmode
                if self.insertmode:
                    self.setalert( "Aggressive insert" )
                else:
                    self.setalert( "Friendly insert" )
            elif self.commonnav( event, midi ):
                return {}
            elif self.commongrid( event, midi ):
                return {}
        return {}
    
    def docommand( self, command, midi ):
        # COMMAND STATE.  in navigation mode, press : and then type various commands:
        if command:
            if command == "quit" or command == "q":
                return { "gamestate" : 0, "printme" : "quitting from edit mode" } 
            elif command == "return":
                midi.clearall()
                return { "gamestate" : config.GAMESTATEmainmenu, 
                         "printme" : "return from edit mode" } 
            elif command == "reload":
                midi.clearall()
                self.__init__( self.piece.piecedir, midi )
                return { "printme" : "reloaded from file" }
            elif command == "save" or command == "s" or command == "w":
                self.piece.settings["BookmarkTicks"] = self.bookmarkticks
                self.piece.writeinfo()
                self.piece.writemidi()
                return self.wrapupcommand( self.piece.piecedir+" saved!" )
            elif command == "clear" or command == "reset":
                midi.clearall()
                self.piece.clear()
                self.play = False
                self.setcurrentticksandload(0)
                return self.wrapupcommand( "all notes erased." )
            elif command == "search":
                self.preemptor = self.preemptingfor["search help"]
                return self.wrapupcommand("search help")
            else:
                split = command.split()

                if split[0] == "v":
                    try:
                        velocity = int(split[1])
                        if velocity <= 0:
                            velocity = 1
                        elif velocity > 127:
                            velocity = 127

                        self.currentvelocity = velocity 
                        return self.wrapupcommand("Setting quick-input velocity to "+str(velocity) )
                    except (IndexError, ValueError):
                        return self.wrapupcommand("use \"v X\" to set velocity/volume to X")

                elif split[0] == "t":
                    try:
                        tempo = float(split[1])
                        if tempo < 10:
                            tempo = 10
                        elif tempo > 300:
                            tempo = 300
                        
                        self.piece.addtempoevent( tempo, 
                            self.roundtonoteticks( self.currentabsoluteticks )
                        )
                        self.setcurrentticksandload( self.currentabsoluteticks )

                        return self.wrapupcommand("setting current tempo to "+str(tempo) )
                    except (IndexError, ValueError):
                        return self.wrapupcommand("use \"t X\" to set tempo to X")
                
                elif split[0] == "ts":
                    try:
                        ts = int(split[1])
                        if ts < 1:
                            ts = 1
                        elif ts > 25:
                            ts = 25
                        
                        self.piece.addtimesignatureevent( ts,  
                            self.roundtonoteticks( self.currentabsoluteticks )
                        )
                        self.setcurrentticksandload( self.currentabsoluteticks )

                        return self.wrapupcommand("setting current time signature to "+str(ts) )
                    except (IndexError, ValueError):
                        return self.wrapupcommand("use \"ts X\" to set time signature numerator to X")
                elif split[0] == "r":
                    try: 
                        split1 = split[1]
                        if split1 == "ts":
                            if self.piece.removetimesignatureevent( self.currentabsoluteticks ):
                                return self.wrapupcommand("no current time signature to remove")
                            else:
                                return self.wrapupcommand("removing current time signature")
                                self.setcurrentticksandload( self.currentabsoluteticks )
                        elif split1 == "t":
                            if self.piece.removetempoevent( self.currentabsoluteticks ):
                                return self.wrapupcommand("no current tempo to remove")
                            else:
                                return self.wrapupcommand("removing current tempo")
                                self.setcurrentticksandload( self.currentabsoluteticks )
                        elif split1 == "a":
                            if self.addremovetext("") == -1:
                                self.setcurrentticksandload(self.currentabsoluteticks)
                                return self.wrapupcommand("removing annotation")
                            else:
                                return self.wrapupcommand("no annotation to remove")
                        else:
                            raise IndexError
                    except IndexError:
                        return self.wrapupcommand("use \"r t|ts|a\" to remove tempo|timesignature|annotation")
                elif split[0] == "i":
                    i = None
                    try:
                        i = int(split[1])
                    except ValueError:
                        try:
                            i = config.INSTRUMENT[split[1]]
                        except KeyError:
                            pass
                    except IndexError:
                        return self.wrapupcommand("use \"i X\" to set track instrument to X")
                    
                    if i == None:
                        return self.wrapupcommand( "unknown instrument" )
                    elif i == "drums":
                        self.piece.setchannel( midi, self.currenttrack, 9 )
                        return self.wrapupcommand( "setting track to drums (channel 9)" )
                    else:
                        if i < 0:
                            i = 0
                        elif i > 127:
                            i = 127
                        self.piece.setinstrument( midi, self.currenttrack, i )
                        return self.wrapupcommand( "setting instrument to "+str(i) )

                elif split[0] == "a":
                    text = " ".join(split[1:])
                    result = self.addremovetext( text )
                    currentticks = self.roundtonoteticks( self.currentabsoluteticks )
                    self.setcurrentticksandload(currentticks)
                    if result == 1:
                        return self.wrapupcommand("Added annotation")
                    elif result == -1:
                        return self.wrapupcommand("Removed annotation")
                    else:
                        return self.wrapupcommand("No annotation to remove here")
                
                elif split[0] == "e":
                    track = None
                    try:
                        track = int(split[1])
                        
                        if track == self.currenttrack:
                            return self.wrapupcommand("you are editing track "+str(track)+" already")
                        else:
                            if track < 0:
                                track = 0
                                return self.wrapupcommand("editing track 0 (no negatives)")
                            elif track >= len(self.piece.notes): 
                                track = len(self.piece.notes)
                                self.addtrack()
                                return self.wrapupcommand("adding track, editing "+str(track))
                            else:
                                return self.wrapupcommand("editing track "+str(track))
                            
                            # switch from one track to another
#                                    self.trackticks[self.currenttrack] = self.currentabsoluteticks
                            self.currenttrack = track
                            self.setcurrentticksandload(self.currentabsoluteticks) #self.trackticks[track] )
#                                    self.previousabsoluteticks = 0 
                            
                    except ValueError:
                        return self.wrapupcommand( "unknown track to edit" )
                elif self.readnotecode( command ):
                    self.setcurrentticksandload( self.currentabsoluteticks )
                    return self.wrapupcommand( "Set notecode to "+self.notecode )
                else:
                    # try to see if the command is an integer (for a line count)
                    try:
                        integer = int(split[0])
                        newticks = self.currentnoteticks*integer
                        if newticks != self.currentabsoluteticks:
                            lastcurrentnoteticks = self.piece.notes[self.currenttrack][-1].absoluteticks
                            lastmeasureticks = self.piece.getfloormeasureticks( lastcurrentnoteticks )
                            if newticks != 0 and newticks != lastmeasureticks:
                                self.previousabsoluteticks = self.currentabsoluteticks

                            self.setcurrentticksandload( newticks )
                            
                        return self.wrapupcommand("at line "+str(integer))
                        
                    except (IndexError, ValueError):
                        return self.wrapupcommand( "unknown command: "+command )

        self.setstate( state=self.NAVIGATIONstate  )
        return { "printme" : "back to navigation" }

    def wrapupcommand( self, alert ):
        self.setstate( state=self.NAVIGATIONstate  )
        self.setalert( alert )
        return { "printme" : alert }

#### EDIT CLASS
    def processmidi( self, midi ):
        # common processing of midi.  always make the sound.
        newnoteson = midi.newnoteson()
        for note in newnoteson:
            midi.startnote( note[0], note[1], self.currenttrack ) #start note[0] with velocity note[1]
            # also light up the appropriate key on the background
            self.keymusic.brightenkey( note[0], note[1] ) 
            
        newnotesoff = midi.newnotesoff()
        for note in newnotesoff:
            midi.endnote( note, self.currenttrack ) # stop note note

        if self.state == self.INSERTstate:
            if len(newnoteson): 
                if not self.play:  # if we are not playing
                    if self.waitforkeytoplay: # see if we are waiting for a key to start play
                        self.play = True

            # on notes go on no matter what
            for note in newnoteson:
                self.addnoteonpresently( midi, note[0], note[1], False ) # but do not sound again

            # off notes are different depending on whether you play or not.
            if self.play:
                # if playing, let the ends of the notes fall where they may.
                for note in newnotesoff:
                    self.addnoteoffpresently( midi, note )
            else:
                # if not playing, offset the ends of the note by currentnoteticks.
                for note in newnotesoff:
                    self.addnoteoffpresently( midi, note, self.currentnoteticks )
        
        return {}

    def sethelperlines( self, state ):
        start = self.helper[ state ][0] 
        self.helperlines = ([ (self.statenames[ state ]).upper() ] 
                            + self.helper[ state ][1][ start : start+self.helperlinemax ])
        
        if len(self.helperlines):
            fontandsize = pygame.font.SysFont(config.FONT, self.helperfontsize)
            self.helperlabel = []
            self.helperlabelbox = []
            self.maxhelperwidth = 0
            for i in range(len(self.helperlines)):
                self.helperlabel.append( fontandsize.render( self.helperlines[i], 1, self.helperfontcolor ) )
                self.helperlabelbox.append( self.helperlabel[-1].get_rect() )
                if self.helperlabelbox[i].width > self.maxhelperwidth:
                    self.maxhelperwidth = self.helperlabelbox[i].width
        
    def metanav( self, event, midi ):
        # metanav for things that are ctrl based...
        if event.type == pygame.KEYDOWN and pygame.key.get_mods() & pygame.KMOD_CTRL:
            if event.key == pygame.K_j or event.key == pygame.K_DOWN: # press down
                # move down in the current helper list
                if self.helper[ self.state ][0] < len(self.helper[ self.state ][1]) - self.helperlinemax:
                    self.helper[ self.state ][0] += 1
                    self.sethelperlines( self.state )
                return 1
            elif event.key == pygame.K_k or event.key == pygame.K_UP: # press up
                # move down in the current helper list
                if self.helper[ self.state ][0] > 0:
                    self.helper[ self.state ][0] -= 1
                    self.sethelperlines( self.state )
                return 1
            elif ( event.key == pygame.K_SLASH ):
                self.preemptor = self.preemptorlist["search help"]
                self.setalert("Search in help.")
                return 1
            elif ( event.key == pygame.K_n ):
                if self.lasthelpsearched:
                    self.searchhelp( self.lasthelpsearched, midi,
                        pygame.key.get_mods() & pygame.KMOD_SHIFT )
                else:
                    self.setalert("Try ctrl+/ to search help.")
                return 1
                
                
        return 0

#### EDIT CLASS 
    
    def addremovetext( self, text ):
        return self.piece.addremovetextevent( text, self.roundtonoteticks( self.currentabsoluteticks ),
            self.currenttrack )

    def searchhelp( self, text, midi, gobackwards=0 ):
        self.lasthelpsearched = text
        if not gobackwards:
            originalindex = self.helper[self.state][0]
            success = False
            i = originalindex+1
            while i < len(self.helper[self.state][1]):
                if text in self.helper[self.state][1][i]:
                    self.helper[self.state][0] = i        
                    success = True
                    break
                i += 1
            if success:
                self.sethelperlines( self.state )
                self.setalert("Text found in help." )
            else:
                i = 0
                while i <= originalindex:
                    if text in self.helper[self.state][1][i]:
                        self.helper[self.state][0] = i        
                        success = True
                        break
                    i += 1
                if success:
                    self.sethelperlines( self.state )
                    self.setalert("Wrapped, found text in help.")
                else:
                    self.setalert("Text not found in help.")
        else:
            # going backwards
            originalindex = self.helper[self.state][0]
            success = False
            i = originalindex-1
            while i >= 0:
                if text in self.helper[self.state][1][i]:
                    self.helper[self.state][0] = i        
                    success = True
                    break
                i -= 1
            if success:
                self.sethelperlines( self.state )
                self.setalert("Text found in help." )
            else:
                i = len(self.helper[self.state][1])-1
                while i > originalindex:
                    if text in self.helper[self.state][1][i]:
                        self.helper[self.state][0] = i        
                        success = True
                        break
                    i -= 1
                if success:
                    self.sethelperlines( self.state )
                    self.setalert("Wrapped, found text in help.")
                else:
                    self.setalert("Text not found in help.")
        return { "printme" : "Searching help for "+text }
    
    def addmidinote( self, note ):
        if note.velocity:
            newnote = MIDI.NoteOnEvent( pitch = note.pitch,
                    velocity = note.data[1] )
        else:
            newnote = MIDI.NoteOffEvent( pitch = note.pitch )
        newnote.absoluteticks = note.absoluteticks 
        self.piece.addmidinote( newnote, self.currenttrack )

    def addnote( self, midinote, velocity, absticks, duration ):
        # abs ticks is the start of the note, duration is how long it is.

        # first delete any notes that are in this vicinity
        selected, midiselected = self.piece.selectnotes( 
            [absticks, absticks+duration], 
            [midinote], 
            self.currenttrack 
        )
        self.piece.deletenotes( selected, self.currenttrack )

        # then add the note 
        self.piece.addnote( midinote, velocity, absticks, duration, self.currenttrack )

    def addsnote( self, midi, midinote, velocity, absticks, duration, playsound=True ):
        ''' add sounded note '''
        self.addnote( midinote, velocity, absticks, duration )

        # and hit a key
        self.keymusic.hitkey( midi, midinote, velocity, self.tickstosecs( duration ),
                              self.piece.channels[self.currenttrack], playsound )

        if not self.play:
            # if we're not playing, then add in the note to the notes that should be sounded
            self.setcurrentticksandload( self.currentabsoluteticks )
        else:
            # if we are playing, we don't want the note to be played twice, once by the player
            # and secondly by the computer.  so just show it onscreen.
            # display turn note on
            reltickpixels = (absticks-self.currentabsoluteticks)* self.pixelspertick
            self.keymusic.addnote( midinote, velocity, reltickpixels )
            reltickpixels += (duration)* self.pixelspertick
            # turn note off after duration...
            self.keymusic.addnote( midinote, 0, reltickpixels )
            

    def addnotepresently( self, midi, midinote, velocity=100, playsound=True ):
        # add note at current absolute ticks, with duration currentnoteticks
        self.addsnote( midi, midinote, velocity, 
                      self.roundtonoteticks( self.currentabsoluteticks ), 
                      self.currentnoteticks-1, playsound )
    
    def addnoteonpresently( self, midi, midinote, velocity=100, playsound=True ):
        # add note at current absolute ticks, with duration currentnoteticks
        self.noteson[ midinote ] = [ velocity, self.roundtonoteticks( self.currentabsoluteticks ) ]

        self.keymusic.hitkey( midi, midinote, velocity, 1.0,
                              self.piece.channels[self.currenttrack], playsound )
    
    def addnoteoffpresently( self, midi, midinote, offset=0 ):
        # add note off at current absolute ticks
        try:
            # self.noteson[ midinote] = [ velocity, start_absoluteticks ]
            note = self.noteson[ midinote ]
            # make the note at least as long as the tick-divisions, if not a bit longer...
            notelength = max(   self.currentnoteticks, 
                                ( self.roundtonoteticks( self.currentabsoluteticks ) 
                                 -note[1] + offset )   ) - config.EDITnotespace
            # args:  midi, midinote, velocity, absticks, duration, playsound=True
            self.addsnote( midi, midinote, note[0], note[1], notelength, False )
            
            del self.noteson[ midinote ]

        except KeyError:
            pass

    def addnoteatcursor( self, midi ):
        self.addnotepresently( midi, self.keymusic.cursorkeyindex + config.LOWESTnote, 
                               self.currentvelocity, True ) # play sound
   
#### EDIT CLASS 

    def changevelocityofselectednotes( self, midi, change, playsound ):
        for note in self.selectedmidinotes:
            if note.name == "Note On":
                note.velocity += change
                if note.velocity > 127:
                    note.velocity = 127
                elif note.velocity <= 0:
                    note.velocity = 1

                if playsound:
                    midi.playnote( note.pitch, note.velocity, 1, 
                                   self.piece.channels[self.currenttrack] )
        
        self.setcurrentticksandload( self.currentabsoluteticks ) 
    
    def changevelocityatcursorselection( self, midi, direction, muchchange=False ):
        tickmin, tickmax, midimin, midimax = self.selectcursorselection()

        if muchchange:
            direction *= 10

        self.changevelocityofselectednotes( midi, direction, True )
        if config.SMALLalerts:
            self.setalert( "Volume changed")
        else:
            self.setalert( "Volume changed "+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" lines." )

#### EDIT CLASS 
    
    def selectnotes( self, tickrange, midirange=None ): 
        self.selectednotes, self.selectedmidinotes = self.piece.selectnotes( 
            tickrange, midirange, self.currenttrack 
        )

    def getselectionregion( self ):
        currentticks = self.roundtonoteticks( self.currentabsoluteticks )
        if self.anchor:
            if currentticks >= self.anchor[1]:
                # we are ahead of the anchor
                tickmin = self.anchor[1]
                tickmax = currentticks + self.currentnoteticks
            else:
                # the anchor is ahead of us
                tickmin = currentticks
                tickmax = self.anchor[1] + self.currentnoteticks

            if self.anchor[0] == -1:
                midimin = config.LOWESTnote
                midimax = config.HIGHESTnote
            else:
                cursormidi = self.keymusic.cursorkeyindex + config.LOWESTnote
                if cursormidi > self.anchor[0]:
                    # we are right of the anchor
                    midimax = cursormidi
                    midimin = self.anchor[0]
                else:
                    # we are left of the anchor
                    midimax = self.anchor[0]
                    midimin = cursormidi
        else:
            tickmin = currentticks
            tickmax = tickmin + self.currentnoteticks
            midimin = self.keymusic.cursorkeyindex + config.LOWESTnote
            midimax = midimin

        return tickmin, tickmax, midimin, midimax

    def selectcursorselection( self ):
        currentticks = self.roundtonoteticks( self.currentabsoluteticks )
        if self.anchor:
            self.previousdeltaregion = []
            if currentticks >= self.anchor[1]:
                # we are ahead of the anchor
                tickmin = self.anchor[1]
                tickmax = currentticks + self.currentnoteticks
                self.previousdeltaregion.append(self.anchor[1] - currentticks)
                self.previousdeltaregion.append(self.currentnoteticks)
            else:
                # the anchor is ahead of us
                tickmin = currentticks
                tickmax = self.anchor[1] + self.currentnoteticks
                self.previousdeltaregion.append(0)
                self.previousdeltaregion.append(self.anchor[1] - currentticks+ self.currentnoteticks)

            if self.anchor[0] == -1:
                midimin = config.LOWESTnote
                midimax = config.HIGHESTnote
                self.previousdeltaregion.append(-127)
                self.previousdeltaregion.append(127)
            else:
                cursormidi = self.keymusic.cursorkeyindex + config.LOWESTnote
                if cursormidi > self.anchor[0]:
                    # we are right of the anchor
                    midimax = cursormidi
                    midimin = self.anchor[0]
                    self.previousdeltaregion.append( self.anchor[0] - cursormidi )
                    self.previousdeltaregion.append(0)
                else:
                    # we are left of the anchor
                    midimax = self.anchor[0]
                    midimin = cursormidi
                    self.previousdeltaregion.append(0)
                    self.previousdeltaregion.append( self.anchor[0] - cursormidi )
        else:
            tickmin = currentticks
            tickmax = tickmin + self.currentnoteticks
            midimin = self.keymusic.cursorkeyindex + config.LOWESTnote
            midimax = midimin
            self.previousdeltaregion = [ 0, self.currentnoteticks, 0, 0 ]

        self.selectnotes( [tickmin,tickmax], [midimin,midimax] )
        return tickmin, tickmax, midimin, midimax

    def deletecursorselection( self, dontkeepnotes=False ):
        # quick delete
        tickmin,tickmax, midimin, midimax = self.selectcursorselection()
        if self.selectednotes:
            # we have a selection going...
            if dontkeepnotes:
                alerttxt = "Deleted notes from "
            else:
                self.copyselectednotes()
                alerttxt = "Cut notes into clipboard from "
            self.piece.deletenotes( self.selectednotes, self.currenttrack )
            self.setcurrentticksandload( self.currentabsoluteticks )
            if config.SMALLalerts:
                self.setalert(alerttxt[:-6])
            else:
                if midimax-midimin >= 127:
                    self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows")
                else:
                    self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows, "+
                    str(midimax-midimin+1)+" columns")
            self.anchor = 0
        else:
            self.setalert("No notes to delete here.")

    def carvecursorselection( self, dontkeepnotes=False ):
        if self.anchor:
            currentticks = self.roundtonoteticks( self.currentabsoluteticks )
            if currentticks >= self.anchor[1]:
                # we are ahead of the anchor
                tickmin = self.anchor[1]
                tickmax = currentticks + self.currentnoteticks
            else:
                # the anchor is ahead of us
                tickmin = currentticks
                tickmax = self.anchor[1] + self.currentnoteticks

            if self.anchor[0] == -1:
                midimin = config.LOWESTnote
                midimax = config.HIGHESTnote
            else:
                cursormidi = self.keymusic.cursorkeyindex + config.LOWESTnote
                if cursormidi > self.anchor[0]:
                    # we are right of the anchor
                    midimax = cursormidi
                    midimin = self.anchor[0]
                else:
                    # we are left of the anchor
                    midimax = self.anchor[0]
                    midimin = cursormidi
        else:
            if self.play:
                tickmin = self.roundtonoteticks( self.currentabsoluteticks )
            else:
                tickmin = self.currentabsoluteticks
            currentticks = tickmin
            tickmax = tickmin + self.currentnoteticks
            midimin = self.keymusic.cursorkeyindex + config.LOWESTnote
            midimax = midimin

        noteclipboard = self.piece.carveoutregion(     #absolute pitches in this noteclipboard
            [tickmin, tickmax],
            [midimin, midimax],
            self.currenttrack )
       
        if noteclipboard:
            if dontkeepnotes:
                alerttxt="Carved notes from "
            else:
                alerttxt="Carved notes to clipboard from "
                self.noteclipboard = []        # relative pitches/ticks in this noteclipboard
                for note in noteclipboard:
                    self.noteclipboard.append( [ note[0] - self.keymusic.cursorkeyindex - config.LOWESTnote,  #pitch
                                              note[1], #velocity
                                              note[2]-currentticks, #absolute ticks
                                              note[3] # duration
                                              ] )
                self.setcurrentticksandload( self.currentabsoluteticks )
            self.anchor = 0
            if config.SMALLalerts:
                self.setalert( alerttxt[:-6] )
            else:
                if midimax-midimin >= 127:
                    self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows")
                else:
                    self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows, "+
                    str(midimax-midimin+1)+" columns")
        else:
            self.setalert("No notes to carve here.")

    def mergecursorselection( self, aggressive=False ):
        # quick delete
        tickmin,tickmax, midimin, midimax = self.selectcursorselection()
        # we have a selection going...
        self.piece.deletenotes( self.selectednotes, self.currenttrack )
        
        i = 0
        while i < len(self.selectednotes):
            notei = self.selectednotes[i]
            j = i + 1 
            while j < len(self.selectednotes):
                notej = self.selectednotes[j]
                if notej[0] == notei[0]: # pitch is the same
                    # modify duration of note i:
                    # duration of note j (notej[3]) plus difference in ticks from i to j:
                    notei[3] = notej[3] + (notej[2] - notei[2]) 
                    del self.selectednotes[j]
                    # would like to "break" here but cannot.  must look at all possible futures.
                else: 
                    j += 1
            i += 1
       
        if self.selectednotes:
            if not aggressive:
                alerttxt = "Merged notes in "
                for note in self.selectednotes:
                    self.piece.addnote( note[0],note[1],note[2],note[3], self.currenttrack )
            else:
                alerttxt = "Attempted a merge next in "
                for note in self.selectednotes:
                    midinote = MIDI.NoteOnEvent( pitch=note[0], velocity=note[1] )
                    midinote.absoluteticks = note[2]
                    # keep the on note for sure:
                    self.addmidinote( midinote )
                    # try to delete any subsequent on notes:
                    if self.piece.deletenextonnote( note[0], note[2], self.currenttrack ):
                        # there were no other on notes.  so we need to add an off note.
                        midinote = MIDI.NoteOffEvent( pitch=note[0] )
                        midinote.absoluteticks = note[2]+note[3]
                        self.addmidinote( midinote )

            self.setcurrentticksandload( self.currentabsoluteticks )
            if config.SMALLalerts: 
                self.setalert( alerttxt[:-4] )
            else:
                if midimax-midimin >= 127:
                    self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows")
                else:
                    self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows, "+
                    str(midimax-midimin+1)+" columns")
            self.anchor = 0
        else:
            self.setalert("No notes to merge here.")
    
    def shortencursorselection( self, aggressive=False ):
        # quick delete
        tickmin,tickmax, midimin, midimax = self.selectcursorselection()
        # we have a selection going...
        self.piece.deletenotes( self.selectednotes, self.currenttrack )
        
        if self.selectednotes:
            for note in self.selectednotes:
                note[3] += config.EDITnotespace
                note[3] *= 0.5**(aggressive+1)
                if note[3] <= config.EDITshortestnote:
                    note[3] = config.EDITshortestnote
                note[3] -= config.EDITnotespace
                self.piece.addnote( note[0],note[1],note[2],note[3], self.currenttrack )
            
            if aggressive:
                alerttxt = "Really shortened notes in "
            else:
                alerttxt = "Shortened notes in "

            self.setcurrentticksandload( self.currentabsoluteticks )
            if config.SMALLalerts: 
                self.setalert( alerttxt[:-4] )
            else:
                if midimax-midimin >= 127:
                    self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows")
                else:
                    self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows, "+
                    str(midimax-midimin+1)+" columns")
        else:
            self.setalert("No notes to shorten here.")
    
    def extendcursorselection( self, aggressive=False ):
        # quick delete
        tickmin,tickmax, midimin, midimax = self.selectcursorselection()
        # we have a selection going...
        self.piece.deletenotes( self.selectednotes, self.currenttrack )
        extension = 0.5*(aggressive+1)*self.currentnoteticks
        i = 0
        while i < len(self.selectednotes):
            notei = self.selectednotes[i]
            j = i + 1 
            while j < len(self.selectednotes):
                notej = self.selectednotes[j]
                if ( notej[0] == notei[0]   # same pitch
                and notej[2] - config.EDITnotespace <= notei[2] + notei[3] + extension ):
                    # pitch is the same and notej got bumped into by notei
                    # so extend notei up into notej
                    notei[3] = notej[3] + (notej[2] - notei[2])  # don't add extension yet.
                    # and note j got killed by note i:
                    del self.selectednotes[j]
                    # would like to "break" here but cannot.  must look at all possible futures.
                else: 
                    j += 1
            i += 1


        if self.selectednotes:
            for note in self.selectednotes:
                # keep the on note for sure:
                midinote = MIDI.NoteOnEvent( pitch=note[0], velocity=note[1] )
                midinote.absoluteticks = note[2]
                self.addmidinote( midinote )
                # try to delete any subsequent on notes which would interfere with
                # this notes extension:
                if self.piece.deleteonnote( note[0], [note[2], note[2]+note[3]+extension+config.EDITnotespace], 
                    self.currenttrack ):
                    # there were no other on notes in the region.  so we need to add an off note.
                    midinote = MIDI.NoteOffEvent( pitch=note[0] )
                    midinote.absoluteticks = note[2]+note[3]+extension
                    self.addmidinote( midinote )

            if aggressive:
                alerttxt="Really extended notes in "
            else:
                alerttxt="Extended notes in "

            self.setcurrentticksandload( self.currentabsoluteticks )
            if config.SMALLalerts: 
                self.setalert( alerttxt[:-4] )
            else:
                if midimax-midimin >= 127:
                    self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows")
                else:
                    self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows, "+
                    str(midimax-midimin+1)+" columns")
        else:
            self.setalert("No notes to extend here.")
    
    def copyselectednotes( self ):
        self.noteclipboard = [] #self.piece.selectednotes[:]
        for note in self.selectednotes:
            self.noteclipboard.append( [ note[0] - self.keymusic.cursorkeyindex - config.LOWESTnote,  #pitch
                                         note[1], #velocity
                                         note[2]-self.currentabsoluteticks, #absolute ticks
                                         note[3] # duration
                                       ] )

    def copycursorselection( self ):
        self.selectcursorselection()
        # we have a selection going...
        if self.selectednotes:
            self.copyselectednotes()
            self.anchor = 0
            self.setalert("Copied notes to clipboard.")
        else:
            self.setalert("No notes to copy.")

    def pastenoteclipboard( self, violently=False, copydeleted=False ):
        if len(self.noteclipboard):
            if self.play:
                currentticks = self.roundtonoteticks( self.currentabsoluteticks )
            else:
                currentticks = self.currentabsoluteticks

            midinote = self.keymusic.cursorkeyindex + config.LOWESTnote   
            if violently or copydeleted:
                # wipe out existing notes in the same area
                tickrange = [ currentticks + self.previousdeltaregion[0],
                              currentticks + self.previousdeltaregion[1] ]

                midirange = [ midinote + self.previousdeltaregion[2],
                              midinote + self.previousdeltaregion[3] ]
                
                # might as well show the region we are destroying, 
                # if we have no anchor already:
                if self.anchor:
                    # don't worry about it
                    pass
                elif midirange[-1] != midirange[0] or tickrange[0] != tickrange[1]:
                    # show the selected|pasted region
                    midi = -1
                    if midirange[0] == midinote:
                        midi = midirange[1]
                    elif midirange[1] == midinote:
                        midi = midirange[0]
                    
                    tick = currentticks
                    if tickrange[0] == currentticks:
                        tick = tickrange[1] - self.currentnoteticks
                    elif tickrange[1] - self.currentnoteticks == currentticks:
                        tick = tickrange[0]
                    self.anchor = [ midi, tick ]

                deadnotes = self.piece.carveoutregion( tickrange, midirange, self.currenttrack )

                for note in self.noteclipboard:
                    self.piece.addnote( note[0]+midinote, note[1], 
                        note[2]+currentticks, note[3], self.currenttrack )
                if copydeleted:
                    if deadnotes:
                        self.noteclipboard = []
                        for note in deadnotes:
                            self.noteclipboard.append( [ note[0] - self.keymusic.cursorkeyindex - config.LOWESTnote,  #pitch
                                                      note[1], #velocity
                                                      note[2]-currentticks, #absolute ticks
                                                      note[3] # duration
                                                      ] )
                        self.setalert("Swapped clipboard/screen contents.")
                    else:
                        self.setalert("Pasted but no existing notes to copy.")
                else:
                    if config.SMALLalerts:
                        self.setalert("Violent paste.")
                    else:
                        self.setalert("Violent paste (deleted underlying note region).")
            else:
                # just remove existing notes when they interfere with adding notes
                self.setalert("Pasted notes from clipboard.")
                for note in self.noteclipboard:
                    absnote = [ note[0]+midinote, note[1], 
                                note[2]+currentticks, note[3] ]
                    # carve out where we add the note, but add a little space for the duration:
                    self.piece.carveoutregion( 
                        [ absnote[2], absnote[2]+note[3]+config.EDITnotespace ],
                        [ absnote[0] ], self.currenttrack 
                    )
                    self.piece.addnote( absnote[0], absnote[1], absnote[2],
                                        absnote[3], self.currenttrack )

            #self.noteclipboard = []
            
            self.setcurrentticksandload( self.currentabsoluteticks )
        else:
            self.setalert("No notes in clipboard.")
    
    def addquickchordinselection( self, text, midi ):
        if text:
            colonindex = text.find(";")
            if colonindex < 0:
                chordtext = text
                arptext = ""
            else:
                chordtext = text[0:colonindex]
                arptext = text[colonindex+1:]
                
            try:
                chordlist = CHORDS.from_shorthand(chordtext)
            except:
                self.setalert("Unknown chord.")
                chordlist = []
                
            if chordlist:
                for i in range(len(chordlist)):
                    chordlist[i] = NOTES.note_to_int(chordlist[i])
                chordlist = list(set(chordlist))
                chordlist.sort()
                
                tickmin, tickmax, midimin, midimax = self.getselectionregion()
                self.addchordinregion( chordlist, [tickmin,tickmax], [midimin,midimax], arptext ) 
                self.setcurrentticksandload( self.currentabsoluteticks )
                #self.anchor = 0
        self.setstate( state=self.NAVIGATIONstate )
        return {}

    def addchordinregion( self, chordlist, tickrange, midirange, arpeggio="" ):
        if arpeggio == "":
            success = False
            absticks = tickrange[0]
            while absticks < tickrange[1]:
                for octave in range(12):
                    for chordnote in chordlist:
                        note = chordnote + octave*12
                        if midirange[0] <= note <= midirange[-1]:
                            self.addnote( note, self.currentvelocity, absticks, 
                                self.currentnoteticks - config.EDITnotespace
                            )
                            success = True

                absticks += self.currentnoteticks

            if success:
                self.setalert("Got chord!")
            else:
                self.setalert("Chord doesn't fit in region")
        else:
            absticks = tickrange[0]
            firstoctave = 12
            lastoctave = 0
            for octave in range(12):
                for chordnote in chordlist:
                    note = chordnote + octave*12
                    if midirange[0] <= note <= midirange[-1]:
                        if octave < firstoctave:
                            firstoctave = octave
                        if octave > lastoctave:
                            lastoctave = octave
            if firstoctave <= lastoctave:
                if arpeggio == "/":
                    deltaoctave = 1 # move up
                    resetoctave = firstoctave
                    initialoctave = firstoctave
                elif arpeggio == "\\":
                    deltaoctave = -1 # move down
                    chordlist.reverse()
                    resetoctave = lastoctave
                    initialoctave = lastoctave 
                elif arpeggio == "/\\":
                    deltaoctave = 1 # move up initially
                    resetoctave = None
                    initialoctave = firstoctave 
                elif arpeggio == "\\/":
                    deltaoctave = -1 # move down
                    chordlist.reverse()
                    resetoctave = None 
                    initialoctave = lastoctave 
                else:
                    self.setalert("Unknown chord modifier.")
                    return
                octave = initialoctave
                while absticks < tickrange[1]:
                    for chordnote in chordlist:
                        note = chordnote + octave*12
                        if midirange[0] <= note <= midirange[-1]:
                            self.addnote( note, self.currentvelocity, absticks, 
                                self.currentnoteticks - config.EDITnotespace
                            )
                            absticks += self.currentnoteticks
                            if absticks >= tickrange[1]:
                                break
                    octave += deltaoctave 
                    if octave > lastoctave or octave < firstoctave:
                        if resetoctave == None:
                            deltaoctave *= -1
                            octave += deltaoctave
                            chordlist.reverse()
                        else:
                            octave = resetoctave

                self.setalert("Arpeggio of type "+arpeggio)
            else:
                self.setalert("Arpeggio doesn't fit here")
        

#### EDIT CLASS 

    def draw( self, screen ):
        if ( self.state == self.NAVIGATIONstate 
          or self.state == self.COMMANDstate or self.state == self.CHORDstate ):
            # draw the cursor if in one of those states:
            self.keymusic.setcursorheight( self.currentnoteticks*self.pixelspertick )

            if self.anchor:
                self.keymusic.setselectanchor( [ self.anchor[0], 
                    (self.anchor[1] - self.currentabsoluteticks)*self.pixelspertick ] )
            else:
                self.keymusic.setselectanchor( 0 )
        else:
            self.keymusic.setcursorheight( 0 )
            self.keymusic.setselectanchor( 0 )

        #backdrop screen
        self.backdrop.draw( screen )
        #draw keyboard and music
        self.keymusic.draw( screen )
        
        if self.preemptor:
            self.preemptor.draw( screen )
        elif self.state == self.COMMANDstate: 
            self.commander.draw( screen )
        elif self.state == self.CHORDstate: 
            self.chordcommander.draw( screen )

        if len(self.helperlines):
            #screenwidth, screenheight = screen.get_size()
            leftx = 10
            topy = 10 #0.1*screenheight
            self.helperlabelbox[0].left = leftx
            self.helperlabelbox[0].top = topy
            helperbgbox = Rect(leftx-5, topy-5, 
                               self.maxhelperwidth+10, 
                               len(self.helperlines)*self.helperlabelbox[0].height+10 )
            pygame.draw.rect( screen, self.helperbackcolor, helperbgbox )
            #pygame.draw.rect( screen, self.helperbackcolor,  self.helperlabelbox[0] )
            screen.blit( self.helperlabel[0], self.helperlabelbox[0] )
            for i in range(1,len(self.helperlines)):
                self.helperlabelbox[i].left = leftx
                self.helperlabelbox[i].top = self.helperlabelbox[i-1].bottom 
                #pygame.draw.rect( screen, self.helperbackcolor,  self.helperlabelbox[i] )
                screen.blit( self.helperlabel[i], self.helperlabelbox[i] )
        
        if self.alerttext:
            self.alertbox.top = 5
            self.alertbox.right = screen.get_width() - 5
            pygame.draw.rect( screen, self.helperbackcolor, self.alertbox ) 
            screen.blit( self.alert, self.alertbox ) 

#### END EDIT CLASS
