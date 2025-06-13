"""
task_manager.py

A command-line task manager that allows users to add, view, sort, 
complete, delete, save, and load tasks.
Uses the rich library for formatted terminal output and dateutil 
for parsing dates.

Tasks are stored in a JSON file named 'tasks.json' in the script directory.

Author: Cameron Ramsey
Year: 2025
"""

import copy
import json
import os
import sys
from datetime import datetime
from dateutil.parser import parse, ParserError
from itertools import filterfalse

from rich.console import Console
from rich.table import Table


base_dir = os.path.dirname(__file__)


class Task:
    """
    Represents an individual task.

    Attributes:
        id (int): Unique identifier for the task.
        title (str): Description or title of the task.
        due_date (datetime): Due date and time for the task.
        priority (int): Priority level (1 = high, 2 = medium, 3 = low).
        _complete (bool): Completion status.
        saved (bool): Whether the task has been saved to file.
        dict (dict): Dictionary representation used for JSON serialization.
    """

    def __init__(self, id, title, due_date: datetime, priority=1, 
                 complete=False, saved=False):
        self.id = id
        self.title = title
        self.due_date = due_date
        self.priority = priority
        self._complete = complete
        self.saved = saved
        self.dict = {'id': self.id,
                     'title': self.title,
                     'due_date': str(self.due_date),
                     'priority': self.priority,
                     'complete': self._complete}

    def __repr__(self):
        """Returns a string representation used to recreate the Task object."""

        return(f'Task({self.id}, {self.title}, {self.due_date},' + 
               f'{self.priority}, {self._complete})')

    @property
    def complete(self):
        """Gets or sets the task's completion status."""

        return self._complete

    @complete.setter
    def complete(self, completed=True):
        self._complete = completed
        self.dict['complete'] = True

    def to_json(self):
        """
        Appends the task to the tasks.json file.
        Creates the file if it does not exist.
        """

        file_path = os.path.join(base_dir, 'tasks.json')
        try:
            with open(file_path, 'r') as f:
                file_data = json.load(f)
        except FileNotFoundError:
            file_data = []
        file_data.append(self.dict)
        with open(file_path, 'w') as f:
            json.dump(file_data, f, indent=2)


