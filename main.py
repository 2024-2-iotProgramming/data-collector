#!/usr/bin/env python

import json
import logging
import time

import requests

from lib import serial


logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(asctime)s] %(message)s',
    handlers=[logging.StreamHandler()],
)


TARGET_URL = 'http://localhost:8000/sensor/radar/'


def main():
    # Django 서버가 실행 중인지 확인
    try:
        res = requests.get(TARGET_URL)
    except requests.exceptions.ConnectionError:
        logging.error(
            f'"{TARGET_URL}"에 연결할 수 없습니다.'
            ' Django 서버를 실행한 후 다시 시도해주세요.'
            ' 서버를 실행하는 방법은 다음과 같습니다:'
            '\n\t1. iotProject 디렉터리로 이동'
            '\n\t2. python manage.py runserver'
        )
        return

    # 시리얼 포트 연결
    port = serial.select_port()
    ser = serial.get_serial(port)

    # 데이터 전송
    while True:
        # 센서에서 데이터 수신
        data = ser.json()
        logging.info(f'{json.dumps(data)}')

        # 서버에 데이터 전송
        res = requests.post(TARGET_URL, data={
            'x': 1,
            'y': data['Mv'],
            'echo_cm': data['L_Dist'],
        })
        res.raise_for_status()
        logging.info(f'{res.status_code} {res.json()}')

        res = requests.post(TARGET_URL, data={
            'x': 0,
            'y': data['Mv'],
            'echo_cm': data['R_Dist'],
        })
        res.raise_for_status()
        logging.info(f'{res.status_code} {res.json()}')

        time.sleep(0.2)

if __name__ == '__main__':
    main()
