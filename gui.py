import tkinter as tk
from tkinter import ttk
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import analyzer

root = tk.Tk()
root.title("So1icitx")
root.geometry("1000x700")
root.configure(bg="#1a1a1a")

conn = sqlite3.connect("[DIRECTORY]/siem.db")  # Replace [DIRECTORY] with your project path (e.g., /home/darklord/SIEM)
cursor = conn.cursor()

alert_frame = tk.Frame(root, bg="#1a1a1a")
alert_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
graph_frame = tk.Frame(root, bg="#1a1a1a")
graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

alert_list = ttk.Treeview(alert_frame, columns=("ID", "Time", "IP", "Desc", "Status"), show="headings", height=20)
alert_list.heading("ID", text="ID")
alert_list.heading("Time", text="Time")
alert_list.heading("IP", text="IP")
alert_list.heading("Desc", text="Description")
alert_list.heading("Status", text="Status")
alert_list.column("ID", width=50)
alert_list.column("Time", width=150)
alert_list.column("IP", width=100)
alert_list.column("Desc", width=250)
alert_list.column("Status", width=100)
scrollbar = ttk.Scrollbar(alert_frame, orient="vertical", command=alert_list.yview)
alert_list.configure(yscrollcommand=scrollbar.set)
alert_list.pack(side=tk.LEFT, fill=tk.Y)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def mark_status(status):
    selected = alert_list.selection()
    if selected:
        alert_id = alert_list.item(selected)["values"][0]
        if status == "Safe":
            cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
            conn.commit()
        else:
            cursor.execute("UPDATE alerts SET status = ? WHERE id = ?", (status, alert_id))
            conn.commit()
        update_alerts()

btn_threat = tk.Button(alert_frame, text="Mark Threat", command=lambda: mark_status("Threat"), bg="#ff4444", fg="white", font=("Arial", 10, "bold"))
btn_threat.pack(pady=5)
btn_safe = tk.Button(alert_frame, text="Mark Safe (Remove)", command=lambda: mark_status("Safe"), bg="#44ff44", fg="black", font=("Arial", 10, "bold"))
btn_safe.pack(pady=5)
btn_ignore = tk.Button(alert_frame, text="Mark Ignore", command=lambda: mark_status("Ignore"), bg="#aaaaaa", fg="black", font=("Arial", 10, "bold"))
btn_ignore.pack(pady=5)

fig, ax = plt.subplots(figsize=(6, 5))
canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def update_alerts():
    alert_list.delete(*alert_list.get_children())
    cursor.execute("SELECT * FROM alerts")
    for row in cursor.fetchall():
        alert_list.insert("", "end", values=row)
    if alert_list.get_children():
        alert_list.see(alert_list.get_children()[-1])

def update_graph():
    cursor.execute("SELECT source_ip, COUNT(*) FROM logs GROUP BY source_ip")
    data = cursor.fetchall()
    ips, counts = zip(*data) if data else ([], [])
    ax.clear()
    ax.bar(ips, counts, color="#00ff00", width=0.5)
    ax.set_title("Events by IP", color="white", fontsize=12)
    ax.set_xlabel("IP Address", color="white", fontsize=10)
    ax.set_ylabel("Event Count", color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=8)
    plt.xticks(rotation=45, ha="right")
    ax.set_facecolor("#333333")
    fig.set_facecolor("#1a1a1a")
    canvas.draw()

def refresh():
    update_alerts()
    update_graph()
    root.after(3000, refresh)

threading.Thread(target=analyzer.main, daemon=True).start()

refresh()
root.mainloop()
