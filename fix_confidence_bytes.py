import sqlite3

DB_PATH = 'attendance.db'

def fix_confidence_bytes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, confidence FROM attendance')
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        row_id, confidence = row
        if isinstance(confidence, bytes):
            try:
                conf_str = confidence.decode('utf-8')
                conf_float = float(conf_str)
                cursor.execute('UPDATE attendance SET confidence = ? WHERE id = ?', (conf_float, row_id))
                updated += 1
            except Exception as e:
                print(f'Could not fix row {row_id}: {e}')
    conn.commit()
    print(f'Updated {updated} rows.')
    conn.close()

if __name__ == '__main__':
    fix_confidence_bytes() 