from kivy.app import App
# from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
# from kivy.uix.video import Video
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty, NumericProperty, BooleanProperty, DictProperty
from kivy.config import Config
from kivy.core.window import Window
from kivy.clock import Clock

import os
import re

from bs4 import BeautifulSoup

# NICE TO HAVE
# TODO use popup
    # check a video is selected and a text file is selected
    # check the file types are correct
# TODO add keybind option to add the name to the caption?
# TODO generalize the options by adding a setting button
    # script format
    # whether to keep silent action or not
# TODO
    # maybe try to automate with whisperX or vosk??????? would need to play around with it a lot

# NEXT UP
# TODO write requirements and README files

Config.set("input", "mouse", "mouse,multitouch_on_demand")

class SrtMakerEntryScreen(Screen):
    buttonPressed = StringProperty()

class FileChooser(Screen):    
    def select(self, *args):
        try: self.label.text = args[1][0]
        except: pass

    def savePath(self, path):
        button = self.manager.get_screen("menu").buttonPressed
        path = os.path.relpath(path)
        # can potentially check whether the file type is correct here
        if button == "video":
            App.get_running_app().video = path
            self.manager.get_screen("video").ids.vPlayer.source = App.get_running_app().video
        elif button == "script":
            App.get_running_app().script = path
        elif button == "srt":
            App.get_running_app().srt = path
    
