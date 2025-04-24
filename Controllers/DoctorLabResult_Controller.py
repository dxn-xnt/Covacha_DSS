import os
import subprocess
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QMessageBox, QLabel, QDialog, QDialogButtonBox, QApplication

from Models import Prescription
from Views.Doctor_LabResult import Ui_MainWindow as DoctorLabResultUI
from Controllers.DoctorAddPrescription_Controller import DoctorAddPrescription
from Models.CheckUp import CheckUp
from Models.Patient import Patient
from Models.LaboratoryTest import Laboratory
from Models.Prescription import Prescription
from datetime import datetime, date

class ConfirmationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Diagnose")
        self.setFixedSize(400, 150)

        # Main layout
        layout = QVBoxLayout()

        # Add message label
        self.message_label = QLabel("Are you sure you want to proceed ?")
        layout.addWidget(self.message_label)

        # Add button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Apply stylesheet to the button box
        self.button_box.setStyleSheet("""
            QPushButton {
                background-color: #2E6E65;
                color: white;
                border-radius: 10px;
                padding: 5px 10px;
                margin-top: 5px
            }
            QPushButton:hover {
                background-color: #235C5A;
            }
        """)
        layout.addWidget(self.button_box)

        # Set layout
        self.setLayout(layout)


def calculate_age(dob):
    """Calculate the age based on the date of birth."""
    today = datetime.today()
    if isinstance(dob, date):  # Use the explicitly imported 'date'
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    else:
        raise ValueError("DOB must be a datetime.date object or a valid date string.")


