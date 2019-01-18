#!/usr/bin/env python

from Tkinter import *

class Widget(object):
    def answer_wounded(self):
        label = Label(self.window, text = "Wait, I am going to call for help.")
        button = Button(self.window, text = "OK", command = self.window.destroy)
        label.pack()
        button.pack()

    def answer_fine(self, room=None):
        if self.hostage_region == "r1":
            label = Label(self.window, text = "Reach the exit. It's in this room!")
        elif self.hostage_region in ["r2", "r4"]:
            label = Label(self.window, text = "Go to r1, and reach the exit.")
        elif self.hostage_region == "r3":
            label = Label(self.window, text = "Go to r4 and r1, and reach the exit. Or you can also go to r2 first, and then r1.")
        button = Button(self.window, text = "OK", command = self.window.destroy)
        label.pack()
        button.pack()

    def run_assertion(self, msg):
        self.window = Tk()
        self.window.geometry("300x200+250+250")
        label = Label(self.window, text = msg)
        button = Button(self.window, text = "OK", command = self.window.destroy)
        label.pack()
        button.pack()
        self.window.mainloop()

    def run_hostage_question(self, hostage_region, msg, left_text, right_text,
                     left_cmd_on_exit, right_cmd_on_exit):
        self.hostage_region = hostage_region
        self.window = Tk()
        self.window.geometry("500x200+250+250")
        label = Label(self.window, text = msg)
        left_button = Button(self.window, text = left_text, command = left_cmd_on_exit)
        right_button = Button(self.window, text = right_text, command = right_cmd_on_exit)
        label.pack()
        left_button.pack()
        right_button.pack()
        self.window.mainloop()

if __name__ == "__main__":
    w = Widget()
    #w.run_assertion("I am going to defuse the bomb.")

    w.run_hostage_question("r3", "Are you wounded?", "I'm wounded", "I'm fine", w.answer_wounded, w.answer_fine)
