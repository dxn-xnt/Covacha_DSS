from datetime import date

from Models.DB_Connection import DBConnection
class Patient:
    @staticmethod
    def get_patient_id(fname, lname):
        conn = DBConnection.get_db_connection()
        if not conn:
            print("Failed to establish database connection.")
            return None

        try:
            with conn.cursor() as cursor:
                query = "SELECT pat_id FROM patient WHERE pat_fname = %s AND pat_lname = %s;"
                cursor.execute(query, (fname, lname))
                result = cursor.fetchone()

                if result:
                    print(f"Found existing patient ID: {result[0]}")
                    return result[0]

                # Patient does not exist
                print("Patient does not exist in the database.")
                return None

        except Exception as e:
            print(f"Error fetching patient ID: {e}")
            return None

        finally:
            if conn:
                conn.close()

    @staticmethod
    def create_new_patient(data):
        conn = DBConnection.get_db_connection()
        if not conn:
            print("Failed to establish database connection.")
            return None

        try:
            with conn.cursor() as cursor:
                # Generate a new patient ID using the sequence
                cursor.execute("SELECT nextval('patient_id_seq');")
                new_pat_id = cursor.fetchone()[0]
                print(f"Generated new patient ID: {new_pat_id}")

                # Insert the new patient record into the database
                query = """
                    INSERT INTO patient (
                        pat_id, pat_lname, pat_fname, pat_mname,
                        pat_address, pat_contact, pat_dob, pat_gender
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    new_pat_id,
                    data["last_name"],
                    data["first_name"],
                    data["middle_name"],
                    data["address"],
                    data["contact"],
                    data["dob"],
                    data["gender"]
                ))

                conn.commit()
                print("New patient data saved successfully.")
                return new_pat_id

        except Exception as e:
            print(f"Database error while creating new patient: {e}")
            conn.rollback()
            return None

        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_patient_details(pat_id):
        conn = DBConnection.get_db_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                        SELECT pat_lname, pat_fname, pat_mname, pat_dob, pat_gender
                        FROM patient
                        WHERE pat_id = %s;
                    """, (pat_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        'pat_lname': result[0],
                        'pat_fname': result[1],
                        'pat_mname': result[2],
                        'pat_dob': result[3],
                        'pat_gender': result[4]
                    }
                return None
        except Exception as e:
            print(f"Error fetching patient details: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_patient_by_id(pat_id):
        conn = DBConnection.get_db_connection()
        if not conn:
            print("Failed to establish database connection.")
            return None

        try:
            with conn.cursor() as cursor:
                # Insert the new patient record into the database
                query = """
                            SELECT pat_id, pat_lname, pat_fname, pat_mname,
                                pat_address, pat_contact, pat_dob, pat_gender
                            FROM patient WHERE pat_id = %s;
                        """
                cursor.execute(query, (pat_id,))
                result = cursor.fetchone()

                if not result:
                    return None

                # Unpack the result tuple
                (id, last_name, first_name, middle_name, address, contact, dob, gender) = result

                # Format names
                last_name = last_name.title() if last_name else ""
                first_name = first_name.title() if first_name else ""
                middle_name = middle_name.title() if middle_name else ""
                # Calculate age if DOB exists
                age = calculate_age(dob)

                return{
                    "id": pat_id,
                    "last_name": last_name or "",
                    "first_name": first_name or "",
                    "middle_name": middle_name or "",
                    "gender": gender or "N/A",
                    "dob": dob or "N/A",
                    "age": age if dob else "N/A",
                    "address": address or "N/A",
                    "contact": contact or "N/A"
                }

        except Exception as e:
            print(f"Database error while creating new patient: {e}")
            return None

        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_all_patients():
        conn = DBConnection.get_db_connection()
        if not conn:
            print("Failed to establish database connection.")
            return None

        try:
            with conn.cursor() as cursor:
                # Insert the new patient record into the database
                query = """
                            SELECT pat_id, pat_lname, pat_fname, pat_mname,
                                pat_address, pat_contact, pat_dob, pat_gender
                            FROM patient;
                        """
                cursor.execute(query)
                rows = cursor.fetchall()

                patients = []
                for row in rows:
                    (pat_id, pat_lname, pat_fname, pat_mname, pat_address, pat_contact, pat_dob, pat_gender) = row
                    # Format names
                    last_name = pat_lname.title() if pat_lname else ""
                    first_name = pat_fname.title() if pat_fname else ""
                    middle_initial = f"{pat_mname[0].upper()}." if pat_mname else ""
                    full_name = f"{last_name}, {first_name} {middle_initial}".strip()

                    patients.append({
                        "id": pat_id,
                        "name": full_name,
                        "gender": pat_gender or "N/A",
                        "dob": pat_dob.strftime('%Y-%m-%d') if pat_dob else "N/A",
                        "age": calculate_age(pat_dob) if pat_dob else "N/A",
                        "address": pat_address or "N/A",
                        "contact": pat_contact or "N/A"
                    })

                conn.commit()

                return patients

        except Exception as e:
            print(f"Database error while creating new patient: {e}")
            conn.rollback()
            return None

        finally:
            if conn:
                conn.close()


def calculate_age(dob):
    """Calculate age from date of birth"""
    if not dob:
        return None
    today = date.today()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age