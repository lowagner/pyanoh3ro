# backdrops.py - more specific backdrops / backgrounds for things to go on top of.
from metagame import *
import config

class ColorOscillatingBackDropClass( BackDropClass ):
    def __init__( self, **kwargs ):
        self.image = 0
        self.allowedchanges = [ "redmean", "redamp", "redfrequency", "redphase",
                                "greenmean", "greenamp", "greenfrequency", "greenphase",
                                "bluemean", "blueamp", "bluefrequency", "bluephase" ]

        self.redmean = 40 # mean of red oscillations
        self.redamp = 20 # amplitude of red oscillations
        self.redfrequency = 0.0001 # frequency of red oscillations
        self.redphase = 0

        self.greenmean = 40 # mean of green oscillations
        self.greenamp = 20 # amplitude of green oscillations
        self.greenfrequency = 0.00015315 # frequency of green oscillations
        self.greenphase = 0

        self.bluemean = 40 # mean of blue oscillations
        self.blueamp = 20 # amplitude of blue oscillations
        self.bluefrequency = 0.000311515151 # frequency of blue oscillations
        self.bluephase = 0

        self.setstate( **kwargs )

    def update( self, dt ):
        self.redphase += self.redfrequency*dt
        self.greenphase += self.greenfrequency*dt
        self.bluephase += self.bluefrequency*dt

        if self.redphase > twopi:
            self.redphase -= twopi
        elif self.greenphase > twopi:
            self.greenphase -= twopi
        elif self.bluephase > twopi:
            self.bluephase -= twopi
            
        self.red = self.redmean + self.redamp * sin( self.redphase )
        self.green = self.greenmean + self.greenamp * sin( self.greenphase )
        self.blue = self.bluemean + self.blueamp * sin( self.bluephase )

    def draw( self, screen ):
        screen.fill( (self.red,self.green,self.blue) )
        self.drawimage( screen )

class LeftPianoKeyClass( PianoKeyClass ):
    ''' this key is anchored on the left by x and centered at y '''
    def draw( self, screen, x, y ):
        pos = Rect(0,0,self.length,self.width) # length is the long part of the key
        pos.left = x
        pos.centery = y 
        pygame.draw.rect( screen, self.fillcolor, pos ) #draw filled

class LeftPianoBackDropClass( ColorOscillatingBackDropClass ):
    ''' this backdrop has a piano on the left-side of the screen '''
#### CLASS LEFTPIANO
    def __init__( self, **kwargs ):
        ColorOscillatingBackDropClass.__init__(self, **kwargs)

        self.allowedchanges = [ "redmean", "redamp", "redfrequency", "redphase",
                                "greenmean", "greenamp", "greenfrequency", "greenphase",
                                "bluemean", "blueamp", "bluefrequency", "bluephase" ]

        self.whitekeyfractions = [ 1.0/7 ] * 7  # height of each white key, 
                                                # as a fraction of the screen's vertical height
        ## make 12 keys
        self.keys = []
        for i in range(12):
            ## make the on colors of the keys a rainbow
            if i in [ 0, 2, 4, 5, 7, 9, 11 ]:  
                #white keys
                self.keys.append( LeftPianoKeyClass( fillcoloroff=(200,200,200), length=130,
                            fillcoloron=config.rainbow[i] ) )
            else: 
                #black keys
                self.keys.append( LeftPianoKeyClass( fillcoloroff=(20,20,20), length=80,
                            fillcoloron=config.rainbow[i] ) )

#### CLASS LEFTPIANO
    def setstate( self, **kwargs ):
        for key, value in kwargs.iteritems():
            if key in self.allowedchanges: 
                setattr( self, key, value )
            else:
                Warn("in LeftPianoBackDropClass:setstate - key "+ key +" is protected!!") 

#### CLASS LEFTPIANO
    def hitrandomkey( self, midi, midioctave=5, notevel=100 ): # midioctave = 5 is middle C
        randompiano = int( random()*12 )
        self.setstate( redphase=randomphase(), 
                       greenphase=randomphase(), 
                       bluephase=randomphase() )
        ## and play it with midi:
        self.hitkey( midi, randompiano + midioctave*12, notevel )

#### CLASS LEFTPIANO
    def brightenkey( self, midinote = 60, notevel = 100 ): # midinote = 60 is middle C
        self.keys[ midinote % 12 ].setstate( on=notevel )

#### CLASS LEFTPIANO
    def hitkey( self, midi, midinote = 60, notevel = 100 ): # midinote = 60 is middle C
        # make the key flash on
        self.brightenkey( midinote, notevel )
        ## and play it with midi:
        midi.playnote( midinote )

#### CLASS LEFTPIANO
    def update( self, dt ):
        ColorOscillatingBackDropClass.update(self, dt)
        for key in self.keys:
            key.update(dt)

#### CLASS LEFTPIANO
    def draw( self, screen ):
        ColorOscillatingBackDropClass.draw(self, screen)
        screenwidth, screenheight = screen.get_size()
        whitekeylength = 0.13*screenwidth
        blackkeylength = 0.08*screenwidth
        iwhite=0
        middleofnote = screenheight + 0.5*screenheight*self.whitekeyfractions[0]
        middles = [ ]
        for i in [ 0, 2, 4, 5, 7, 9, 11 ]:  # white keys
            middleofnote -= screenheight*self.whitekeyfractions[iwhite] 
            middles.append( middleofnote ) 
            self.keys[i].setstate( width=0.4*screenheight*self.whitekeyfractions[iwhite],
                                   length=whitekeylength )
            self.keys[i].draw( screen, 0, middleofnote )
            iwhite += 1

        iwhite = 0
        for i in [ 1, 3, 6, 8, 10 ]: # black keys
            self.keys[i].setstate( width=0.16*screenheight*(self.whitekeyfractions[iwhite]
                                                             +self.whitekeyfractions[iwhite+1]),
                                   length=blackkeylength )
            self.keys[i].draw( screen, 0, 0.5*(middles[iwhite]+middles[iwhite+1]) )
            iwhite += 1
            if i == 3:
                iwhite += 1
        
        self.drawimage( screen )

