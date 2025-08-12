import sqlite3

DB_PATH = 'attendance.db'

def delete_corrupt_attendance():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, confidence FROM attendance')
    rows = cursor.fetchall()
    to_delete = []
    for row in rows:
        row_id, confidence = row
        # Try to convert to float, if fails, mark for deletion
        try:
            if isinstance(confidence, bytes):
                # Try to decode as utf-8, if fails, mark for deletion
                conf_str = confidence.decode('utf-8')
                float(conf_str)
            else:
                float(confidence)
        except Exception:
            to_delete.append(row_id)
    for row_id in to_delete:
        cursor.execute('DELETE FROM attendance WHERE id = ?', (row_id,))
    conn.commit()
    print(f'Deleted {len(to_delete)} corrupt rows.')
    conn.close()

if __name__ == '__main__':
    delete_corrupt_attendance() 