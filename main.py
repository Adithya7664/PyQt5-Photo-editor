import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("GenPhoto")
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())