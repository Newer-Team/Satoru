
import os
import os.path
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets; Qt = QtCore.Qt



class MainWindow(QtWidgets.QMainWindow):
    """
    A generic main window that can be customized.
    """

    includeNewInFileMenu = True
    filetypeName = '<undefined>'
    filetypeExts = 'All files (*)'

    programTitle = '<undefined>'

    fp = ''
    unsaved = False

    def __init__(self):
        super().__init__()
        self.setWindowTitle('nsmbulib GUI: ' + self.programTitle)

        self.setupMenuBar()


    @staticmethod
    def addMenuItem(menu, name, callback, shortcut):
        """
        Add an item to a menu in a single line!
        """
        act = menu.addAction(name, callback)
        act.setShortcut(shortcut)
        return act


    def setupMenuBar(self):
        """
        Set up the menu bar and return it. Override this to add on to
        the menu bar.
        """
        mb = self.menuBar()

        fm = mb.addMenu('&File')
        self.setupFileMenu(fm)

        return mb


    def setupFileMenu(self, fileMenu):
        """
        Add items to the File menu
        """
        add = self.addMenuItem
        if self.includeNewInFileMenu:
            add(fileMenu, '&New...', self.handleNew, 'Ctrl+N')
        add(fileMenu, '&Open...', self.handleOpen, 'Ctrl+O')
        add(fileMenu, '&Save', self.handleSave, 'Ctrl+S')
        add(fileMenu, 'Save &As...', self.handleSaveAs, 'Ctrl+Shift+S')
        add(fileMenu, '&Close', self.handleClose, 'Ctrl+Q')


    def handleOpen(self):
        """
        Open a new file
        """
        if self.checkUnsaved(): return

        # Get a file path
        fp = QtWidgets.QFileDialog.getOpenFileName(self,
                                                   'Open ' + self.filetypeName,
                                                   self.currentDir,
                                                   self.filetypeExts)[0]
        if not fp: return

        self.fp = fp
        self.unsaved = False

        self.loadData()


    def handleSave(self):
        """
        Save back to the original file
        """

        # If this is a new file, do a Save As instead
        if not self.fp:
            return self.handleSaveAs()

        try:
            self.saveData()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                'Error',
                'Could not save the file. Full traceback below:\n\n' + \
                    traceback.format_exc() + \
                    "\n\n(Your work has not been saved! Don't close the "
                    "program, or you'll lose it all!)",
                )
            return False

        return True


    def handleSaveAs(self):
        """
        Save to a new file
        """
        # Get a file path
        fp = QtWidgets.QFileDialog.getSaveFileName(self,
                                                   'Save ' + self.filetypeName,
                                                   self.currentDir,
                                                   self.filetypeExts)[0]
        if not fp: return

        # Set the current file path to that, and save
        self.fp = fp
        return self.handleSave()


    def handleClose(self):
        """
        Close the program
        """
        # We do NOT check self.checkUnsaved() here because that is
        # called automatically in closeEvent().
        self.close()


    def checkUnsaved(self):
        """
        Check for unsaved changes. True is returned if the user is
        actually not done. False is returned if the caller can continue
        on with the operation that may cause data loss.
        """
        if not self.unsaved: return False

        msg = QtWidgets.QMessageBox()
        msg.setText('There are unsaved changes.')
        msg.setInformativeText('Would you like to save them first?')
        msg.setStandardButtons(QtWidgets.QMessageBox.Save
                               | QtWidgets.QMessageBox.Discard
                               | QtWidgets.QMessageBox.Cancel)
        msg.setDefaultButton(QtWidgets.QMessageBox.Save)
        ret = msg.exec_()

        if ret == QtWidgets.QMessageBox.Save:
            return not self.handleSave()
        elif ret == QtWidgets.QMessageBox.Discard:
            return False
        elif ret == QtWidgets.QMessageBox.Cancel:
            return True


    def closeEvent(self, event):
        """
        This allows us to prevent unsaved changes from being lost.
        """
        if self.checkUnsaved():
            event.ignore()
        else:
            event.accept()


    @property
    def currentDir(self):
        """
        The directory of the current file
        """
        return os.path.dirname(self.fp)

    @property
    def fileTitle(self):
        """
        The name of the current file, minus the extension. (Will default
        to 'file' if there is no current file, to avoid being empty.)
        """
        ft = os.path.splitext(os.path.basename(self.fp))[0]
        return ft if ft else 'file'


    def loadData(self):
        """
        A new file was opened. Load the file at `self.fp`.
        """
        raise NotImplementedError('Implement loadData() in subclasses.')


    def saveData(self):
        """
        Save the data to the file at `self.fp`.
        """
        raise NotImplementedError('Implement saveData() in subclasses.')
