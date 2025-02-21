import requests
import threading
import time
import os
import json
import socket
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TimeRemainingColumn
from rich.text import Text

console = Console()

# Bersihkan layar sebelum meminta input
os.system("clear")

# Tampilan Profesional
console.print(Panel("[bold red]🔥 SUPER LOAD TESTER ULTRA PRO MAX 🔥[/bold red]\n[bold cyan]by Alvin[/bold cyan]", expand=False))

# Input URL
console.print(Panel("[bold cyan]Masukkan URL website yang ingin diuji:[/bold cyan]"), end=" ")
URL = input().strip()

if not URL.startswith(("http://", "https://")):
    URL = "https://" + URL

# Auto-detect apakah website aktif
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

# Ping ke website
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

# Menampilkan informasi server
server_info = response.headers.get("Server", "Tidak diketahui")
content_length = response.headers.get("Content-Length", "Tidak diketahui")
if content_length != "Tidak diketahui":
    content_length = f"{int(content_length) / 1024:.2f} KB"

console.print(Panel(f"🖥️ [bold cyan]Informasi Server:[/bold cyan]\nServer: {server_info}\nUkuran Response: {content_length}"))

# Pilih mode uji coba
console.print(Panel("[bold magenta]Pilih mode pengujian:\n1. Normal (1000 request)\n2. Brutal (10000 request)\n3. Max Destruction (100000 request)[/bold magenta]"), end=" ")
mode = int(input().strip())

if mode == 1:
    TOTAL_REQUESTS = 1000
elif mode == 2:
    TOTAL_REQUESTS = 10000
else:
    TOTAL_REQUESTS = 100000

console.print(Panel("[bold yellow]Masukkan jumlah thread (lebih banyak = lebih cepat, tapi bisa memberatkan server!):[/bold yellow]"), end=" ")
THREADS = int(input().strip())

# Statistik
success = 0
fail = 0
status_codes = {}
response_times = []
lock = threading.Lock()

# Buat session biar lebih cepat
session = requests.Session()

# Fungsi pengiriman request
def send_request(progress, task):
    global success, fail
    retries = 3
    while retries > 0:
        try:
            start_time = time.time()
            response = session.get(URL, timeout=5)
            elapsed_time = (time.time() - start_time) * 1000  # Convert ke ms
            
            with lock:
                response_times.append(elapsed_time)
                status_codes[response.status_code] = status_codes.get(response.status_code, 0) + 1
                if response.status_code == 200:
                    success += 1
                    console.print(f"[bold green]✅ Request sukses! {response.status_code} ({elapsed_time:.2f} ms)[/bold green]")
                else:
                    fail += 1
                    console.print(f"[bold yellow]⚠️ Request gagal! {response.status_code} ({elapsed_time:.2f} ms)[/bold yellow]")

            progress.update(task, advance=1)
            return  
        except Exception as e:
            retries -= 1
            console.print(f"[bold red]❌ Request error: {str(e)}. Retry {retries}x lagi...[/bold red]")

    with lock:
        fail += 1
    progress.update(task, advance=1)

# Menjalankan uji coba
def run_test():
    with Progress(
        "[bold green]{task.description}",
        BarColumn(),
        "[bold yellow]{task.completed}/{task.total} Request",
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("📡 Mengirim Request...", total=TOTAL_REQUESTS)

        threads = []
        for _ in range(TOTAL_REQUESTS):
            thread = threading.Thread(target=send_request, args=(progress, task))
            thread.start()
            threads.append(thread)

            if len(threads) >= THREADS:
                for t in threads:
                    t.join()
                threads = []

        for t in threads:
            t.join()

console.print(Panel(f"🔥 [bold red]Menjalankan Load Testing ke {URL} dengan {TOTAL_REQUESTS} request menggunakan {THREADS} thread...[/bold red]"))
start = time.time()
run_test()
end = time.time()

# Hasil akhir
average_time = sum(response_times) / len(response_times) if response_times else 0
speed = TOTAL_REQUESTS / (end - start)

# Status server
if average_time < 100:
    server_status = "[bold green]🟢 Server Sehat[/bold green]"
elif average_time < 500:
    server_status = "[bold yellow]🟠 Server Lemot[/bold yellow]"
else:
    server_status = "[bold red]🔴 Server Bisa Down![/bold red]"

# Menampilkan hasil
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

# Simpan hasil dalam JSON
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
