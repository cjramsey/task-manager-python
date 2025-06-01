
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

    def __init__(self, title, due_date: datetime, priority=1, complete=False, saved=False):
        self.title = title
        self.due_date = due_date
        self.priority = priority
        self._complete = complete
        self.saved = saved
        self.dict = {'title': self.title,
                     'due_date': str(self.due_date),
                     'priority': self.priority,
                     'complete': self._complete}


    def __str__(self):
        return(
            f'{self.title.capitalize()} - '
            f'Due:  {self.due_date.strftime('%d-%m-%Y')} - '
            f'Priority: {self.priority}'
        )


    @property
    def complete(self):
        return self._complete
    

    @complete.setter
    def complete(self, comp=True):
        self._complete = comp
        self.dict['complete'] = True


    def to_json(self):
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
        cls.console.print(cls.table)


    def __init__(self):
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
        

    def print_tasks(self, tasks_):
        table = Table(title='Tasks', title_justify='center')
        table.add_column('No.')
        table.add_column('Completed', justify='center')
        table.add_column('Due Date')
        table.add_column('Title')
        table.add_column('Priority', justify='center')

        for i, task in enumerate(tasks_, start=1):
            complete = u'\u2713' if task.complete else ''
            if task.complete:
                style = '#00d700 bold' 
            elif task.due_date < datetime.today():
                style = '#d70000 bold'
            else:
                style = 'bold'
            table.add_row(f'{i}', complete, f'{task.due_date.strftime('%d-%m-%Y')}', f'{task.title}', f'{task.priority}', style=style)

        self.console.print(table)


    def view_tasks(self):
        tasks_ = copy.copy(self.tasks)
        if not self.tasks:
            self.console.print('You currently have no tasks.')
        else:
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
                except:
                    pass
            
            self.console.print('\n')
            self.print_tasks(tasks_)
        

    def add_task(self):
        title = self.console.input('Enter title: ')
        while True:
            try:
                due_date = parse(self.console.input('Enter due date: '))
                break
            except ParserError:
                self.console.print('Date input was invalid.')

        priority = self.console.input('Enter priority (1=high, 2=medium, 3=low): ')
        if priority == None:
            priority = 1

        try:
            task = Task(title, due_date, priority)
            self.tasks.append(task)
            self.console.print('Task added.')
        except ValueError:
            self.console.print('Date input was invalid.')


    def complete_task(self):
        self.print_tasks(self.tasks)
        index = self.console.input('Please select which task to complete: ')
        task = self.tasks[int(index) - 1]
        task.complete = True
        self.console.print('Task marked as complete.')

    
    def remove_task(self):
        self.print_tasks(self.tasks)
        index = self.console.input('Please select which task to delete: ')
        self.tasks.pop(int(index) - 1)
        self.console.print('Task successfully deleted.')


    def save_tasks(self):
        file_path = os.path.join(base_dir, 'tasks.json')
        file_data = []
        for task in self.tasks:
            file_data.append(task.dict)
            task.saved = True
        with open(file_path, 'w') as f:
            json.dump(file_data, f, indent=2)
        self.console.print('Tasks saved to tasks.json')
            

    def load_tasks(self):
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
            self.tasks.clear()
            for data in file_data:
                task = Task(data['title'], parse(data['due_date']), 
                            data['priority'], data['complete'], saved=True)
                self.tasks.append(task)
            self.console.print('Tasks loaded from tasks.json')
        except FileNotFoundError:
            self.console.print('No tasks saved.')

    
    def undo(self):
        self.tasks = self.previous_state.tasks
        self.previous_state = self.previous_state.previous_state
        self.console.print('Undo complete.')


    def exit(self):
        sys.exit()


    def run(self):
        os.system('cls')
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
    task_manager = TaskManager()
    task_manager.run()


if __name__ == '__main__':
    main()

