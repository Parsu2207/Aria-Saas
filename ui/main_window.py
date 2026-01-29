# ui/main_window.py
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QTableView, QMessageBox
)
from .alerts_table_model import AlertsTableModel
from .api_client import ApiClient


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api = ApiClient()
        self.setWindowTitle("ARIA Desktop – Alert & Response Intelligence Agent")
        self.resize(1100, 600)

        central = QWidget()
        layout = QVBoxLayout()
        controls = QHBoxLayout()

        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])

        self.refresh_btn = QPushButton("Refresh Alerts")
        self.refresh_btn.clicked.connect(self.refresh_alerts)

        controls.addWidget(self.priority_filter)
        controls.addWidget(self.refresh_btn)

        self.table = QTableView()
        self.model = AlertsTableModel()
        self.table.setModel(self.model)

        layout.addLayout(controls)
        layout.addWidget(self.table)
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.refresh_alerts()

    def refresh_alerts(self):
        try:
            priority = self.priority_filter.currentText()
            if priority == "ALL":
                priority = None
            alerts = self.api.get_alerts(priority=priority)
            self.model.update_alerts(alerts)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load alerts: {e}")
