import pygame
import config
from collections import deque # this is for fast popping of lists from the left
import itertools

class CommandClass( object ): 
#### COMMAND CLASS
    def __init__( self, commandactivate, commandname="cmd" ):
        self.commandfont = config.FONT
        self.commandfontcolor = (255,255,255)
        self.commandfontsize = int(24*config.FONTSIZEmultiplier)
        self.commandbackcolor = (0, 0, 0)
        
        self.commandname = commandname
        self.commandhistory = deque([], config.COMMANDhistory)
        self.commandindex = -1
        # for grabbing information...
        self.commanddo = commandactivate
        self.command = ""
    
    def process( self, event, midi ):
        if event.type == pygame.KEYDOWN:
            # if we're waiting for a message from the user
            if event.key == 27:
                if self.commandindex < 0:
                    if len(self.command):
                        if len(self.commandhistory):
                            if self.commandhistory[0] != self.command:
                                self.commandhistory.appendleft(self.command)
                        else:
                            self.commandhistory.appendleft(self.command)
                else:
                    # if we were looking at the commandhistory, see if we did not
                    # edit the command we used previously:
                    if (  self.command != self.commandhistory[self.commandindex]
                    and ( self.commandindex == 0 
                      or self.command != self.commandhistory[self.commandindex-1] )  ):
                        self.commandhistory = deque( 
                            list(itertools.islice(self.commandhistory,0,self.commandindex))+
                            [self.command] +
                            list(itertools.islice(self.commandhistory,self.commandindex,len(self.commandhistory))),
                            config.COMMANDhistory )
                    
                self.commandindex = -1
                self.command = ""
                return self.commanddo( "", midi )
                
            elif event.key == pygame.K_BACKSPACE:
                self.command = self.command[0:-1] # take out last letter

            elif event.key == pygame.K_RETURN:
                if self.command:
                    # add the message to the history:
                    if not len(self.commandhistory) or self.commandhistory[0] != self.command:
                        self.commandhistory.appendleft( self.command )
                    # keep the message
                    thecommand = self.command
                    # destroy it for next time
                    self.command = ""
                    # enact the message:
                    return self.commanddo( thecommand, midi ) 
                else:
                    return self.commanddo( "", midi ) 

            elif event.key == pygame.K_UP:
                # navigate the listening history
                if self.commandindex < 0:
                    if len(self.command):
                        if len(self.commandhistory):
                            if self.commandhistory[0] != self.command:
                                self.commandhistory.appendleft(self.command)
                                self.commandindex = 0
                        else:
                            self.commandhistory.appendleft(self.command)
                            self.commandindex = 0
                else:
                    # if we were looking at the commandlist, see if we did not
                    # edit the command we used previously:
                    if (  self.command != self.commandhistory[self.commandindex]
                    and ( self.commandindex == len(self.commandhistory)-1 
                      or self.command != self.commandhistory[self.commandindex+1] )   ):
                        self.commandhistory = deque( 
                            list(itertools.islice(self.commandhistory,0,self.commandindex+1))+
                            [self.command] +
                            list(itertools.islice(self.commandhistory,self.commandindex+1,len(self.commandhistory))),
                            config.COMMANDhistory 
                        )
                        #self.commandlist.insert(self.commandindex+1, self.command)
                        self.commandindex += 1
                    
                self.commandindex += 1
                if self.commandindex >= len(self.commandhistory):
                    self.commandindex = len(self.commandhistory)-1
                self.command = self.commandhistory[ self.commandindex ]
            
            elif event.key == pygame.K_DOWN:
                # navigate the command history
                if self.commandindex < 0:
                    if len(self.command):
                        if len(self.commandhistory):
                            if self.commandhistory[0] != self.command:
                                self.commandhistory.appendleft(self.command)
                        else:
                            self.commandhistory.appendleft(self.command)
                else:
                    # if we were looking at the commandhistory, see if we did not
                    # edit the command we used previously:
                    if (  self.command != self.commandhistory[self.commandindex]
                    and ( self.commandindex == 0 
                      or self.command != self.commandhistory[self.commandindex-1] )  ):
                        self.commandhistory = deque( 
                            list(itertools.islice(self.commandhistory,0,self.commandindex))+
                            [self.command] +
                            list(itertools.islice(self.commandhistory,self.commandindex,len(self.commandhistory))),
                            config.COMMANDhistory )
                        #self.commandindex -= 1
                    
                self.commandindex -= 1
                if self.commandindex < 0:
                    self.command = ""
                else:
                    self.command = self.commandhistory[ self.commandindex ]

            elif event.key == pygame.K_PAGEUP:
                # navigate the command history
                if self.commandindex < 0:
                    if len(self.command):
                        if len(self.commandhistory):
                            if self.commandhistory[0] != self.command:
                                self.commandhistory.appendleft(self.command)
                                self.commandindex = 0
                        else:
                            self.commandhistory.appendleft(self.command)
                            self.commandindex = 0
                else:
                    # if we were looking at the commandlist, see if we did not
                    # edit the command we used previously:
                    if (  self.command != self.commandhistory[self.commandindex]
                    and ( self.commandindex == len(self.commandhistory)-1 
                      or self.command != self.commandhistory[self.commandindex+1] )  ):
                        self.commandhistory = deque( 
                            list(itertools.islice(self.commandhistory,0,self.commandindex+1))+
                            [self.command] +
                            list(itertools.islice(self.commandhistory,self.commandindex+1,len(self.commandhistory))),
                            config.COMMANDhistory 
                        )
                        #self.commandlist.insert(self.commandindex+1, self.command)
                        self.commandindex += 1
                
                if len(self.commandhistory): 
                    self.commandindex = len(self.commandhistory)-1
                    self.command = self.commandhistory[ self.commandindex ]
                else:
                    self.commandindex = -1
                    self.command = ""
            
            elif event.key == pygame.K_PAGEDOWN:
                # navigate the command history
                if self.commandindex < 0:
                    if len(self.command):
                        if len(self.commandhistory):
                            if self.commandhistory[0] != self.command:
                                self.commandhistory.appendleft(self.command)
                        else:
                            self.commandhistory.appendleft(self.command)
                else:
                    # if we were looking at the commandlist, see if we did not
                    # edit the command we used previously:
                    if (  self.command != self.commandhistory[self.commandindex]
                    and ( self.commandindex == 0 
                      or self.command != self.commandhistory[self.commandindex-1] )  ):
                        self.commandhistory = deque( 
                            list(itertools.islice(self.commandhistory,0,self.commandindex))+
                            [self.command] +
                            list(itertools.islice(self.commandhistory,self.commandindex,len(self.commandhistory))),
                            config.COMMANDhistory )
                    
                self.commandindex = -1
                self.command = ""

            elif event.key < 128:
                newletter = chr(event.key) #here's our new letter
                if pygame.key.get_mods() & pygame.KMOD_SHIFT: # if the shift key is held down
                    newletter = newletter.upper() #make it uppercase
                self.command += newletter #add it to the message
        
        return {}

#### COMMAND CLASS 

    def draw( self, screen ):
        fontandsize = pygame.font.SysFont(self.commandfont, self.commandfontsize)
        commanddrawtext = fontandsize.render( self.commandname + ": " + self.command, 
                                            1, self.commandfontcolor )
        commanddrawbox = commanddrawtext.get_rect()
        commanddrawbox.left = 10
        commanddrawbox.bottom = screen.get_height() - 10
        pygame.draw.rect( screen, self.commandbackcolor, commanddrawbox )
        screen.blit( commanddrawtext, commanddrawbox )

#### END COMMAND CLASS
