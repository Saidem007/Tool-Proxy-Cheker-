import time
import aiohttp
import asyncio
import tqdm
import os
from aiohttp_socks import ProxyConnector
import json

from Scraping_proxie import guardar

# URL objetivo
timeaOut= 15
statuscode= 200
api_url= ""

headers = {}

payload = {}
# Menú de selección
def copiar_url():
    global api_url
    with open("API/URL.txt", 'r', encoding='utf-8') as file:
        api_url = file.read().strip()

def copiar_headers():
    global headers
    with open("API/Headers.txt", 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line and ':' in line:
                clave, valor = line.split(':', 1)
                headers[clave.strip()] = valor.strip()

def copiar_payload():
    global payload
    with open('API/Payload.json', 'r', encoding='utf-8') as file:
        payload = json.load(file)
    return payload
def seleccionar_tipos():
    print("\n📌 Selecciona el tipo de proxy a validar:")
    print("1. Solo HTTP")
    print("2. Solo SOCKS4")
    print("3. Solo SOCKS5")
    print("4. Todos (HTTP + SOCKS4 + SOCKS5)")
    opcion = input("👉 Opción (1-4): ").strip()

    if opcion == "1":
        return ["http"]
    elif opcion == "2":
        return ["socks4"]
    elif opcion == "3":
        return ["socks5"]
    elif opcion == "4":
        return ["http", "socks4", "socks5"]
    else:
        print("❌ Opción inválida. Usando todos por defecto.")
        return ["http", "socks4", "socks5"]

# Carga y limpieza de proxies
async def cargar(nombre_archivo):
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            return list(set([linea.strip() for linea in archivo if linea.strip()]))
    except FileNotFoundError:
        print(f"No se encontró el archivo: {nombre_archivo}")
        return []

# Lock global para escritura concurrente
write_lock = asyncio.Lock()

# Guardar proxy válido al instante
async def guardar_proxy_instantaneo(tipo, proxy):
    carpeta = "valid"
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"Proxys_{tipo.upper()}.txt")
    async with write_lock:
        with open(ruta, 'a', encoding='utf-8') as f:
            f.write(f"{proxy}\n")

# Validar proxy por tipo
async def peticiones(proxy, sem, barra, clasificados, tipos_a_probar):
    async with sem:
        for tipo in tipos_a_probar:
            try:
                if tipo in ["socks4", "socks5"]:
                    connector = ProxyConnector.from_url(f"{tipo}://{proxy}")
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.post(api_url, headers=headers, json=payload, timeout=timeaOut) as resp:
                            if resp.status == statuscode:
                                clasificados[tipo].append(proxy)
                                await guardar_proxy_instantaneo(tipo, proxy)
                                break
                else:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(api_url, proxy=f"{tipo}://{proxy}", headers=headers, json=payload, timeout=5) as resp:
                            if resp.status == 201:
                                clasificados[tipo].append(proxy)
                                await guardar_proxy_instantaneo(tipo, proxy)
                                break
            except:
                pass
            finally:
                barra.update(1)
                barra.set_postfix({k.upper(): len(v) for k, v in clasificados.items()})

# Iterar sobre proxies
async def iterar(lista_proxies, tipos_a_probar):
    sem = asyncio.Semaphore(800)
    barra = tqdm.tqdm(total=len(lista_proxies), desc="🔍 Validando", ncols=100)
    clasificados = {tipo: [] for tipo in tipos_a_probar}
    tareas = [peticiones(proxy, sem, barra, clasificados, tipos_a_probar) for proxy in lista_proxies]
    await asyncio.gather(*tareas)
    barra.close()
    return clasificados

# Flujo principal
def start():
    global timeaOut
    global statuscode
    copiar_url()
    copiar_headers()
    copiar_payload()
    tipos_a_probar = seleccionar_tipos()
    entrada = input("Ingrese status code esperado (por defecto 200): ").strip()
    statuscode = int(entrada) if entrada else 200
    timeaOut= int(input("Ingrese el tiempo de espera en segundos (por defecto 15): ").strip() or 15)

    lista = asyncio.run(cargar("Proxy.txt"))
    tiempo_inicio = time.time()
    clasificados = asyncio.run(iterar(lista, tipos_a_probar))
    tiempo_fin = time.time()

    total = sum(len(v) for v in clasificados.values())
    print(f"\n✅ Se encontraron {total} proxies válidos en {tiempo_fin - tiempo_inicio:.2f} segundos")
    for tipo, proxies in clasificados.items():
        print(f"{tipo.upper()} válidos: {len(proxies)}")

