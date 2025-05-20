import os
import json
import sys
from datetime import datetime
from dateutil.parser import parse, ParserError


class Task:

    def __init__(self, title, due_date, priority=1, complete=False, saved=False):
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
        return(f'{self.title.capitalize()} - Due:  {self.due_date.strftime('%d-%m-%Y')} - Priority: {self.priority}')
    

    @property
    def complete(self):
        return self._complete
    

    @complete.setter
    def complete(self, comp=True):
        self._complete = comp
        self.dict['complete'] = True


    def to_json(self):
        os.chdir('/Users/camer/Documents/Quant/notes/MiniProjects')
        try:
            with open('tasks.json', 'r') as f:
                file_data = json.load(f)
        except FileNotFoundError:
            file_data = []
        file_data.append(self.dict)
        with open('tasks.json', 'w') as f:
            json.dump(file_data, f, indent=2)


class TaskManager:

    def __init__(self):
        self.tasks = []
        self.choices = {'1': self.view_tasks,
                        '2': self.add_task,
                        '3': self.complete_task,
                        '4': self.remove_task,
                        '5': self.save_tasks,
                        '6': self.load_tasks,
                        '7': self.exit}


    def display_menu(self):
        print('')
        print(('Task Manager').center(26, '='))
        print('1. View tasks \n' \
        '2. Add task \n' \
        '3. Mark task as complete \n' \
        '4. Delete task \n' \
        '5. Save tasks \n' \
        '6. Load tasks \n' \
        '7  Quit')


    def view_tasks(self):
        if self.tasks == []:
            print('\nYou currently have no tasks. \n')

        else:
            sort = input('Would you like to sort the tasks? (y/n): ')

            if sort == 'y':
                print('Sorting options:')
                print('1. By Due Date')
                print('2. By Priority')
                choice = input('Enter the desired sorting option: ')

                choices = {'1': lambda x: (x.due_date, x.priority),
                           '2': lambda x: (x.priority, x.due_date)}
                
                action = choices.get(choice)
                try:
                    self.tasks.sort(key=action)
                except:
                    pass

        for index, task in enumerate(self.tasks, start=1):
            complete = 'X' if task._complete == True else ' '
            print(f'[{complete}] {index}. {task}')
        

    def add_task(self):
        title = input('Enter title: ')
        while True:
            try:
                due_date = parse(input('Enter due date: '))
                break
            except ParserError:
                print('Date input was invalid.')

        priority = input('Enter priority (1=high, 2=medium, 3=low): ')
        if priority == None:
            priority = 1
        try:
            task = Task(title, due_date, priority)
            self.tasks.append(task)
            print('Task added.')
        except ValueError:
            print('Date input was invalid.')


    def complete_task(self):
        index = input('Please select which task to complete: ')
        task = self.tasks[int(index) - 1]
        task.complete = True
        print('Task marked as complete.')

    
    def remove_task(self):
        index = input('Please select which task to delete: ')
        self.tasks.pop(int(index) - 1)
        print('Task successfully deleted.')


    def save_tasks(self):
        original = os.getcwd()
        os.chdir('/Users/camer/Documents/Quant/notes/MiniProjects')
        file_data = []
        for task in self.tasks:
            file_data.append(task.dict)
            task.saved = True
        with open('tasks.json', 'w') as f:
            json.dump(file_data, f, indent=2)
        print('Tasks saved to tasks.json')
        os.chdir(original)
            

    def load_tasks(self):
        original = os.getcwd()
        os.chdir('/Users/camer/Documents/Quant/notes/MiniProjects')

        def saved(x):
            return x.saved
        
        unsaved = list(filter(saved, self.tasks))

        choice = None
        if len(unsaved) != 0:
            choice = input('You have unsaved changes. Save before loading new tasks? (y/n): ')

        if choice == 'y':
            self.save_tasks()

        try:
            with open('tasks.json', 'r') as f:
                file_data = json.load(f)
                self.tasks.clear()
                for data in file_data:
                    task = Task(data['title'], parse(data['due_date']), data['priority'], data['complete'], saved=True)
                    self.tasks.append(task)
            print('Tasks loaded from tasks.json')
        except FileNotFoundError:
            print('No tasks saved.')
        os.chdir(original)


    def exit(self):
        sys.exit()


    def run(self):
        while True:
            self.display_menu()
            choice = input('Please select an option: ')
            action = self.choices.get(choice)
            if callable(action):
                action()
            else:
                print('That is not a valid choice.')


def main():
    task_manager = TaskManager()
    task_manager.run()


if __name__ == '__main__':
    main()

