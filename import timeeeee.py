import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import pwmio
from adafruit_motor import servo
import requests

# Firebase config
API_KEY = "AIzaSyD7m-1wIA0uDtMyXQyhZRI4Osa0eJPEoIM"
EMAIL = "nsir.ahmed16062004@gmail.com"
PASSWORD = "ahmed123"
DATABASE_URL = "https://arm-robot3-default-rtdb.firebaseio.com"

def firebase_sign_in(email, password, api_key):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()["idToken"]

def update_servo_angle(token, s1_angle, s2_angle):
    data = {
        "s1": s1_angle,
        "s2": s2_angle
    }
    url = f"{DATABASE_URL}/servo.json?auth={token}"
    r = requests.patch(url, json=data)
    r.raise_for_status()
    return r.json()

# I2C / ADC setup
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1

ldr_top_left = AnalogIn(ads, ADS.P0)
ldr_top_right = AnalogIn(ads, ADS.P1)
ldr_bottom_left = AnalogIn(ads, ADS.P2)
ldr_bottom_right = AnalogIn(ads, ADS.P3)

# Servo setup
pwm_servo_x = pwmio.PWMOut(board.D17, duty_cycle=0, frequency=50)
pwm_servo_y = pwmio.PWMOut(board.D18, duty_cycle=0, frequency=50)

servo_x = servo.Servo(pwm_servo_x)
servo_y = servo.Servo(pwm_servo_y)

angle_x = 90
angle_y = 90
servo_x.angle = angle_x
servo_y.angle = angle_y

# Authenticate once before loop
print("Authenticating to Firebase...")
id_token = firebase_sign_in(EMAIL, PASSWORD, API_KEY)
print("Authenticated successfully.")

def read_and_move():
    global angle_x, angle_y

    tl = ldr_top_left.value
    tr = ldr_top_right.value
    bl = ldr_bottom_left.value
    br = ldr_bottom_right.value

    print(f"TL: {tl}, TR: {tr}, BL: {bl}, BR: {br}")

    avg_top = (tl + tr) / 2
    avg_bottom = (bl + br) / 2
    avg_left = (tl + bl) / 2
    avg_right = (tr + br) / 2

    vertical_diff = avg_top - avg_bottom
    horizontal_diff = avg_left - avg_right

    tolerance = 100

    moved = False

    if abs(horizontal_diff) > tolerance:
        if horizontal_diff > 0 and angle_x < 180:
            angle_x += 1
            moved = True
        elif horizontal_diff < 0 and angle_x > 0:
            angle_x -= 1
            moved = True
        servo_x.angle = angle_x

    if abs(vertical_diff) > tolerance:
        if vertical_diff > 0 and angle_y < 180:
            angle_y += 1
            moved = True
        elif vertical_diff < 0 and angle_y > 0:
            angle_y -= 1
            moved = True
        servo_y.angle = angle_y

    print(f"X: {angle_x}, Y: {angle_y}")

    return moved  # Return whether servo moved

try:
    while True:
        moved = read_and_move()
        if moved:
            # Update Firebase only if there was a movement
            update_servo_angle(id_token, angle_x, angle_y)
            print("Updated servo angles to Firebase.")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Programme arrêté.")
