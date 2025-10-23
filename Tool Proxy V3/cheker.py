import time
import aiohttp
import asyncio
import tqdm
import os
import random
from aiohttp_socks import ProxyConnector

# URL objetivo
timeOut = 15
target_url = ""

# Lista de User-Agents variados
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 12; Mobile; rv:118.0) Gecko/118.0 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
]

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
            headers = {
                "User-Agent": random.choice(user_agents)
            }
            try:
                if tipo in ["socks4", "socks5"]:
                    connector = ProxyConnector.from_url(f"{tipo}://{proxy}")
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get(target_url, headers=headers, timeout=timeOut) as resp:
                            if resp.status == 200:
                                clasificados[tipo].append(proxy)
                                await guardar_proxy_instantaneo(tipo, proxy)
                                break
                else:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(target_url, proxy=f"{tipo}://{proxy}", headers=headers, timeout=timeOut) as resp:
                            if resp.status == 200:
                                clasificados[tipo].append(proxy)
                                await guardar_proxy_instantaneo(tipo, proxy)
                                break
            except:
                pass
            finally:
                barra.update(1)
                barra.set_postfix({k: len(v) for k, v in clasificados.items()})

# Iterar sobre proxies
async def iterar(lista_proxies, tipos_a_probar):
    sem = asyncio.Semaphore(800)
    barra = tqdm.tqdm(total=len(lista_proxies) * len(tipos_a_probar), desc="Validando")
    clasificados = {tipo: [] for tipo in tipos_a_probar}
    tasks = [peticiones(proxy, sem, barra, clasificados, tipos_a_probar) for proxy in lista_proxies]
    await asyncio.gather(*tasks)
    barra.close()
    return clasificados

# Cargar proxies desde archivo
async def cargar(nombre_archivo):
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            return [linea.strip() for linea in archivo if linea.strip()]
    except FileNotFoundError:
        print(f"No se encontró el archivo: {nombre_archivo}")
        return []

# Menú de selección
def seleccionar_tipos():
    print("\n📌 Selecciona el tipo de proxy a validar:")
    print("1. Solo HTTP")
    print("2. Solo SOCKS4")
    print("3. Solo SOCKS5")
    print("4. Todos (HTTP + SOCKS4 + SOCKS5)")
    print("Url: "+target_url)
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

# Flujo principal
def start():
    global target_url  # ⚠️ IMPORTANTE: Declarar como global
    global timeOut
    target_url = input("🌐 Ingrese la URL a CHEKING: ").strip()
    timeOut = int(input("⏱️ Ingrese el tiempo de espera (por defecto 15): ").strip() or 15)
    tipos_a_probar = seleccionar_tipos()
    lista = asyncio.run(cargar("Proxy.txt"))
    tiempo_inicio = time.time()
    clasificados = asyncio.run(iterar(lista, tipos_a_probar))
    tiempo_fin = time.time()

    total = sum(len(v) for v in clasificados.values())
    print(f"\n✅ Se encontraron {total} proxies válidos en {tiempo_fin - tiempo_inicio:.2f} segundos")
    for tipo, proxies in clasificados.items():
        print(f"{tipo.upper()} válidos: {len(proxies)}")

