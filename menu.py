# this file defines all the necessary 
from metagame import *
from backdrops import *
from iomidi import *
import pygame
import config

class MenuClass( GameChunkClass ): # inherit from the GameChunkClass
#### MENU CLASS
    def __init__( self, entries ):
        #DisplayClass.__init__(self) #if necessary
        #choose a backdrop
        self.backdrop = LeftPianoBackDropClass()
        ## for midi input on various settings / menu items
        self.midiimage = pygame.image.load(os.path.join(config.RESOURCEdirectory, "respondstomidi.png"))
        self.midiimagerect = self.midiimage.get_rect()
        # setup all the entries
        self.setupentries( entries )
        # start with the first selectable entry            
        self.currentselectedofselectable = 0 # which menu entry to have selected

    def setupentries( self, entries ):
        # Most important part of MenuClass is a list of EntryClass classes: 
        self.entries = entries
        self.numentries = len(entries)
        # The MenuClass must take care of where to put those entries.
        self.yentries = [0] # y positions of the entries, relative to offset
        for i in range(1,self.numentries):
            ## 
            self.yentries.append( self.yentries[-1] + self.entries[i-1].height )
        self.yentries.append( self.yentries[-1] + self.entries[-1].height ) # only used to determine padding
        ## now go back OVER things and add space to top and bottom:
## ADD HERE

        self.yoffset = 0 ## current y-offset in case the menu goes below screen
                         ## we can shift yoffset in order to view those

        # iterate through to see which entries are selectable
        self.selectableentries = range(self.numentries)
        for i in range(self.numentries):
            if not self.entries[i].selectable:
                ## if this entry isn't selectable
                self.selectableentries.remove(i)
        
        if len( self.selectableentries ) == 0:
            Error("Initialization of MenuClass has no selectable menu items")


