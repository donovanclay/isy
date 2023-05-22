# # # importing tkinter gui
# # import tkinter as tk
 
# # #creating window
# # window=tk.Tk()
 
# # #getting screen width and height of display
# # # width= window.winfo_screenwidth()
# # # height= window.winfo_screenheight()
# # #setting tkinter window size
# # window.geometry("%dx%d" % (1200, 900))
# # window.title("Indoor Air Quality")
# # label = tk.Label(window, text="Hello Tkinter!")
# # label.pack()
 
# # window.mainloop()


# from tkinter import *
import tkinter as tk
from  tkinter import ttk

WIDTH = 1200
HEIGHT = 900
COLUMNS = 5
COLUMN_WIDTH = ((WIDTH//2)//COLUMNS) - 10

ws  = tk.Tk()
ws.title('PythonGuides')
# ws.geometry('500x500')
ws.geometry("%dx%d" % (WIDTH, HEIGHT))
ws['bg'] = '#1f3456'

game_frame = tk.Frame(ws)
# game_frame.pack(ipadx=10, ipady=10, anchor=CENTER)
game_frame.pack(ipadx=20, ipady=20, fill=tk.X, side=tk.LEFT)
# game_frame.place(anchor="c", relx=.5, rely=.5)

my_game = ttk.Treeview(game_frame)
style = ttk.Style()
style.configure("Treeview.Heading", font=(None, 200))

my_game['columns'] = ('player_id', 'player_name', 'player_Rank', 'player_states', 'player_city')



my_game.column("#0", width=0,  stretch=tk.NO)
my_game.column("player_id",anchor=tk.CENTER, width=COLUMN_WIDTH)
my_game.column("player_name",anchor=tk.CENTER,width=COLUMN_WIDTH)
my_game.column("player_Rank",anchor=tk.CENTER,width=COLUMN_WIDTH)
my_game.column("player_states",anchor=tk.CENTER,width=COLUMN_WIDTH)
my_game.column("player_city",anchor=tk.CENTER,width=COLUMN_WIDTH)

my_game.heading("#0",text="",anchor=tk.CENTER)
my_game.heading("player_id",text="Fan Name",anchor=tk.CENTER)
my_game.heading("player_name",text="Value",anchor=tk.CENTER)
my_game.heading("player_Rank",text="Max CFM",anchor=tk.CENTER)
my_game.heading("player_states",text="Type",anchor=tk.CENTER)
my_game.heading("player_city",text="States",anchor=tk.CENTER)

my_game.insert(parent='',index='end',iid=0,text='',
values=('1','Ninja','101','Oklahoma', 'Moore'))
my_game.insert(parent='',index='end',iid=1,text='',
values=('2','Ranger','102','Wisconsin', 'Green Bay'))
my_game.insert(parent='',index='end',iid=2,text='',
values=('3','Deamon','103', 'California', 'Placentia'))
my_game.insert(parent='',index='end',iid=3,text='',
values=('4','Dragon','104','New York' , 'White Plains'))
my_game.insert(parent='',index='end',iid=4,text='',
values=('5','CrissCross','105','California', 'San Diego'))
my_game.insert(parent='',index='end',iid=5,text='',
values=('6','ZaqueriBlack','106','Wisconsin' , 'TONY'))

my_game.pack(anchor=tk.CENTER, expand=True)

game_frame2 = tk.Frame(ws)
# game_frame.pack(ipadx=10, ipady=10, anchor=CENTER)
game_frame2.pack(ipadx=20, ipady=20, fill=tk.X, side=tk.RIGHT)
# game_frame.place(anchor="c", relx=.5, rely=.5)

my_game2 = ttk.Treeview(game_frame2)
style = ttk.Style()
style.configure("Treeview.Heading", font=(None, 200))

my_game2['columns'] = ('player_id', 'player_name', 'player_Rank', 'player_states', 'player_city')

my_game2.column("#0", width=0,  stretch=tk.NO)
my_game2.column("player_id",anchor=tk.CENTER, width=(COLUMN_WIDTH) - 40)
my_game2.column("player_name",anchor=tk.CENTER,width=COLUMN_WIDTH)
my_game2.column("player_Rank",anchor=tk.CENTER,width=COLUMN_WIDTH)
my_game2.column("player_states",anchor=tk.CENTER,width=COLUMN_WIDTH)
my_game2.column("player_city",anchor=tk.CENTER,width=COLUMN_WIDTH)

my_game2.heading("#0",text="",anchor=tk.CENTER)
my_game2.heading("player_id",text="Fan",anchor=tk.CENTER)
my_game2.heading("player_name",text="Name",anchor=tk.CENTER)
my_game2.heading("player_Rank",text="Rank",anchor=tk.CENTER)
my_game2.heading("player_states",text="States",anchor=tk.CENTER)
my_game2.heading("player_city",text="States",anchor=tk.CENTER)

my_game2.insert(parent='',index='end',iid=0,text='',
values=('1','Ninja','101','Oklahoma', 'Moore'))
my_game2.insert(parent='',index='end',iid=1,text='',
values=('2','Ranger','102','Wisconsin', 'Green Bay'))
my_game2.insert(parent='',index='end',iid=2,text='',
values=('3','Deamon','103', 'California', 'Placentia'))
my_game2.insert(parent='',index='end',iid=3,text='',
values=('4','Dragon','104','New York' , 'White Plains'))
my_game2.insert(parent='',index='end',iid=4,text='',
values=('5','CrissCross','105','California', 'San Diego'))
my_game2.insert(parent='',index='end',iid=5,text='',
values=('6','ZaqueriBlack','106','Wisconsin' , 'TONY'))

my_game2.pack(anchor=tk.CENTER, expand=True)

# for x in my_game.get_children():
#     print(type(x))

while True:
    rank = input("change ZaqueriBlack's rank: ")
    my_game.item("5", values=('6','ZaqueriBlack',str(rank),'Wisconsin' , 'TONY'))
    # my_game.insert(parent='',index='end',iid=5,text='', 
    #                values=('6','ZaqueriBlack',str(rank),'Wisconsin' , 'TONY'))
    ws.update()




# import tkinter as tk

# root=tk.Tk()
# f1 = tk.Frame(width=200, height=200, background="red")
# f2 = tk.Frame(width=100, height=100, background="blue")

# f1.pack(fill="both", expand=True, padx=20, pady=20)
# f2.place(in_=f1, anchor="c", relx=.5, rely=.5)

# root.mainloop()