class DoctorLabResult(QMainWindow):
    def __init__(self, checkup_id=None, parent=None, refresh_callback=None, view = False):
        super().__init__(parent)
        self.ui = DoctorLabResultUI()
        self.ui.setupUi(self)

        self.checkup_id = checkup_id
        self.refresh_callback = refresh_callback
        self.view = view
        print(parent)
        print(f"Check_Up Id: {self.checkup_id}")

        # Load and display data related to the checkup ID
        self.load_data()
        self.apply_table_styles()
        self.refresh_all_tables()

        if self.view is True:
            self.setup_view()
            self.initialize_diagnosis()
        else:
            self.ui.AddPrescription.clicked.connect(self.open_add_prescription_form)
            self.ui.DiagnoseButton.clicked.connect(self.confirm_and_add_diagnosis)

        self.ui.ViewLabResult.clicked.connect(self.view_file)



    def setup_view(self):
        self.ui.AddPrescription.setVisible(False)
        self.ui.EditPrescription.setVisible(False)
        self.ui.DeletePrescription.setVisible(False)
        self.ui.DiagnoseButton.setVisible(False)
        self.ui.Cancel.setVisible(False)
        self.ui.DiagnoseText.setReadOnly(True)
        self.ui.DiagnoseNotes.setReadOnly(True)

    def initialize_diagnosis(self):
        checkup = CheckUp.get_checkup_details(self.checkup_id)
        if not checkup:
            print('No checkup for checkup id: ' + self.checkup_id)
        diagnosis = checkup.get("chck_diagnoses")
        notes = checkup.get("chck_notes")
        self.ui.DiagnoseText.setText(diagnosis)
        self.ui.DiagnoseNotes.setText(notes)

    def refresh_all_tables(self):
        try:
            print("Refreshing all tables...")
            self.load_lab_attach_table()
            self.load_prescription_table()
            print("All tables refreshed successfully!")
        except Exception as e:
            print(f"Error refreshing all tables: {e}")
            QMessageBox.critical(self, "Error", f"Failed to refresh tables: {e}")

    def apply_table_styles(self):
        self.ui.LabTestTabe.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.ui.LabTestTabe.horizontalHeader().setVisible(True)

        # Align headers to the left
        self.ui.LabTestTabe.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.ui.LabTestTabe.verticalHeader().setVisible(False)

        self.ui.LabTestTabe_2.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.ui.LabTestTabe_2.horizontalHeader().setVisible(True)

        # Align headers to the left
        self.ui.LabTestTabe_2.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.ui.LabTestTabe_2.verticalHeader().setVisible(False)

    def load_lab_attach_table(self):
        try:
            # Clear the table before populating it
            self.ui.LabTestTabe.setRowCount(0)

            # Fetch lab codes and attachments for the given check-up ID
            lab_tests = CheckUp.get_test_by_check_id(self.checkup_id)
            if not lab_tests:
                print(f"No lab tests found for chck_id: {self.checkup_id}")

                # Add a single row with "No Lab Test Request"
                row_position = self.ui.LabTestTabe.rowCount()
                self.ui.LabTestTabe.insertRow(row_position)
                self.ui.LabTestTabe.setItem(row_position, 0, QtWidgets.QTableWidgetItem("No Lab Test Request"))
                self.ui.LabTestTabe.setItem(row_position, 1, QtWidgets.QTableWidgetItem(""))  # Empty attachment status
                return

            for lab_test in lab_tests:
                if isinstance(lab_test, dict):
                    lab_code = lab_test.get('lab_code')
                    lab_attachment = lab_test.get('lab_attachment')
                elif isinstance(lab_test, tuple):
                    # Assume the tuple structure is (lab_code, lab_attachment)
                    if len(lab_test) < 2:
                        print(f"Invalid tuple structure: {lab_test}, Skipping...")
                        continue
                    lab_code, lab_attachment = lab_test[:2]
                else:
                    print(f"Unexpected data type for lab_test: {type(lab_test)}, Skipping...")
                    continue

                # Validate lab_code
                if not lab_code:
                    print(f"Missing lab_code in lab_test: {lab_test}")
                    continue

                # Fetch the lab test name using the lab code
                lab_test_details = Laboratory.get_test_by_lab_code(lab_code)
                if not lab_test_details:
                    print(f"No lab test details found for lab_code: {lab_code}")
                    continue

                if isinstance(lab_test_details, tuple):
                    if len(lab_test_details) > 0 and isinstance(lab_test_details[0], dict):
                        lab_test_details = lab_test_details[0]
                    else:
                        print(f"Invalid tuple structure for lab_code '{lab_code}', Skipping...")
                        continue

                # Validate lab_test_details
                if not isinstance(lab_test_details, dict):
                    print(f"Unexpected return type from get_test_by_labcode: {type(lab_test_details)}, Skipping...")
                    continue

                lab_test_name = lab_test_details.get('lab_test_name', 'Unknown').capitalize()

                # Determine attachment status
                if lab_attachment:
                    # Convert memoryview to string and extract the file name
                    if isinstance(lab_attachment, memoryview):
                        lab_attachment = lab_attachment.tobytes().decode('utf-8')
                    file_name = os.path.basename(lab_attachment)
                    attachment_status = file_name
                else:
                    attachment_status = "No Attach File"

                # Add a new row to the table
                row_position = self.ui.LabTestTabe.rowCount()
                self.ui.LabTestTabe.insertRow(row_position)

                # Insert data into the table
                self.ui.LabTestTabe.setItem(row_position, 0, QtWidgets.QTableWidgetItem(lab_test_name))
                self.ui.LabTestTabe.setItem(row_position, 1, QtWidgets.QTableWidgetItem(attachment_status))

            print("Lab Attach Table loaded successfully!")

        except Exception as e:
            print(f"Error loading lab attach table: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load lab attach table: {e}")

    def load_prescription_table(self):
        """Load and display prescription data in the LabTestTabe_2 table."""
        try:
            # Clear existing rows in the table
            self.ui.LabTestTabe_2.setRowCount(0)

            # Fetch prescriptions for the given check-up ID
            prescriptions = Prescription.display_prescription(self.checkup_id)
            if not prescriptions:
                print(f"No prescriptions found for chck_id: {self.checkup_id}")
                # Add a single row with "No Prescriptions"
                row_position = self.ui.LabTestTabe_2.rowCount()
                self.ui.LabTestTabe_2.insertRow(row_position)
                self.ui.LabTestTabe_2.setItem(row_position, 0, QtWidgets.QTableWidgetItem("No Prescriptions"))
                return

            # Populate the table with prescription details
            for prescription in prescriptions:
                # Extract prescription data
                med_name = prescription.get("pres_medicine", "")
                dosage = prescription.get("pres_dosage", "")
                intake = prescription.get("pres_intake", "")

                # Add a new row to the table
                row_position = self.ui.LabTestTabe_2.rowCount()
                self.ui.LabTestTabe_2.insertRow(row_position)

                # Insert data into the table
                self.ui.LabTestTabe_2.setItem(row_position, 0, QtWidgets.QTableWidgetItem(med_name))
                self.ui.LabTestTabe_2.setItem(row_position, 1, QtWidgets.QTableWidgetItem(dosage))
                self.ui.LabTestTabe_2.setItem(row_position, 2, QtWidgets.QTableWidgetItem(intake))

            print("Prescription Table loaded successfully!")
        except Exception as e:
            print(f"Error loading prescription table: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load prescription table: {e}")

    def load_data(self):
        """Load both check-up and patient details and populate the UI."""
        try:
            # Step 1: Fetch check-up details
            checkup_details = CheckUp.get_checkup_details(self.checkup_id)
            print(checkup_details)
            if not checkup_details:
                raise ValueError("No check-up details found for the given ID.")

            # Extract check-up data
            pat_id = checkup_details['pat_id']
            chck_bp = checkup_details['chck_bp']
            chck_temp = checkup_details['chck_temp']
            chck_height = checkup_details['chck_height' ]
            chck_weight = checkup_details['chck_weight']

            # Step 2: Fetch patient details
            patient_details = Patient.get_patient_details(pat_id)
            print(patient_details)
            if not patient_details:
                raise ValueError("No patient details found for the given ID.")

            # Extract patient data
            pat_lname = patient_details['pat_lname' ]
            pat_fname = patient_details['pat_fname']
            pat_mname = patient_details['pat_mname']
            pat_dob = patient_details['pat_dob']
            pat_gender = patient_details['pat_gender']

            # Calculate age based on date of birth
            age = calculate_age(pat_dob)

            # Convert pat_dob to a string for display
            Birthday = pat_dob.strftime("%Y-%m-%d")

            # Step 3: Populate the UI
            self.populate_patient_info(pat_id,pat_lname, pat_fname, pat_mname, Birthday, age , pat_gender)
            self.populate_checkup_info(chck_bp, chck_temp, chck_height, chck_weight)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    def populate_patient_info(self, pat_id ,pat_lname, pat_fname, pat_mname, pat_dob, age, gender):
        self.ui.PatID.setText(str(pat_id))
        self.ui.PatName.setText(f"{pat_lname}, {pat_fname} {pat_mname}")
        self.ui.PatDoB.setText(pat_dob)
        self.ui.PatAge.setText(str(age))
        self.ui.PatGender.setText(gender)

    def populate_checkup_info(self, chck_bp, chck_temp, chck_height, chck_weight):
        self.ui.BloodPressure.setText(str(chck_bp + " bpm"))
        self.ui.Temperature.setText(str(chck_temp  + " C"))
        self.ui.Height.setText(str(chck_height + " cm"))
        self.ui.Weight.setText(str(chck_weight + " kg"))
        self.ui.CheckUpID.setText(self.checkup_id)

    def view_file(self):
        # Get the currently selected row in the LabTable
        selected_row = self.ui.LabTestTabe.currentRow()
        if selected_row == -1:  # No row selected
            QMessageBox.warning(self, "Selection Error", "Please select a lab test from the table.")
            return

        # Retrieve the lab_test_name from the selected row
        lab_test_name = self.ui.LabTestTabe.item(selected_row, 0).text()

        # Normalize the lab_test_name: strip whitespace and convert to lowercase
        lab_test_name = lab_test_name.strip().lower()

        # Retrieve the lab_code using the normalized lab_test_name
        lab_code = Laboratory.get_lab_code_by_name(lab_test_name)
        if not lab_code:
            QMessageBox.critical(self, "Error", "Failed to retrieve lab code.")
            return

        print(f"Retrieved lab code: {lab_code}")

        # Fetch the file path from the CheckUp model
        file_path = CheckUp.get_lab_attachment(self.checkup_id, lab_code)
        if not file_path:
            QMessageBox.warning(self, "No Attachment", "No file is attached to this lab test.")
            return

        print(f"File path to open: {file_path}")

        # Check if the file exists
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"The file '{file_path}' does not exist.")
            return

        # Open the file using the default application
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            else:  # Unix-like systems
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, file_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def open_add_prescription_form(self):
        print("Opening Add Lab Test Form...")
        try:
            self.add_prescription_window = DoctorAddPrescription(
                chck_id=self.checkup_id,
                parent=self,
                refresh_callback=self.refresh_all_tables
            )
            self.add_prescription_window.show()
            print("Add Lab Test Form shown successfully!")
        except Exception as e:
            print(f"Error opening Add Lab Test Form: {e}")

    def confirm_and_add_diagnosis(self):
        try:
            # Get the diagnosis text and notes from the UI
            chck_diagnoses = self.ui.DiagnoseText.text().strip()
            chck_notes = self.ui.DiagnoseNotes.text().strip() or None

            # Validate the diagnosis text
            if not chck_diagnoses:
                QMessageBox.warning(self, "Validation Error", "Diagnosis text is required.")
                return

            # Show confirmation dialog
            confirmation_dialog = ConfirmationDialog(self)
            if confirmation_dialog.exec_() == QDialog.Rejected:
                print("Diagnosis confirmation cancelled by the user.")
                return

            print("User confirmed diagnosis.")

            # Update the check-up status to "Completed"
            success = CheckUp.change_status_completed(self.checkup_id)
            if not success:
                raise ValueError("Failed to change check-up status to Completed.")

            # Save the diagnosis notes
            success = CheckUp.add_diagnosis_notes(
                chck_id=self.checkup_id,
                chck_diagnoses=chck_diagnoses,
                chck_notes=chck_notes
            )
            if not success:
                raise ValueError("Failed to save diagnosis notes.")

            # Notify the user of success
            QMessageBox.information(self, "Success", "Diagnosis saved successfully!")
            print("Diagnosis saved successfully!")

            # Refresh the tables in the parent window
            if self.refresh_callback:
                self.refresh_callback()

            # Close the modal
            self.close()

            # Open or focus the DoctorRecords window
            self.open_or_focus_doctor_records()

        except Exception as e:
            print(f"Error during diagnosis: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save diagnosis: {e}")

    def open_or_focus_doctor_records(self):
        from Controllers.DoctorRecords_Controller import DoctorRecords
        app = QApplication.instance()  # Get the current application instance


        for widget in app.topLevelWidgets():
            if isinstance(widget, DoctorRecords):
                doctor_records_window = widget
                doctor_records_window.activateWindow()
                doctor_records_window.show()
                print("DoctorRecords window is already active. Bringing it to focus.")
                return  # Exit early since the window is already open

        # If no existing window is found, create a new one
        checkup_details = CheckUp.get_checkup_details(self.checkup_id)
        if not checkup_details or 'doc_id' not in checkup_details:
            print("Error: Invalid or missing check-up details.")
            return

        doc_id = checkup_details['doc_id']
        print(f"Creating new DoctorRecords window for doc_id={doc_id}")

        # Create a new DoctorRecords window and store it as an instance variable
        self.doctor_records_window = DoctorRecords(doc_id=doc_id)  # Persistent reference
        self.doctor_records_window.show()
        print("New DoctorRecords window opened successfully.")
