import pygame
if not pygame.font.get_init(): pygame.init()

# Modified from http://www.pygame.org/wiki/TextWrap
def drawText(text, color=(245,245,245), surface=None, lineSpacing=-2, font=pygame.font.Font(pygame.font.match_font('helvetica, calibri, arial'), 20), aa=True, bkg=None):
    ''' drawText will add some text into a Surface object, automatically wrapping words as necessary. return (Surface, String) or (False, String)
        
        Input:
        text = The text to be drawn (String).
        color = Optional: The RGB color to use for drawing the text (Tuple). Default = (245, 245, 245)
        surface = Optional: A Pygame Surface or Rect object which sets the boundaries of the text (Surface or Rect). Default = pygame.display.get_surface()
        lineSpacing = Optional: The amount of separation added between lines (Integer). Default = -2
        font = Optional: A Pygame Font object used for the text (Font). Default = 20pt Calibri, Arial, or Helvetica
        aa = Optional: Use Anti-Aliasing for text (Boolean). Default = True
        bkg = Optional: The RGB background color to put behind the text (Tuple). Default = None
        
        Returns a new Surface object plus any extra text that didn't fit into the supplied rectangle on success.
        Returns False and an error message if the text can't be added.
    '''
    text=str(text)
    text=text.replace('\r\n','\n')
    text=text.replace('\r','\n')
    t=text.split('\n')
    unused=[]
    try:
        if surface==None:
            s = pygame.Surface(pygame.display.get_surface().get_rect().size, flags=pygame.SRCALPHA)  #Make a new Surface on which to apply text
        elif type(surface)==pygame.Rect:
            s = pygame.Surface(surface.size, flags=pygame.SRCALPHA)  #Make a new Surface on which to apply text
        elif type(surface)!=pygame.Surface:
            return False, "Provided surface parameter is neither a Surface nor Rect"
        else:
            s = pygame.Surface(surface.get_rect().size, flags=pygame.SRCALPHA)  #Make a new Surface on which to apply text
        
        s.fill((0,0,0,0), special_flags=pygame.BLEND_RGBA_MIN)
        rect=s.get_rect()
        y = rect.top
        lineSpacing = int(lineSpacing)
        # get the height of the font
        fontHeight = font.size("Tg")[1]
        for text in t:
            if len(text)==0:
                y += fontHeight + lineSpacing
            else:
                while text:
                    i = 1
             
                    # determine if the row of text will be outside our area
                    if y + fontHeight > rect.bottom:
                        break
             
                    # determine maximum width of line
                    while font.size(text[:i])[0] < rect.width and i < len(text):
                        i += 1
             
                    # if we've wrapped the text, then adjust the wrap to the last word      
                    if i < len(text): 
                        i = text.rfind(" ", 0, i) + 1
             
                    # render the line and blit it to the surface
                    if bkg:
                        image = font.render(text[:i], 1, color, bkg)
                        image.set_colorkey(bkg)
                    else:
                        image = font.render(text[:i], aa, color)
             
                    s.blit(image, (rect.left, y))
                    y += fontHeight + lineSpacing
             
                    # remove the text we just blitted
                    text = text[i:]
            if text: unused.append(text)
        
        return s, '\n'.join(unused)   #Return the new text surface, and any unused text
    except OSError:
        return False, "Unknown problem adding text."

#Make alternate function names for adding word-wrapped text
wrapText=drawText
wrapped=drawText

#### Test of drawText
'''
size=(320, 240)			    #The size of the test window, in pixels
window=pygame.display.set_mode(size)	#Open window
window.fill((255,255,255))	#Set the background to white
textbox=window.get_rect()
textbox.inflate_ip(-20,-20)   #Easy way to make the textbox rectangle 20 pixels smaller than the window (10 pixels on each side)
test_sentence="This is a long sentence that will need to be wrapped in order\n\r\n.\r.\n.\nto fit in this small window. It's also much too long to fit vertically, so some of the text is going to be truncated and returned.\nThen the remainder can be called again if necessary."
wrapped_text=wrapped(test_sentence,(80,80,80),textbox)
if wrapped_text:
    print wrapped_text[1]   #Print any remaining text
    window.blit(wrapped_text[0], textbox)
pygame.display.flip()		#Update the window to show text
pygame.time.wait(10000)     #Wait 10 seconds before closing window
#Nothing more to do, the window closes and program ends
'''