# metagame includes basic stuff on backdrops and the gamechunk class
from metagame import *
# playclass inherits from the gamechunk class:  the actual game
from play import *
# menuclass also inherits from gamechunk.  it's for the main menu, setting menu, etc.
from menu import *
# for nice midi input from a keyboard, and output via fluidsynth
from iomidi import *
# for editing compositions:
from edit import *
# for read-writing of dictionaries (settings file) and reading directories for pieces
import pickle
# configuration file for random computer/OS-specific guys
import config
    
class GameClass:
#### GAMECLASS
    def __init__( self ):
        # initialize the pygame module
        pygame.init()
        pygame.mouse.set_visible( False ) # kill the mouse pointer
        pygame.fastevent.init() ## we need fastevents because of midi input 
        self.midi = MidiClass()

        ## GAME STATE AND OTHER GLOBAL SETTINGS
        ## the following may be changed in "setstate"
        self.allowedchanges = [ "gamestate",    # an integer, see config.py
                                "settings",     # dict to things like fullscreen, etc.
                                "piecedir",     # directory to the piece which we play or edit
                                #"piecesettings", # dict to things like tempo, piece, etc.
                                "printme" ]

        self.printme = ""  # printme is a basic debugging guy

        ## GLOBAL GAME SETTINGS, TO BE SET IN THE SETTINGS MENU
        self.allowedsettings = [ "Midi Input Channel",    
                                 "Lowest Note", 
                                 "Highest Note", 
                                 "Fullscreen" ]
        
        ## try to load the game settings, otherwise specify defaults
        try:
            settingsdir = os.path.join( config.RESOURCEdirectory, "settings.pkl" )
            with open(settingsdir, 'rb') as handle:
                self.settings = pickle.loads( handle.read() )
        except IOError:
            print "settings file does not exist.  setting defaults."
            self.settings = { 'Midi Input Channel': 3,  # self explanatory!  it's three on my machine.
                              'Lowest Note': 9,        # lowest note on your keyboard
                              'Highest Note': 96,      # highest note
                              'Fullscreen': 0 }        
       
        ## this gets us a list of available midi input, resets the default Midi Input Channel
        ##  if the one given above does not exist
        self.checkandsetmidi()

        ## INDIVIDUAL GAME SETTINGS, TO BE SET IN THE PIECE MENU
        self.allowedpiecesettings = [ "Name",
                                      "TempoPercent",   # percentage of Tempo to play at
                                      "Difficulty",  # integer 
                                      "PlayerTrack",
                                      "Metronome",
                                      "BookmarkTicks",
                                      "Sandbox" ]    # if true, then not penalized for missing notes

        ## ACTUALIZE THE GAMESTATE
        ## set the gamestate.  first it's uninitialized (-1) so that it doesn't match anything
        self.gamestate = -1
        # otherwise it won't switch to the right state when we do the following:
        self.setstate( gamestate=config.GAMESTATEmainmenu )

        ## turn on the clock
        self.clock = pygame.time.Clock()

        # load and set the logo
        logo = pygame.image.load(os.path.join(config.RESOURCEdirectory, "logo32x32.png")) #awesome piano logo
        pygame.display.set_icon(logo)
        pygame.display.set_caption("PyanoH3ro") #awesome caption

        self.displayinfo = pygame.display.Info()

        self.setscreen()

#### GAMECLASS
    def checkandsetmidi( self ): 
        '''this gets us a list of available midi input, and resets the default Midi Input Channel
        in settings if the currently set one is not an input channel'''
        self.midiinputs, self.midiinputnames = self.midi.getallowedinputs()
        if len(self.midiinputs) == 0:
            Warn("No recognizable midi inputs.  Please plug something in.")
        else:
            if self.settings["Midi Input Channel"] not in self.midiinputs:
                self.settings["Midi Input Channel"] = self.midiinputs[-1] 

        self.midi.setinput( self.settings["Midi Input Channel"] )

    def setscreen( self, newsize=config.DEFAULTresolution ):
        if self.settings['Fullscreen']: # we are changing to fullscreen, ignore newsize
            self.screen = pygame.display.set_mode( (self.displayinfo.current_w, self.displayinfo.current_h),
                                                   pygame.FULLSCREEN ) 
        else: # we want a newsize non-fullscreen setting...
            self.screen = pygame.display.set_mode( newsize, pygame.RESIZABLE ) #display resolution
        

