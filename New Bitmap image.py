import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import pwmio
from adafruit_motor import servo
import firebase_admin
from firebase_admin import credentials, db

# === Configuration Firebase ===
cred = credentials.Certificate("/home/molka/Téléchargements/TON_FICHIER_FIREBASE.json")  # Remplace ici
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://solar-tracking-81b09-default-rtdb.firebaseio.com/'
})

# === I2C / ADC ===
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1

# === LDRs ===
ldr_top_left = AnalogIn(ads, ADS.P0)
ldr_top_right = AnalogIn(ads, ADS.P1)
ldr_bottom_left = AnalogIn(ads, ADS.P2)
ldr_bottom_right = AnalogIn(ads, ADS.P3)

# === Servos (Horizontal = GPIO25, Vertical = GPIO22) ===
pwm_servo_x = pwmio.PWMOut(board.D25, duty_cycle=0, frequency=50)
pwm_servo_y = pwmio.PWMOut(board.D22, duty_cycle=0, frequency=50)

servo_x = servo.Servo(pwm_servo_x)
servo_y = servo.Servo(pwm_servo_y)

angle_x = 90
angle_y = 90
servo_x.angle = angle_x
servo_y.angle = angle_y

# === Paramètres ===
tolerance = 100  # Sensibilité
seuil_lumiere = 15000  # Seuil pour considérer qu'il fait "sombre"

def read_and_move():
    global angle_x, angle_y

    # Lire les LDR
    tl = ldr_top_left.value
    tr = ldr_top_right.value
    bl = ldr_bottom_left.value
    br = ldr_bottom_right.value

    # Moyennes
    avg_top = (tl + tr) / 2
    avg_bottom = (bl + br) / 2
    avg_left = (tl + bl) / 2
    avg_right = (tr + br) / 2

    # Différences
    vertical_diff = avg_top - avg_bottom
    horizontal_diff = avg_left - avg_right

    # Mouvement horizontal
    if abs(horizontal_diff) > tolerance:
        if horizontal_diff > 0 and angle_x < 180:
            angle_x += 1
        elif horizontal_diff < 0 and angle_x > 0:
            angle_x -= 1
        servo_x.angle = angle_x

    # Mouvement vertical
    if abs(vertical_diff) > tolerance:
        if vertical_diff > 0 and angle_y < 180:
            angle_y += 1
        elif vertical_diff < 0 and angle_y > 0:
            angle_y -= 1
        servo_y.angle = angle_y

    # Affichage
    print(f"X: {angle_x} | Y: {angle_y}")
    print(f"LDRs: TL={tl}, TR={tr}, BL={bl}, BR={br}")

    # === Envoi vers Firebase ===
    moyenne_lum = (tl + tr + bl + br) // 4
    led_status = "ON" if moyenne_lum < seuil_lumiere else "OFF"

    db.reference("servos/s1").set(angle_x)
    db.reference("servos/s2").set(angle_y)
    db.reference("led").set(led_status)
    db.reference("ldr_moyenne").set(moyenne_lum)

# === Boucle principale ===
try:
    while True:
        read_and_move()
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Programme arrêté.")