#### MENU CLASS
    def update( self, dt, midi ):
        self.backdrop.update( dt )

    def process( self, event, midi ):
        '''here we provide methods for changing things on the menu'''

        if event.type == pygame.KEYDOWN:
            iselected = self.selectableentries[self.currentselectedofselectable]
            if event.key == pygame.K_DOWN or event.key == pygame.K_j: #keyin.down:
                ## strike a random key on the piano.  light it up on the background:
                self.backdrop.hitrandomkey( midi, 4 ) # octave below middle C
                ## now actually move the selection
                self.currentselectedofselectable += 1
                if self.currentselectedofselectable >= len(self.selectableentries):
                    self.currentselectedofselectable = 0
                    yoffset = 0
                return {}

            elif event.key == pygame.K_UP or event.key == pygame.K_k: # keyin.up:
                ## strike a random key on the piano.  light it up on the background:
                self.backdrop.hitrandomkey( midi, 5 ) # octave of middle C
                self.currentselectedofselectable -= 1
                if self.currentselectedofselectable < 0:
                    self.currentselectedofselectable = len(self.selectableentries) - 1
                return {}

            elif event.key == K_RETURN or event.key == K_SPACE: #keyin.enter:
                ## execute the entry that is currently selected
                if self.entries[iselected].respondstomidi:
                    self.backdrop.hitkey( midi, self.entries[iselected].value )
                return self.entries[iselected].execute()

            elif event.key == pygame.K_RIGHT or event.key == pygame.K_l:
                switchvalue = self.entries[iselected].switchvalueright(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                if self.entries[iselected].respondstomidi:
                    self.backdrop.hitkey( midi, self.entries[iselected].value )
                return switchvalue
                    
            elif event.key == pygame.K_LEFT or event.key == pygame.K_h:
                switchvalue = self.entries[iselected].switchvalueleft(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                if self.entries[iselected].respondstomidi:
                    self.backdrop.hitkey( midi, self.entries[iselected].value )
                return switchvalue
 
            elif event.key == pygame.K_BACKSPACE:
                return self.backspaceaction

        ## gamechunk must return a dictionary after processing events.
        ## if you don't want anything to happen, pass an empty dict:
        return {}

#### MENU CLASS
    def processmidi( self, midi ):
        newnotes = midi.newnoteson()
        lastnote = -1
        for note in newnotes:
            midi.startnote( note[0], note[1], config.PIANOchannel ) #start note[0] with velocity note[1]
            # grab the note in the octave (from 0 to 11) 
            octave, noteinoctave = divmod( note[0], 12 ) 
            # so that we can light up the appropriate key on the background
            self.backdrop.brightenkey( note[0] ) #setstate( noteon=noteinoctave, notevel=note[1] ) 
            lastnote = note[0] 
            
        newnotes = midi.newnotesoff()
        for note in newnotes:
            midi.endnote( note, config.PIANOchannel ) # stop note note

        if lastnote >= 0: 
            iselected = self.selectableentries[self.currentselectedofselectable]
            if self.entries[iselected].respondstomidi:
                if lastnote in self.entries[iselected].allowedvalues:
                    self.entries[iselected].currentvalueindex = self.entries[iselected].allowedvalues.index( lastnote )
                    self.entries[iselected].setvaluefromindex()
                    return self.entries[iselected].execute()
                else:
                    Warn( "Midi note was not allowed as input to TextEntryClass" )
        return {}
        
#### MENU CLASS
    def draw(self, screen):
        '''here we draw our entries onto the screen'''
        screencenterx = screen.get_rect().centerx
        screenwidth, screenheight = screen.get_size()
        remainingheight = screenheight - self.yentries[-1]
        if remainingheight > 0:
            extrapadding = 1.0*remainingheight / (self.numentries+3)
        else:
            extrapadding = 0
            
        # first add in backdrop
        self.backdrop.draw( screen )
######## find the entry which is selected -- it's indexed in the selectable entries list:
        iselected = self.selectableentries[self.currentselectedofselectable]
######## now loop through all entries, selectable or not
        i=0
        while i < iselected:
            # do not highlight these entries, they are not selected
            self.entries[i].draw( screen, screencenterx, 
                                  -self.yoffset + self.yentries[i] + (i+2)*extrapadding, 0 )
            i += 1


######## consider the highlighted guy... he's selected.  get his y position...
        yselected = -self.yoffset + self.yentries[i] + (i+2)*extrapadding
        ## so throw on a midi picture if he responds to midi
        if self.entries[i].respondstomidi:
            self.midiimagerect.y = yselected
            self.midiimagerect.left = (0.4*screenwidth + 0.6*screencenterx) 
            screen.blit( self.midiimage, self.midiimagerect )

######## draw the highlighted guy (he's selected)
        self.entries[i].draw( screen, screencenterx, yselected, 1 ) 
        i += 1

        
        while i < self.numentries:
            # do not highlight these entries, they are not selected
            self.entries[i].draw( screen, screencenterx, 
                                  -self.yoffset + self.yentries[i] + (i+2)*extrapadding, 0 )
            i += 1
        
        
            
#### END MENU CLASS



class EntryClass:
    def __init__( self, **kwargs ):
        self.allowedchanges = [ "action" ] 
        self.setstate( **kwargs )
    def setstate( self, **kwargs ):
        ## set defaults
        self.action = dict()
        ## grab user input
        for key, value in kwargs.iteritems():
            ## grab all the new properties from keyword arguments
            if key in self.allowedchanges:
                setattr( self, key, value )
            else:
                Warn("in EntryClass:setstate - key "+ key +" is protected!!")
        ## post process stuff
        ## now create the stuff that will get drawn
    def draw( self, screen, x, y, highlighted ):
        pass 
    def execute( self ):
        return self.action
            
            
        
#### END ENTRY CLASS


class TextEntryClass:
    ''' this actually doesn't allow for text entry into some form, it's about
    having a text entry on a menu.'''
#### CLASS TEXTENTRY
    def __init__( self, **kwargs ):
        self.allowedchanges = [ "text",
                                "font",
                                "infolines",
                                "fontsize",
                                "fontcolor",
                                "selectedfontcolor",
                                "respondstomidi",
                                "selectable",
                                "action",
                                "asetting", ## whether i'm a setting or not
                                "height",
                                "value",
                                "currentvalueindex",
                                "valuefontsize",
                                "captionfontcolor",
                                "allowedvalues",
                                "captionvalues",
                                "bgcolor",
                                "showleftrightarrows",
                                ] 
        self.setstate( **kwargs )

#### CLASS TEXTENTRY
    def setstate( self, **kwargs ):
        ## set defaults 
        self.font = config.FONT
        self.fontcolor = (255,255,255)
        self.selectedfontcolor = (255,255,255)
        self.captionfontcolor = (205,205,205)
        self.text = ""
        self.infolines = []
        self.fontsize = 24
        self.valuefontsize = 20
        self.selectable = False
        self.respondstomidi = False
        self.action = {}
        self.height = 0
        self.bgcolor = (50,50,50)
        self.asetting = False
        self.allowedvalues = []
        self.captionvalues = []
        self.showleftrightarrows = False
        self.picturefile = ""

        for key, value in kwargs.iteritems():
            ## grab all the new properties from keyword arguments
            if key in self.allowedchanges:
                setattr( self, key, value )
            else:
                Warn("in TextEntryClass:setstate - key "+ key +" is protected!!")

        self.fontsize *= config.FONTSIZEmultiplier
        self.valuefontsize *= config.FONTSIZEmultiplier
        self.fontsize = int(self.fontsize)
        self.valuefontsize = int(self.valuefontsize)
        
        ## set some post-defaults
        if self.height == 0:
            if self.text:
                self.height += self.fontsize
            if self.asetting:
                self.height += self.valuefontsize
                if len(self.captionvalues) > 0:
                    self.height += 1.2*self.valuefontsize
       
        if self.asetting:
            try: 
                if self.value not in self.allowedvalues:
                    self.currentvalueindex = len(self.allowedvalues) - 1
                    self.value = self.allowedvalues[self.currentvalueindex]
                else:
                    self.currentvalueindex = self.allowedvalues.index( self.value )
            except AttributeError:
                self.currentvalueindex = len(self.allowedvalues) - 1
                self.value = self.allowedvalues[self.currentvalueindex]
            
            if self.showleftrightarrows and len(self.allowedvalues) == 1:
                self.showleftrightarrows = False

            if len(self.captionvalues) > 0:
                if len(self.captionvalues) != len(self.allowedvalues):
                    Error("Need as many captions as values, if you're going to use captions")
      
        
        ## now make everything happen
        if self.text:
            fontandsize = pygame.font.SysFont(self.font, self.fontsize)
            self.label = fontandsize.render( self.text, 1, self.fontcolor )
            self.selectedlabel = fontandsize.render( self.text, 1, self.selectedfontcolor )
            self.labelbox = self.label.get_rect()

        if len(self.infolines) > 0:
            fontandsize = pygame.font.SysFont(self.font, self.fontsize - 2)
            self.infolabel = []
            self.infolabelbox = []
            for i in range(len(self.infolines)):
                self.infolabel.append( fontandsize.render( self.infolines[i], 1, self.fontcolor ) )
                self.infolabelbox.append( self.infolabel[-1].get_rect() )

        self.setvaluefromindex()

#### CLASS TEXTENTRY
    def setvaluefromindex( self ): 
        if self.asetting:
            self.value = self.allowedvalues[ self.currentvalueindex ]
            fontandsize = pygame.font.SysFont(self.font, self.valuefontsize)
            self.valuelabel = fontandsize.render( str(self.value), 1, self.fontcolor )
            self.valuelabelbox = self.valuelabel.get_rect()

            if len(self.captionvalues) > 0:
                self.captionvalue = self.captionvalues[ self.currentvalueindex ]
                self.captionlabel = fontandsize.render( self.captionvalue, 1, self.captionfontcolor )
                self.captionlabelbox = self.captionlabel.get_rect()

#            if self.showleftrightarrows:
#                fontandsize = pygame.font.SysFont(self.font, (self.valuefontsize-2))
#                self.valuelabel = fontandsize.render( str(self.value), 1, self.fontcolor )
#                self.valuelabelbox = self.valuelabel.get_rect()
            self.action[self.text] = self.value
                

#### CLASS TEXTENTRY
    def draw( self, screen, x, y, highlighted ):
        screenwidth, screenheight = screen.get_size()
        if self.text:
            self.labelbox.centerx = x
            self.labelbox.centery = y
            if self.bgcolor:
                hangover = 5
                bgrect = Rect( self.labelbox.x - hangover, self.labelbox.y - 5,
                               self.labelbox.width + 2*hangover, self.labelbox.height + 10 )
                pygame.draw.rect( screen, self.bgcolor,  bgrect )
                
            if highlighted:
                screen.blit( self.selectedlabel, self.labelbox )
                # draw an underline on the text box
                pygame.draw.line( screen, self.selectedfontcolor, 
                                  self.labelbox.bottomleft, self.labelbox.bottomright )
            else:
                screen.blit( self.label, self.labelbox )

        if len(self.infolines) and highlighted:
            rightx = 0.9*screenwidth
            self.infolabelbox[0].right = rightx
            self.infolabelbox[0].top = 0.1*screenheight
            screen.blit( self.infolabel[0], self.infolabelbox[0] )
            for i in range(1,len(self.infolines)):
                self.infolabelbox[i].right = rightx
                self.infolabelbox[i].top = self.infolabelbox[i-1].bottom + 10
                screen.blit( self.infolabel[i], self.infolabelbox[i] )

        if self.asetting:
            self.valuelabelbox.centerx = x
            if self.text:
                self.valuelabelbox.top = self.labelbox.bottom + 0.5*self.fontsize
                if self.bgcolor and not self.text:
                    hangover = 5
                    bgrect = Rect( self.valuelabelbox.x - hangover, self.valuelabelbox.y - 5,
                                   self.valuelabelbox.width + 2*hangover, self.valuelabelbox.height + 10 )
            else:
                self.valuelabelbox.centery = y
                if self.bgcolor and not self.text:
                    hangover = 5
                    bgrect = Rect( self.valuelabelbox.x - hangover, self.valuelabelbox.y - 5,
                                   self.valuelabelbox.width + 2*hangover, self.valuelabelbox.height + 10 )
                pygame.draw.rect( screen, self.bgcolor,  bgrect )
                if highlighted:
                    # if we're a setting without text, but highlighted,
                    # draw an underline on the text box:
                    pygame.draw.line( screen, self.selectedfontcolor, 
                                      self.valuelabelbox.bottomleft, self.valuelabelbox.bottomright )
            
            screen.blit( self.valuelabel, self.valuelabelbox )

            if len(self.captionvalues) > 0:
                self.captionlabelbox.centerx = x
                self.captionlabelbox.top = self.valuelabelbox.bottom + 0.5*self.fontsize
                screen.blit( self.captionlabel, self.captionlabelbox )


            if highlighted and self.showleftrightarrows:
                # this part will show left/right arrows if the textbox is highlighted
                if self.text:
                    rightx = self.labelbox.right + 20
                    leftx = self.labelbox.left - 20
                    topy = y + self.fontsize
                else:
                    rightx = self.valuelabelbox.right + 20
                    leftx = self.valuelabelbox.left - 20
                    topy = self.valuelabelbox.top

                boty = topy + 20
                midy = topy + 10
                triwidth = 15
                # draw right triangle
                pygame.draw.polygon(screen, self.selectedfontcolor,
                                            [ ( rightx, topy ), 
                                              ( rightx + triwidth, midy ), 
                                              ( rightx, boty ) ] )
                # draw left triangle
                pygame.draw.polygon(screen, self.selectedfontcolor,
                                            [ ( leftx, boty ), 
                                              ( leftx  - triwidth, midy ), 
                                              ( leftx, topy ) ] )
                  
#### CLASS TEXTENTRY
    def execute( self ):
        return self.action
    
#### CLASS TEXTENTRY
    def switchvalueright( self, bigshift = False ):
        if self.asetting and len(self.allowedvalues) > 0:
            if bigshift: 
                self.currentvalueindex += max(1, len(self.allowedvalues)/10)
            else:
                self.currentvalueindex += 1

            if self.currentvalueindex >= len(self.allowedvalues):
                self.currentvalueindex = 0
            
            self.setvaluefromindex()

            if self.text:
                return { self.text : self.value }
        return {}
            
#### CLASS TEXTENTRY
    def switchvalueleft( self, bigshift = False ):
        if self.asetting and len(self.allowedvalues) > 0:
            if bigshift: 
                self.currentvalueindex -= max(1, len(self.allowedvalues)/10)
            else:
                self.currentvalueindex -= 1

            if self.currentvalueindex < 0:
                self.currentvalueindex = len(self.allowedvalues) - 1
            
            self.setvaluefromindex()
            if self.text:
                return { self.text : self.value }
        return {}

#### END TEXTENTRY CLASS



class DirectoryMenuClass( MenuClass ): # inherit from the DisplayClass
#### DIRECTORY MENU CLASS
    def __init__( self, extraentries, rootdir, creatoraction={} ):
        self.backdrop = LeftPianoBackDropClass()
        self.rootdir = str(rootdir)
        self.extraentries = extraentries 
        self.font = config.FONT
        #self.fontcolor = (190,210,200)
        self.fontcolor = (255,255,255)
        self.fontsize = 18

        # for grabbing information...
        self.listeningfortext = False
        self.askingfor = ""
        self.listeningmessage = ""
        self.listeningaction = creatoraction
        
        if len(creatoraction) == 0:
            self.creator = False
        else:
            self.creator = True
            self.extraentries.append( TextEntryClass( text="Mode", fontsize=18,
                                                      fontcolor=self.fontcolor,
                                                      selectable=True,
                                                      bgcolor=randomcolor(),
                                                      valuefontsize=self.fontsize,
                                                infolines=["Press [enter] to compose,",
                                                           "select edit/new by left/right arrows",
                                                           "or [backspace] to main menu"],
                                                  allowedvalues=["Edit", "New"],
                                                  value="Edit",
                                                  asetting=True,
                                                  showleftrightarrows=True,
                                                  action=creatoraction ) )
                                                  #selectedfontcolor=randomcolor() ) )


        self.mode = 0   # 0 = browse directories all the way down to piece directories
                        # 1 = browse directories, but don't show the individual piece directories
        # self.mode = 0 for standard browsing stuff.
        # self.mode = 1 when we want to create a piece in a given subdirectory

        self.allowedsubdirs = [ os.walk(self.rootdir).next()[1] ] # the 1 grabs the directories
        if len(self.allowedsubdirs[0]) == 0:
            Error(" No directories found in directory "+self.rootdir+". ")
        
        # this first set of allowed directories never changes, but we can change which directory
        # to first look into
        if self.creator:
            # if we are in creator mode, look into compositions...
            self.currentsubdir = [ "Compositions" ]
        else:
            #here we choose a random directory within the rootdir:
            self.currentsubdir = [ self.allowedsubdirs[0][int(random()*len(self.allowedsubdirs[0]))] ]

        self.directoryentries = [ TextEntryClass( fontsize=18,
                                                  fontcolor=self.fontcolor,
                                                    bgcolor=randomcolor(),
                                                  selectable=True,
                                                  valuefontsize=self.fontsize,
                                                infolines=["Choose a top directory with left/right arrows."],
                                                  height=-25,
                                                  allowedvalues=self.allowedsubdirs[0],
                                                  asetting=True,
                                                  value=self.currentsubdir[0],
                                                  showleftrightarrows=True ) ]
                                                  #selectedfontcolor=randomcolor() ) ]

        # descend into this directory, and add in TextEntryClasses to the directory entry list
        self.descend() 
        # start with the first selectable entry            
        self.currentselectedofselectable = 0 # which menu entry to have selected

    def descend( self, startingdepth = 1, maxdepth = 6 ): 
        ''' here we plot a random descent into the directory structure '''
        ## start from the root dir and get all the way down to the specified starting depth
        descendingdirectory = self.rootdir
        for i in range(startingdepth):
            # get into all the "current" directories up to that point
            descendingdirectory = os.path.join( descendingdirectory, self.currentsubdir[i] )

        # start with a fresh slate past the starting depth...
        del self.allowedsubdirs[startingdepth:] # delete everything past the starting depth
        del self.directoryentries[startingdepth:] # we will recreate it in a second
        del self.currentsubdir[startingdepth:] # we will setup a new list of current directories

        descendingdirectorycontents = os.walk(descendingdirectory).next()[1] # 1 for directories only
        numcontents = len(descendingdirectorycontents)
        currentdepth = startingdepth
        while numcontents > 0 and currentdepth <= maxdepth:
            ## add the contents of this directory into the allowed values the TextEntry can take
            self.allowedsubdirs.append( descendingdirectorycontents )
            # choose a random directory to be selected in the TextEntry
            self.currentsubdir.append( self.allowedsubdirs[-1][int(  random()*numcontents  )] )

            # descend further into a random directory, to see if there's more depth
            descendingdirectory = os.path.join(descendingdirectory,self.currentsubdir[-1])
            # and look for the contents of this directory
            descendingdirectorycontents = os.walk(descendingdirectory).next()[1] # 1 for directories only
            # check how many there are
            numcontents = len(descendingdirectorycontents)

            # make a text entry at the head of it:
            if numcontents:
                self.directoryentries.append( TextEntryClass( selectable=True,
                                                          height = -25, # this squishes things together
                                                          valuefontsize=self.fontsize,
                                                          fontcolor=self.fontcolor,
                                              infolines=["Choose sub-directory with left/right arrows."],
                                                          allowedvalues=self.allowedsubdirs[-1],
                                                          fontsize=18,asetting=True,
                                                          value=self.currentsubdir[-1], 
                                                          showleftrightarrows=True,
                                                          bgcolor=randomcolor() ) )
                                                          #selectedfontcolor=randomcolor() ) )
            elif self.mode == 0: # only append the final piece class if mode == 0
                self.directoryentries.append( TextEntryClass( selectable=True,
                                                          height = -25, # this squishes things together
                                                          valuefontsize=self.fontsize,
                                                          fontcolor=self.fontcolor,
                                              infolines=["Choose piece with left/right arrows."],
                                                          allowedvalues=self.allowedsubdirs[-1],
                                                          fontsize=18,asetting=True,
                                                          value=self.currentsubdir[-1], 
                                                          showleftrightarrows=True,
                                                          bgcolor=randomcolor()) )
                                                          #selectedfontcolor=randomcolor() ) )

            currentdepth += 1
        
        if (currentdepth >= maxdepth and numcontents > 0):
            Error(" Your file directory is too deep.  Simmer down! ")
       
        # add some action.  "descendingdirectory" is actually the piece directory relative to root.
        # so we want to be able to change the "piecedir" for the main game by pressing enter on
        # pretty much any of the entries.
        # get them ready for displaying 
        if self.creator:
            self.extraentries[-1].action["piecedir"] = descendingdirectory
            for d in self.directoryentries:
                d.action =  { "piecedir" : descendingdirectory,
                              "gamestate" : self.extraentries[-1].action["gamestate"],
                              "printme" : self.extraentries[-1].action["printme"]  }
        else:
            self.extraentries[1].action["piecedir"] = descendingdirectory
            for d in self.directoryentries:
                d.action =  { "piecedir" : descendingdirectory,
                              "gamestate" : self.extraentries[1].action["gamestate"],
                              "printme" : self.extraentries[1].action["printme"]  }

        self.setupentries( self.extraentries + self.directoryentries )

#### DIRECTORY MENU CLASS
    def update( self, dt, midi ):
        self.backdrop.update( dt )

    def process( self, event, midi ):
        '''here we provide methods for changing things on the menu'''
        if event.type == pygame.KEYDOWN:
            if self.listeningfortext: 
                # if we're waiting for a message from the user
                if event.key == pygame.K_BACKSPACE:
                    self.listeningmessage = self.listeningmessage[0:-1] # take out last letter
                elif event.key == pygame.K_RETURN:
                    self.listeningfortext = False
                    self.listeningaction[self.askingfor] = self.listeningmessage # add an entry
                    print "Listened, and got ", self.listeningmessage
                    return self.listeningaction
                elif event.key < 128:
                    newletter = chr(event.key) #here's our new letter
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT: # if the shift key is held down
                        newletter = newletter.upper() #make it uppercase
                    self.listeningmessage += newletter #add it to the message
                    

            else: 
                # if we are just waiting for general input
                iselected = self.selectableentries[self.currentselectedofselectable]
                if event.key == pygame.K_DOWN or event.key == pygame.K_j: #keyin.down:
                    ## strike a random key on the piano.  light it up on the background:
                    self.backdrop.hitrandomkey( midi, 4 ) # octave below middle C
                    ## now actually move the selection
                    self.currentselectedofselectable += 1
                    if self.currentselectedofselectable >= len(self.selectableentries):
                        self.currentselectedofselectable = 0
                        yoffset = 0
                    return {}

                elif event.key == pygame.K_UP or event.key == pygame.K_k: # keyin.up:
                    ## strike a random key on the piano.  light it up on the background:
                    self.backdrop.hitrandomkey( midi, 5 ) # octave of middle C
                    self.currentselectedofselectable -= 1
                    if self.currentselectedofselectable < 0:
                        self.currentselectedofselectable = len(self.selectableentries) - 1
                    return {}

                elif event.key == K_RETURN or event.key == K_SPACE: #keyin.enter:
                    ## execute the entry that is currently selected
                    if self.entries[iselected].respondstomidi:
                        self.backdrop.hitkey( midi, self.entries[iselected].value )

                    if iselected == len(self.extraentries) - 1:
                        # this is our special edit/new command
                        if self.extraentries[iselected].value == "New":
                            # we just hit [enter] on the New command...
                            self.listeningfortext = True
                            self.askingfor = "Name"
                            # this puts "process" into a special mode where
                            # it cannot respond to regular input, but must
                            # listen for text-based messages
                            return {}
                            
                    return self.entries[iselected].execute()

                elif event.key == pygame.K_RIGHT or event.key == pygame.K_l:
                    try:
                        oldvalue = self.entries[iselected].value
                        switchaction = self.entries[iselected].switchvalueright(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                        newvalue = self.entries[iselected].value
                        if self.entries[iselected].respondstomidi:
                            self.backdrop.hitkey( midi, self.entries[iselected].value )

                        if oldvalue != newvalue:
                            # THIS PART IS NEW in the DIRECTORY MENU class
                            depth =  iselected - len(self.extraentries) + 1
                            if depth == 0 and self.creator: ## we just toggled new/edit on the creator bar
                                if self.extraentries[iselected].value == "Edit":
                                    # we switched to edit
                                    self.mode = 0
                                else:
                                    # we switched to create
                                    self.mode = 1
                                # we may want to remove the last little bit, or descend from a different spot...
                                # depends on if we're in edit or new mode.  new doesn't show the last piece folder.
                                depth = max(1, len(self.currentsubdir) - 1)
                                self.descend( depth )
                                return {}
                            elif depth > 0:
                                # we are switching subdirectories after the point depth!
                                self.currentsubdir[depth-1] = self.entries[iselected].value
                                self.descend( depth )
                                return {}
                        return switchaction
                    except AttributeError:
                        return {}
                        
                elif event.key == pygame.K_LEFT or event.key == pygame.K_h:
                    try:
                        oldvalue = self.entries[iselected].value
                        switchaction = self.entries[iselected].switchvalueleft(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                        newvalue = self.entries[iselected].value
                        if self.entries[iselected].respondstomidi:
                            self.backdrop.hitkey( midi, self.entries[iselected].value )

                        if oldvalue != newvalue:
                            # THIS PART IS NEW in the DIRECTORY MENU class
                            depth =  iselected - len(self.extraentries) + 1
                            if depth == 0 and self.creator: ## we just toggled new/edit on the creator bar
                                if self.extraentries[iselected].value == "Edit":
                                    # we switched to edit
                                    self.mode = 0
                                else:
                                    # we switched to create
                                    self.mode = 1
                                # we may want to remove the last little bit, or descend from a different spot...
                                # depends on if we're in edit or new mode.  new doesn't show the last piece folder.
                                depth = max(1, len(self.currentsubdir) - 1)
                                self.descend( depth )
                                return {}
                            elif depth > 0:
                                # we are switching subdirectories after the point depth!
                                self.currentsubdir[depth-1] = self.entries[iselected].value
                                self.descend( depth )
                                return {}
                        return switchaction
                    except AttributeError:
                        return {}

                elif event.key == pygame.K_BACKSPACE:
                    return self.backspaceaction
 
        ## gamechunk must return a dictionary after processing events.
        ## if you don't want anything to happen, pass an empty dict:
        return {}

#### DIRECTORY MENU CLASS
    def draw( self, screen ):
        MenuClass.draw( self, screen )
        screenwidth, screenheight = screen.get_size()

        if self.listeningfortext:
            fontandsize = pygame.font.SysFont(self.font, self.fontsize)
            listenerlabel = fontandsize.render( self.askingfor + ": " + self.listeningmessage, 
                                                1, self.fontcolor )
            listenerbox = listenerlabel.get_rect()
            listenerbox.left = 0.2*screenwidth
            listenerbox.bottom = screenheight - 10
            screen.blit( listenerlabel, listenerbox )


#### END DIRECTORY MENU CLASS




