import requests
import re
from concurrent.futures import ThreadPoolExecutor
import threading
import os


def cargar_proxies(ruta_archivo="Proxie.txt"):
    with open(ruta_archivo, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def scrape_single_proxy(proxy_url, headers, pattern):
    try:
        response = requests.get(proxy_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return re.findall(pattern, response.text)
        return []
    except requests.RequestException:
        return []


def scraping(proxies):
    proxy_list = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}'  # Formato ip:puerto
    lock = threading.Lock()

    def process_proxy(proxy_url):
        proxies = scrape_single_proxy(proxy_url, headers, pattern)
        with lock:
            proxy_list.extend(proxies)

    # Using ThreadPoolExecutor for concurrent scraping
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(process_proxy, proxies)

    return proxy_list


def limpiar_archivo(nombre_archivo):
    """Elimina el contenido del archivo si existe"""
    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, 'w') as f:
            f.write('')


def guardar(nombre_archivo, contenido):
    # Eliminar duplicados antes de guardar
    contenido_unico = list(set(contenido))
    with open(nombre_archivo, 'w') as f:
        for proxy in contenido_unico:
            f.write(proxy + '\n')
    return len(contenido_unico)


def main():
    print("📂 Cargando URLs...")
    txt = cargar_proxies(ruta_archivo="Proxie.txt")
    print(f"✅ {len(txt)} URLs cargadas")

    # Limpiar archivo antes de empezar
    limpiar_archivo("Proxy.txt")

    print("🔍 Scrapeando proxies...")
    sc = scraping(txt)

    # Eliminar duplicados
    sc_unicos = list(set(sc))



    # Si prefieres ordenar por puerto, descomenta esta línea y comenta la anterior
    # sc_ordenados = sorted(sc_unicos, key=lambda x: int(x.split(":")[1]))

    total_guardados = guardar("Proxy.txt", sc_unicos)
     print(f"✅ Scraping finalizado [{len(sc)} → {total_guardados} únicos ordenados] proxies")

    print(f"✅ Scraping finalizado [{len(sc)}] proxies")
