import redis
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QMessageBox

class ConnectionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Redis Connection Details")
        
        self.form_layout = QFormLayout()
        self.host_edit = QLineEdit()
        self.port_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.username_edit = QLineEdit()

        # Set the default host name to "127.0.0.1"
        self.host_edit.setText("127.0.0.1")

        self.form_layout.addRow("Host:", self.host_edit)
        self.form_layout.addRow("Port:", self.port_edit)
        self.form_layout.addRow("Password:", self.password_edit)
        self.form_layout.addRow("Username (optional):", self.username_edit)

        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.test_button)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    def test_connection(self):
        host = self.host_edit.text()
        port = int(self.port_edit.text())
        password = self.password_edit.text()

        try:
            redis_client = redis.StrictRedis(
                host=host, 
                port=port, 
                password=password
            )
            redis_client.ping()
            QMessageBox.information(self, "Connection Test", "Connection successful")
        except redis.AuthenticationError as ae:
            QMessageBox.warning(self, "Connection Failed", "Invalid username or password")
        except redis.ConnectionError as ce:
            QMessageBox.critical(self, "Connection Test", "Connection failed")

