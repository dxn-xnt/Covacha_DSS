from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem
from PyQt5.QtCore import QTimer

from Controllers.DataRequest_Controller import DataRequest
from Views.Staff_Dashboard import Ui_MainWindow as StaffDashboardUi
from Controllers.StaffAddCheckUp_Controller import StaffAddCheckUp
from Controllers.StaffLabRequest_Controller import StaffLabRequest
from Controllers.StaffTransactionModal_Controller import StaffTransactionModal
from Controllers.StaffTransactionList_Controllerr import StaffTransactionList
from datetime import datetime


class StaffDashboardController(QMainWindow):
    def __init__(self, staff_id=None):
        super().__init__()
        self.ui = StaffDashboardUi()
        self.ui.setupUi(self)
        print("StaffDashboard UI initialized!")

        # Initialize dynamic date and time labels
        try:
            self.update_time_labels()
            print("Time labels updated successfully.")
        except Exception as e:
            print(f"Error updating time labels: {e}")

        # Set up a timer to update the labels every second
        try:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_time_labels)
            self.timer.start(1000)
            print("Timer started successfully.")
        except Exception as e:
            print(f"Error setting up timer: {e}")

        # Store the staff ID
        self.staff_id = staff_id
        print(f"StaffDashboard initialized for staff ID: {self.staff_id}")

        # Connect buttons
        try:
            if hasattr(self.ui, 'LabRequestButton'):
                self.ui.LabRequestButton.clicked.connect(self.ViewStaffLabRequest)
                print("LabRequestButton connected successfully.")
            if hasattr(self.ui, 'AddCheckUp'):
                self.ui.AddCheckUp.clicked.connect(self.open_checkup_user_form)
                print("AddCheckUp connected successfully.")
            if hasattr(self.ui, 'AddTransac'):
                self.ui.AddTransac.clicked.connect(self.open_transaction_modal)
                print("AddTransac connected successfully.")
            if hasattr(self.ui, 'TransactionButton'):
                self.ui.TransactionButton.clicked.connect(self.ViewStaffTransaction)
                print("TransactionButton connected successfully.")
        except Exception as e:
            print(f"Error connecting buttons: {e}")

        # Load pending check-ups
        try:
            self.load_pending_checkups()
            print("Pending check-ups loaded successfully.")
        except Exception as e:
            print(f"Error loading pending check-ups: {e}")

        # Apply table styles
        try:
            self.apply_table_styles()
            print("Table styles applied successfully.")
        except Exception as e:
            print(f"Error applying table styles: {e}")

    def apply_table_styles(self):
        """Apply custom styles to the tables"""
        # Style for PatientDetails table
        self.ui.PendingTable.setStyleSheet("""
               QTableWidget {
                background-color: #F4F7ED;
                gridline-color: transparent;
                border-radius: 10px;
            }
            QTableWidget::item {
                border: none;
                font: 16pt "Lexend";
            }
            QTableWidget::item:selected {
                background-color: rgba(46, 110, 101, 0.3);
            }
            QTableWidget QHeaderView::section {
                background-color: #2E6E65;
                color: white;
                padding: 5px;
                font: 18px "Lexend Medium";
                border: 2px solid #2E6E65;
            }

            Scroll Area CSS
            QScrollBar:vertical {
                 background: transparent;
                 width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                    background: #C0C0C0;
                    border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                    background: #A0A0A0;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical{
                    background: none;
                    border: none;
            }
           """)

        # Ensure horizontal headers are visible
        self.ui.PendingTable.horizontalHeader().setVisible(True)

        # Align headers to the left
        self.ui.PendingTable.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        # Hide the vertical header (row index)
        self.ui.PendingTable.verticalHeader().setVisible(False)

        # Set selection behavior
        self.ui.PendingTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

    def load_pending_checkups(self):
        """Fetch and display pending check-ups in the PatientDetails table."""
        try:
            # Fetch pending check-ups from the database
            pending_checkups = DataRequest.send_command("GET_PENDING_CHECKUP")
            print(pending_checkups)

            # Get today's date in the format YYYYMMDD
            today_date = datetime.now().strftime("%Y%m%d")

            # Filter check-ups for today
            todays_checkups = [
                checkup for checkup in pending_checkups
                if checkup["chck_id"].startswith(today_date)
            ]

            # Clear the table before populating it
            self.ui.PendingTable.setRowCount(0)

            # Check if there are no check-ups for today
            if not todays_checkups:
                print("No check-ups found for today.")

                # Add a single row with the message "No Check Ups For Today"
                self.ui.PendingTable.insertRow(0)
                no_data_item = QTableWidgetItem("No Check Ups For Today")
                self.ui.PendingTable.setItem(0, 0, no_data_item)

                # Span the message across all columns
                column_count = self.ui.PendingTable.columnCount()
                self.ui.PendingTable.setSpan(0, 0, 1, column_count)
                return

            # Populate the table with today's check-ups
            for row, checkup in enumerate(todays_checkups):
                pat_id = checkup["pat_id"]
                chck_id = checkup["chck_id"]
                chck_type = checkup["chckup_type"]

                # Fetch patient details
                request = f"GET_PATIENT_BY_ID {pat_id}"
                patient = DataRequest.send_command(request)
                print(patient)
                if not patient:
                    print(f"No patient found for pat_id={pat_id}")
                    continue

                # Extract patient name and capitalize the first letter of each word
                full_name = f"{patient['last_name'].capitalize()}, {patient['first_name'].capitalize()}"

                # Insert data into the table in the new column order (Check Up ID, Patient Name, Type)
                self.ui.PendingTable.insertRow(row)
                self.ui.PendingTable.setItem(row, 0, QTableWidgetItem(chck_id))  # Check Up ID
                self.ui.PendingTable.setItem(row, 1, QTableWidgetItem(full_name))  # Patient Name
                self.ui.PendingTable.setItem(row, 2, QTableWidgetItem(chck_type))  # Check-Up Type

            # Resize columns to fit the content
            self.ui.PendingTable.resizeColumnsToContents()

            # Optionally, set minimum widths for specific columns
            self.ui.PendingTable.setColumnWidth(0, 150)  # Check Up ID column
            self.ui.PendingTable.setColumnWidth(1, 150)  # Patient Name column
            self.ui.PendingTable.setColumnWidth(2, 200)  # Check-Up Type column

        except Exception as e:
            print(f"Error loading pending check-ups: {e}")

    def open_checkup_user_form(self):
        print("Opening Add Check-Up Form...")
        try:
            # Pass the staff_id and a refresh callback to the AddCheckUp form
            self.add_checkup_window = StaffAddCheckUp(parent=self, staff_id=self.staff_id)
            self.add_checkup_window.refresh_callback = self.load_pending_checkups
            self.add_checkup_window.show()
            print("Add Check-Up Form shown successfully!")
        except Exception as e:
            print(f"Error opening Add Check-Up Form: {e}")

    def open_transaction_modal(self):
        """Open the StaffTransaction modal."""
        print("Opening Add Transaction Modal...")
        try:
            # Open the modal window with a reference to the parent (dashboard)
            self.add_transaction_window = StaffTransactionModal(parent=self, staff_dashboard=self)
            self.add_transaction_window.show()
            print("Add Transaction Modal shown successfully!")
        except Exception as e:
            print(f"Error opening Add Transaction Modal: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open Add Transaction Modal: {e}")

    def ViewStaffTransaction(self):
        """Open the StaffTransactionList window."""
        self.staff_transaction_window = StaffTransactionList()
        self.staff_transaction_window.show()
        self.close()

    def ViewStaffLabRequest(self):
        print("Opening staff lab request feature")
        try:
            # Instantiate and show the AdminStaffsController window
            self.staff_request_controller = StaffLabRequest(self.staff_id)
            self.staff_request_controller.show()
            self.hide()  # Hide the current dashboard window
        except Exception as e:
            print(f"Error loading tables: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load tables: {e}")

    def setup_ui(self):
        self.update_time_labels()

    def update_time_labels(self):
        """Update the Time, Day, and Month labels with current values."""
        now = datetime.now()  # Corrected: Use datetime.now() directly
        # Format time (e.g., 03:45 PM)
        time_format = now.strftime("%I:%M %p")
        self.ui.Time.setText(time_format)
        # Format day (e.g., Sunday)
        day_format = now.strftime("%A")
        self.ui.Day.setText(day_format)
        # Format month and year (e.g., October 15, 2023)
        month_year_format = f"{now.strftime('%B')} {now.day}, {now.year}"
        self.ui.Month.setText(month_year_format)
        # Force refresh the UI
        self.repaint()

