#!/usr/bin/env python3
from tkinter import *

'''
def btn_click():
    res = txt.get()
    lbl.configure(text=res)
'''

def insert():
    pass


def get():
    pass

window = Tk()
#window.title("Python GUI Program")
#window.geometry("350x200")

'''
lbl = Label(window, text="Hello", background="red")
lbl.grid(column=0, row=1)

btn = Button(window, text="Submit", command=btn_click)
btn.grid(column=1, row=0)

txt = Entry(window,width=10)
txt.grid(column=0, row=0)

txt.focus()
'''

lbl_id = Label(window, text="Enter Book ID")
lbl_title = Label(window, text="Enter Book Title")
lbl_author = Label(window, text="Enter Book Author")
lbl_year = Label(window, text="Enter Book Year")
txt_id = Entry(window,width=10)
txt_title = Entry(window,width=10)
txt_author = Entry(window,width=10)
txt_year = Entry(window,width=10)
btn_insert = Button(window, text="Insert", command=insert)
btn_get = Button(window, text="Get", command=get)


lbl_id.grid(column=0, row=0)
lbl_title.grid(column=0, row=1)
lbl_author.grid(column=0, row=2)
lbl_year.grid(column=0, row=3)
txt_id.grid(column=1, row=0)
txt_title.grid(column=1, row=1)
txt_author.grid(column=1, row=2)
txt_year.grid(column=1, row=3)
btn_insert.grid(column=0, row=4)
btn_get.grid(column=1, row=4)

txt_id.focus()
window.mainloop()

