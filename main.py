import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import tkcalendar as tkc
import mysql.connector

cnx = mysql.connector.connect(user="root", password="password", host="localhost", database="todo")
cursor = cnx.cursor()



class TodoList:
    def __init__(self, master):
        self.master = master
        master.title("To-Do List")
        self.calendar_window = None
        self.curr_date = datetime.now().date()
        self.selected_date = self.curr_date

        # Creating a label to display date
        self.date_label = tk.Label(master)
        self.date_label.pack()
        self.date_label.config(text=str(self.curr_date))
        # Creating a label to display time
        self.time_label = tk.Label(master)
        self.time_label.pack()
        self.clock()

        # Create the listbox to display tasks
        self.listbox = tk.Listbox(master, height=10, width=50)
        self.listbox.pack(pady=10)

        self.tasks = []
        query = f"CALL sys.table_exists('todo', '{self.curr_date}', @exists);"
        cursor.execute(query)
        cursor.execute("SELECT @exists;")
        result = cursor.fetchone()
        if result[0] == '':
            query = f"""
                            CREATE TABLE `{self.curr_date}`(
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            task VARCHAR(200),
                            completed BOOLEAN
                            );
                            """
            cursor.execute(query)
        else:
            query = f"SELECT * FROM `{self.curr_date}`;"
            cursor.execute(query)
            tasks = cursor.fetchall()
            self.listbox.delete(0, tk.END)
            self.tasks = []
            for task in tasks:
                self.tasks.append(task)

        self.task_displayer()
        # Create the entry box to add new tasks
        self.new_task_entry = tk.Entry(master, width=40)
        self.new_task_entry.pack(side=tk.LEFT, padx=10)

        # Create the add button to add new tasks to the list
        self.add_button = tk.Button(master, text="Add", command=self.add_task)
        self.add_button.pack(side=tk.LEFT)

        # Create the complete button to mark tasks as completed
        self.complete_button = tk.Button(master, text="Complete", command=self.complete_task)
        self.complete_button.pack(side=tk.LEFT)

        # Create the delete button to delete tasks from the list
        self.delete_button = tk.Button(master, text="Delete", command=self.delete_task)
        self.delete_button.pack(side=tk.LEFT)

        self.calender_selector_button = tk.Button(master, text="Select Date", command=self.select_date)
        self.calender_selector_button.pack(side=tk.TOP, pady=10)

    # Initialize the task list

    def add_task(self, event=None):
        if self.curr_date == self.selected_date:
            index = len(self.tasks) + 1
            task = (index, self.new_task_entry.get().title(), 0)
            flag = False
            for i in self.tasks:
                if i[1] == task[1]:
                    flag = True
            if flag:
                messagebox.showerror(title="Already Exists", message="Task already in list")
            else:
                if task:
                    self.tasks.append(task)
                    query = f"""
                                INSERT INTO `{self.selected_date}` VALUES({index}, '{task[1]}', {task[2]});
                            """
                    cursor.execute(query)
                    cnx.commit()
                    self.listbox.insert(tk.END, self.tasks[-1][1])
                    self.new_task_entry.delete(0, tk.END)
                else:
                    messagebox.showerror(title="No task", message="Please enter the task you would like to add.")
        else:
            messagebox.showerror(title="Date Error", message="You can only add task to today's list")

    def complete_task(self):
        if self.curr_date == self.selected_date:
            task_index = self.listbox.curselection()
            if task_index:
                task_index = task_index[0]
                self.listbox.itemconfig(task_index, fg="gray")
                query = f"""
                            UPDATE `{self.curr_date}` SET completed = 1 WHERE id = {task_index+1}
                        """
                cursor.execute(query)
                cnx.commit()
            else:
                messagebox.showerror(title="No task selected", message="Please select a task to mark complete.")
        else:
            messagebox.showerror(title="Date Error", message="You can only add task to today's list")

    def delete_task(self):
        if self.curr_date == self.selected_date:
            task_index = self.listbox.curselection()
            if task_index:
                task_index = task_index[0]
                self.listbox.delete(task_index)
                print(task_index)
                query = f"""
                            DELETE FROM `{self.curr_date}` WHERE id = {task_index+1};
                        """
                cursor.execute(query)
                cnx.commit()
                del self.tasks[task_index]
                query = f"""
                            UPDATE `{self.curr_date}` SET id = (id - 1) WHERE id > {task_index+1};
                        """
                cursor.execute(query)
                cnx.commit()

            else:
                messagebox.showerror(title="No task selected", message="Please select a task to mark complete.")
        else:
            messagebox.showerror(title="Date Error", message="You can only add task to today's list")

    def get_time(self):
        time = datetime.now().strftime("%H:%M")
        hour = int(time[:2])
        meridian = ''
        if hour >= 12:
            meridian = 'PM'
        else:
            meridian = 'AM'
        display_time = f"{time[:2]}:{time[3:5]} {meridian}"
        return display_time

    def clock(self):
        time = self.get_time()
        self.time_label.config(text=time)
        self.time_label.after(1000, self.clock)

    def select_date(self):
        if self.calendar_window is not None:
            return
        self.calendar_window = tk.Toplevel(self.master)
        calendar = tkc.Calendar(self.calendar_window, selectmode='day')
        calendar.pack()

        def save_date():
            self.selected_date = (calendar.selection_get())
            query = f"CALL sys.table_exists('todo', '{self.selected_date}', @exists);"
            cursor.execute(query)
            cursor.execute("SELECT @exists;")
            result = cursor.fetchone()
            if result[0] == '':
                messagebox.showerror(title="ToDo List not found", message="There is no to do list on the selected date")
            else:
                query = f"SELECT * FROM `{self.selected_date}`;"
                cursor.execute(query)
                tasks = cursor.fetchall()
                self.tasks = []
                for task in tasks:
                    self.tasks.append(task)
                self.task_displayer()
            self.date_label.config(text=str(self.selected_date))
            self.set_none()

        save_button = tk.Button(self.calendar_window, text="Select Date", command=save_date)
        save_button.pack()

        self.calendar_window.protocol("WM_DELETE_WINDOW", self.set_none)

    def set_none(self):
        self.calendar_window.destroy()
        self.calendar_window = None

    def task_displayer(self):
        print(self.tasks)
        self.listbox.delete(0, tk.END)
        for task in self.tasks:
            if task[2] == 0:
                self.listbox.insert(tk.END, task[1])
            else:
                self.listbox.insert(tk.END, task[1])
                self.listbox.itemconfig(tk.END, fg="gray")


root = tk.Tk()
todo_list = TodoList(root)
root.mainloop()