#### GAMECLASS
    def setstate( self, **kwargs ):
######## GAMECLASS:setstate
        oldgamestate = self.gamestate
        for key, value in kwargs.iteritems():
            allowed = False # this key is not allowed until proven otherwise!
            ## grab all the new properties from keyword arguments
            if key in self.allowedchanges:
                setattr( self, key, value )
                allowed = True
            else:
                #if oldgamestate == config.GAMESTATEsettings: ## we were in the settings menu
                if key in self.allowedsettings:
                    originalvalue = self.settings[key]
                    self.settings[key] = value
                    allowed = True
                    if key == "Midi Input Channel": # if the player adjusted the midi input,
                        self.checkandsetmidi()      # then attempt to reset it
                    elif key == "Fullscreen" and originalvalue != value: # we are changing the setting
                        self.setscreen()
                #elif ( oldgamestate == config.GAMESTATEpiecesettings or 
                #        oldgamestate == config.GAMESTATEeditmenu ): # we were in the piece settings menu
                elif key in self.allowedpiecesettings:
                    self.piecesettings[key] = value
                    allowed = True
            if not allowed:            
                Warn("in GameClass:setstate - key "+ key +" is protected!!")

######## GAMECLASS:setstate
        if self.gamestate != oldgamestate:
            print "Changing gamestate from",oldgamestate,"to ",self.gamestate
            if self.printme:
                print self.printme
            print
            self.printme = ""

            if oldgamestate == config.GAMESTATEsettings: # if we were on settings
                print "saving settings:"
                print self.settings
                try:
                    settingsdir = os.path.join( config.RESOURCEdirectory, "settings.pkl" )
                    with open(settingsdir, 'wb') as handle:
                        pickle.dump(self.settings, handle)
                except IOError:
                    print "WARNING.  error saving settings."

            #something new is happening for sure!

############ GAMECLASS:setstate:  trying to set a new gamestate, load menus or play

            if self.gamestate == config.GAMESTATEplay: #standard play
                self.gamechunk = PlayClass( self.piecedir, self.midi, self.piecesettings )
            
############ GAMECLASS:setstate:  trying to set a new gamestate, load menus or play

            elif self.gamestate == config.GAMESTATEmainmenu: #main menu
                self.gamechunk = MenuClass( [ TextEntryClass( text="Main Menu",
                                                              selectable=False,
                                                              fontsize=25 ),
                                              TextEntryClass( text="Play",
                                                              bgcolor=(50,0,10),
                                                              infolines=["Press [enter] to play,",
                                                                         "or manuever with arrows"],
                                                              selectable=True,
                                                              fontsize=20,
                                                              action={'gamestate':config.GAMESTATEpieceselection, # level selection
                                                                      'printme':"Select your level."} ),
                                              TextEntryClass( text="Create",
                                                              bgcolor=(80,80,0),
                                                              infolines=["Press [enter] to compose,",
                                                                         "or manuever with arrows"],
                                                              selectable=True,
                                                              #selectedfontcolor=randomcolor(),
                                                              fontsize=20,
                                                              action={'gamestate':config.GAMESTATEeditmenu, 
                                                                      'printme':"Going to edit menu."} ),
                                              TextEntryClass( text="Settings",
                                                              bgcolor=(10,60,0),
                                                              infolines=["Press [enter] to choose settings,",
                                                                         "or manuever with arrows"],
                                                              selectable=True,
                                                              #selectedfontcolor=(0,200,140),
                                                              fontsize=20,
                                                              action={'gamestate':config.GAMESTATEsettings, # setting selection
                                                                      'printme':"Set your settings."} ),
                                              TextEntryClass( text="Exit",
                                                              bgcolor=(0,30,50),
                                                              selectable=True,
                                                              infolines=["Press [enter] to quit,",
                                                                         "or manuever with arrows"],
                                                              fontsize=20,
                                                              #selectedfontcolor=(255,100,0),
                                                              action={'gamestate':0, # quitting
                                                                      'printme':"exiting from main menu."} )
                                                 ] ) 
                self.gamechunk.setbackspaceaction( {'gamestate':0,
                                             'printme':"exiting main menu via backspace."} )
                
                image = pygame.image.load(os.path.join(config.RESOURCEdirectory,"PyanoH3ro.png"))
                self.gamechunk.backdrop.addimage( image, "center" )

