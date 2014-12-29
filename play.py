from ddr import *

# GAMEPLAY
# ddrstyle  :   notes fly from top of screen to bottom onto piano keyboard
#           :   hit the note when it hits the keyboard to get the points

class PlayClass( DDRClass ):
    def __init__( self, piecedir, midi, piecesettings = { "TempoPercent" : 100, "Difficulty" : 0,
                                                    "Sandbox" : config.SANDBOXplay,
                                                    "PlayerStarts" : config.PLAYERstarts,
                                                    "PlayerTrack" : config.ALLOWEDplayertracks } ):
        DDRClass.__init__( self, piecedir, midi, piecesettings )
        try:
            self.play = not self.piece.settings["PlayerStarts"]
        except KeyError:
            self.play = config.PLAYERstarts
       
        # don't let the player track play
        if isinstance( piecesettings["PlayerTrack"], list ):
            for track in piecesettings["PlayerTrack"]:
                self.noisytracks.remove(track)
        else:
            self.noisytracks.remove(piecesettings["PlayerTrack"])

    def update( self, dt, midi ):
        DDRClass.update( self, dt, midi )

    def process( self, event, midi ):
        if event.type == pygame.KEYDOWN:
            ## CERTAIN events are allowed in regular play mode
            if event.key == 27: # escape key
                midi.clearall()
                return { "gamestate" : config.GAMESTATEmainmenu, "printme" : "ESCAPE FROM PLAY MODE" }
            elif self.commonnav( event, midi ):
                return {}
            elif self.commongrid( event, midi ):
                return {}
                        
        return {}


    def processmidi( self, midi ):
        DDRClass.processmidi( self, midi )
        self.play = True

        return {}

    def draw( self, screen ):
        DDRClass.draw( self, screen )
