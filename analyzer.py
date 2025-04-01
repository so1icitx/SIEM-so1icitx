import re
import sqlite3
from collections import defaultdict
import time

def main():
    conn = sqlite3.connect("[DIRECTORY]/siem.db")  # Replace [DIRECTORY] with your project path (e.g., /home/darklord/SIEM)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, timestamp TEXT, source_ip TEXT, event TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY, timestamp TEXT, source_ip TEXT, description TEXT, status TEXT DEFAULT 'Pending')")
    conn.commit()

    failed_logins = defaultdict(int)

    def analyze_log_line(line):
        print(f"Line read: {line.strip()}")
        if "Failed password" in line:
            ip_match = re.search(r"from (\d+\.\d+\.\d+\.\d+)", line)
            if ip_match:
                ip = ip_match.group(1)
                failed_logins[ip] += 1
                print(f"Detected failed login from {ip}, count: {failed_logins[ip]}")
                cursor.execute("INSERT INTO logs (timestamp, source_ip, event) VALUES (datetime('now'), ?, ?)", (ip, "Failed password attempt"))
                if failed_logins[ip] > 5:
                    print(f"Alert triggered for {ip}")
                    print("\a")
                    cursor.execute("INSERT INTO alerts (timestamp, source_ip, description) VALUES (datetime('now'), ?, ?)", (ip, f"Possible brute force: {failed_logins[ip]} attempts"))
                conn.commit()
        elif "message repeated" in line:
            repeat_match = re.search(r"message repeated (\d+) times: \[ Failed password for .* from (\d+\.\d+\.\d+\.\d+)", line)
            if repeat_match:
                repeat_count = int(repeat_match.group(1))
                ip = repeat_match.group(2)
                failed_logins[ip] += repeat_count
                print(f"Detected {repeat_count} repeated failed logins from {ip}, total: {failed_logins[ip]}")
                for _ in range(repeat_count):
                    cursor.execute("INSERT INTO logs (timestamp, source_ip, event) VALUES (datetime('now'), ?, ?)", (ip, "Failed password attempt (repeated)"))
                if failed_logins[ip] > 5:
                    print(f"Alert triggered for {ip}")
                    print("\a")
                    cursor.execute("INSERT INTO alerts (timestamp, source_ip, description) VALUES (datetime('now'), ?, ?)", (ip, f"Possible brute force: {failed_logins[ip]} attempts"))
                conn.commit()

    with open("/var/log/auth.log", "r") as f:  # System log path - adjust if your log file is elsewhere
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            analyze_log_line(line)

if __name__ == "__main__":
    main()
