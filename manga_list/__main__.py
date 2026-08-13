"""Entry point: ``python -m manga_list``."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from manga_list import log_config

from manga_list.gui.main_window import MainWindow, _build_app_icon


def main() -> int:
    log_config.setup()
    # On Windows, set an explicit AppUserModelID so the taskbar uses our icon
    # instead of grouping under the generic python.exe icon.
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "manga_list.classifier.1"
            )
        except (AttributeError, OSError):
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("Manga List Classifier")
    app.setWindowIcon(_build_app_icon())
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
