# metagame.py - backdrops and gamechunk parent classes
import pygame, sys, os
from pygame.locals import *
from math import *
from random import random

twopi = 2*pi

def randomcolor( targetbrightness = 200): 
    Rcolor = int( random() * 300 )
    Gcolor = int( random() * 300 )
    Bcolor = int( random() * 300 )
    norm = 1.0*targetbrightness / (Rcolor + Gcolor + Bcolor)
    Rcolor = min(int(norm*Rcolor), 255)
    Gcolor = min(int(norm*Gcolor), 255)
    Bcolor = min(int(norm*Bcolor), 255)
    return (Rcolor, Gcolor, Bcolor)

def randomphase():
    return random()*twopi

def Error(msg):
    pygame.quit()
    sys.exit(msg)

def Warn(msg):
    print "WARNING!", msg




class BackDropClass:
    def __init__( self, **kwargs ):
        self.allowedchanges = []
        self.image = 0
    def setstate( self, **kwargs ):
        for key, value in kwargs.iteritems():
            if key in self.allowedchanges:
                setattr( self, key, value )
            else:
                Warn("in BackDropClass:setstate - key "+ key +" is protected!!") 
    def update( self, dt ):
        pass
    
    def addimage( self, image, loc="center" ):
        self.image = image
        self.imagerect = self.image.get_rect()
        self.imageloc = loc
    
    def drawimage( self, screen ):
        if self.image:
            screenwidth, screenheight = screen.get_size()
            if self.imageloc == "center":
                self.imagerect.centerx = screenwidth*0.5
                self.imagerect.centery = screenheight*0.5
            elif self.imageloc == "centerright":
                self.imagerect.right = screenwidth-10
                self.imagerect.centery = screenheight*0.5
            elif self.imageloc == "centerleft":
                self.imagerect.left = 10
                self.imagerect.centery = screenheight*0.5
            elif self.imageloc == "bottomright":
                self.imagerect.right = screenwidth-10
                self.imagerect.bottom = screenheight-10
            
            screen.blit( self.image, self.imagerect )
        
    def draw( self, screen ): 
        screen.fill( (0,0,0) )
        self.drawimage( screen )
            
            

class GameChunkClass:
    def __init__( self ):
        self.backdrop = BackDropClass()
    def update( self, dt, midi ):
        self.backdrop.update( dt )
    def setbackspaceaction( self, action ):
        self.backspaceaction = action
    def process( self, event, midi ):
        return {}
    def processmidi( self, midi ):
        return {}
    def draw( self, screen ):
        #black out screen
        self.backdrop.draw( screen )
        #draw stuff... (none for default)
    def quit( self ):
        pass

class GameElementClass:
    def __init__( self, **kwargs ):
        self.allowedchanges = []
    def setstate( self, **kwargs ):
        for key, value in kwargs.iteritems():
            if key in self.allowedchanges:
                setattr( self, key, value )
            else:
                Warn("in GameElementClass:setstate - key "+ key +" is protected!!") 
    def update( self, dt ):
        pass
    def draw( self, screen, x, y ):
        pass

class PianoKeyClass( GameElementClass ):
    def __init__( self, **kwargs ):
        self.allowedchanges = [ "on", #set to the notes velocity when struck
                                "fadespeed", # how quickly the note's "on" deteriorates
                                "width",
                                "white",
                                "length",
                                "whitekeyindex",
                                "fillcoloroff",
                                "fillcoloron" ]
        # setting defaults
        self.on = 0
        self.fadespeed = 0.06
        self.width = 30
        self.length = 100
        self.whitekeyindex = 0
        self.white = True
        self.fillcoloroff = (200,200,200)
        self.fillcoloron = (255,100,100)
        # now set whatever the user tells you to
        self.setstate( **kwargs )
        self.fillcolor = (0,0,0) #will be set later
    
    def update( self, dt ):
        if self.on > 0:  
            self.on -= self.fadespeed * dt
        else:
            self.on = 0
        
        #max velocity is 127
        onpercentage = self.on * 1.0 / 127
        self.fillcolor = ( self.fillcoloron[0]*onpercentage + self.fillcoloroff[0]*(1-onpercentage),
                           self.fillcoloron[1]*onpercentage + self.fillcoloroff[1]*(1-onpercentage),
                           self.fillcoloron[2]*onpercentage + self.fillcoloroff[2]*(1-onpercentage) )

