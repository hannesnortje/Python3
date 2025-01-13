import sys
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from mpmath import mp


class PiDistanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pi Consecutive Number Distance Calculator")
        self.setGeometry(100, 100, 800, 400)

        # Set up main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Input fields
        input_layout = QHBoxLayout()
        self.number1_input = QLineEdit()
        self.number1_input.setPlaceholderText("Enter the first sequence")
        self.number2_input = QLineEdit()
        self.number2_input.setPlaceholderText("Enter the second sequence")
        input_layout.addWidget(QLabel("Number 1:"))
        input_layout.addWidget(self.number1_input)
        input_layout.addWidget(QLabel("Number 2:"))
        input_layout.addWidget(self.number2_input)
        self.layout.addLayout(input_layout)

        # Result label
        self.result_label = QLabel("Results will be shown here.")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.result_label)

        # Table for results
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Time", "Number 1", "Number 2", "Distance"])
        self.layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.clicked.connect(self.calculate_distance)
        self.save_button = QPushButton("Save Table")
        self.save_button.clicked.connect(self.save_table)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_inputs)
        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.close)
        button_layout.addWidget(self.calculate_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.quit_button)
        self.layout.addLayout(button_layout)

        # Initialize variables
        self.precision = 1000000
        mp.dps = self.precision
        self.pi_digits = str(mp.pi)[2:]

    def calculate_distance(self):
        number1 = self.number1_input.text()
        number2 = self.number2_input.text()

        # Validate input
        if not number1.isdigit() or not number2.isdigit():
            QMessageBox.warning(self, "Invalid Input", "Please enter valid sequences of digits.")
            return

        # Find positions
        pos1 = self.pi_digits.find(number1)
        pos2 = self.pi_digits.find(number2)

        if pos1 == -1 or pos2 == -1:
            QMessageBox.warning(self, "Not Found", f"One or both sequences not found in the first {self.precision} digits of pi.")
            return

        # Calculate the distance in digits
        distance = abs(pos2 - pos1) - len(number1)

        self.result_label.setText(f"Distance between '{number1}' and '{number2}' is {distance} digits.")

        # Add result to table
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem(current_time))
        self.table.setItem(row_position, 1, QTableWidgetItem(number1))
        self.table.setItem(row_position, 2, QTableWidgetItem(number2))
        self.table.setItem(row_position, 3, QTableWidgetItem(str(distance)))

        # Update inputs for next test
        self.number1_input.setText(number2)
        self.number2_input.clear()

    def save_table(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Table", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, "w") as file:
                    file.write("Time,Number 1,Number 2,Distance\n")
                    for row in range(self.table.rowCount()):
                        line = []
                        for column in range(self.table.columnCount()):
                            item = self.table.item(row, column)
                            line.append(item.text() if item else "")
                        file.write(",".join(line) + "\n")
                QMessageBox.information(self, "Success", "Table saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def reset_inputs(self):
        self.number1_input.clear()
        self.number2_input.clear()
        self.result_label.setText("Results will be shown here.")
        self.table.setRowCount(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PiDistanceApp()
    window.show()
    sys.exit(app.exec())
