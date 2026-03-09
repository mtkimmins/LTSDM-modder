import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from tkinter import filedialog
#########################################
#   FUNC/CLASSES
#########################################
class AudioFrame:
    def __init__(self, mainframe:ttk.Frame, column:int, row:int)->None:
        self.name:str = ""
        self.mainframe:ttk.Frame = mainframe
        self.column:int = column
        self.row:int = row
        self.width:int = 1
        self.height:int = 4
        self.audio_file_path:str = ""

        self.title_label:ttk.Label = ttk.Label(self.mainframe, text=self.name)
        self.title_label.grid(column=self.column, row=self.row)

        self.file_display_label:ttk.Label = ttk.Label(self.mainframe, text=self.audio_file_path)
        self.file_display_label.grid(column=self.column, row=(self.row+1))
        
        self.add_button:ttk.Button = ttk.Button(self.mainframe, text="Add Wave File", command=self.uploadAudioFile)
        self.add_button.grid(column=self.column, row=(self.row+2))

        self.clear_button:ttk.Button = ttk.Button(self.mainframe, text="Clear", command=self.clear)
        self.clear_button.grid(column=self.column, row=(self.row+3))

    def setName(self, name)->None:
        self.name = name
        self.title_label.configure(text=self.name)

    def updateFileName(self)->None:
        self.file_display_label.configure(text=self.audio_file_path[-10:])

    def uploadAudioFile(self)->None:
        file_path = filedialog.askopenfilename(
            title="Select a wave file",
            filetypes=[("All files","*.*")]
        )
        self.audio_file_path = file_path
        self.updateFileName()

    def clear(self)->None:
        self.audio_file_path = ""
        self.updateFileName()



class StoryContainer:
    def __init__(self, mainframe:ttk.Frame, column:int, row:int)->None:
        self.mainframe = mainframe
        self.frames:list[AudioFrame] = []
        self.n_frames:int = 12
        self.column = column
        self.row = row
        for x in range(12):
            frame = AudioFrame(mainframe, self.column+x, 1)
            frame.setName(f"Frame {x+1}")
            self.frames.append(frame)

        self.compile_button = ttk.Button(mainframe, text="Compile", command=self.compile)
        self.compile_button.grid(column=2, row=5)
        
        self.clear_button = ttk.Button(mainframe, text="Clear All", command=self.clear)
        self.clear_button.grid(column=3, row=5)

    def clear(self):
        for frame in self.frames:
            frame.clear()

    def compile(self):
        pass
        #no lights data
        #take each frame data and turn it into an .a18
        #from patterns, construct a full .bin
        #insert frames 1-12 as .a18
        #export the custom .bin

#################
#   RUNTIME     #
#################
root = tk.Tk()
root.title("LTSDM Modder")

mainframe = ttk.Frame(root, padding=(5,5,5,5))
mainframe.grid(column=0, row=0)

ttk.Label(mainframe, text="Upload 12 wave files corresponding to the 12 frames:").grid(column=1, columnspan=99, row=0)
story_container = StoryContainer(mainframe, 0, 1)

root.mainloop()
