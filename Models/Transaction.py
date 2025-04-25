from idlelib.pyparse import trans
from typing import final

from Models.DB_Connection import DBConnection

class Transaction:
    @staticmethod
    def add_transaction(chck_id, trans_data):
        conn = DBConnection.get_db_connection()

        if not conn:
            return[]

        try:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO transaction (
                    chck_id, tran_discount, tran_base_charge, tran_lab_charge, tran_status
                    ) VALUES ( %s, %s, %s, %s, %s)
                """

                cursor.execute(query, (
                    chck_id,
                    trans_data ["discount"],
                    trans_data ["base_charge"],
                    trans_data ["lab_charge"],
                    "Completed"
                ))

                conn.commit()
                print("transaction data saved successfully")

        except Exception as e:
            print(f"Database error while creating new patient: {e}")
            conn.rollback()
            return None

        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_all_transaction():
        """Fetch all transactions with their chck_id and tran_status."""
        conn = DBConnection.get_db_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                # Fetch all transactions
                cursor.execute("""
                    SELECT chck_id, tran_status
                    FROM transaction;
                """)

                results = cursor.fetchall()

                # Convert results to a list of dictionaries
                transactions = []
                for row in results:
                    transactions.append({
                        'chck_id': row[0],
                        'tran_status': row[1],
                    })

                # Debug: Log the fetched transactions
                return transactions

        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return []

        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_transaction_by_patient(pat_id):
        """Fetch all transactions with their chck_id and tran_status."""
        conn = DBConnection.get_db_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                # Fetch all transactions
                cursor.execute("""
                            SELECT chck_id, tran_status
                            FROM transaction;
                        """)

                results = cursor.fetchall()

                # Convert results to a list of dictionaries
                transactions = []
                for row in results:
                    transactions.append({
                        'chck_id': row[0],
                        'tran_status': row[1],
                    })

                # Debug: Log the fetched transactions
                return transactions

        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return []

        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_transaction_by_id(transaction_id):
        conn = DBConnection.get_db_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cursor:
                # Fetch the transaction
                cursor.execute("""
                    SELECT chck_id, tran_status, tran_discount, tran_base_charge, tran_lab_charge
                    FROM transaction 
                    WHERE chck_id = %s;
                """, (transaction_id,))

                row = cursor.fetchone()  # Use fetchone() since we're getting a single record

                if not row:
                    return None

                # Convert result to a dictionary
                return {
                    'chck_id': row[0],
                    'tran_status': row[1],
                    'tran_discount': row[2],
                    'tran_base_charge': row[3],
                    'tran_lab_charge': row[4]
                }

        except Exception as e:
            print(f"Error fetching transaction: {e}")
            return None

        finally:
            if conn:
                conn.close()