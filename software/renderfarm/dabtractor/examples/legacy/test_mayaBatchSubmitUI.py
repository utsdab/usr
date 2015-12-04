#!/usr/bin/python

__author__ = '120988'

from Tkinter import *
import ttk
import tkMessageBox
import datetime
import dabtractor.api.author as author
import sys
import os


'''
class Window:
    def __init__(self, master):
        self.filename=""
        mayaprojdir=Label(root, text="Maya Project").grid(row=1, column=0)
        bar1=Entry(master).grid(row=1, column=1)
        mayascenefile=Label(root, text="Maya Scene File").grid(row=2, column=0)
        bar2=Entry(master).grid(row=2, column=1)

        #Buttons
        y=7
        self.cbutton= Button(root, text="OK", command=self.process_csv)
        y+=1
        self.cbutton.grid(row=10, column=3, sticky = W + E)

        self.bbutton= Button(root, text="Browse", command=self.browsecsv)
        self.bbutton.grid(row=1, column=3)


    def browsecsv(self):
        from tkFileDialog import askopenfilename

        Tk().withdraw()
        self.filename = askopenfilename()
    def process_csv(self):
        if self.filename:
            with open(self.filename, 'rb') as csvfile:
                logreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                rownum=0

                for row in logreader:
                    NumColumns = len(row)
                    rownum += 1

                Matrix = [[0 for x in xrange(NumColumns)] for x in xrange(rownum)]

root = Tk()
window=Window(root)
root.mainloop()

'''

fields = 'Maya Version', 'Maya Project Full Path', 'Scene', 'Start', 'End', 'By', 'Chunks', 'Batch Options'

def fetch(entries):
   for entry in entries:
      field = entry[0]
      text  = entry[1].get()
      print('%s: "%s"' % (field, text))

def makeform(root, fields):
   entries = []
   for field in fields:
      row = Frame(root)
      lab = Label(row, width=20, text=field, anchor='w')
      ent = Entry(row)
      row.pack(side=TOP, fill=X, padx=5, pady=5)
      lab.pack(side=LEFT)
      ent.pack(side=RIGHT, expand=YES, fill=X)
      entries.append((field, ent))
   return entries


def makeJob(entries):
    for entry in entries:
        field = entry[0]
        text = entry[1].get()
        print('%s: "%s"' % ( field, text))

    mayaversion = entries[0][1].get()
    mayaprojectpath = entries[1][1].get()
    mayascene = entries[2][1].get()
    mayascenefullpath = "%s/%s" % (mayaprojectpath, mayascene)

    mayascenebase = os.path.splitext(mayascene)[0]
    startframe = (entries[3][1].get())
    endframe = (entries[4][1].get())
    byframe = (entries[5][1].get())
    chunks = (entries[6][1].get())
    options = (entries[7][1].get())

    job = author.Job(title="MayaBatch Render Job",
                     priority=100,
                     envkey=["maya%s" % mayaversion],
                     service="PixarRender")

    task = author.Task(title="Copy Project Locally", service="PixarRender")
    copyin = author.Command(argv=["scp", "remote:%s" % (mayaprojectpath), "/Volume/localrender/"])
    task.addCommand(copyin)
    job.addChild(task)

    task = author.Task(title="Make output directory", service="PixarRender")
    makediectory = author.Command(argv=["mkdir", "%s/%s/%s" % (mayaprojectpath, "images", mayascenebase)])
    task.addCommand(makediectory)
    job.addChild(task)

    if ( int(chunks) > (int(endframe) - int(startframe)) ):
        chunk = 1
        framesperchunk = (int(endframe) - int(startframe) + 1)
        remainder = 0
    else:
        (framesperchunk, remainder) = divmod((int(endframe) - int(startframe) + 1), int(chunks))
        chunk = chunks

    # print int(startframe),int(endframe),int(chunk),int(chunks),int(remainder),int(framesperchunk)


    task = author.Task(title="Rendering", service="PixarRender")
    for i in range(0, int(chunk)):
        sf = (int(startframe) + (i * int(framesperchunk)) )
        ef = (int(startframe) + (i * int(framesperchunk)) + int(framesperchunk) - 1 )

        if (ef >= int(endframe) or (i == int(chunks) - 1)):
            ef = int(endframe)

        render = author.Command(argv=["mayabatch",
                                      options,
                                      "-proj", mayaprojectpath,
                                      "-start", "%s" % (sf),
                                      "-end", "%s" % (ef),
                                      "-by", byframe,
                                      mayascenefullpath])

        task.addCommand(render)
    job.addChild(task)

    task = author.Task(title="Copy Project Back", service="PixarRender")
    copyout = author.Command(argv=["scp", "/local/file.tif", "remote:/path/file.tif"])
    task.addCommand(copyout)
    job.addChild(task)

    print "\n{}".format(job.asTcl())


if __name__ == '__main__':
   root = Tk()
   root.title("Maya Batch Submit")
   ents = makeform(root, fields)
   root.bind('<Return>', (lambda event, e=ents: fetch(e)))
   b1 = Button(root, text='Submit', command=(lambda e=ents: makeJob(e)))
   b1.pack(side=LEFT, padx=5, pady=5)
   b2 = Button(root, text='Quit', command=root.quit)
   b2.pack(side=LEFT, padx=5, pady=5)
   root.mainloop()

