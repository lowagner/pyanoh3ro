PyanoH3ro
=========

ABOUT
-----

PyanoH3ro is an open-source python code for creating, playing, and learning music
using any midi-enabled instrument as input, e.g. a USB piano MIDI keyboard.  There are
many ways to use this program (at least, these are the goals):

+ Compose your own music, output to midi (beta status),
+ Study how to play the piano (or organ) (alpha? status),
+ Play a notes-flying keys-on-fire DDR-style game (pre-alpha status),
+ Freestyle jam with other instruments in the background (N/A status),
+ Develop your own style, or integrate or build on others' (unknown status),
+ Share any of the above with friends, family, and the world (MIA).

As seen above, we're somewhere between pre-alpha and beta.  So in addition (or subtraction)
to the above, there will be some perhaps undesired "features" when using the program,
such as sudden crashing/freezing, losing all your hard work, and/or deleting the internet.  Use
at your own risk.  Please read the LICENSE file for more details about things that
can go wrong, and what I'm not responsible for.

To expand the music library:  if you are so inclined, send me your original music 
(midi files are especially great!) and permission to use, and I might include your 
pieces in the database with proper attribution to you.  I will try to ensure that the
actual copyright holder has given me permission.  If somehow your work has been included
without your permission, I am very sorry:  please let me know and upon verification I
will remove it from the database.  Please read the ATTRIB file for other important
attributions and contributions to this program.

I am happy to hear your thoughts and uses for the code.  The code is in its infancy,
so there are plenty of bugs (some known in the TODO list).   Please let me know of 
any bugs I haven't found, as well as how to reproduce any bugs (file an issue at 
github).  Also, if you have any fixes/improvements please share them on github 
(submit a pull request).  If your changes are in line with the above 
vision and the following code practices, I will probably implement them:

+ Easy to read and understand code, well commented.  (I fail this one sometimes, 
  so you can help with commenting if you want.)
+ I adhere to some standard python etiquette except spaces near parentheses.  I
  sometimes use more negative space to improve readability.  YMMV.  I won't be
  too picky about it if you add code, but if I later make changes I may
  add spaces.  But if you are just converting my code into "proper" form I'll be 
  offended and ignore you.

For the motivated, read the TODO list in the root directory for possible things
to work on.


DEPENDENCIES
------------

You must install the following in order for PyanoH3ro to run at all:

+ python-pygame
    - available as a package on most Linux distributions
    - e.g. `apt-get install python-pygame`

+ python-mingus
    - this can be installed via `pip install mingus`
    - https://code.google.com/p/mingus/

+ python-midi
    - this must be installed by hand.  Download from:
    - https://github.com/vishnubob/python-midi
    - Additionally you may need to install `swig` to compile python-midi.

+ FluidR3_GM-2.sf2
    - download this SoundFont from the internet and put it in the resources directory.
   
Let me know if there are any other dependencies not listed above,
or if you have troubles installing/running even after doing the above.


INSTALLATION / RUNNING
----------------------

You can create a fork of this github project (recommended if you want to edit the
code at all) or you can download via `git clone https://github.com/lowagner/pyanoh3ro`.  Either
method requires the git program, or you can download the zip file (off to the right of the
github page).

You will also need to install the dependencies (see section above), set some configuration 
options in a config.py file (see below in configuration section), and then run 

    python pyano3.py
    
to start the game/editor.  To navigate the menus, use only your computer 
keyboard (arrow keys, enter key, backspace) and the USB midi keyboard you 
setup in the settings menu.  The mouse does zilch (cf. nada).  Don't try 
to click anything, ever.  

Let me emphasize, using your mouse does zip.  I am unlikely to add
mouse input to the game, but feel free to add it yourself and make a pull request.  To start 
practicing mouse-free living, use the Vim keys h|j|k|l to navigate the menus.

When first booting PyanoH3ro, if you have a MIDI instrument, 
you should choose it in the "Settings" from the main menu.

### Configuration

In the root directory, copy the file defaultconfig.py to config.py, and
then edit config.py.  This file contains some important variables which allow
you to tune how PyanoH3ro runs.  

The most important variable is the sound driver for Fluidsynth.  This is 
related to the python-mingus package above.  Without the right driver, the
midi may sound bad or not sound at all.

For aesthetics reasons, you may also want to change the default on-start display
resolution, but the program is resizable.

Those are the first two or three variables in config.py, and they are the
most important.  Everything else is more or less self-explanatory, but not 
necessary for main game play.

### Controls

There's lots of different controls for each game chunk.  Check out "Create" first,
and the Navigation mode there gives you an idea of what you can do in the Sandbox mode 
of "Play".


INSPIRATION
-----------

I am a classically trained pianist who took lessons from second
grade through college, and then began playing contemporary music 
in a church band.  That change was quite drastic to me, but I've
enjoyed both very much.  I hope this program can be useful to
people studying the piano, whether their aim is classical,
contemporary, or whatever!

In creating the game, I have been inspired by certain other games.  For
some of these muses, I was upset that I didn't actually learn
how to play instruments, except drums or vocals.  I am also
inspired by the text editor Vim; anyone familiar with Vim will
be familiar with some of the editing commands in the Create mode.  If I
recall correctly, this code was entirely written in Vim.  I really
only use a subset of useful Vim commands, and I'm not religiously 
copying them over.

I developed most of this code without even realizing there was a
closed-source alternative available, Synthesia.  I have never used
that program, but there are bound to be some similarities.  If you
want a more professional and bug-free program, that might be your
best bet.
