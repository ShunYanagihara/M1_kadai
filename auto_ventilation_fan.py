import requests
import json
import time
from datetime import datetime
import RPi.GPIO as GPIO
import slackweb



#GPIOピン指定
GPIO_motion = 3
BtnPin = 18
LedPin = 16

#セットアップ
def setup():
    GPIO.setmode(GPIO.BOARD)       # Numbers GPIOs by physical location
    GPIO.setup(GPIO_motion, GPIO.IN)
    GPIO.setup(LedPin, GPIO.OUT)   # Set LedPin's mode is output
    GPIO.setup(BtnPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)    # Set BtnPin's mode is input, and pull up to high level(3.3V)
    GPIO.output(LedPin, GPIO.LOW) # Set LedPin low to off led


Led_status = 0

#繰り返し時間間隔
interval = 5

#初期化
humidity = 0
temp = 0
fan_status = 0
aircon_status = 0

room_no = "a305"

#湿度情報取得
def humidity_data():
    url = "http://172.26.16.8/api/00001C00000000000002000000063440/sensorstate/"
    req = requests.get(url)
    #requestで取得したのがresponse型のため、json型に変換してから指定
    global humidity
    humidity = req.json()[0]["value"]

#温度情報取得
def temp_data():
    url = "http://172.26.16.8/api/00001C0000000000000200000006343F/sensorstate/"
    req = requests.get(url)
    global temp
    temp = req.json()[0]["value"]

#換気扇稼働情報取得
def fan_data():
    url = "http://172.26.16.8/api/ducrbcontrol/ventilationunit/a305/"
    req = requests.get(url, auth=('koshizukaLab', '8TxgS73KmG'))
    global fan_status
    fan_status = req.json()[0]["status"]

#エアコン稼働情報取得
def aircon_data():
    url = "http://172.26.16.8/api/ducrbcontrol/airconditioner/a305/"
    req = requests.get(url, auth=('koshizukaLab', '8TxgS73KmG'))
    global aircon_status
    aircon_status = req.json()[0]["status"]

#A305換気扇ON
def fan_on():
    url = "http://172.26.16.8/api/ducrbcontrol/ventilationunit/"
    headers = {
            "Content-Type": "application/json"}
    putdata = {
        'id': room_no, # RoomName or VentilationUnit ID
        'setting_bit': 0x01,
        'on_off': 1,
        'operation_mode': 32,
        'ventilation_mode': 4,
        'ventilation_amount': 4,
        'set_point': 0,
        'fan_speed': 0,
        'fan_direction': 0,
        'filter_sign_reset': 0
        }
    req = requests.put(url, data=json.dumps(putdata), headers=headers, auth=('koshizukaLab', '8TxgS73KmG'))

#A305換気扇OFF
def fan_off():
    url = "http://172.26.16.8/api/ducrbcontrol/ventilationunit/"
    headers = {
            "Content-Type": "application/json"}
    putdata = {
        'id': room_no, # RoomName or VentilationUnit ID
        'setting_bit': 0x01,
        'on_off': 0,
        'operation_mode': 32,
        'ventilation_mode': 4,
        'ventilation_amount': 4,
        'set_point': 0,
        'fan_speed': 0,
        'fan_direction': 0,
        'filter_sign_reset': 0
        }
    req = requests.put(url, data=json.dumps(putdata), headers=headers, auth=('koshizukaLab', '8TxgS73KmG'))

#エアコンON
def aircon_on():
    url = "http://172.26.16.8/api/ducrbcontrol/airconditioner/"
    headers = {
        "Content-Type": "application/json"}
    putdata = {
        'id': room_no, # RoomName or Aircon ID
        'setting_bit': 0x01,
        'on_off': 1,
        'operation_mode': 4,
        'ventilation_mode': 0,
        'ventilation_amount': 0,
        'set_point': 25.0,
        'fan_speed': 2,
        'fan_direction': 7,
        'filter_sign_reset': 0
    }
    req = requests.put(url, data=json.dumps(putdata), headers=headers, auth=('koshizukaLab', '8TxgS73KmG'))

#エアコンOFF
def aircon_off():
    url = "http://172.26.16.8/api/ducrbcontrol/airconditioner/"
    headers = {"Content-Type": "application/json"}
    putdata = {
        'id': room_no, # RoomName or Aircon ID
        'setting_bit': 0x01,
        'on_off': 0,
        'operation_mode': 0,
        'ventilation_mode': 0,
        'ventilation_amount': 0,
        'set_point': 0,
        'fan_speed': 0,
        'fan_direction': 0,
        'filter_sign_reset': 0
    }
    req = requests.put(url, data=json.dumps(putdata), headers=headers, auth=('koshizukaLab', '8TxgS73KmG'))




def swLed(ev=None):
    global Led_status
    global room_no
    Led_status = not Led_status
    GPIO.output(LedPin, Led_status)  # switch led status(on-->off; off-->on)
    
    if Led_status ==1:
        print("change a305 -> a304")
        room_no = "a304"
    else:
        print("change a304 -> a305")
        room_no = "a305"

def loop():
    GPIO.add_event_detect(BtnPin, GPIO.FALLING, callback=swLed, bouncetime=5) # wait for falling
    while True:
        pass   # Don't do anything

def destroy():
    GPIO.output(LedPin, GPIO.LOW)     # led off
    GPIO.cleanup()                     # Release resource

setup()
GPIO.add_event_detect(BtnPin, GPIO.FALLING, callback=swLed, bouncetime=5) # wait for falling

#人感センサーの感知による分岐
while True:
    #湿度情報を取得
    humidity_data()
    print("湿度："+ str(humidity) + "％")
    #温度情報取得
    temp_data()
    print("温度" + str(temp) + "℃")
    #換気扇稼働情報取得
    fan_data()
    print(fan_status)
    #エアコン稼動情報取得
    aircon_data()
    
    #条件に応じた換気扇の操作
    if float(humidity)>=30 and fan_status==0:
        fan_on()
        print(room_no + ":換気扇をONにしました")
    elif float(humidity)>=30 and fan_status==1:
        print( room_no + ":換気扇は稼働中です")
    elif float(humidity)<=30 and fan_status==0:
        print(room_no + ":換気扇はOFFです")
    else:
        fan_off()
        print(room_no + ":換気扇は停止中です")

    #条件に応じたクーラーの操作
    if float(temp) >= 25 and aircon_status ==0:
        aircon_on()
        print(room_no + ":エアコンががONになりました")
    elif float(temp) >= 25 and aircon_status ==1:
        print(room_no + ":エアコンは稼働中です")
    elif float(temp) < 25 and aircon_status ==0:
        print(room_no + ":エアコンは停止中です")
    else:
        aircon_off()
        print(room_no + ":エアコンをOFFにしました")


#slack = slackweb.Slack(url="https://hooks.slack.com/services/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")
#slack.notify(text=str(temp))

    
    time.sleep(interval)





#if __name__ == '__main__':     # Program start from here
#setup()
# try:
# loop()
# except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
#    destroy()
