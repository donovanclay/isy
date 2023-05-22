# from tkinter import *
# import tkinter.ttk as ttk

# root = Tk()

# tree = ttk.Treeview(root)
# tree.pack()

# style = ttk.Style()
# style.configure("Treeview.Heading", font=(None, 10))

# tree["columns"] = ("one", "two", "three")
# tree.column("one", width=150)
# tree.column("two", width=150)
# tree.column("three", width=150)
# tree.heading("one", text="Naar")
# tree.heading("two", text="Spoor")
# tree.heading("three", text="Vetrektijd")
# tree['show'] = 'headings'

# root.mainloop()



# Python program to create a table
  
from tkinter import *
 
 
class Table:
     
    def __init__(self,root):
         
        # code for creating table
        for i in range(total_rows):
            for j in range(total_columns):
                 
                self.e = Entry(root, width=20, fg='blue',
                               font=('Arial',16,'bold'))
                 
                self.e.grid(row=i, column=j)
                self.e.insert(END, lst[i][j])
 
# take the data
lst = [(1,'Raj','Mumbai',19),
       (2,'Aaryan','Pune',18),
       (3,'Vaishnavi','Mumbai',20),
       (4,'Rachna','Mumbai',21),
       (5,'Shubham','Delhi',21)]
  
# find total number of rows and
# columns in list
total_rows = len(lst)
total_columns = len(lst[0])
  
# create root window
root = Tk()
t = Table(root)
root.mainloop()