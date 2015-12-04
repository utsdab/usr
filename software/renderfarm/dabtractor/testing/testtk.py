#!/opt/pixar/Tractor-2.0/bin/rmanpy
__author__ = '120988'
from Tkinter import *
from Tkinter import _setit
from random import randint

dayVar = None
dayMenu = None
monthVar = None

def main():
    global dayVar
    global dayMenu
    global monthVar

    root = Tk()
    root.title("Exmaple")

    dayVar = IntVar()
    dayVar.set(1)

    dayMenu = OptionMenu(root, dayVar, 1, 2, 3)
    dayMenu.pack()

    monthVar = StringVar()
    monthVar.set("Jan")
    # When the variable monthVar changes (i.e., when you selected something in the list) then the function repopulateDayMenu will get called
    # I don't know what the "w" is for, but it doesn't work without it.
    monthVar.trace("w", repopulateDayMenu)

    monthMenu = OptionMenu(root, monthVar, "Jan", "Feb", "Mar", "Apr")
    monthMenu.pack()

    b = Button(root, text="Print Date", command=printDate)
    b.pack()

    root.mainloop()

# Ignore the parameters - the call back system provides some parameters but I am not sure what they are - just use the definition of the function like this
def repopulateDayMenu(*args):
    # Delete all items in the option menu
    dayMenu["menu"].delete(0,"end")

    # As an example, populate the menu with numbers from 1 to a random numner lower than 30
    for i in range(1, randint(1, 30)):
        # Add a new item (i - in this case an int) to the option menu
        dayMenu['menu'].add_command(label=i, command= _setit(dayVar,i))
        dayVar.set(1)

def printDate() :
    print("The day is %d and the month is %s" % (dayVar.get(), monthVar.get()))

main()