############ GAMECLASS:setstate:  trying to set a new gamestate, load menus or play

            elif self.gamestate == config.GAMESTATEpieceselection: # open piece menu
                
                self.gamechunk = DirectoryMenuClass( [ TextEntryClass( text="Piece Menu",
                                                              selectable=False,
                                                              fontsize=25 ), 
                  TextEntryClass( text="Play",
                                  selectable=True,
                                  infolines=["Press [enter] to choose this piece,",
                                             "or manuever with arrows"],
                                  fontsize=18,
                                  #selectedfontcolor=(0,200,150),
                                  bgcolor=(0,100,50),
                                  #selectedfontcolor=(0,200,150),
                                  action={'gamestate':config.GAMESTATEpiecesettings,
                                  "printme" : "piece chosen."} ),
                  TextEntryClass( text="Return to Main Menu",
                                  selectable=True,
                                  fontsize=18,
                                  infolines=["Press [enter] to go back,",
                                             "or manuever with arrows"],
                                  height=25,
                                  bgcolor=(100,10,10),
                                  #selectedfontcolor=(255,50,50),
                                  action={'gamestate':config.GAMESTATEmainmenu,
                                     'printme':"return to main menu."} ),
                  TextEntryClass( text="Selection",
                                  fontsize=22,
                                  height=-20, #negative height will squish
                                  #fontcolor=(230,230,230), # things together
                                  selectable=False,
                                  valuefontsize=20 ) ],
                config.PIECEdirectory) # rootdir for our directory menu class to parse
                
                self.gamechunk.setbackspaceaction( {'gamestate':config.GAMESTATEmainmenu,
                                             'printme':"return to main menu via backspace."} )

            elif self.gamestate == config.GAMESTATEeditmenu: #  compose menu
                self.piecesettings = {}
                self.gamechunk = DirectoryMenuClass( [ TextEntryClass( text="Compose Menu",
                                                              selectable=False,
                                                              fontsize=25 ) ], 
                                            config.PIECEdirectory,  # rootdir for our directory menu class to parse
                 {'gamestate':config.GAMESTATEedit, # whether or not to include a "new" or "edit" selector
                 'printme':"Going to edit mode."}  ) # -- depends on whether we put this dict in here.
                
                # without this next piece of code, it's impossible to back out of the above menu
                self.gamechunk.setbackspaceaction( {'gamestate':config.GAMESTATEmainmenu,
                                             'printme':"return to main menu via backspace."} )
            
            elif self.gamestate == config.GAMESTATEedit: #editing!
                if "Name" in self.piecesettings.keys():
                    # if we have a name, then we probably need to create the directory
                    # but in the following, we only want creating new directories in a certain
                    # level of the hierarchy...
                    piecedir = self.piecedir.split( os.path.sep )
                    piecedir = piecedir[:3] # only go three levels deep.
                    self.piecedir = (os.path.sep).join( piecedir ) 
                    self.piecedir = os.path.join( self.piecedir, self.piecesettings["Name"] )
                    if os.path.isdir(self.piecedir):
                        #print "opening ",self.piecedir, " for editting"
                        pass
                    else:
                        print "Creating new music directory",self.piecedir, "for editting"
                        os.makedirs( self.piecedir )
                else:
                    print "Opening",self.piecedir, "for editting"

                self.piecesettings = getpiecesettings( self.piecedir )
                self.gamechunk = EditClass( self.piecedir, self.midi, self.piecesettings )

            elif self.gamestate == config.GAMESTATEpiecesettings: #  piece settings menu
                #piececonfig = importlib.import_module(self.piecedir)
                # get min/max tempo, also default tempo
                # 
                self.piecesettings = getpiecesettings( self.piecedir )
                self.piecesettings["Metronome"] = config.METRONOMEdefault
                print "piece settings = ", self.piecesettings
                
                piecemenu = [ TextEntryClass( text="Piece Settings",
                                              selectable=False,
                                              fontsize=25 ),
                              TextEntryClass( text="Play",
                                              selectable=True,
                                              fontsize=18,
                                              infolines=["Press [enter] to play!",
                                                         "or manuever with arrows"],
                                              bgcolor=(100,10,10),
                                              #selectedfontcolor=(255,50,50),
                                              action={'gamestate':config.GAMESTATEplay,
                                                        'printme':"start game!"} ),  
                              TextEntryClass( text="Sandbox",
                                              asetting=True, # a flag for fancy setting behavior
                                              selectable=True,
                                              fontsize=18,
                                              valuefontsize=15,
                                              allowedvalues = [0,1],
                                              value=self.piecesettings["Sandbox"],
                                                              infolines=["Choose 1",
                                                                         "to avoid grading"],
                                              #selectedfontcolor=(255,50,50),
                                              bgcolor=(100,100,0),
                                              showleftrightarrows=True),
                              TextEntryClass( text="TempoPercent",
                                              asetting=True, # a flag for fancy setting behavior
                                              selectable=True,
                                              fontsize=18,
                                              valuefontsize=15,
                                              allowedvalues=range(20,201),
                                              value=100,
                                                      infolines=["Percent by which",
                                                                 "to modify the tempo."],
                                              bgcolor=(50,100,0),
                                              #selectedfontcolor=(255,50,50),
                                              showleftrightarrows=True),
                              TextEntryClass( text="Difficulty",
                                              asetting=True, # a flag for fancy setting behavior
                                              selectable=True,
                                              fontsize=18,
                                              valuefontsize=15,
                                                      infolines=["Set the difficulty."],
                                              allowedvalues = self.piecesettings["AllowedDifficulties"],
                                              value=self.piecesettings["Difficulty"],
                                              bgcolor=(0,100,50),
                                              #selectedfontcolor=(255,50,50),
                                              showleftrightarrows=True) ]
                try:
                    if len(self.piecesettings["AllowedPlayerTracks"]) > 1:
                        piecemenu.append( TextEntryClass( text="PlayerTrack",
                                                  asetting=True, # a flag for fancy setting behavior
                                                  selectable=True,
                                                  fontsize=18,
                                                  valuefontsize=15,
                                                  allowedvalues = self.piecesettings["AllowedPlayerTracks"],
                                                  infolines=["Choose which track","the player will play"],
                                                  value=self.piecesettings["PlayerTrack"],
                                                  #selectedfontcolor=(255,50,50),
                                                  bgcolor=(0,50,100),
                                                  showleftrightarrows=True) )
                except KeyError:
                    self.piecesettings["PlayerTrack"] = config.DEFAULTplayertrack
                    
                piecemenu.append( TextEntryClass( text="Metronome",
                                          asetting=True, # a flag for fancy setting behavior
                                          selectable=True,
                                          fontsize=18,
                                          valuefontsize=15,
                                          allowedvalues = [ True, False ],
                                          infolines=["metronome on/off"],
                                          value=self.piecesettings["Metronome"],
                                          #selectedfontcolor=(255,50,50),
                                          bgcolor=(100,100,100),
                                          showleftrightarrows=True) )

                piecemenu.append( TextEntryClass( text="Return to Main Menu",
                                                  selectable=True,
                                                  fontsize=18,
                                                  #selectedfontcolor=(255,50,50),
                                                  bgcolor=(100,0,100),
                                                  action={'gamestate':config.GAMESTATEpieceselection,
                                                            'printme':"return to piece selection."} ) )
                self.gamechunk = MenuClass( piecemenu )
                
                self.gamechunk.setbackspaceaction( {'gamestate':config.GAMESTATEpieceselection,
                                             'printme':"return to main menu via backspace."} )

            elif self.gamestate == config.GAMESTATEsettings: # open settings menu
                ## make sure midi is working ok, 
                ## or set a default if currently we don't have anything working good.
                self.checkandsetmidi()

                self.gamechunk = MenuClass( [ TextEntryClass( text="Settings Menu",
                                                              selectable=False,
                                                              fontsize=25 ), 
                                        TextEntryClass( text="Midi Input Channel",
                                                        selectable=True,
                                                        fontsize=18,
                                                        valuefontsize=15,
                                      infolines=["Switch midi inputs", "using left/right arrows,",
                                                 "then try playing", "your midi keyboard.",
                                                 "If you forgot", "to plug it in,", "do so and restart",
                                                "the game."],
                                                        asetting=True, # a flag for fancy setting behavior
                                                        value=self.settings["Midi Input Channel"],
                                                        allowedvalues=self.midiinputs,
                                                        captionvalues=self.midiinputnames,
                                                        showleftrightarrows=True,
                                                        bgcolor=(100,10,120) ),
                                                        #selectedfontcolor=(150,50,200) ),
                                        TextEntryClass( text="Lowest Note",
                                                        selectable=True,
                                                        fontsize=18,
                                                        valuefontsize=15,
                                      infolines=["Once midi input is set,",
                                                 "play the lowest note", "on the keyboard,",
                                                 "or set with", "left/right arrows"],
                                                        asetting=True, # a flag for fancy setting behavior
                                                        value=self.settings["Lowest Note"],
                                                        respondstomidi=True, # will get value of midi
                                                        allowedvalues=range(21,97),
                                                        showleftrightarrows=True,
                                                        #selectedfontcolor=(20,200,50) ),
                                                        bgcolor=(10,100,30) ),
                                        TextEntryClass( text="Highest Note",
                                                        selectable=True,
                                                        fontsize=18,
                                                        valuefontsize=15,
                                      infolines=["Once midi input is set,",
                                                 "play the highest note", "on the keyboard,",
                                                 "or set with", "left/right arrows"],
                                                        asetting=True, # a flag for fancy setting behavior
                                                        value=self.settings["Highest Note"],
                                                        respondstomidi=True, # will get value of midi
                                                        allowedvalues=range(33,109),
                                                        showleftrightarrows=True,
                                                        bgcolor=(150,150,0) ),
                                                        #selectedfontcolor=(220,220,0) ),
                                        TextEntryClass( text="Fullscreen",
                                                        selectable=True,
                                                        fontsize=18,
                                      infolines=["Toggle full-screen","with left/right arrows."],
                                                        valuefontsize=15,
                                                        asetting=True, # a flag for fancy setting behavior
                                                        value=self.settings["Fullscreen"],
                                                        allowedvalues=[0,1],
                                                        captionvalues=["off","on"],
                                                        showleftrightarrows=True,
                                                        bgcolor=(100,50,00) ),
                                                        #selectedfontcolor=(255,100,0) ),
                                        TextEntryClass( text="Return to Main Menu",
                                                        selectable=True,
                                                        fontsize=18,
                                      infolines=["Press [enter] to return",
                                                 "to the main menu"],
                                                        #selectedfontcolor=(255,50,50),
                                                        bgcolor=(50,25,25) ,
                                                        action={'gamestate':config.GAMESTATEmainmenu,  
                                                                'printme':"return to main menu."} ) ] )
