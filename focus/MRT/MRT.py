#Seli, Ralph, Risko, Schooler, Schacter, and Smilek (2017)
#Programmed by Brandon Ralph, University of Waterloo
import numpy as np
import time
import sys, pygame, random, datasaver, text_wrapper

disable_music = False
#if len(sys.argv) > 1:
#    if sys.argv[1] == 'no-music':
#        print('Disabling music')
#        disable_music = True

experiment_start = time.time()

pygame.init()
pygame.mixer.init(frequency=22050, channels=1, buffer=64)
clock=pygame.time.Clock()

#create subject number
from datetime import datetime
if len(sys.argv) > 1:
    subject = sys.argv[1]
else:
    subject = int( (datetime.today()).__format__("%y%m%d%H%M%S") )
#create data file
datasaver.save("./focus/MRT/data/"+str(subject),("subject", "trial", "omission", "RT_from_metronome", "probeType", "TaskFocus", "Confidence", "bored1Effort", "bored2Frustration", "bored3Distress", "bored4Boredom", "bored5Fatigue", "timestamp", "audio"))

#set up window
window=pygame.display.set_mode((0,0),pygame.FULLSCREEN)
centre=window.get_rect().center
pygame.mouse.set_visible(False)

#colours
black = (0, 0, 0)
white = (255, 255, 255)

#set keys
continueKey = pygame.K_SPACE
terminate = pygame.K_SPACE #pygame.K_t
exitKey = pygame.K_e
escapeKey = pygame.K_ESCAPE
#startKey = pygame.K_s
#skipKey = pygame.K_n
#selfCaughtKey = pygame.K_m

#display messages
resolutionX = 1920
resolutionY = 1080
edge = 100
text_pos = (edge, edge)
wrapSize = (resolutionX - 2*edge, resolutionY - 2*edge)
text_spacing = 3
font=pygame.font.Font(pygame.font.match_font('garamond, times, arial'), 32)

