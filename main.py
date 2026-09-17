import sys
import os

from PySide6.QtWidgets import QApplication

from ui import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    if len(sys.argv) > 1:
        # Pass first CLI argument as file to open
        filepath = sys.argv[1]
        if os.path.exists(filepath):
            window.open_file(filepath)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()