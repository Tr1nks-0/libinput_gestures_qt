'''libinput-gestures-qt. User interface for the libinput-gestures utility. 
    Copyright (C) 2019  Michael Voronov

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
"""
This is a GUI for libinout-gestures-utility. Allows to set up touchpad gestures:
allows to edit the configuration file and control utility status.

Variables:
--------------
Paths:
-----
HOME: str
    path to user's home directory
CONFIG_LOCATION: str
    path to the location of the configuration file
Mappings:
--------
actions_mapping: dict
    finger actions in human-readable form >> finger actions in config-readable form
reversed_mapping: dict
    finger actions in config-readable form >> finger actions in human-readable form
keys_mapping: dict
    qt keys (lowered) >> xdotool keys
    
--------------
Classes:
GesturesApp(QtWidgets.QMainWindow, main_window.Ui_MainWindow)
    Main window.
EditGestures(QtWidgets.QWidget, edit_window.Ui_Form)
    Secondary window for adding/editing gestures.
--------------
Functions: read_config, write_config, find_key_combo, main
--------------
"""

import sys
from PyQt5 import QtWidgets, QtCore
import main_window
import edit_window

import subprocess
from pathlib import Path

import collections

HOME = str(Path.home())
CONFIG_LOCATION = HOME + '/.config/libinput-gestures.conf'

actions_mapping = {
    'Swipe Up': 'gesture swipe up',
    'Swipe Down': 'gesture swipe down',
    'Swipe Left': 'gesture swipe left',
    'Swipe LeftUp': 'gesture swipe left_up',
    'Swipe LeftDown': 'gesture swipe  left_down',
    'Swipe Right': 'gesture swipe right',
    'Swipe RightUp': 'gesture swipe right_up',
    'Swipe RightDown': 'gesture swipe right_down',
    'Pinch In': 'gesture pinch in',
    'Pinch Out': 'gesture pinch out',
    'Pinch Clockwise': 'gesture pinch clockwise',
    'Pinch Anticlockwise': 'gesture pinch anticlockwise',
}

reversed_mapping = {
    'gesture swipe up': 'Swipe Up',
    'gesture swipe down': 'Swipe Down',
    'gesture swipe left': 'Swipe Left',
    'gesture swipe left_up': 'Swipe LeftUp',
    'gesture swipe left_down': 'Swipe LeftDown',
    'gesture swipe right': 'Swipe Right',
    'gesture swipe right_up': 'Swipe RightUp',
    'gesture swipe right_down': 'Swipe RightDown',
    'gesture pinch in': 'Pinch In',
    'gesture pinch out': 'Pinch Out',
    'gesture pinch clockwise': 'Pinch Clockwise',
    'gesture pinch anticlockwise': 'Pinch Anticlockwise'
}

keys_mapping = {
    'meta': 'super',
    'pgdown': 'Page_Down',
    'pgup': 'Page_Up',
    'right': 'Right',
    'left': 'Left',
    'up': 'Up',
    'down': 'Down',
    'f1': 'F1',
    'f2': 'F2',
    'f3': 'F3',
    'f4': 'F4',
    'f5': 'F5',
    'f6': 'F6',
    'f7': 'F7',
    'f8': 'F8',
    'f9': 'F9',
    'f10': 'F10',
    'f11': 'F11',
    'f12': 'F12',
}

def read_config():
    """Reads config file by lines
    
    Config under CONFIG_LOCATION = ~/.config/libinput-gestures.conf
    Returns '' if there is no config file.
    """
    try:
        with open(CONFIG_LOCATION, 'r') as config:
            conf = config.readlines()
        return conf
    except FileNotFoundError:
        return ''


def write_config(new_conf):
    """Writes config under CONFIG_LOCATION
    
    Parameter: new_conf, list of strings
    """
    with open(CONFIG_LOCATION, 'w') as config:
        config.write(''.join(new_conf))


def fix_config():
    """Fixes config
    
    Reads config, goes by lines.
    If lise starts with '#', it is preserved.
    If line starts with 'gesture', 'device' or 'swipe_threshold'
        and this line is ok, it is preserved.
    Other lines are deleted.
    """
    conf = read_config()
    fixed_conf = []
    for line in conf:
        if line.startswith('#'):
            fixed_conf.append(line)
        else:
            splitted = line.replace('\t', ' ').split()
            if splitted[0] in ['gesture', 'device', 'swipe_threshold']:
                if splitted[0] == 'gesture':
                    if splitted[4] == 'xdotool':
                        if splitted[5] == 'key' and len(splitted) == 7:
                            fixed_conf.append(line)
                    else:
                        fixed_conf.append(line)
                else:
                    if len(splitted) == 2:
                        fixed_conf.append(line)
    write_config(''.join(fixed_conf))
                


def find_key_combo(qt_key_combo):
    """Key combo translator
    
    Takes string with QT-like key combo (generated by PyQt5.QtWidgets.QKeySequenceEdit)
    mapes into a string consumable by xdotool
    """
    xdotool_key_combo = []
    for qt_key in qt_key_combo.split('+'):
        lowered_key = qt_key.lower()
        if lowered_key in keys_mapping:
            xdotool_key_combo.append(keys_mapping[lowered_key])
        else:
            xdotool_key_combo.append(lowered_key)
    return '+'.join(xdotool_key_combo)


class GesturesApp(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    """Main window.
    
    Display current configuration, menubar and the 'Add' button.
    """
    def __init__(self, parent=None):
        """init
        
        Calls for self.display_config() and adds triggers to all the events.
        Tries to launch libinput-gestures-setup:
            if it works, sets self.installed to True
            if not sets self.installed to False
        """
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('Libinput Gestures Qt')

        self.display_config()

        self.actionAdd.triggered.connect(self.start_adding)
        self.actionRefresh.triggered.connect(self.refresh)
        
        self.actionStatus.triggered.connect(self.display_status)
        self.actionRestart.triggered.connect(self.restart_utility)
        self.actionStop.triggered.connect(self.stop_utility)
        self.actionStart.triggered.connect(self.start_utility)

        self.pushButton.clicked.connect(self.start_adding)

        try:
            subprocess.run(['libinput-gestures-setup', 'status'])
            self.installed = True
        except FileNotFoundError:
            QtWidgets.QMessageBox.about(self, "Problem", "Cannot find libinput-gestures. Are you sure it is installed correctly?")
            self.installed = False

    def start_adding(self):
        """Shows EditGestures window"""
        self.adding = EditGestures(self)
        self.adding.setWindowModality(QtCore.Qt.WindowModal)
        self.adding.show()

    def refresh(self):
        """Refresh content of the main window"""
        self.display_config(refresh=True)
    
    def display_status(self):
        """Check status of libinput-gestures and shows it in message box"""
        if self.installed:
            status = subprocess.run(['libinput-gestures-setup', 'status'], capture_output=True)
            status = status.stdout.decode('utf-8')
            installed = 'no'
            if 'is installed' in status:
                installed = 'yes'
            running = 'no'
            if 'is running' in status:
                running = 'yes'
            set_to_autostart = 'no'
            if 'is set to autostart' in status:
                set_to_autostart = 'yes'
            status = 'Installed: {}\nRunning: {}\nAutostart: {}\n'.format(installed, running, set_to_autostart)
            QtWidgets.QMessageBox.about(self, "Status", status)
    
    def restart_utility(self):
        """Runs 'libinput-gestures-setup restart', displays output in message box"""
        if self.installed:
            status = subprocess.run(['libinput-gestures-setup', 'restart'], capture_output=True)
            status = status.stdout.decode('utf-8')
            QtWidgets.QMessageBox.about(self, "Status", status)
    
    def stop_utility(self):
        """Runs 'libinput-gestures-setup stop', displays output in message box"""
        if self.installed:
            status = subprocess.run(['libinput-gestures-setup', 'stop'], capture_output=True)
            status = status.stdout.decode('utf-8')
            QtWidgets.QMessageBox.about(self, "Status", status)
    
    def start_utility(self):
        """Runs 'libinput-gestures-setup start', displays output in message box"""
        if self.installed:
            status = subprocess.run(['libinput-gestures-setup', 'start'], capture_output=True)
            status = status.stdout.decode('utf-8')
            QtWidgets.QMessageBox.about(self, "Status", status)

    def sort_config(self):
        """Sorts config contents alphabetically.
        
        Assigns new values for:
            self.gestures: list of str
                finger actions in human-readable form
                e.g. ['Swipe Up']
            self.fingers: list of int
                amount of fingers
                e.g. [3]
            self.shortcuts: list of str
                keyboard shortcuts (in the xdotool form)
                OR commands
                e.g. ['ctrl+super+Page_Down']
                e.g. ['echo "Hello"']
            self.buttons: list of str
                finger action in config-readable form
                e.g. ['gesture swipe up']
            self.actions: list of str
                either 'shortcut' (stands for a keyboard shortcut)
                or 'command'
        """
        for_sorting = []
        for i, el in enumerate(self.gestures):
            for_sorting.append([el, (self.fingers[i], self.shortcuts[i], self.buttons[i], self.actions[i])])
        sorted_conf = sorted(for_sorting)
        
        self.gestures = []
        self.fingers = []
        self.shortcuts = []
        self.buttons = []
        self.actions = []
        for line in sorted_conf:
            self.gestures.append(line[0])
            self.fingers.append(line[1][0])
            self.shortcuts.append(line[1][1])
            self.buttons.append(line[1][2])
            self.actions.append(line[1][3])
    
    def prepare_config_for_displaying(self):
        """Creates widgets for all stuff read from config
        
        Assigns new values for:                                                         V-----------------------------------V
            self.gestures: list of str                   <============ Translates from 'gesture <type:swipe|pinch> <direction> ...'
                finger actions in human-readable form
                e.g. ['Swipe Up']                                                                       V-------V
            self.fingers: list of int                    <============ Exact values of  '... <direction> <fingers> <command>...'
                amount of fingers
                e.g. [3]                                                                               V-------V
            self.shortcuts: list of str                  <======------ Exact values of  '... <fingers> <command>'
                keyboard shortcuts (in the xdotool form)        \ <<or>>                                         V-----------------V
                OR commands                                      ----- Exact values of '... <fingers> xdotool key <keyboard_shortcut>
                e.g. ['ctrl+super+Page_Down']                     
                e.g. ['echo "Hello"']                                                    V------------------------------------V
            self.buttons: list of str                    <============ Exact values of  'gesture <type:swipe|pinch> <direction> ...'
                finger action in config-readable form
                e.g. ['gesture swipe up']
            self.actions: list of str                    <============ Depend on whether xdotool is used in config line
                either 'shortcut' (stands for a keyboard shortcut)
                or 'command'
        """
        conf = read_config()
        self.gestures = []
        self.fingers = []
        self.shortcuts = []
        self.buttons = []
        self.actions = []
        for line in conf:
            if line.startswith('gesture'):
                splitted = line.replace('\t', ' ').split()
                action = '{} {} {}'.format(splitted[0], splitted[1], splitted[2])
                self.gestures.append(reversed_mapping['{} {} {}'.format(splitted[0], splitted[1], splitted[2])])
                self.fingers.append(splitted[3])
                if splitted[4] == 'xdotool' and splitted[5] == 'key':
                    self.actions.append('shortcut')
                    self.shortcuts.append(splitted[6])
                else:
                    self.actions.append('command')
                    self.shortcuts.append(' '.join(splitted[4:]))
                self.buttons.append(action)

    def display_config(self, refresh=False):
        """Displays current configuration in main window
        
        Finally gathers all widgets (creates a couple new) and puts them into nice layouts.
        """
        if refresh:
            self.area.deleteLater()
        
        try:
            self.prepare_config_for_displaying()
        except Exception:
            reply = QtWidgets.QMessageBox.question(
                self, 'Problem',
                "Something is wrong with the configuration file...\nFix it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                fix_config()
                self.prepare_config_for_displaying()
            else:
                sys.exit()

        self.sort_config()
        
        self.layout = self.verticalLayout
        self.area = QtWidgets.QScrollArea()
        content_widget = QtWidgets.QWidget()
        self.area.setWidget(content_widget)
        flay = QtWidgets.QGridLayout(content_widget)
        self.area.setWidgetResizable(True)

        for i, label in enumerate(self.gestures):
            flay.addWidget(QtWidgets.QLabel(label), i, 0)

        for i, label in enumerate(self.fingers):
            flay.addWidget(QtWidgets.QLabel(label), i, 1)

        for i, label in enumerate(self.actions):
            flay.addWidget(QtWidgets.QLabel(label), i, 2)

        for i, label in enumerate(self.shortcuts):
            flay.addWidget(QtWidgets.QLabel(label), i, 3)

        for i, button in enumerate(self.buttons):
            deleteButton = QtWidgets.QPushButton("Delete")
            deleteButton.setAccessibleName(button)
            deleteButton.clicked.connect(self.delete_entry)
            flay.addWidget(deleteButton, i, 4)

        self.layout.addWidget(self.area)

    def delete_entry(self):
        """Delete line from config
        
        Triggered by 'Delete' buttons.
        """
        button = self.sender()
        if isinstance(button, QtWidgets.QPushButton):
            reply = QtWidgets.QMessageBox.question(
                self, 'Message',
                "Are you sure to delete?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                conf = read_config()
                new_conf = [line for line in conf if not line.startswith(button.accessibleName())]
                write_config(new_conf)
                self.display_config(refresh=True)
        
        
class EditGestures(QtWidgets.QWidget, edit_window.Ui_Form):
    """Secondary window for adding/editing gestures
    
    Child to main window (GesturesApp).
    """
    def __init__(self, parent):
        """init
        
        Sets widgets and their attributes that I could not set in QT Designer.
        Adds events to buttons.
        """
        super().__init__()
        self.setupUi(self)
        self.parent = parent
        self.setWindowTitle('Add Gestures')

        self.action = 'gesture swipe up'
        self.fingers = 3
        self.shortcut = ''
        
        self.fingersLine.setMinimum(3)

        self.draw_shortcut()
        self.shortcut_command.activated[str].connect(self.shortcut_or_command)
        
        self.actionMenu.activated[str].connect(self.action_chosen)
        self.fingersLine.valueChanged[int].connect(self.fingers_chosen)
        self.saveButton.clicked.connect(self.save_changes)

    def shortcut_or_command(self, text):
        """Chose whether you want to add plain command or xdotool command using QKeySequenceEdit
        
        Does not delete previous widgets: they are stored one upon another.
        HELP NEEDED -- it works but it's stupid :(
        """
        if text == 'Keyboard Shortcut':
            self.draw_shortcut()
        else:
            self.draw_command()

    def draw_shortcut(self):
        """Draws keyboard shortcut input
        
        ... so that user could just press buttons (sh|h)e wants
        istead of manually typing 'xdotool key <key combo>' and remember differences between xdotool/Gnome/KDE/etc.
        """
        self.actionType.setText('Keyboard Shortcut')
        self.keyboardLine = QtWidgets.QKeySequenceEdit()
        self.gridLayout.addWidget(self.keyboardLine, 4, 2)
        self.keyboardLine.keySequenceChanged.connect(self.shortcut_chosen)
        
    def draw_command(self):
        """Draws command input
        
        ... because I don't want users to be stuck with xdotool
        """
        self.actionType.setText('Command')
        self.commandLine = QtWidgets.QLineEdit()
        self.gridLayout.addWidget(self.commandLine, 4, 2)
        self.commandLine.textChanged[str].connect(self.command_chosen)

    def action_chosen(self, text):
        """Event when fingers action is chosen"""
        if 'Pinch' in text:
            self.fingersLine.setMinimum(2)
            self.fingersLine.setValue(2)
        else:
            self.fingersLine.setMinimum(3)
            self.fingersLine.setValue(3)
        self.action = actions_mapping[text]

    def fingers_chosen(self, value):
        """Event when amount of fingers is chosen"""
        self.fingers = value

    def shortcut_chosen(self, text):
        """Event when keyboard shortcut is chosen"""
        shortcut = text.toString().split(',')[0]
        self.shortcut = 'xdotool key ' + find_key_combo(shortcut)

    def command_chosen(self, text):
        """Event when command is typed in"""
        self.shortcut = text

    def save_changes(self):
        """Writes input data into config file"""
        if self.action and self.fingers and self.shortcut:
            conf = read_config()
            new_conf = []
            for line in conf:
                if not line.replace('\t', ' ').startswith('{} {}'.format(self.action, str(self.fingers))):
                    new_conf.append(line)
            new_conf.append('{}\t{} {}\n'.format(self.action, str(self.fingers), self.shortcut))
            write_config(new_conf)
            self.actionMenu.setCurrentIndex(0)
            self.fingersLine.setValue(0)
            #self.keyboardLine.setText('')
            QtWidgets.QMessageBox.about(self, "Success", "Cofiguration successfully edited.")
            self.parent.display_config(refresh=True)
            self.close()
        else:
            QtWidgets.QMessageBox.about(self, "Fail", "Please, fill all the forms.")


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = GesturesApp()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