instructionsP0 = text_wrapper.drawText(
'Metronome Response Task'
+'\n\nI have seen the consent form and I voluntarily agree to participate in this study.'
+'\n\nPress the <spacebar> to consent to the study.'
+'\n\nIf you do not consent to participate please speak to the experimenter now.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

instructionsP1 = text_wrapper.drawText(
'For this experiment you will hear a metronome sound presented at a constant rate via the headphones.'
+'\n\nYour task is to press the <spacebar> in synchrony with the onset of the metronome so that you press the space bar exactly when each metronome sound is presented.'
+'\n\nEvery once in a while you will be presented with a thought-sampling screen that will ask you to indicate what you were experiencing immediately before the thought-sampling screen appeared.'
+'\n\nYour options will be "On Task", "Mind Wandering Unintentionally", and "Mind Wandering Intentionally"'
+'\n\nYou will then be presented with a screen that will ask you to indicate the degree of your Confidence in your response.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

instructionsP2 = text_wrapper.drawText(
'"On Task" means that you were focused on completing the task immediately before the thought-sampling screen appeared. '
+'"On Task" thoughts include thoughts about your performance on the task, your responses, or the experiment. Being totally focused on the task also counts. '
+'\n\n"Mind Wandering" means that you were thinking about something unrelated to the task immediately before the thought-sampling screen appeared. '
+'"Mind Wandering" thoughts include thoughts about your courses, plans with friends, food, or any other thoughts not related to this experiment. '
+'\n\n"Mind Wandering Unintentionally" means your thoughts drifted away from the task despite your intention to focus on the task. '
+'\n"Mind Wandering Intentionally" means you decided to think about things that are unrelated to the task. '
+'\n\nYou will use the keyboard to select the response option that best describes your mental state just before this screen appeared. '
+'\n\nThe thought-sampling screen will look like this:'
+'\n\nSTOP!'
+'\nWhich of the following best characterizes your mental state JUST BEFORE this screen appeared:'
+'\n     (1)  Completely Focused (Highest Focus)'
+'\n     (2)  Mostly Focused'
+'\n     (3)  Mostly Mind-Wandering'
+'\n     (4)  Completely Mind-Wandering (Lowest Focus)'
+'\n\nPlease use the keyboard to select the response option that best describes your mental state just before this screen appeared.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

instructionsP3 = text_wrapper.drawText(
'You will then be presented with a screen that will ask you to indicate the degree of your Confidence in your response.'
+'\n\nConfidence means how sure you are that your response accurately reflects your mental state just before the thought-sampling screen appeared.'
+'\n\n\nThe screen will look like this:'
+'\nTo what degree are you Confident your current response accurately reflects your mental state just before the thought-sampling screen appeared:'
+'\n     (1)  Extremely Confident'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  Not At All Confident'
+'\n\nPlease use the keyboard to select the response option that best describes your confidence in the accuracy of your response.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

instructionsP4 = text_wrapper.drawText(
'Sometimes you will also be presented with a screen that will ask you about your experience with the experiment so far. '
+'\nAs with the other questions you will use the keyboard to select the response option that best describes your experience. '
+'\n\nYou are now going to complete a brief practice session to help you become familiar with the task. '
+'\n\nWhen you are ready to proceed, please press the <spacebar> to begin the practice session.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

instructions= [instructionsP0[0], instructionsP1[0], instructionsP2[0], instructionsP3[0], instructionsP4[0]]

practice_over = text_wrapper.drawText(
'The practice trials are now over.'
+'\n\nIf you have any questions please ask the experimenter now.'
+'\n\nThe full session will last about 20 minutes.'
+'\nIf you are ready to begin the full session please press the <spacebar>.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

preScreen = text_wrapper.drawText(
'We have some questions about your expectations for the experiment.'
+'\nPlease indicate responses to the following questions in a similar way as the others'
+'\nThat is, you will use the keyboard to select the response option that best describes your experience.'
+'\n\nPress the <spacebar> to continue to the questions',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

preScreen1 = text_wrapper.drawText(
'\n\n\nHow much mental effort do you think the task will require?'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your expectation.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

preScreen2 = text_wrapper.drawText(
'\n\n\nHow much frustration do you think the task will make you experience?'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your expectation.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

preScreen3 = text_wrapper.drawText(
'\n\n\nHow much discomfort or distress do you think the task will make you experience?'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your expectation.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

preScreen4 = text_wrapper.drawText(
'\n\n\nHow much boredom do you think the task will make you experience?'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your expectation.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

preScreen5 = text_wrapper.drawText(
'\n\n\nHow much mental fatigue do you think the task will make you experience?'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your expectation.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

probeScreenOne = text_wrapper.drawText(
'\n\nSTOP!'
+'\nWhich of the following best characterizes your mental state JUST BEFORE this screen appeared:'
+'\n     (1)  Completely Focused (Highest Focus)'
+'\n     (2)  Mostly Focused'
+'\n     (3)  Mostly Mind-Wandering'
+'\n     (4)  Completely Mind-Wandering (Lowest Focus)'
+'\n\nPlease use the keyboard to select the response option that best describes your mental state just before this screen appeared.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

probeScreenTwo = text_wrapper.drawText(
'\n\n\nTo what degree are you Confident your current response accurately reflects your mental state just before the thought-sampling screen appeared:'
+'\n     (1)  Extremely Confident'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  Not At All Confident'
+'\n\nPlease use the keyboard to select the response option that best describes your confidence in the accuracy of your response.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

boredScreen = text_wrapper.drawText(
'Now we will ask you about your experience with the experiment so far.'
+'\nPlease indicate responses to the following questions in a similar way as the others'
+'\nThat is, you will use the keyboard to select the response option that best describes your experience.'
+'\n\nPress the <spacebar> to continue to the questions',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

boredScreen1 = text_wrapper.drawText(
'\n\n\nTo what degree was the task requiring mental effort just before the thought-sampling screen appeared:'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your current experience.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

boredScreen2 = text_wrapper.drawText(
'\n\n\nTo what degree was the task frustrating you just before the thought-sampling screen appeared:'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your current experience.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

postScreen = text_wrapper.drawText(
'We have some questions about your experience with the experiment overall.'
+'\nPlease indicate responses to the following questions in a similar way as the others'
+'\nThat is, you will use the keyboard to select the response option that best describes your experience.'
+'\n\nPress the <spacebar> to continue to the questions',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

postScreen1 = text_wrapper.drawText(
'\n\n\nHow much mental effort did the task require?'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your experience.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

postScreen2 = text_wrapper.drawText(
'\n\n\nHow much frustration did the task cause?'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your experience.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

postScreen3 = text_wrapper.drawText(
'\n\n\nHow much discomfort or distress did the task cause?'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your experience.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

postScreen4 = text_wrapper.drawText(
'\n\n\nHow much boredom did the task cause?'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your experience.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

postScreen5 = text_wrapper.drawText(
'\n\n\nHow much mental fatigue did the task cause?'
+'\n     (1)  None'
+'\n     (2)  '
+'\n     (3)  '
+'\n     (4)  '
+'\n     (5)  '
+'\n     (6)  A lot'
+'\n\nPlease use the keyboard to select the response option that best describes your experience.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

thank_you = text_wrapper.drawText(
'\n\n\nThe metronome task is now over.'
+'\n\nWe have a few more questions for you.'
+'\n\nWhen you are ready press the <spacebar> to continue to the last questions.', 
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

missScreen = text_wrapper.drawText(
'\n\n\nYou have missed quite a few trials.'
+'\n\nWhile we expect that participants will miss some trials, if you miss too many trials we will not be able to use your data.',
white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

#load sound
metronome = pygame.mixer.Sound('./focus/MRT/metronomeMono.wav')

#load image
resume = text_wrapper.drawText('\n\n\nWhen you are ready press the <spacebar> to resume the task', white, surface=pygame.transform.scale(window, wrapSize), lineSpacing = text_spacing, font=font)

#trial information
pre_targ = 650  #arbitrary
targ_time = 75  #arbitrary
post_targ = 575 #arbitrary
trial_duration = pre_targ + targ_time + post_targ #total trial time = 1300 ms

#probe information
debug = False
if debug:
    num_practice = 2 #arbitrary
    experimentLengthMinutes = 2 #arbitrary
    num_trials = int((experimentLengthMinutes*60*1000)//trial_duration) #experimentLength (in miliseconds) // trial_duration (ms)
    probefrequency = 60 #arbitrary: probe frequency: 1 per XXX seconds
    blocksize = int((probefrequency*1000)//trial_duration)
    num_probes = num_trials // blocksize
else:
    num_practice = 18 #arbitrary
    experimentLengthMinutes = 19.5 #arbitrary
    num_trials = int((experimentLengthMinutes*60*1000)//trial_duration) #experimentLength (in miliseconds) // trial_duration (ms)
    blocksize = 25 #50 #arbitrary
    num_probes = num_trials // blocksize #50 trial blocks (900 / 50) = 18

    
#Miss Counter
missCount = 0 #counter
missCountAbs = 0 #counter
missMaxAbs = int(num_trials//10) #arbitrary: from original papers

probeBlocks=range(0,num_trials+blocksize,blocksize)
probeList = []
for i in range(num_probes):
    probeList.append(random.randint(probeBlocks[i]+3,probeBlocks[i+1]-2))

audio_fpath = './focus/MRT/distraction_music/01 Permission to Dance.mp3'
music_trials = np.zeros(num_trials)
inds = np.random.permutation(len(probeList))[:int(len(probeList)/2)]
for ind in inds:
    if ind == 0:
        # Do not play music during learning period
        continue
    start_mask = probeList[ind]+1
    if ind == len(probeList)-1:
        end_mask = -1
    else:
        end_mask = probeList[ind+1]
    music_trials[start_mask:end_mask+1] = 1
if disable_music:
    music_trials[:] = 0
pygame.mixer.music.load(audio_fpath)
pygame.mixer.music.set_volume(0.2)
for i in range(len(inds)):
    pygame.mixer.music.queue(audio_fpath)
music_started = False
music_is_playing = False

def drawScreen(text_to_draw):
    pygame.display.update([window.fill(black),window.blit(text_to_draw,text_pos)])

def responseLoop():
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == escapeKey: 
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == continueKey:
                done = True
        clock.tick()

def drawProbe(stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, probeType):

    if not stop and (probeType=="probe" or probeType=="full"): #probe caught: draw first probe asking about on-task, mind wandering unintentionally, or mind wandering intentionally
        drawScreen(probeScreenOne[0])        
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_1: done=True; TaskFocus="OTC"#Completely On-Task'
                    elif event.key == pygame.K_2:done=True; TaskFocus="OTM"#Mostly On-Task'
                    elif event.key == pygame.K_3:done=True; TaskFocus="MWM"#Mostly Mind-Wandering'
                    elif event.key == pygame.K_4:done=True; TaskFocus="MWC"#Completely Mind-Wandering'
            if stop:break
            clock.tick()
    
    if not stop and (probeType=="probe" or probeType=="full"): #ask about confidence
        drawScreen(probeScreenTwo[0])        
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_1: done=True; Confidence="1"#Extremely Confident'
                    elif event.key == pygame.K_2:done=True; Confidence="2"#Very Confident'
                    elif event.key == pygame.K_3:done=True; Confidence="3"#Moderately Confident'
                    elif event.key == pygame.K_4:done=True; Confidence="4"#Somewhat Confident'
                    elif event.key == pygame.K_5:done=True; Confidence="5"#Not Very Confident'
                    elif event.key == pygame.K_6:done=True; Confidence="6"#Not At All Confident'
            if stop:break
            clock.tick()

    if not stop and probeType == "full": #boredom probes
        drawScreen(boredScreen[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    done=True
            if stop:break
            clock.tick()
    
    if not stop and probeType == "full": #boredom probe: ask about mental effort
        drawScreen(boredScreen1[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored1="0"
                    elif event.key == pygame.K_1: done=True; bored1="1"
                    elif event.key == pygame.K_2:done=True; bored1="2"
                    elif event.key == pygame.K_3:done=True; bored1="3"
                    elif event.key == pygame.K_4:done=True; bored1="4"
                    elif event.key == pygame.K_5:done=True; bored1="5"
                    elif event.key == pygame.K_6:done=True; bored1="6"
                    #elif event.key == pygame.K_7:done=True; bored1="7"
                    #elif event.key == pygame.K_8:done=True; bored1="8"
                    #elif event.key == pygame.K_9:done=True; bored1="9"
                    #elif event.key == pygame.K_0:done=True; bored1="10"
            if stop:break
            clock.tick()

    if not stop and probeType == "full": #boredom probe: ask about discomfort or distress
        drawScreen(boredScreen2[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored2="0"
                    elif event.key == pygame.K_1: done=True; bored2="1"
                    elif event.key == pygame.K_2:done=True; bored2="2"
                    elif event.key == pygame.K_3:done=True; bored2="3"
                    elif event.key == pygame.K_4:done=True; bored2="4"
                    elif event.key == pygame.K_5:done=True; bored2="5"
                    elif event.key == pygame.K_6:done=True; bored2="6"
                    #elif event.key == pygame.K_7:done=True; bored2="7"
                    #elif event.key == pygame.K_8:done=True; bored2="8"
                    #elif event.key == pygame.K_9:done=True; bored2="9"
                    #elif event.key == pygame.K_0:done=True; bored2="10"
            if stop:break
            clock.tick()
    
    if not stop and probeType == "miss": #The participant keeps missing trials
        drawScreen(missScreen[0])
        global missWarning
        missWarning=0
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    done=True
            if stop:break
            clock.tick()
    
    
    if not stop and probeType == "pre": #pre questionnaire
        drawScreen(preScreen[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    done=True
            if stop:break
            clock.tick()
    
    if not stop and probeType == "pre": #pre probes
        drawScreen(preScreen1[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored1="0"
                    elif event.key == pygame.K_1: done=True; bored1="1"
                    elif event.key == pygame.K_2:done=True; bored1="2"
                    elif event.key == pygame.K_3:done=True; bored1="3"
                    elif event.key == pygame.K_4:done=True; bored1="4"
                    elif event.key == pygame.K_5:done=True; bored1="5"
                    elif event.key == pygame.K_6:done=True; bored1="6"
                    #elif event.key == pygame.K_7:done=True; bored1="7"
                    #elif event.key == pygame.K_8:done=True; bored1="8"
                    #elif event.key == pygame.K_9:done=True; bored1="9"
                    #elif event.key == pygame.K_0:done=True; bored1="10"
            if stop:break
            clock.tick()
    
    if not stop and probeType == "pre": #pre probes
        drawScreen(preScreen2[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored2="0"
                    elif event.key == pygame.K_1: done=True; bored2="1"
                    elif event.key == pygame.K_2:done=True; bored2="2"
                    elif event.key == pygame.K_3:done=True; bored2="3"
                    elif event.key == pygame.K_4:done=True; bored2="4"
                    elif event.key == pygame.K_5:done=True; bored2="5"
                    elif event.key == pygame.K_6:done=True; bored2="6"
                    #elif event.key == pygame.K_7:done=True; bored2="7"
                    #elif event.key == pygame.K_8:done=True; bored2="8"
                    #elif event.key == pygame.K_9:done=True; bored2="9"
                    #elif event.key == pygame.K_0:done=True; bored2="10"
            if stop:break
            clock.tick()
    
    if not stop and probeType == "pre": #pre probes
        drawScreen(preScreen3[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored3="0"
                    elif event.key == pygame.K_1: done=True; bored3="1"
                    elif event.key == pygame.K_2:done=True; bored3="2"
                    elif event.key == pygame.K_3:done=True; bored3="3"
                    elif event.key == pygame.K_4:done=True; bored3="4"
                    elif event.key == pygame.K_5:done=True; bored3="5"
                    elif event.key == pygame.K_6:done=True; bored3="6"
                    #elif event.key == pygame.K_7:done=True; bored3="7"
                    #elif event.key == pygame.K_8:done=True; bored3="8"
                    #elif event.key == pygame.K_9:done=True; bored3="9"
                    #elif event.key == pygame.K_0:done=True; bored3="10"
            if stop:break
            clock.tick()
    
    if not stop and probeType == "pre": #pre probes
        drawScreen(preScreen4[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored4="0"
                    elif event.key == pygame.K_1: done=True; bored4="1"
                    elif event.key == pygame.K_2:done=True; bored4="2"
                    elif event.key == pygame.K_3:done=True; bored4="3"
                    elif event.key == pygame.K_4:done=True; bored4="4"
                    elif event.key == pygame.K_5:done=True; bored4="5"
                    elif event.key == pygame.K_6:done=True; bored4="6"
                    #elif event.key == pygame.K_7:done=True; bored4="7"
                    #elif event.key == pygame.K_8:done=True; bored4="8"
                    #elif event.key == pygame.K_9:done=True; bored4="9"
                    #elif event.key == pygame.K_0:done=True; bored4="10"
            if stop:break
            clock.tick()
    
    if not stop and probeType == "pre": #pre probes
        drawScreen(preScreen5[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored5="0"
                    elif event.key == pygame.K_1: done=True; bored5="1"
                    elif event.key == pygame.K_2:done=True; bored5="2"
                    elif event.key == pygame.K_3:done=True; bored5="3"
                    elif event.key == pygame.K_4:done=True; bored5="4"
                    elif event.key == pygame.K_5:done=True; bored5="5"
                    elif event.key == pygame.K_6:done=True; bored5="6"
                    #elif event.key == pygame.K_7:done=True; bored5="7"
                    #elif event.key == pygame.K_8:done=True; bored5="8"
                    #elif event.key == pygame.K_9:done=True; bored5="9"
                    #elif event.key == pygame.K_0:done=True; bored5="10"
            if stop:break
            clock.tick()
    
    if not stop and probeType == "post": #post questionnaire
        drawScreen(postScreen[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    done=True
            if stop:break
            clock.tick()
    
    if not stop and probeType == "post": #post probes
        drawScreen(postScreen1[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored1="0"
                    elif event.key == pygame.K_1: done=True; bored1="1"
                    elif event.key == pygame.K_2:done=True; bored1="2"
                    elif event.key == pygame.K_3:done=True; bored1="3"
                    elif event.key == pygame.K_4:done=True; bored1="4"
                    elif event.key == pygame.K_5:done=True; bored1="5"
                    elif event.key == pygame.K_6:done=True; bored1="6"
                    #elif event.key == pygame.K_7:done=True; bored1="7"
                    #elif event.key == pygame.K_8:done=True; bored1="8"
                    #elif event.key == pygame.K_9:done=True; bored1="9"
                    #elif event.key == pygame.K_0:done=True; bored1="10"
            if stop:break
            clock.tick()
    
    if not stop and probeType == "post": #post probes
        drawScreen(postScreen2[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored2="0"
                    elif event.key == pygame.K_1: done=True; bored2="1"
                    elif event.key == pygame.K_2:done=True; bored2="2"
                    elif event.key == pygame.K_3:done=True; bored2="3"
                    elif event.key == pygame.K_4:done=True; bored2="4"
                    elif event.key == pygame.K_5:done=True; bored2="5"
                    elif event.key == pygame.K_6:done=True; bored2="6"
                    #elif event.key == pygame.K_7:done=True; bored2="7"
                    #elif event.key == pygame.K_8:done=True; bored2="8"
                    #elif event.key == pygame.K_9:done=True; bored2="9"
                    #elif event.key == pygame.K_0:done=True; bored2="10"
            if stop:break
            clock.tick()
    
    if not stop and probeType == "post": #post probes
        drawScreen(postScreen3[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored3="0"
                    elif event.key == pygame.K_1: done=True; bored3="1"
                    elif event.key == pygame.K_2:done=True; bored3="2"
                    elif event.key == pygame.K_3:done=True; bored3="3"
                    elif event.key == pygame.K_4:done=True; bored3="4"
                    elif event.key == pygame.K_5:done=True; bored3="5"
                    elif event.key == pygame.K_6:done=True; bored3="6"
                    #elif event.key == pygame.K_7:done=True; bored3="7"
                    #elif event.key == pygame.K_8:done=True; bored3="8"
                    #elif event.key == pygame.K_9:done=True; bored3="9"
                    #elif event.key == pygame.K_0:done=True; bored3="10"
            if stop:break
            clock.tick()
    
    if not stop and probeType == "post": #post probes
        drawScreen(postScreen4[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored4="0"
                    elif event.key == pygame.K_1: done=True; bored4="1"
                    elif event.key == pygame.K_2:done=True; bored4="2"
                    elif event.key == pygame.K_3:done=True; bored4="3"
                    elif event.key == pygame.K_4:done=True; bored4="4"
                    elif event.key == pygame.K_5:done=True; bored4="5"
                    elif event.key == pygame.K_6:done=True; bored4="6"
                    #elif event.key == pygame.K_7:done=True; bored4="7"
                    #elif event.key == pygame.K_8:done=True; bored4="8"
                    #elif event.key == pygame.K_9:done=True; bored4="9"
                    #elif event.key == pygame.K_0:done=True; bored4="10"
            if stop:break
            clock.tick()
    
    if not stop and probeType == "post": #post probes
        drawScreen(postScreen5[0])
        done=False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
                elif event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_BACKQUOTE: done=True; bored5="0"
                    elif event.key == pygame.K_1: done=True; bored5="1"
                    elif event.key == pygame.K_2:done=True; bored5="2"
                    elif event.key == pygame.K_3:done=True; bored5="3"
                    elif event.key == pygame.K_4:done=True; bored5="4"
                    elif event.key == pygame.K_5:done=True; bored5="5"
                    elif event.key == pygame.K_6:done=True; bored5="6"
                    #elif event.key == pygame.K_7:done=True; bored5="7"
                    #elif event.key == pygame.K_8:done=True; bored5="8"
                    #elif event.key == pygame.K_9:done=True; bored5="9"
                    #elif event.key == pygame.K_0:done=True; bored5="10"
            if stop:break
            clock.tick()
    
    
    if not probeType == "post":
        drawScreen(resume[0])
        responseLoop()
    pygame.display.update(window.fill(black))
    
    return stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, probeType

#### trial builder
def doTrial(recordData, trial, probeList):
    global missCount
    global missCountAbs
    global missMaxAbs
    global music_started
    global music_is_playing
    missLimit = 5 #arbitrary: limit for number of consecutive missed trials before warning
    probeType=''
    TaskFocus=''
    Confidence=''
    bored1=''
    bored2=''
    bored3=''
    bored4=''
    bored5=''
    
    RT_from_metronome = ''
    stop = False
    resp = False
    omission = 1
    audio = 'False'
    
    #trialOver = False  #not used in this version
    trial_start = pygame.time.get_ticks()
    trial_stop = trial_start + trial_duration
    soundPlayed = False
    
    if music_trials[trial] == 1:
        audio = 'True'
        if not music_started:
            pygame.mixer.music.play()
            music_started = True
            music_is_playing = True
        else:
            if not music_is_playing:
                pygame.mixer.music.unpause()
                music_is_playing = True
    else:
        pygame.mixer.music.pause()
        music_is_playing = False

    timestamp = time.time()#-experiment_start
    while pygame.time.get_ticks() < trial_stop:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == exitKey: stop = True
            elif not resp and event.type == pygame.KEYDOWN and event.key == continueKey: 
                timestamp = time.time()#-experiment_start
                now = pygame.time.get_ticks() - trial_start
                RT_from_metronome = now - pre_targ # get RT in reference to when tone is presented
                resp = True
                omission = 0
                missCount = 0
#            elif event.type==pygame.KEYDOWN and event.key == selfCaughtKey: #not used in this version
#                [stop, TaskFocus, Confidence, probeThreeResp, probeFourResp, probeType] = drawProbe(stop, TaskFocus, Confidence, probeThreeResp, probeFourResp,"self")
#                omission = 0
#                trialOver=True
#                break
       
        if not soundPlayed and (pygame.time.get_ticks()-trial_start) >= pre_targ: 
            metronome.play()
            soundPlayed = True
            #tone_at = pygame.time.get_ticks() - trial_start

        if stop: break
        clock.tick()
        
    if trial in probeList: #ask the full list of questions at the first third and second third
        if music_is_playing:
            pygame.mixer.music.pause()
            
        if recordData and (trial==probeList[(num_probes//3)*1] or trial==probeList[(num_probes//3)*2]):
            #timestamp = time.time()-experiment_start
            [stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, probeType] = drawProbe(stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, "full")
        else:
            #timestamp = time.time()-experiment_start
            [stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, probeType] = drawProbe(stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, "probe")
    
    if recordData:
        data = [subject, trial, omission, RT_from_metronome, probeType, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, timestamp, audio]
        datasaver.save("data/"+str(subject), data)   #Save Data
    
    #Miss Counter
    missCount += omission
    missCountAbs += omission
    if (missCount==missLimit) or (missCountAbs==(missMaxAbs*8//10)): #New: add warning for too many misses
            #timestamp = time.time()-experiment_start
            [stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, probeType] = drawProbe(stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, "miss")
            if recordData:
                data = [subject, trial, omission, RT_from_metronome, probeType, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, timestamp, audio]
                datasaver.save("data/"+str(subject), data)   #Save Miss Data
    
    return stop

#### Instructions
for i in range(len(instructions)):
    drawScreen(instructions[i])
    responseLoop()  

#### Practice Trials
pygame.display.update(window.fill(black))
recordData = False
practiceProbe = [num_practice/2]
for p in range(num_practice):
    stop = doTrial(recordData, p, practiceProbe)
    if stop:
        break

#### Intermission
drawScreen(practice_over[0])
responseLoop() 
recordData = True

#### Pre-Questions
probeType=''
TaskFocus=''
Confidence=''
bored1=''
bored2=''
bored3=''
bored4=''
bored5=''
stop = False
audio = 'False'
timestamp = time.time()#-experiment_start
[stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, probeType] = drawProbe(stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, "pre")
#data = [subject, trial, omission, RT_from_metronome, probeType, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5]
data = [subject, '', '', '', probeType, '', '', bored1, bored2, bored3, bored4, bored5, timestamp, audio]
datasaver.save("data/"+str(subject), data)   #Save Data

#### Experimental Trials
pygame.display.update(window.fill(black))
for trial in range(num_trials):
    stop = doTrial(recordData, trial, probeList)
    if stop or missCountAbs==missMaxAbs: #stop if they miss so many trials that we are going to have to drop them anyway
        break

#### Post-Questions
probeType=''
TaskFocus=''
Confidence=''
bored1=''
bored2=''
bored3=''
bored4=''
bored5=''
stop = False
timestamp = time.time()#-experiment_start
audio = 'False'
[stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, probeType] = drawProbe(stop, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5, "post")
#data = [subject, trial, omission, RT_from_metronome, probeType, TaskFocus, Confidence, bored1, bored2, bored3, bored4, bored5]
data = [subject, '', '', '', probeType, '', '', bored1, bored2, bored3, bored4, bored5, timestamp, audio]
datasaver.save("data/"+str(subject), data)   #Save Data

#### EXIT
datasaver._quit()
drawScreen(thank_you[0])
done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: done = True
        elif event.type == pygame.KEYDOWN and (event.key == terminate or event.key == escapeKey): done = True
pygame.mixer.music.unload()
pygame.quit()

#import webbrowser
#open using default web browser
#qualtrics = "https://utorontopsych.az1.qualtrics.com/jfe/form/SV_395lhrSC2gHqxb7"
#url = qualtrics + "?SubjectID=" + str(subject)
#webbrowser.open_new(url)

sys.exit()