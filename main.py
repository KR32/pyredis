import sys
import redis
import pickle
import json

import qdarkstyle
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QToolButton
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QInputDialog

from connect import ConnectionDialog
from encoder import CustomJSONEncoder


class RedisClientApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Redis Client")
        self.setGeometry(100, 100, 800, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.redis_client = None
        self.connection_dialog = ConnectionDialog()
        self.dark_theme_enabled = False

        # Flag that indicates the value layout is in edit mode.
        self.edit_mode = False

        self.init_connection()

        self.init_ui()

    def init_connection(self):
        result = self.connection_dialog.exec_()
        if result == QDialog.Accepted:

            self.connection_dialog.test_connection()

            host = self.connection_dialog.host_edit.text()
            port = int(self.connection_dialog.port_edit.text())
            password = self.connection_dialog.password_edit.text()
            username = self.connection_dialog.username_edit.text()
            
            self.redis_client = self.connect_to_redis(host, port, password)

    def connect_to_redis(self, host, port, password):
        return redis.StrictRedis(host=host, port=port, password=password)

    def add_key(self):
        if self.redis_client:
            key, ok = QInputDialog.getText(self, "Add Key", "Enter the key:")
            if ok:
                value, ok = QInputDialog.getText(self, "Add Key", "Enter the value:")
                if ok:
                    try:
                        # Serialize the new value using pickle
                        serialized_value = pickle.dumps(value)
                        self.redis_client.set(key, serialized_value)
                        QMessageBox.information(self, "Add Key", f"Key '{key}' added successfully")
                        self.list_keys()  # Refresh the key list
                    except pickle.PickleError:
                        QMessageBox.critical(self, "Add Key", f"Failed to serialize the data for key '{key}'")
        else:
            QMessageBox.critical(self, "Add Key", "No Redis connection established")

    def search_keys(self, search_text):
        if self.redis_client:
            keys = self.redis_client.keys(f'*{search_text}*')
            self.key_list.clear()
            for key in keys:
                key_str = key.decode('utf-8')
                self.key_list.addItem(key_str)

    def edit_value(self):
        key = self.key_list.currentItem()

        if key is None:
            QMessageBox.critical(self, "Edit Value", "Select any key to edit its value")
        else:
            key = key.text()

            new_value = self.value_display.toPlainText()

            if self.redis_client:
                try:
                    # Serialize the new value using pickle
                    serialized_value = pickle.dumps(new_value)
                    self.redis_client.set(key, bytes(serialized_value))
                    QMessageBox.information(self, "Edit Value", f"Value for key '{key}' edited and saved successfully")
                except pickle.PickleError:
                    QMessageBox.critical(self, "Edit Value", f"Failed to serialize the data for key '{key}'")
            else:
                QMessageBox.critical(self, "Edit Value", "No Redis connection established")

    def delete_value(self):
        key = self.key_list.currentItem()
        
        if key is None:
            QMessageBox.critical(self, "Delete Key", "Select any key to delete")
        else:
            key = key.text()

            if self.redis_client:
                result = self.redis_client.delete(key)
                if result > 0:
                    self.list_keys()  # Refresh the key list
                    QMessageBox.information(self, "Delete Key", f"Key '{key}' deleted successfully")
                else:
                    QMessageBox.warning(self, "Delete Key", f"Key '{key}' not found")
            else:
                QMessageBox.critical(self, "Delete Key", "No Redis connection established")

    def list_keys(self, edit_button):
        self.value_display.setPlainText(f"Select any one of the keys from the  list to view the value")
        if self.redis_client:
            keys = self.redis_client.keys('*')
            self.key_list.clear()
            for key in keys:
                key_str = key.decode('utf-8')  # Decode the bytes to a string
                self.key_list.addItem(key_str)
        
        if self.edit_mode is True:
            self.toggle_edit_mode(edit_button)

    def get_value(self, item):
        key = item.text()
        value = self.redis_client.get(key)
        if value is not None:
            try:
                # Deserialize the binary data using pickle
                deserialized_value = pickle.loads(value)            
                formatted_json = json.dumps(deserialized_value, cls=CustomJSONEncoder, indent=4)
                self.value_display.setPlainText(formatted_json)
            except pickle.PickleError:
                self.value_display.setPlainText(str(value))
        else:
            self.value_display.setPlainText(f"Key '{key}' not found")
    
    def init_ui(self):
        if self.redis_client:
            layout = QHBoxLayout()

            # Left Panel: Key List with Search Bar
            key_layout = QVBoxLayout()

            # Search bar
            search_bar = QLineEdit("Search keys...")
            search_bar.textChanged.connect(lambda text: self.search_keys(text))
            key_layout.addWidget(search_bar)

            key_label = QLabel("Keys:")
            self.key_list = QListWidget()
            key_layout.addWidget(key_label)
            key_layout.addWidget(self.key_list)

            # Right Panel: Value Display
            value_layout = QVBoxLayout()
            value_buttons_layout = QHBoxLayout()  # Buttons layout at the top
            value_label = QLabel("Value:")
            self.value_display = QTextEdit()

            # Buttons with icons
            add_key_button = QToolButton()
            add_key_button.setToolTip("Add Key")
            add_key_button.setIcon(QIcon("images/add.png"))
            edit_button = QToolButton()
            edit_button.setToolTip("Save changes")
            edit_button.setIcon(QIcon("images/edit.png"))
            delete_button = QToolButton()
            delete_button.setToolTip("Delete Key")
            delete_button.setIcon(QIcon("images/bin.png"))
            refresh_button = QToolButton()
            refresh_button.setToolTip("Refresh Key")
            refresh_button.setIcon(QIcon("images/refresh.png"))

            # Connect button actions
            add_key_button.clicked.connect(self.add_key)
            edit_button.clicked.connect(lambda: self.toggle_edit_mode(edit_button))
            delete_button.clicked.connect(self.delete_value)
            refresh_button.clicked.connect(lambda: self.list_keys(edit_button))
            value_buttons_layout.addWidget(add_key_button)
            value_buttons_layout.addSpacing(10)
            value_buttons_layout.addWidget(edit_button)
            value_buttons_layout.addSpacing(10)
            value_buttons_layout.addWidget(delete_button)
            value_buttons_layout.addSpacing(10)
            value_buttons_layout.addWidget(refresh_button)
            value_buttons_layout.addSpacing(10)

            value_layout.addLayout(value_buttons_layout)  # Add the buttons layout
            value_layout.addWidget(value_label)
            value_layout.addWidget(self.value_display)

            layout.addLayout(key_layout)
            layout.addLayout(value_layout)

            self.central_widget.setLayout(layout)

            # List all keys and connect click event
            self.list_keys(edit_button)
            self.key_list.itemClicked.connect(self.get_value)

    def toggle_dark_theme(self):
        if self.dark_theme_enabled:
            app.setStyleSheet('')
            self.dark_theme_enabled = False
        else:
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            self.dark_theme_enabled = True
            
    def toggle_edit_mode(self, edit_button):
        if self.edit_mode:
            edit_button.setIcon(QIcon("images/edit.png"))
            edit_button.setText("Edit")  # Change button text
        
            # Save changes
            self.edit_value()
            self.value_display.setReadOnly(True)  # Set to read-only
        else:
            # Enter edit mode
            edit_button.setIcon(QIcon("images/save.png"))
            edit_button.setText("Save")  # Change button text
            self.value_display.setReadOnly(False)  # Allow editing

        # Toggle the mode
        self.edit_mode = not self.edit_mode

    def create_menu_bar(self):
        menubar = self.menuBar()
        theme_menu = menubar.addMenu("Theme")

        toggle_theme_action = QAction("Toggle Dark Theme", self)
        toggle_theme_action.triggered.connect(self.toggle_dark_theme)
        theme_menu.addAction(toggle_theme_action)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RedisClientApp()

    # Enable dark theme by default
    window.toggle_dark_theme()

    window.show()

    sys.exit(app.exec_())
