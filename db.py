# db.py - MariaDB/MySQL compatible version using PyMySQL

import pymysql
from datetime import datetime, timedelta

class Database:
    def __init__(self, host, user, password, database):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'autocommit': True,
            'cursorclass': pymysql.cursors.DictCursor
        }
        self.conn = None
        self.cursor = None

    def _connect(self):
        self.conn = pymysql.connect(**self.config)
        self.cursor = self.conn.cursor()

    def _disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def initialize(self):
        self._connect()
        # สร้างตารางถ้ายังไม่มี
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INT AUTO_INCREMENT PRIMARY KEY,
            camera_id VARCHAR(100) NOT NULL,
            timestamp DATETIME NOT NULL,
            confidence FLOAT NOT NULL,
            image_path TEXT,
            created_at DATETIME NOT NULL
        )
        ''')
        
        self.cursor.execute('''
            SELECT COUNT(1) AS idx_exists
            FROM information_schema.statistics 
            WHERE table_schema = %s AND table_name = 'detections' AND index_name = 'idx_camera_timestamp'
        ''', (self.config['database'],))
        exists = self.cursor.fetchone()
        if exists['idx_exists'] == 0:
            self.cursor.execute('''
                CREATE INDEX idx_camera_timestamp 
                ON detections (camera_id, timestamp)
            ''')
        self._disconnect()

    def add_detection(self, camera_id, timestamp, confidence, image_path=""):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self._connect()
        self.cursor.execute('''
            INSERT INTO detections (camera_id, timestamp, confidence, image_path, created_at)
            VALUES (%s, %s, %s, %s, %s)
        ''', (camera_id, timestamp, confidence, image_path, created_at))
        self._disconnect()


    def get_recent_detections(self, camera_id, limit=10):
        self._connect()
        self.cursor.execute('''
            SELECT * FROM detections WHERE camera_id = %s 
            ORDER BY timestamp DESC LIMIT %s
        ''', (camera_id, limit))
        results = self.cursor.fetchall()
        self._disconnect()
        return results

    def get_recent_detections_all(self, limit=20):
        self._connect()
        self.cursor.execute('''
            SELECT * FROM detections 
            ORDER BY timestamp DESC LIMIT %s
        ''', (limit,))
        results = self.cursor.fetchall()
        self._disconnect()
        return results

    def get_detection_counts(self, camera_id):
        self._connect()
        self.cursor.execute('''
            SELECT COUNT(*) AS person_count FROM detections WHERE camera_id = %s
        ''', (camera_id,))
        result = self.cursor.fetchone()
        self._disconnect()
        return {"person": result['person_count'] if result else 0}

    def get_total_counts(self):
        self._connect()
        self.cursor.execute('''
            SELECT camera_id, COUNT(*) AS count FROM detections GROUP BY camera_id
        ''')
        results = {row['camera_id']: row['count'] for row in self.cursor.fetchall()}
        self.cursor.execute('SELECT COUNT(*) AS total FROM detections')
        results['total'] = self.cursor.fetchone()['total']
        self._disconnect()
        return results

    def get_all_detections(self):
        self._connect()
        self.cursor.execute('''
            SELECT * FROM detections ORDER BY timestamp DESC
        ''')
        results = self.cursor.fetchall()
        self._disconnect()
        return results

    def get_detections_by_date(self, date):
        self._connect()
        self.cursor.execute('''
            SELECT * FROM detections 
            WHERE DATE(timestamp) = %s
            ORDER BY timestamp DESC
        ''', (date,))
        results = self.cursor.fetchall()
        self._disconnect()
        return results

    def delete_old_detections(self, days=30):
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        self._connect()
        self.cursor.execute('''
            DELETE FROM detections WHERE DATE(timestamp) < %s
        ''', (cutoff_date,))
        deleted_count = self.cursor.rowcount
        self._disconnect()
        return deleted_count