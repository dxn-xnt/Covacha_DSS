import psycopg2

from Models.DB_Connection import DBConnection

class CheckUp:
    @staticmethod
    def get_next_sequence_number(checkup_date):
        conn = DBConnection.get_db_connection()
        if not conn:
            return None
        try:
            with conn.cursor() as cursor:
                sequence_name = f"checkup_seq_{checkup_date.replace('-', '')}"
                cursor.execute(f"""
                    CREATE SEQUENCE IF NOT EXISTS {sequence_name}
                    START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 999 CYCLE;
                """)
                cursor.execute(f"SELECT nextval('{sequence_name}');")
                next_val = cursor.fetchone()[0]
                return f"{next_val:03d}"

        except Exception as e:
            print(f"Error fetching sequence number: {e}")
            return None

        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_lab_attachment(chck_id, lab_code):
        """Retrieve the file path (lab_attachment) for a specific check-up ID and lab code."""
        conn = DBConnection.get_db_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                        SELECT lab_attachment
                        FROM checkup_lab_tests
                        WHERE chck_id = %s AND lab_code = %s;
                    """, (chck_id, lab_code))
                result = cursor.fetchone()

                if result:
                    # Convert memoryview to string if necessary
                    lab_attachment = result[0]
                    if isinstance(lab_attachment, memoryview):
                        lab_attachment = lab_attachment.tobytes().decode('utf-8')
                    return lab_attachment
                return None
        except Exception as e:
            print(f"Error fetching lab attachment: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def save_checkup(data):
        conn = DBConnection.get_db_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cursor:
                print(f"Inserting check-up data: {data}")

                checkup_date = data["date_joined"].replace("-", "")
                sequence_number = CheckUp.get_next_sequence_number(checkup_date)
                if not sequence_number:
                    raise ValueError("Failed to generate sequence number.")

                chck_id = f"{checkup_date}-{sequence_number}"


                query = """
                    INSERT INTO checkup (
                        chck_id, chck_date, chck_status, pat_id,
                        chck_bp, chck_height, chck_weight, chck_temp, staff_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    chck_id,
                    data["date_joined"],
                    "Pending",
                    int(data["id"]),
                    data["bloodpressure"],
                    data["height"],
                    data["weight"],
                    data["temperature"],
                    int(data["staff_id"])
                ))

                conn.commit()
                return True

        except Exception as e:
            print(f"Database error: {e}")
            conn.rollback()
            return False

        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_test_by_check_id(chck_id):
        conn = DBConnection.get_db_connection()
        if not conn:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                        SELECT lab_code, lab_attachment
                        FROM checkup_lab_tests
                        WHERE chck_id = %s;
                    """, (chck_id,))
                result = cursor.fetchall()
                return [
                    {'lab_code': row[0], 'lab_attachment': row[1]}
                    for row in result
                ]
        except Exception as e:
            print(f"Error fetching laboratory test details: {e}")
            return []
        finally:
            if conn:
                conn.close()


    @staticmethod
    def get_checkup_details(checkup_id):
        conn = DBConnection.get_db_connection()
        if not conn:
            return None

        try:
            print(checkup_id, type(checkup_id))
            with conn.cursor() as cursor:
                cursor.execute("""
                        SELECT chck_id, chck_bp, chck_height, chck_weight, chck_temp, pat_id,
                               chck_status, doc_id, chckup_type, chck_date, chck_diagnoses, chck_notes
                        FROM checkup
                        WHERE chck_id = %s;
                    """, (checkup_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        'chck_id': result[0],
                        'chck_bp': result[1],
                        'chck_height': result[2],
                        'chck_weight': result[3],
                        'chck_temp': result[4],
                        'pat_id': result[5],
                        'chck_status': result[6],
                        'doc_id': result[7],
                        'chckup_type': result[8],
                        'chck_date': result[9],
                        'chck_diagnoses': result[10],
                        'chck_notes': result[11]
                    }
                return None
        except Exception as e:
            print(f"Error fetching check-up details: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_checkup_by_pat_id(pat_id):
        conn = None
        try:
            conn = DBConnection.get_db_connection()
            if not conn:
                raise ConnectionError("Failed to establish database connection")

            with conn.cursor() as cursor:
                query = """
                        SELECT 
                            chck_id, chck_date, chck_diagnoses, 
                            chck_bp, chck_height, chck_weight, chck_temp,
                            doc_id, staff_id
                        FROM checkup 
                        WHERE chck_status = 'Completed' AND pat_id = %s
                        ORDER BY chck_date DESC
                        """
                cursor.execute(query, (pat_id,))
                rows = cursor.fetchall()

                checkups = []
                for row in rows:
                    try:
                        (chck_id, chck_date, chck_diagnosis,
                         chck_bp, chck_height, chck_weight, chck_temp,
                         doc_id, staff_id) = row

                        checkups.append({
                            "id": chck_id,
                            "date": chck_date,
                            "diagnosis": chck_diagnosis or "N/A",
                            "bp": chck_bp or "N/A",
                            "height": f"{chck_height} cm" if chck_height else "N/A",
                            "weight": f"{chck_weight} kg" if chck_weight else "N/A",
                            "temp": f"{chck_temp} °C" if chck_temp else "N/A",
                            "staff": staff_id,
                            "doctor": doc_id
                        })
                    except (ValueError, TypeError) as row_error:
                        print(f"Error processing row {row}: {row_error}")
                        continue
                return checkups

        except psycopg2.Error as db_error:
            print(f"Database error fetching checkups: {db_error}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching checkups: {str(e)}")
            return []
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as close_error:
                    print(f"Error closing connection: {close_error}")

    @staticmethod
    def get_all_checkup(self):
        conn = None
        try:
            conn = DBConnection.get_db_connection()
            if not conn:
                raise ConnectionError("Failed to establish database connection")

            with conn.cursor() as cursor:
                query = """
                            SELECT chck_id, chck_date, chck_status, chck_diagnoses, pat_id,
                                   chck_bp, chck_height, chck_weight, chck_temp, staff_id, doc_id
                            FROM check WHERE chck_status = "completed"
                        """
                cursor.execute(query)
                rows = cursor.fetchall()

                checkups = []
                for row in rows:
                    (chck_id, chck_date, chck_status, chck_diagnosis, pat_id,
                     chck_bp, chck_height, chck_weight, chck_temp, staff_id, doc_id) = row

                    checkups.append({
                        "id": chck_id,
                        "date": chck_date,
                        "diagnosis": chck_diagnosis,
                        "bp": chck_bp or "N/A",
                        "height": chck_height or "N/A",
                        "weight": chck_weight or "N/A",
                        "temp": chck_temp or "N/A",
                        "patient": pat_id,
                        "doctor": doc_id
                    })

                return checkups

        except Exception as e:
            print(f"Error fetching doctors: {str(e)}")
            return []

        finally:
            if conn:
                conn.close()