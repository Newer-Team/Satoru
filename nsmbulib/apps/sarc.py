# 8/17/16

import sys
import os
import os.path

from PyQt5 import QtCore, QtGui, QtWidgets; Qt = QtCore.Qt
import nsmbulib.Sarc

import _base_ui


SARC_EXTENSIONS = 'SARC Archives (*.sarc);;All files (*)'


class FileTreeItem(QtWidgets.QTreeWidgetItem):
    """
    Either a file or a folder.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

    @property
    def name(self):
        return self.text(0)
    @name.setter
    def name(self, value):
        self.setText(0, value)

    def __str__(self):
        return '<' + type(self).__name__ + ' "' + self.name + '">'


class FileItem(FileTreeItem):
    """
    A tree widget item that represents (and contains the data for) a
    file.
    """
    def __init__(self, name, data):
        super().__init__([name])
        self.data = data

    def itemDropped(self, item):
        ...

    def itemsDropped(self, items):
        ...


class FolderItem(FileTreeItem):
    """
    A tree widget item that represents a folder.
    """
    def __init__(self, name):
        super().__init__([name])

    def itemDropped(self, item):
        ...

    def itemsDropped(self, items):
        ...


class FileTree(QtWidgets.QTreeWidget):
    """
    A tree view that accepts file/folder drag-and-drops.
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.header().close()
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)

    ################################################################
    ######################### Drag and Drop ########################
    ################################################################

    def mimeTypes(self):
        return [
            'text/uri-list',
            'application/x-qabstractitemmodeldatalist',
            ]

    def dragEnterEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        mimeData = event.mimeData()

        if not mimeData.hasUrls(): return
        pathList = [url.toLocalFile() for url in mimeData.urls()]

        dropOnto = self.itemFromIndex(self.indexAt(event.pos()))
        # dropOnto is None, a FileItem or a FolderItem

        # print(isinstance(dropOnto, FileItem))
        # if dropOnto is None: print(None)
        # else: print(dropOnto.text(0))

        def createItems(paths):
            # paths must be complete paths

            items = []
            for path in paths:
                if os.path.isfile(path):
                    with open(path, 'rb') as f:
                        items.append(
                            FileItem(os.path.basename(path), f.read()))
                else:
                    folder = FolderItem(os.path.basename(path))
                    items.append(folder)
                    folder.addItems(createItems(
                        os.path.join(path, p) for p in os.listdir(path)))
            return items

        itemList = []
        if len(pathList) > 1:
            for path in pathList:
                if os.path.isfile(path):
                    with open(path, 'rb') as f:
                        data = f.read()
                    itemList.append(FileItem(os.path.basename(path), data))
                else:
                    itemList.append(makeFolderItemFromPath(path))
        else:
            ...

    ################################################################
    ####################### End Drag and Drop ######################
    ################################################################

    def addFiles(self, files):
        """
        Add this dictionary of files to the file tree widget.
        """

        files = {
            'a/1.txt': '',
            'a/2.txt': '',
            'a/3.txt': '',
            'b/1.txt': '',
            'b/2.txt': '',
            'b/3.txt': '',
            'c/a/1.txt': '',
            'c/a/2.txt': '',
            'c/a/3.txt': '',
            'c/b/1.txt': '',
            'c/b/2.txt': '',
            'c/b/3.txt': '',
            '1.txt': '',
            '2.txt': '',
            '3.txt': '',
        }

        # Un-flatten the file structure
        rootFolder = {}
        for file, data in files.items():
            currentFolder = rootFolder
            for folderName in file.split('/')[:-1]:
                if folderName not in currentFolder:
                    currentFolder[folderName] = {}
                currentFolder = currentFolder[folderName]
            currentFolder[file.split('/')[-1]] = data

        # Add items
        def setupFolder(addFxn, contents):
            for name, data in contents.items():
                if isinstance(data, dict):
                    folder = FolderItem(name)
                    addFxn(folder)
                    setupFolder(folder.addChild, data)
                else:
                    addFxn(FileItem(name, data))
        setupFolder(self.addTopLevelItem, rootFolder)


class SarcMainWindow(_base_ui.MainWindow):
    """
    A MainWindow for the SARC program.
    """

    includeNewInFileMenu = False
    filetypeName = 'SARC'
    filetypeExts = 'SARC Archives (*.sarc);;All files (*)'

    programTitle = 'SARC'

    def __init__(self):
        super().__init__()

        self.fileTree = FileTree(self)
        self.setCentralWidget(self.fileTree)


    def setupFileMenu(self, fileMenu):
        """
        Add some more things to the File menu.
        """
        super().setupFileMenu(fileMenu)
        add = self.addMenuItem

        fileMenu.addSeparator()
        add(fileMenu, '&Export All...', self.handleExportAll, 'Ctrl+E')


    def handleExportAll(self):
        """
        Export all files in the SARC.
        """
        # Get a folder path
        dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Export ' + self.filetypeName,
            self.currentDir)
        if not dir: return

        for fn, fd in self.FILES.items():
            fullFn = os.path.join(dir, self.fileTitle, fn)
            if not os.path.isdir(os.path.dirname(fullFn)):
                os.makedirs(os.path.dirname(fullFn))
            with open(fullFn, 'wb') as f:
                f.write(fd)


    def loadData(self):
        """
        Load a SARC from `self.fp`.
        """
        with open(self.fp, 'rb') as f:
            data = f.read()

        files = nsmbulib.Sarc.load(data)
        self.fileTree.clear()
        self.fileTree.addFiles(files)


    def saveData(self):
        """
        Save a SARC to `self.fp`.
        """
        ...


def main(argv):
    """
    Main function for the SARC script
    """
    app = QtWidgets.QApplication(argv)
    mw = SarcMainWindow()
    mw.show()
    app.exec_()

main(sys.argv)