############ GAMECLASS:setstate:  trying to set a new gamestate, load menus or play
                self.gamechunk.setbackspaceaction( {'gamestate':config.GAMESTATEmainmenu,
                                             'printme':"return to main menu via backspace."} )

            elif self.gamestate == 0:
                self.quit()

        else:
            # game state was same as previous... not sure what to do!
            pass

######## end GAMECLASS:setstate

#### GAMECLASS
    def mainloop( self ): 
        while self.gamestate:     
            dt = self.clock.tick()
            ## update midi
            self.midi.update( dt )
            ## update the gamechunk
            self.gamechunk.update( dt, self.midi )
            
            ## display the gamechunk 
            self.gamechunk.draw( self.screen )
            
            ## process events in the gamechunk
            #for event in pygame.event.get(): #slow events :(
            processmidi = False # innocent until proven we need to process midi
            for event in pygame.fastevent.get(): # need fast events for midi
                # check some global events first.
                if event.type == QUIT:
                    self.gamestate = 0
                elif event.type == VIDEORESIZE:
                    if event.size[0] > 100 and event.size[1] > 100:
                        self.setscreen( event.size )
                    else:
                        print "Error!  don't resize window that small."
                        self.quit()
                elif self.midi.process( event ):
                    processmidi = True  # yes we need to process midi
                else:
                    ## allow the event to make changes to the midi, like play sounds, etc.
                    returnvalue = self.gamechunk.process( event, self.midi )
                    # if the event triggered anything according to the current gamechunk,
                    # it will output a dictionary that can be read by our **kwargs guy
                    if ( len(returnvalue) > 0 ):
                        self.setstate( **returnvalue )
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F11:
                            self.setstate( Fullscreen = (not self.settings["Fullscreen"]) )
                
            if processmidi:  # process midi at the end.  self.midi stores the relevant stuff
                returnvalue = self.gamechunk.processmidi( self.midi )
                if ( len(returnvalue) > 0 ):
                    self.setstate( **returnvalue )

            ## flip screen
            pygame.display.flip()
        
        self.quit()
    
    def quit( self ):
        # turn off fullscreen before exiting, in case pygame midi hangs.
        self.settings['Fullscreen'] = False
        self.setscreen()

        self.midi.quit()
        pygame.quit()
        sys.exit()

#### end GAMECLASS
            