class TaskManager:
    """
    Main interface for interacting with the task system via command-line.
    Handles task creation, display, persistence, and user interaction.

    Attributes:
        tasks (list[Task]): List of current tasks in memory.
        previous_state (TaskManager): Deep copy of the previous state (for undo).
        choices (dict): Maps menu options to corresponding method handlers.
        next_id (int): Next available task ID.

    Class Attributes:
        console (rich.Console): Rich console for styled output.
        table (rich.Table): Static menu table displayed at startup.
    """

    console = Console(style='bold')
    table = Table(title='Task Manager', title_justify='center')

    table.add_column('Option', justify='center')
    table.add_column('Action')

    table.add_row('1', 'View tasks' )
    table.add_row('2', 'Add task')
    table.add_row('3', 'Mark task as complete')
    table.add_row('4', 'Delete tasks')
    table.add_row('5', 'Save tasks')
    table.add_row('6', 'Load tasks')
    table.add_row('7', 'Undo')
    table.add_row('8', 'Quit')


    @classmethod
    def display_menu(cls):
        """Displays the interactive menu using rich's Table."""

        cls.console.print(cls.table)

    def __init__(self):
        self.next_id = 0
        self.tasks = []
        self.previous_state = []
        self.choices = {'1': self.view_tasks,
                        '2': self.add_task,
                        '3': self.complete_task,
                        '4': self.remove_task,
                        '5': self.save_tasks,
                        '6': self.load_tasks,
                        '7': self.undo,
                        '8': self.exit}

    def get_next_id(self):
        """
        Calculates the next available task ID.
        Checks the existing IDs in the tasks.json file, if it exists.

        Returns:
            Maximum ID found in tasks.json + 1.
            0 if tasks.json does not exist.
        """

        file_path = os.path.join(base_dir, 'tasks.json')
        try:
            with open(file_path, 'r') as f:
                file_data = json.load(f)
        except FileNotFoundError:
            return 0
        finally:
            ids = []
            for task in file_data:
                ids.append(task['id'])
                max_id = max(ids)
            return max_id + 1   


    def print_tasks(self, tasks_):
        """
        Prints a styled table of tasks to the console.
        Highlights overdue tasks and completed tasks with color formatting.
        """

        table = Table(title='Tasks', title_justify='center')
        table.add_column('ID')
        table.add_column('Completed', justify='center')
        table.add_column('Due Date')
        table.add_column('Title')
        table.add_column('Priority', justify='center')

        for task in tasks_:
            complete = u'\u2713' if task.complete else ''
            if task.complete:
                style = '#00d700 bold' 
            elif task.due_date < datetime.today():
                style = '#d70000 bold'
            else:
                style = 'bold'
            table.add_row(str(task.id), complete, 
                          task.due_date.strftime('%d-%m-%Y'), task.title, 
                          f'{task.priority}', style=style)

        self.console.print(table)


    def view_tasks(self):
        """
        Displays all current tasks with optional sorting by due date or priority.
        Informs the user if there are no tasks.
        """

        if not self.tasks:
            self.console.print('You currently have no tasks.')
            return
        
        tasks_ = copy.copy(self.tasks)
        sort = self.console.input('Would you like to sort the tasks? (y/n): ')

        if sort == 'y':
            self.console.print('Sorting options:')
            self.console.print('1. By Due Date')
            self.console.print('2. By Priority')
            choice = self.console.input('Enter the desired sorting option: ')
            choices = {'1': lambda x: (x.due_date, x.priority),
                        '2': lambda x: (x.priority, x.due_date)}
            action = choices.get(choice)
            try:
                tasks_ = sorted(self.tasks, key=action)
            except TypeError:
                self.console.print(f'{choice} is not a valid sorting option.')

        self.console.print('\n')
        self.print_tasks(tasks_)
        

    def add_task(self):
        """
        Prompts the user to enter task details and adds a new Task to the list.
        Increments the ID counter.
        """

        title = self.console.input('Enter title: ')
        while True:
            try:
                due_date = parse(self.console.input('Enter due date: '))
            except ParserError:
                self.console.print('Date input was invalid.')
            finally:
                break

        priority = self.console.input('Enter priority (1=high, 2=medium, 3=low): ')
        if priority == None:
            priority = 1

        try:
            task = Task(self.next_id, title, due_date, priority)
            self.tasks.append(task)
            self.console.print('Task added.')
        except ValueError:
            self.console.print('Date input was invalid.')
        else:
            self.next_id += 1
        

    def complete_task(self):
        """Marks a selected task as complete, based on user input. """

        self.print_tasks(self.tasks)
        id = self.console.input('Please select which task to complete: ')
        task_ = None
        for task in filter(lambda x: x.id == int(id), self.tasks):
            task_ = task
        task_.complete = True
        self.console.print('Task marked as complete.')

    
    def remove_task(self):
        """Removes a selected task from the list, based on user input. """

        self.print_tasks(self.tasks)
        id = self.console.input('Please select which task to delete: ')
        for task in filter(lambda x: x.id == int(id), self.tasks):
            task_ = task
        self.tasks.remove(task_)
        self.console.print('Task successfully deleted.')


    def save_tasks(self):
        """
        Writes all current tasks to the tasks.json file, overwriting any 
        previous content.
        Flags each task as saved.
        """

        file_path = os.path.join(base_dir, 'tasks.json')
        file_data = []
        for task in self.tasks:
            file_data.append(task.dict)
            task.saved = True
        with open(file_path, 'w') as f:
            json.dump(file_data, f, indent=2)
        self.console.print('Tasks saved to tasks.json')
            

    def load_tasks(self):
        """
        Loads tasks from the tasks.json file and replaces current task list.
        Prompts to save unsaved tasks first if necessary.
        """

        file_path = os.path.join(base_dir, 'tasks.json')
        unsaved = list(filterfalse(lambda x: x.saved, self.tasks))
        choice = None
        if unsaved:
            choice = self.console.input(
                                'You have unsaved changes.' 
                                'Save before loading new tasks? (y/n): '
                                )

        if choice == 'y':
            for task in unsaved:
                task.to_json()

        try:
            with open(file_path, 'r') as f:
                file_data = json.load(f)
        except FileNotFoundError:
            self.console.print('No tasks saved.')
        else:
            self.tasks.clear()
            for data in file_data:
                task = Task(data['id'], data['title'], parse(data['due_date']), 
                            data['priority'], data['complete'], saved=True)
                self.tasks.append(task)
            self.console.print('Tasks loaded from tasks.json')

    
    def undo(self):
        """
        Restores the previous state of the TaskManager (used before most 
        user actions).
        """

        self.tasks = self.previous_state.tasks
        self.previous_state = self.previous_state.previous_state
        self.console.print('Undo complete.')


    def exit(self):
        """Exits the application."""

        sys.exit()


    def run(self):
        """
        Main application loop. Displays the menu and handles user interaction.
        Refreshes the console screen after each action.
        """

        os.system('cls')
        self.next_id = self.get_next_id()
        while True:
            self.display_menu()

            choice = self.console.input('Please select an option: ')
            if choice not in ['1','5', '6', '7', '8']:
                self.previous_state = copy.deepcopy(self)
            action = self.choices.get(choice)

            if callable(action):
                action()
            else:
                self.console.print('That is not a valid choice.')
            self.console.input('Press enter to return to the menu. \n')
            os.system('cls')


def main():
    """
    Entry point for the application. 
    Creates a TaskManager instance and runs it.
    """

    task_manager = TaskManager()
    task_manager.run()


if __name__ == '__main__':
    main()

