import sys

from GUI.main_window import MainWindow
from PyQt6.QtWidgets import QApplication

from argparse import ArgumentParser


if __name__ == '__main__':
    argparser = ArgumentParser()
    argparser.add_argument("-d", dest="debug", required=False, default=False, action='store_true')
    args = argparser.parse_args()
    app = QApplication(sys.argv)
    window = MainWindow(args.debug)
    window.show()
    sys.exit(app.exec())
