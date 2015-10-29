#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys
import signal
import time

from PyQt4 import QtGui, QtCore

# Local imports
from config import setup
from main import main as maybe_slouching
from main import config

# Qt4 threading advice from here: https://joplaete.wordpress.com/2010/07/21/threading-with-pyqt4/

check_frequency = int(config['MAIN']['poll_rate'])
# alert_duration  = int(config['MAIN']['alert_duration'])

class TrayIcon(QtGui.QSystemTrayIcon):
  def __init__(self, icon, parent=None):
    QtGui.QSystemTrayIcon.__init__(self, icon, parent)
    self.workThread = SlouchingThread()

    menu        = QtGui.QMenu(parent)
    setupAction = menu.addAction("Setup")
    exitAction  = menu.addAction("Quit")
    self.setContextMenu(menu)

    self.connect(exitAction, QtCore.SIGNAL('triggered()'), sys.exit)
    self.connect(setupAction, QtCore.SIGNAL('triggered()'), setup)

  def __del__(self):
    QtGui.QSystemTrayIcon.__del__(self)
    self.workThread.terminate()

  def alert(self):
    # Alerting by receiving a signal
    self.connect(self.workThread, QtCore.SIGNAL("slouching_alert(QString, QString)"),
                 self.showMessage)
    self.workThread.start()

  # def showMessage(*args, **kwargs):
  #   if 'msecs' not in kwargs:
  #     kwargs['msecs'] = alert_duration

  #   QtGui.QSystemTrayIcon.showMessage(*args, **kwargs)

class WrapperWidget(QtGui.QWidget):
  def __init__(self, parent=None):
    QtGui.QWidget.__init__(self, parent)

    self.setGeometry(100, 100, 100, 100)
    self.setWindowTitle('threads')
    # self.show()

class SlouchingThread(QtCore.QThread):
  def __init__(self):
    QtCore.QThread.__init__(self)
    self.run_loop = True

  # Helps ensure that the thread quits before it's destroyed.
  def __del__(self):
    self.wait()

  # I can't get the timing right but I think having this
  # will help kill our while loop in run()
  # This hopefully avoids a race condition where the camera is stuck active
  # if we quit while it's taking a picture.
  # I could be entirely wrong though...
  def terminate(self):
    self.run_loop = False

  # Called run but start() actually runs this
  def run(self):
    while self.run_loop:

      # TODO: Possibly collect a certain number of readings and then only bother people if all or most of the readings indicate slouching. Best 2 out of 3?
      slouching = maybe_slouching()

      if slouching.success:
        if slouching.result == True:
          self.emit(QtCore.SIGNAL('slouching_alert(QString, QString)'),
                    "You're slouching", "Stop slouching!")
      else:
        self.emit(QtCore.SIGNAL('slouching_alert(QString, QString)'),
                  "Error encountered", str(slouching.result))

      time.sleep(check_frequency)

app = QtGui.QApplication(sys.argv)
signal.signal(signal.SIGINT, signal.SIG_DFL) #Force PYQT to handle SIGINT (CTRL+C)

w = WrapperWidget()
tray = TrayIcon(QtGui.QIcon('slouchy_icon.png'), w)

tray.show()
tray.alert()
sys.exit(app.exec_())
