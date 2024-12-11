import csv
import sys
import sqlite3

from PyQt5.QtCore import QDate, QTime, Qt, QTimer
from PyQt5.QtGui import QColor, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QFormLayout, QLineEdit, QDateEdit, QTimeEdit,
    QMessageBox, QFileDialog, QDialog, QLabel, QComboBox, QCheckBox, QInputDialog, QCalendarWidget)


class EventManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расписание")
        self.resize(800, 600)

        self.init_ui()
        self.create_database()
        self.load_events()

    def init_ui(self):
        container = QWidget()
        self.setCentralWidget(container)

        layout = QVBoxLayout()

        header_layout = QHBoxLayout()

        self.image_label = QLabel()
        self.image_label.setPixmap(QPixmap("./static/img/event_image.png").scaled(100, 100, Qt.KeepAspectRatio))
        self.image_label.setAlignment(Qt.AlignLeft)

        self.title_label = QLabel("Расписание")
        self.title_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.title_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter)

        header_layout.addWidget(self.image_label)
        header_layout.addWidget(self.title_label)

        layout.addLayout(header_layout)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Добавить событие")
        self.add_button.clicked.connect(self.add_event_dialog)

        self.delete_button = QPushButton("Удалить событие")
        self.delete_button.clicked.connect(self.delete_event)

        self.edit_button = QPushButton("Редактировать событие")
        self.edit_button.clicked.connect(self.edit_event)

        self.export_button = QPushButton("Экспортировать CSV")
        self.export_button.clicked.connect(self.export_schedule)

        self.export_txt_button = QPushButton("Экспортировать TXT")
        self.export_txt_button.clicked.connect(self.export_to_txt)

        self.import_button = QPushButton("Импортировать")
        self.import_button.clicked.connect(self.import_schedule)

        self.search_button = QPushButton("Поиск событий")
        self.search_button.clicked.connect(self.search_event_dialog)

        self.filter_button = QPushButton("Фильтровать по дате")
        self.filter_button.clicked.connect(self.filter_by_date_dialog)

        self.setting_button = QPushButton("Настройки")
        self.setting_button.clicked.connect(self.change_table_style)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.export_txt_button)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.filter_button)
        button_layout.addWidget(self.setting_button)

        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(6)
        self.schedule_table.setHorizontalHeaderLabels([
            "ID", "Название", "Дата", "Начало", "Конец", "Тип"
        ])
        self.schedule_table.resizeColumnsToContents()
        self.schedule_table.setSortingEnabled(True)

        layout.addLayout(button_layout)
        layout.addWidget(self.schedule_table)

        container.setLayout(layout)

        self.filter_button = QPushButton("Фильтровать события")
        self.filter_button.clicked.connect(self.filter_events)
        button_layout.addWidget(self.filter_button)

        self.calendar_button = QPushButton("Календарь")
        self.calendar_button.clicked.connect(self.show_calendar)
        button_layout.addWidget(self.calendar_button)

        self.theme_button = QPushButton("Сменить тему")
        self.theme_button.clicked.connect(self.toggle_theme)
        button_layout.addWidget(self.theme_button)

        self.start_notification_timer()

    def create_database(self):
        conn = sqlite3.connect("./db/schedule.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                type_id INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def add_event_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить событие")
        layout = QFormLayout(dialog)

        title_input = QLineEdit()

        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())

        start_time_input = QTimeEdit()
        start_time_input.setTime(QTime.currentTime())

        end_time_input = QTimeEdit()
        end_time_input.setTime(QTime.currentTime().addSecs(3600))

        type_input = QLineEdit()

        layout.addRow("Название:", title_input)
        layout.addRow("Дата:", date_input)
        layout.addRow("Начало:", start_time_input)
        layout.addRow("Конец:", end_time_input)
        layout.addRow("Тип:", type_input)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.add_event(
            title_input.text(),
            date_input.date().toString("yyyy-MM-dd"),
            start_time_input.time().toString("HH:mm:ss"),
            end_time_input.time().toString("HH:mm:ss"),
            type_input.text(),
            dialog
        ))
        layout.addWidget(save_button)

        dialog.exec_()

    def load_events(self):
        self.schedule_table.setRowCount(0)

        conn = sqlite3.connect("./db/schedule.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events")
        events = cursor.fetchall()
        conn.close()

        for row_idx, event in enumerate(events):
            self.schedule_table.insertRow(row_idx)
            for col_idx, data in enumerate(event):
                item = QTableWidgetItem(str(data))

                if col_idx == 2:
                    event_date = QDate.fromString(data, "yyyy-MM-dd")
                    if event_date < QDate.currentDate():
                        item.setBackground(QColor("lightgray"))

                self.schedule_table.setItem(row_idx, col_idx, item)

        self.add_styling_to_rows()

    def add_event(self, title, date, start_time, end_time, event_type, dialog):
        if QTime.fromString(start_time, "HH:mm:ss") >= QTime.fromString(end_time, "HH:mm:ss"):
            QMessageBox.warning(self, "Ошибка", "Время начала должно быть раньше времени окончания!")
            return

        try:
            conn = sqlite3.connect("./db/schedule.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (title, date, start_time, end_time, type_id)
                VALUES (?, ?, ?, ?, ?)
            """, (title, date, start_time, end_time, event_type))
            conn.commit()
            QMessageBox.information(self, "Успех", "Событие добавлено!")
            dialog.accept()
            self.load_events()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Ошибка добавления: {str(e)}")
        finally:
            if conn:
                conn.close()

    def edit_event(self):
        selected_row = self.schedule_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите событие для редактирования.")
            return

        event_id = self.schedule_table.item(selected_row, 0).text()
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать событие")
        layout = QFormLayout(dialog)

        conn = sqlite3.connect("./db/schedule.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, date, start_time, end_time, type_id FROM events WHERE event_id = ?",
                        (event_id,))
        event_data = cursor.fetchone()
        conn.close()

        title_input = QLineEdit(event_data[0])
        date_input = QDateEdit(QDate.fromString(event_data[1], "yyyy-MM-dd"))
        start_time_input = QTimeEdit(QTime.fromString(event_data[2], "HH:mm:ss"))
        end_time_input = QTimeEdit(QTime.fromString(event_data[3], "HH:mm:ss"))
        type_input = QLineEdit(event_data[4])

        layout.addRow("Название:", title_input)
        layout.addRow("Дата:", date_input)
        layout.addRow("Начало:", start_time_input)
        layout.addRow("Конец:", end_time_input)
        layout.addRow("Тип:", type_input)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.update_event(
            event_id,
            title_input.text(),
            date_input.date().toString("yyyy-MM-dd"),
            start_time_input.time().toString("HH:mm:ss"),
            end_time_input.time().toString("HH:mm:ss"),
            type_input.text(), save_button.clicked.connect(lambda: self.update_event(
                event_id,
                title_input.text(),
                date_input.date().toString("yyyy-MM-dd"),
                start_time_input.time().toString("HH:mm:ss"),
                end_time_input.time().toString("HH:mm:ss"),
                type_input.text(),
                dialog
            ))))
        layout.addWidget(save_button)

        dialog.exec_()

    def update_event(self, event_id, title, date, start_time, end_time, event_type, dialog):
        if QTime.fromString(start_time, "HH:mm:ss") >= QTime.fromString(end_time, "HH:mm:ss"):
            QMessageBox.warning(self, "Ошибка", "Время начала должно быть раньше времени окончания!")
            return

        try:
            conn = sqlite3.connect("./db/schedule.db")
            cursor = conn.cursor()
            cursor.execute("""
                    UPDATE events
                    SET title = ?, date = ?, start_time = ?, end_time = ?, type_id = ?
                    WHERE event_id = ?
                """, (title, date, start_time, end_time, event_type, event_id))
            conn.commit()
            QMessageBox.information(self, "Успех", "Событие обновлено!")
            dialog.accept()
            self.load_events()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Ошибка обновления: {str(e)}")
        finally:
            if conn:
                conn.close()

    def delete_event(self):
        selected_row = self.schedule_table.currentRow()

        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите событие для удаления.")
            return

        event_id = self.schedule_table.item(selected_row, 0).text()

        reply = QMessageBox.question(
            self,
            "Подтвердить удаление",
            "Вы уверены, что хотите удалить это событие?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect("./db/schedule.db")
                cursor = conn.cursor()

                cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
                conn.commit()

                QMessageBox.information(self, "Успех", "Событие удалено!")

                self.load_events()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка базы данных", f"Ошибка удаления: {str(e)}")
            finally:
                if conn:
                    conn.close()

    def search_event_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Поиск событий")

        layout = QFormLayout(dialog)

        title_input = QLineEdit()

        type_input = QLineEdit()

        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())

        layout.addRow("Название:", title_input)
        layout.addRow("Тип:", type_input)
        layout.addRow("Дата:", date_input)

        search_button = QPushButton("Найти")

        search_button.clicked.connect(lambda: self.search_events(
            title_input.text(),
            type_input.text(),
            date_input.date().toString("yyyy-MM-dd"),
            dialog
        ))

        layout.addWidget(search_button)

        dialog.exec_()

    def search_events(self, title, event_type, date, dialog):
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if title:
            query += " AND title LIKE ?"
            params.append(f"%{title}%")

        if event_type:
            query += " AND type_id LIKE ?"
            params.append(f"%{event_type}%")

        if date:
            query += " AND date = ?"
            params.append(date)

        conn = sqlite3.connect("./db/schedule.db")
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        self.schedule_table.setRowCount(0)

        for row_idx, event in enumerate(results):
            self.schedule_table.insertRow(row_idx)
            for col_idx, data in enumerate(event):
                self.schedule_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

        dialog.accept()

    def filter_by_date_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Фильтровать по дате")

        layout = QFormLayout(dialog)

        start_date_input = QDateEdit()
        start_date_input.setCalendarPopup(True)
        start_date_input.setDate(QDate.currentDate())

        end_date_input = QDateEdit()
        end_date_input.setCalendarPopup(True)
        end_date_input.setDate(QDate.currentDate())

        layout.addRow("Дата начала:", start_date_input)
        layout.addRow("Дата окончания:", end_date_input)

        filter_button = QPushButton("Применить")
        filter_button.clicked.connect(lambda: self.filter_by_date(
            start_date_input.date().toString("yyyy-MM-dd"),
            end_date_input.date().toString("yyyy-MM-dd"),
            dialog
        ))
        layout.addWidget(filter_button)

        dialog.exec_()

    def filter_by_date(self, start_date, end_date, dialog):
        conn = sqlite3.connect("./db/schedule.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE date BETWEEN ? AND ?", (start_date, end_date))
        results = cursor.fetchall()
        conn.close()

        self.schedule_table.setRowCount(0)
        for row_idx, event in enumerate(results):
            self.schedule_table.insertRow(row_idx)
            for col_idx, data in enumerate(event):
                self.schedule_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

        dialog.accept()

    def filter_events(self):
        date, ok = QInputDialog.getText(self, "Фильтр по дате", "Введите дату в формате YYYY-MM-DD:")
        if ok and date:
            try:
                conn = sqlite3.connect("./db/schedule.db")
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM events WHERE date = ?", (date,))
                events = cursor.fetchall()
                conn.close()

                self.schedule_table.setRowCount(0)
                for row_idx, event in enumerate(events):
                    self.schedule_table.insertRow(row_idx)
                    for col_idx, data in enumerate(event):
                        self.schedule_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка базы данных", f"Ошибка фильтрации: {str(e)}")

    def export_to_txt(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить в TXT", "./static/files", "Text Files (*.txt)")
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as txt_file:
                txt_file.write("ID\tНазвание\tДата\tНачало\tКонец\tТип\n")
                for row in range(self.schedule_table.rowCount()):
                    row_data = []
                    for col in range(self.schedule_table.columnCount()):
                        item = self.schedule_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    txt_file.write("\t".join(row_data) + "\n")
            QMessageBox.information(self, "Успех", "Расписание экспортировано в TXT!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать: {str(e)}")

    def export_schedule(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Экспортировать расписание", "./static/files", "CSV Files (*.csv)", options=options)

        if file_name:
            try:
                conn = sqlite3.connect("./db/schedule.db")
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM events")
                events = cursor.fetchall()

                with open(file_name, mode='w', newline='', encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["ID", "Название", "Дата", "Начало", "Конец", "Тип"])
                    writer.writerows(events)

                QMessageBox.information(self, "Успех", "Расписание экспортировано!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка базы данных", f"Ошибка экспорта: {str(e)}")
            finally:
                if conn:
                    conn.close()

    def import_schedule(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Импортировать расписание", "./static/files", "CSV Files (*.csv)", options=options)

        if file_name:
            try:
                with open(file_name, mode='r', encoding="utf-8") as file:
                    reader = csv.reader(file)
                    header = next(reader)

                    conn = sqlite3.connect("./db/schedule.db")
                    cursor = conn.cursor()

                    for row in reader:
                        cursor.execute("""
                            INSERT INTO events (event_id, title, date, start_time, end_time, type_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (row[0], row[1], row[2], row[3], row[4], row[5]))

                    conn.commit()
                    QMessageBox.information(self, "Успех", "Расписание импортировано!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка базы данных", f"Ошибка импорта: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при чтении файла: {str(e)}")
            finally:
                if conn:
                    conn.close()

    def start_notification_timer(self):
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_upcoming_events)
        self.notification_timer.start(60000)  # Проверка каждую минуту

    def check_upcoming_events(self):
        conn = sqlite3.connect("./db/schedule.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, date, start_time FROM events")
        events = cursor.fetchall()
        conn.close()

        current_date = QDate.currentDate().toString("yyyy-MM-dd")
        current_time = QTime.currentTime()

        for title, event_date, start_time in events:
            if event_date == current_date:
                event_time = QTime.fromString(start_time, "HH:mm:ss")
                if current_time.secsTo(event_time) <= 900:  # 15 минут до события
                    QMessageBox.information(self, "Напоминание", f"Скоро начнется событие: {title}")

    def show_calendar(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Календарь событий")
        layout = QVBoxLayout(dialog)

        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.clicked.connect(lambda date: self.show_events_for_date(date.toString("yyyy-MM-dd")))
        layout.addWidget(calendar)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.exec_()

    def show_events_for_date(self, date):
        QMessageBox.information(self, "События", f"Показать события для даты: {date}")

    def change_table_style(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки таблицы")
        layout = QVBoxLayout(dialog)

        font_size_combo = QComboBox()
        font_size_combo.addItems([str(size) for size in range(8, 25)])
        layout.addWidget(QLabel("Размер шрифта:"))
        layout.addWidget(font_size_combo)

        alternating_row_check = QCheckBox("Чередовать строки")
        layout.addWidget(alternating_row_check)

        apply_button = QPushButton("Применить")
        apply_button.clicked.connect(lambda: self.apply_table_style(
            int(font_size_combo.currentText()),
            alternating_row_check.isChecked(),
            dialog
        ))
        layout.addWidget(apply_button)

        dialog.exec_()

    def apply_table_style(self, font_size, alternate_rows, dialog):
        font = QFont("Arial", font_size)
        self.schedule_table.setFont(font)
        self.schedule_table.setAlternatingRowColors(alternate_rows)
        dialog.accept()

    def add_styling_to_rows(self):
        for row in range(self.schedule_table.rowCount()):
            for col in range(self.schedule_table.columnCount()):
                item = self.schedule_table.item(row, col)
                if item:
                    item.setFont(QFont("Arial", 10))
                    if row % 2 == 0:
                        item.setBackground(QColor("lightblue"))

    def set_theme(self, theme):
        if theme == "dark":
            self.setStyleSheet("background-color: #2e2e2e; color: white;")
        else:
            self.setStyleSheet("")

    def toggle_theme(self):
        current_theme = self.styleSheet()
        if "background-color: #2e2e2e" in current_theme:
            self.set_theme("light")
        else:
            self.set_theme("dark")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EventManager()
    window.show()
    sys.exit(app.exec_())