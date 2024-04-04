# srtMaker
This is a program to assist with manual caption writing by timestamping a video's script dialogue. I was inspired to make this program by my inability to watch and understand dialogue in media without captions.

## Quick Start
You will need:
- Video file (any video format should work)
- Script in HTML format 

For ease of use, move these files to the `srtMaker` folder. You can make additional folders as needed to organize your project files.
### Create a New Project
Use the file navigator to select your video file and script. 
### Load an Existing Project
On the home page, load the `.srt` file in addition to your video and script.
### Writing Captions 
Play the video by pressing the green triangle. As dialogue is spoken, press the spacebar to indicate the start and end timestamps of the line of dialogue displayed in the bottom left-hand corner of the program.

If the background is green, the program is waiting for the start timestamp of the dialogue to be indicated. If the background is red, the program is waiting for the stop timestamp of the dialogue to be indicated. 

Press save to update the `.srt` caption file. If the file does not exist (i.e., this is a new project), it is created. Simultaneously, this displays saved captions in real time.
## Limitations
This project is by no means complete. It assumes that script files are in a specific format. It cannot currently "undo" or "redo" caption timestamp writes, nor can it adjust timestamps after they are first created. These, and more, are feature I hope to include in future releases.