class SrtMaker(Screen):
    def __init__(self, **kw):
        super(SrtMaker, self).__init__(**kw)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down = self._on_keyboard_down)

        self.script = StringProperty()
        self.srtStr = StringProperty()
        self.strLst = ListProperty()
        self.i = NumericProperty()
        self.tStart = NumericProperty()
        self.recording = BooleanProperty()
        self.dialogueColor = DictProperty()
        self.timeStamp = NumericProperty()

    def on_enter(self, *args):
        self.recording = False
        self.dialogueColor = {True: (245/255, 39/255, 39/255, 0.8), 
                              False: (36/255, 179/255, 36/255, 0.8)}
        self.timeStamp = -1

        self.script = self.reformatScript()
        self.srtStr, self.srtLst, self.i, self.tStart = self.initSRT()
                
        self.ids.name.text = self.script[self.i][0]
        self.ids.dialogue.text = self.script[self.i][1]

    def _keyboard_closed(self):
        print('My keyboard have been closed!')
        self._keyboard.unbind(on_key_down = self._on_keyboard_down)
        self._keyboard = None
    
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print("The key {} has been pressed".format(keycode))
        
        if keycode[1] == 'p':
            self.ids.vPlayer.state = 'play'
            Clock.schedule_once(self.callbackSetVideoInitSeek, 0.2)

        elif keycode[1] == 'spacebar':
            self.recordTimestamps()
            
        return True
    
    def recordTimestamps(self):
        # change recording status
        self.recording = not self.recording

        # set initial timestamp
        if self.recording:
            self.timeStamp = self.ids.vPlayer.position
        # write timestamp
        else:
            caption = []
            # index number
            caption.append(str(self.i + 1) + "\n")
            # start and end timestamp
            startTime = self.formatTime(self.timeStamp)
            stopTime = self.formatTime(self.ids.vPlayer.position)
            caption.append("{} --> {}\n".format(startTime, stopTime))
            # dialogue
            caption.append(self.ids.dialogue.text + "\n")

            print("\n".join(caption))
            self.srtLst.append(caption)
            self.i += 1
            self.ids.name.text = self.script[self.i][0]
            self.ids.dialogue.text = self.script[self.i][1]

        # change color
        self.ids.name.background_color = self.dialogueColor[self.recording]
        self.ids.dialogue.background_color = self.dialogueColor[self.recording]

    def callbackSetVideoInitSeek(self, dt):
        self.ids.vPlayer.state = 'pause'
        self.ids.vPlayer.seek(self.tStart/self.ids.vPlayer.duration)
        
    def formatTime(self, time):
        # time is in seconds
        res = ""

        h = int(time // 3600)
        if h != 0: time %= h * 3600

        res += self.formatTimeDigits(h, 2) + ":"

        m = int(time // 60)
        if m != 0: time %= m * 60

        res += self.formatTimeDigits(m, 2) + ":"
        
        s = int(time)
        time -= s

        res += self.formatTimeDigits(s, 2) + ","

        ms = int(time * 1000)

        res += self.formatTimeDigits(ms, 3)
        return res
    
    def formatTimeDigits(self, time, nDigits):
        if len(str(time)) == nDigits: 
            return str(time)
        elif len(str(time)) < nDigits: 
            return "0" * (nDigits - len(str(time))) + str(time)
        else: 
            return str(time)

    def reformatScript(self):
        script = App.get_running_app().script
        soup = BeautifulSoup(open(script), 'html.parser')
        
        # gets each line without silent action in the form [[name, line],]
        text = [[re.match(r'[A-Z\-]+:', br.nextSibling.replace("\n", "")).group(), br.nextSibling.replace("\n", "")[re.match(r'[A-Z\-]+:', br.nextSibling.replace("\n", "")).end():].strip()] for br in soup.findAll("br") if re.match(r'[A-Z\-]+:', br.nextSibling.replace("\n", "")) != None]

        ''' breakdown the above one-line mess for readability
        text = [br.nextSibling.replace("\n", "") for br in soup.findAll("br") if re.match(r'[A-Z\-]+:', br.nextSibling.replace("\n", "")) != None]
        for line in text: 
            regex = re.match(r'[A-Z\-]+:', line)
            name = regex.group()
            dialogue = line[regex.end():].strip()
        '''
        
        # separate each line into two lines of 32char chunks each
        captions = []
        for line in text:
            name, dialogue = line
            # is this if statement necessary
            if len(dialogue) <= 32:
                captions.append(line)
            else:
                # get 32 char chunks without interrupting words
                while len(dialogue) > 0:
                    newDialogue = ""
                    for _ in range(2):
                        words = dialogue.split(" ")
                        dialoguePiece = " ".join([words[i] for i in range(len(words)) if len(" ".join(words[:i+1])) <= 32])
                        newDialogue += dialoguePiece + "\n"
                        dialogue = dialogue[len(dialoguePiece):].strip()
                    newDialogue = newDialogue.strip()
                    captions.append([name, newDialogue])

        return captions
    
    # loads srt file as string
    def initSRT(self):
        if App.get_running_app().srt != 'Select SRT File (optional)':
            srtStr = open(App.get_running_app().srt).read()
            # set the script to read the line after the last registered one in the srt file
            srtLst = [[line + "\n" for line in item.split("\n") if line != ''] for item in srtStr.split("\n\n")]
            iStart = int(srtLst[-1][0]) 
            tStart = self.convertSRTTimeDigits(srtLst[-1][1].strip().split(" --> ")[1])
        else: 
            srtStr = ''
            srtLst = []
            iStart = 0
            tStart = 0
        
        return srtStr, srtLst, iStart, tStart
    
    def convertSRTTimeDigits(self, t):
        hms, ms = t.split(",")
        h, m, s = hms.split(":")
        return int(h) * 60 * 60 + int(m) * 60 + int(s) + int(ms)/1000

    def saveSRT(self):
        srt = "\n".join(["".join(entry) for entry in self.srtLst])
        print(srt)

        if ".srt" in App.get_running_app().srt:
            f = open(App.get_running_app().srt, "w")
        else:
            f = open(App.get_running_app().video + ".srt", "w")
        f.write(srt)
        f.close

        
''' SRT FORMAT
index number
hh:mm:ss,msx --> hh:mm:ss,msx
text1
text2

'''

''' SRT Lst FORMAT
[[index number, hh:mm:ss,msx --> hh:mm:ss,msx, text1, text2],]
'''

class SrtMakerApp(App):
    video = StringProperty('Select Video')
    script = StringProperty('Select Script')
    srt = StringProperty('Select SRT File (optional)')

    def build(self):
        sm = ScreenManager()
        sm.add_widget(SrtMakerEntryScreen(name="menu"))
        sm.add_widget(FileChooser(name="file directory"))
        sm.add_widget(SrtMaker(name="video"))
        sm.current = 'menu'
        return sm

if __name__ == "__main__":
    SrtMakerApp().run()