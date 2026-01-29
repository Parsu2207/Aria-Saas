# ui/alerts_table_model.py
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant


class AlertsTableModel(QAbstractTableModel):
    HEADERS = ["Alert ID", "Time", "Source", "Severity", "Event", "Entity", "Priority", "Score"]

    def __init__(self, alerts=None):
        super().__init__()
        self._alerts = alerts or []

    def update_alerts(self, alerts):
        self.beginResetModel()
        self._alerts = alerts
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._alerts)

    def columnCount(self, parent=None):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return QVariant()

        alert = self._alerts[index.row()]
        col = index.column()

        if col == 0:
            return alert.get("alert_id")
        if col == 1:
            return alert.get("timestamp")
        if col == 2:
            return alert.get("source")
        if col == 3:
            return alert.get("severity")
        if col == 4:
            return alert.get("event_type")
        if col == 5:
            ents = alert.get("entities", {})
            return ents.get("user") or ents.get("ip")
        if col == 6:
            return alert.get("priority_bucket")
        if col == 7:
            return f"{alert.get('priority_score', 0):.2f}"

        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return section + 1
