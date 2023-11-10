from machine import Pin
import time
import socket
import network

ssid = "BBLim_EXT"
password = "bb235563"


def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
    ip = wlan.ifconfig()[0]
    print(wlan.ifconfig())
    print(f"Connected on {ip}")
    return ip


def open_socket(ip):
    address = (ip, 3002)
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.bind(address)
    connection.listen(1)
    return connection


led_left = Pin(15, Pin.OUT)
led_right = Pin(14, Pin.OUT)

motor_left_pins = [Pin(21, Pin.OUT),  # IN1
                   Pin(20, Pin.OUT),  # IN2
                   Pin(19, Pin.OUT),  # IN3
                   Pin(18, Pin.OUT)]  # IN4

motor_right_pins = [Pin(10, Pin.OUT),  # IN1
                    Pin(11, Pin.OUT),  # IN2
                    Pin(12, Pin.OUT),  # IN3
                    Pin(13, Pin.OUT)]  # IN4

full_step_sequence_forward = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1]
]

full_step_sequence_backward = [
    [0, 0, 0, 1],
    [0, 0, 1, 0],
    [0, 1, 0, 0],
    [1, 0, 0, 0]
]

net_height = 0
default_net_height = 4
floor_level = 0


def on_led():
    led_left.value(1)
    led_right.value(1)


def off_led():
    led_left.value(0)
    led_right.value(0)


def upward():
    for step_left, step_right in zip(full_step_sequence_forward, full_step_sequence_backward):
        for i in range(len(motor_left_pins)):
            motor_left_pins[i].value(step_left[i])
            motor_right_pins[i].value(step_right[i])
            time.sleep(0.001)


def downward():
    for step_left, step_right in zip(full_step_sequence_forward, full_step_sequence_backward):
        for i in range(len(motor_left_pins)):
            motor_left_pins[i].value(step_right[i])
            motor_right_pins[i].value(step_left[i])
            time.sleep(0.001)


def handle_request(request):
    print(request)
    if "ac-court" in request:
        on_led()
        global net_height, defalt_net_height
        for i in range(default_net_height-net_height):
            for j in range(380):
                upward()
        net_height = net_height + default_net_height
        print(f"Net Height: {net_height}")
        response = f"Activate court"
        return response

    if "de-court" in request:
        off_led()
        global net_height, floor_level
        for i in range((net_height-floor_level)):
            for j in range(480):
                downward()
        net_height = floor_level
        print(f"Net Height: {net_height}")
        response = f"Deactivate court"
        return response

    if "up-net" in request:
        global net_height
        if net_height != 7:
            for _ in range(380):
                upward()
            net_height = net_height + 1
            response = f"Net Height set to {net_height}"
            print(f"Net Height: {net_height}")
        else:
            response = "Net Height already at maximum"
        return response

    if "down-net" in request:
        global net_height
        if net_height != 0:
            for _ in range(380):
                downward()
            net_height = net_height - 1
            response = f"Net Height set to {net_height}"
            print(f"Net Height: {net_height}")
        else:
            response = "Net Height already at minimum"
        return response

    if "on-light" in request:
        print("on")
        on_led()
        response = "Lights turned on"
        return response

    if "off-light" in request:
        print("off")
        off_led()
        response = "Lights turned off"
        return response

    if "default-net" in request:
        global net_height
        if net_height > default_net_height:
            for i in range(net_height-default_net_height):
                for j in range(380):
                    downward()
            net_height = net_height - (net_height - default_net_height)
            response = f"Net Height set to {net_height}"
            print(f"Net Height: {net_height}")
            return response
        if net_height < default_net_height:
            for i in range(default_net_height-net_height):
                for j in range(380):
                    upward()
            net_height = net_height + (default_net_height-net_height)
            response = f"Net Height set to {net_height}"
            print(f"Net Height: {net_height}")
            return response

    else:
        response = "Unknown command"
        return response


ip = connect()
connection = open_socket(ip)

while True:
    try:
        client = connection.accept()[0]
        request = ""
        request = client.recv(1024).decode('utf-8')
        response = handle_request(request)
        client.send(response)
        client.close()
    except Exception as e:
        print(f"Error in server: {e}")
