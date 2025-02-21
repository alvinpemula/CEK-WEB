import requests
import threading
import time
import os
import json
import socket
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live

# Inisialisasi Console Rich
console = Console()

# Bersihkan layar
os.system("clear" if os.name == "posix" else "cls")

# Tampilan Awal (Langsung Ditampilkan)
console.print(Panel("[bold red]🔥 SUPER LOAD TESTER ULTRA PRO MAX 🔥[/bold red]\n[bold cyan]by Alvin[/bold cyan]", expand=False))

# Masukkan URL
console.print(Panel("[bold cyan]Masukkan URL website yang ingin diuji:[/bold cyan]"))
URL = console.input("[bold yellow]>> [/bold yellow]").strip()

if not URL.startswith(("http://", "https://")):
    URL = "https://" + URL

# Mengecek Status Website
console.print(Panel("[bold yellow]🔍 Mengecek status website...[/bold yellow]"))
try:
    response = requests.get(URL, timeout=5)
    if response.status_code == 200:
        console.print("[bold green]✅ Website aktif![/bold green]")
    else:
        console.print(f"[bold yellow]⚠️ Website merespon dengan status {response.status_code}[/bold yellow]")
except:
    console.print("[bold red]❌ Website tidak dapat diakses![/bold red]")
    exit()

# Mengecek Latensi Website
console.print(Panel("[bold yellow]🔍 Mengecek latensi website...[/bold yellow]"))
hostname = URL.replace("https://", "").replace("http://", "").split("/")[0]
try:
    ip = socket.gethostbyname(hostname)
    ping_start = time.time()
    requests.get(URL, timeout=5)
    ping_end = time.time()
    latency = (ping_end - ping_start) * 1000
    console.print(f"[bold cyan]📡 Ping ke {hostname} ({ip}): {latency:.2f} ms[/bold cyan]")
except:
    console.print("[bold red]❌ Tidak dapat mengukur latensi![/bold red]")

# Informasi Server
server_info = response.headers.get("Server", "Tidak diketahui")
content_length = response.headers.get("Content-Length", "Tidak diketahui")
if content_length != "Tidak diketahui":
    content_length = f"{int(content_length) / 1024:.2f} KB"

console.print(Panel(f"🖥️ [bold cyan]Informasi Server:[/bold cyan]\nServer: {server_info}\nUkuran Response: {content_length}"))

# Pilih Mode Pengujian
console.print(Panel("[bold magenta]Pilih mode pengujian:\n1. Normal (1000 request)\n2. Brutal (10000 request)\n3. Max Destruction (100000 request)[/bold magenta]"))
mode = int(console.input("[bold yellow]>> [/bold yellow]").strip())

TOTAL_REQUESTS = {1: 1000, 2: 10000, 3: 100000}.get(mode, 1000)

# Masukkan Jumlah Thread
console.print(Panel("[bold yellow]Masukkan jumlah thread (lebih banyak = lebih cepat, tapi bisa memberatkan server!):[/bold yellow]"))
THREADS = int(console.input("[bold yellow]>> [/bold yellow]").strip())

# Statistik
success = 0
fail = 0
active_threads = 0
lock = threading.Lock()
session = requests.Session()

# Fungsi untuk update tabel real-time
def generate_table():
    table = Table(title="📊 Status Pengujian (Real-Time)", style="bold green")
    table.add_column("✅ Request Berhasil", style="bold cyan", justify="center")
    table.add_column("❌ Request Gagal", style="bold red", justify="center")
    table.add_column("🔄 Threads Aktif", style="bold yellow", justify="center")
    
    with lock:
        table.add_row(str(success), str(fail), str(active_threads))

    return table

# Fungsi untuk mengirim request
def send_request():
    global success, fail, active_threads
    retries = 3

    with lock:
        active_threads += 1

    while retries > 0:
        try:
            response = session.get(URL, timeout=5)
            with lock:
                if response.status_code == 200:
                    success += 1
                else:
                    fail += 1
            break  # Berhenti jika berhasil
        except:
            retries -= 1

    with lock:
        active_threads -= 1

# Menjalankan Load Test
console.print(Panel(f"🔥 [bold red]Menjalankan Load Testing ke {URL} dengan {TOTAL_REQUESTS} request menggunakan {THREADS} thread...[/bold red]"))
start = time.time()

with Live(generate_table(), refresh_per_second=1) as live:
    threads = []
    for _ in range(TOTAL_REQUESTS):
        thread = threading.Thread(target=send_request)
        thread.start()
        threads.append(thread)

        if len(threads) >= THREADS:
            for t in threads:
                t.join()
            threads = []

        live.update(generate_table())

    for t in threads:
        t.join()

end = time.time()

# Hasil Akhir
average_time = (end - start) / TOTAL_REQUESTS * 1000 if TOTAL_REQUESTS else 0
speed = TOTAL_REQUESTS / (end - start)

if average_time < 100:
    server_status = "[bold green]🟢 Server Sehat[/bold green]"
elif average_time < 500:
    server_status = "[bold yellow]🟠 Server Lemot[/bold yellow]"
else:
    server_status = "[bold red]🔴 Server Bisa Down![/bold red]"

# Tampilkan Hasil Akhir
result_table = Table(title="📊 Hasil Load Testing", style="bold green")
result_table.add_column("📌 Keterangan", style="bold cyan", justify="left")
result_table.add_column("🔢 Data", style="bold white", justify="right")

result_table.add_row("✅ Request Berhasil", str(success))
result_table.add_row("❌ Request Gagal", str(fail))
result_table.add_row("⏳ Rata-rata Response Time", f"{average_time:.2f} ms")
result_table.add_row("⚡ Kecepatan Request", f"{speed:.2f} req/detik")
result_table.add_row("📡 Status Server", server_status)
result_table.add_row("⏱️ Total Waktu", f"{end - start:.2f} detik")

console.print(result_table)

# Simpan hasil ke JSON
result_data = {
    "URL": URL,
    "Total Requests": TOTAL_REQUESTS,
    "Threads": THREADS,
    "Request Berhasil": success,
    "Request Gagal": fail,
    "Response Time Rata-rata": average_time,
    "Kecepatan Request": speed,
    "Status Server": server_status,
    "Total Waktu": end - start
}

with open("load_test_result.json", "w") as f:
    json.dump(result_data, f, indent=4)

console.print(Panel(f"📁 [bold cyan]Hasil pengujian telah disimpan di load_test_result.json[/bold cyan]"))
