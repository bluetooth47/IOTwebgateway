import network

import socket

import time

from machine import Pin

 

# --- 1. Hardware Configuration ---

relay = Pin(14, Pin.OUT)

 

# --- 2. Network Configuration ---

SSID = "cmap2551"

PASSWORD = "25512551"

 

wlan = network.WLAN(network.STA_IF)

wlan.active(True)

wlan.connect(SSID, PASSWORD)

 

print(f"Booting IoT Gateway. Connecting to {SSID}...")

while not wlan.isconnected():

    print(".", end="")

    time.sleep(0.5)

 

gateway_ip = wlan.ifconfig()[0]

print(f"\n[SYSTEM ONLINE] Access the dashboard at: http://{gateway_ip}")

 

# --- 3. The Front-End (HTML Generator) ---

def web_page():

    """Generates the HTML dashboard dynamically based on the current hardware state."""

   

    # Check the physical pin to see if it is currently on or off

    if relay.value() == 1:

        relay_state = "ONLINE"

    else:

        relay_state = "OFFLINE"

       

    # We use a multi-line string (""") to write standard HTML

    html = f"""

    <!DOCTYPE html>

    <html>

    <head>

        <title>NOC IoT Gateway</title>

        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>

            body {{ font-family: Arial; text-align: center; margin-top: 50px; background-color: #121212; color: white; }}

            .btn {{ padding: 15px 40px; font-size: 24px; margin: 10px; cursor: pointer; border: none; border-radius: 5px; }}

            .btn-on {{ background-color: #28a745; color: white; }}

            .btn-off {{ background-color: #dc3545; color: white; }}

            .status {{ font-size: 30px; font-weight: bold; margin-bottom: 30px; }}

        </style>

    </head>

    <body>

        <h1>Remote Hardware Override</h1>

        <div class="status">Current Status: {relay_state}</div>

       

        <a href="/?relay=on"><button class="btn btn-on">SYSTEM ON</button></a>

        <a href="/?relay=off"><button class="btn btn-off">SYSTEM OFF</button></a>

    </body>

    </html>

    """

    return html

 

# --- 4. The Socket Server ---

# Create an INET (IPv4), STREAMing (TCP) socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

 

# Bind the socket to all available interfaces ('') on Port 80 (HTTP)

s.bind(('', 80))

 

# Start listening for incoming browser connections (max 5 in queue)

s.listen(5)

 

# --- 5. The Main Server Loop ---

while True:

    try:

        # .accept() pauses the loop until a web browser connects

        conn, addr = s.accept()

        print(f"\n[+] Incoming connection from client: {addr}")

       

        # Receive the raw HTTP request from the browser (1024 bytes is enough for GET)

        request = conn.recv(1024).decode('utf-8')

       

        # DANGER: Sometimes browsers open empty connections. If request is blank, skip it.

        if not request:

            conn.close()

            continue

 

        # Parse the HTTP request to see which button was clicked

        # The request will look like: "GET /?relay=on HTTP/1.1..."

        if '/?relay=on' in request:

            print("Command Received: Activating Relay.")

            relay.value(1)

        if '/?relay=off' in request:

            print("Command Received: Deactivating Relay.")

            relay.value(0)

           

        # --- 6. Send the Response ---

        # First, send the mandatory HTTP Status Code and Headers

        conn.send('HTTP/1.1 200 OK\n')

        conn.send('Content-Type: text/html\n')

        conn.send('Connection: close\n\n') # The extra \n\n means the header section is done

       

        # Second, send the dynamic HTML payload

        conn.sendall(web_page())

       

        # Finally, close the connection so the browser finishes loading

        conn.close()

 

    except Exception as e:

        print(f"Socket Error: {e}")

        # Always attempt to clean up the connection on a crash

        if 'conn' in locals():

            conn.close()