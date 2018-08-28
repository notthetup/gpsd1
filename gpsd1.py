#
# GPS Daemon for Wemos D1
#

SIM_UART = True
PORT = 2947
SSID = "myssid"
PASS = "lamepassword"

import uerrno as errno
import uasyncio as asyncio

if not SIM_UART:
    from machine import UART
    uart = UART(0, 115200)

clients = []
closed_client = []
msg = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\n"

def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(SSID, PASS)
        while not sta_if.isconnected():
            pass
    print('Connected to WiFi', sta_if.ifconfig())

async def handle_echo(reader, writer):
    clients.append(tuple([reader, writer]))
    print("Client connected", );

async def periodic():
    while True:
        yield from sendToAllClients(msg,clients)
        yield from asyncio.sleep(5)

async def sendToAllClients(msg, clients):
    for client in clients:
        try:
            yield from client[1].awrite(msg)
        except OSError as e:
            if e.args[0] == errno.ECONNRESET or e.args[0] == errno.EPIPE:
                client[1].aclose()
                closed_client.append(client)
    clients = [client for client in clients if client not in closed_client]
    print("Total active clients", len(clients));

async def receiver():
    sreader = asyncio.StreamReader(uart)
    while True:
        res = await sreader.readline()
        if (res):
           sendToAllClients(res, clients)

loop = asyncio.get_event_loop()

if not SIM_UART:
    rec_coro = loop.create_task(receiver())
else:
    rec_coro = loop.create_task(periodic())

server_coro = asyncio.start_server(handle_echo, '0.0.0.0', PORT)
server = loop.run_until_complete(server_coro)

# Serve requests until Ctrl+C is pressed
print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
