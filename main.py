#
# GPS Daemon for Wemos D1
#
import uos as os
os.dupterm(None, 0)

LED_PIN = 2
PORT = 2947
SSID = "myssid"
PASS = "lamepassword"
# FILTER_NMEA = []
FILTER_NMEA = ["$GPRMC", "$GPGGA", "$GNGGA"]
UART_DELAY = 0.01

import time
import uerrno as errno
import uasyncio as asyncio
from machine import Pin
from machine import UART

pkts = 0
clients = []
closed_client = []

def toggle_led():
    if led.value() == 1:
        led.value(0)
    else:
        led.value(1)

def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(SSID, PASS)
        while not sta_if.isconnected():
            pass
    print('Connected to WiFi', sta_if.ifconfig())

async def handle_conn(reader, writer):
    clients.append(tuple([reader, writer]))
    print("Client connected", );

async def sendToAllClients(msg, clients):
    for client in clients:
        try:
            await client[1].awrite(msg)
        except OSError as e:
            if e.args[0] == errno.ECONNRESET or e.args[0] == errno.EPIPE:
                client[1].aclose()
                closed_client.append(client)
    clients = [client for client in clients if client not in closed_client]

async def receiver():
    sreader = asyncio.StreamReader(uart)
    while True:
        res = await sreader.readline()
        if (res):
            res_str = res.decode('utf-8')
            if len(FILTER_NMEA) == 0 or any(nmea for nmea in FILTER_NMEA if res_str.startswith(nmea)):
                await sendToAllClients(res_str, clients)
                toggle_led()
        await asyncio.sleep(UART_DELAY)

# do_connect()
uart = UART(0, 9600);
loop = asyncio.get_event_loop()
led = Pin(LED_PIN,Pin.OUT)
led.value(1)
time.sleep(1)
led.value(0)

rec_coro = loop.create_task(receiver())
server_coro = asyncio.start_server(handle_conn, '0.0.0.0', PORT)
server = loop.call_soon(server_coro)

# Serve requests until Ctrl+C is pressed
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
