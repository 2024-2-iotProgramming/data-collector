import json
import logging
import random
import typing

import serial
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo


def _DEFAULT_DUMMY_SERIAL_READLINE() -> str:
    """더미로 건네주어야 하는 데이터를 생성하는 함수"""
    return json.dumps({
        'L_Dist': random.randint(200, 20000) / 100,
        'R_Dist': random.randint(200, 20000) / 100,
        'Mv': random.randint(0, 52),
    }) + '\r\n'


DUMMY_SERIAL_READLINE = _DEFAULT_DUMMY_SERIAL_READLINE


class Serial(serial.Serial):
    def readline(self, size: int | None = -1) -> bytes:
        if not self.readable():
            logging.error('기기에서 데이터를 읽어 올 수 없습니다.')
            logging.error('기기를 다른 곳에서 사용중이거나, 올바르게 연결되었는지 확인해주세요.')
            raise ConnectionError()
        return super().readline(size)

    def json(self) -> dict:
        while (line := self.readline()) == b'':
            pass
        try:
            data = json.loads(line.decode())
            assert isinstance(data, dict)
            return data
        except json.JSONDecodeError:
            logging.error(f'잘못된 데이터가 수신되었습니다: {line}')
        except UnicodeDecodeError:
            logging.error(f'잘못된 인코딩 데이터가 수신되었습니다: {line}')
        except AssertionError:
            logging.error(f'잘못된 데이터 형식이 수신되었습니다: {line}')
        except Exception as e:
            logging.error(f'알 수 없는 오류가 발생했습니다: {e}')
        return {}


class DummySerial(Serial):
    DEVICE_NAME = 'test'

    def __init__(self, port=None, *args, **kwargs):
        pass

    def readable(self) -> bool:
        return True

    def readline(self, size: int | None = -1) -> bytes:
        return bytes(DUMMY_SERIAL_READLINE().encode())


def select_port() -> ListPortInfo:
    """사용자가 직접 사용할 포트를 선택하고, 선택된 포트를 반환합니다."""
    print('다음의 포트 목록 중 하나를 선택해주세요. (일반적으로는 USB 포트를 선택하면 됩니다.)')
    ports = list_ports(include_dummy=True)
    for i, port in enumerate(ports):
        print(f'[{i}] {port.device}')
    i = int(input('> '))
    logging.info(f'포트 선택됨: {ports[i].device}')
    return ports[i]


def list_ports(include_dummy=False) -> typing.List[ListPortInfo]:
    ports = []
    if include_dummy:
        dummy_port_info = ListPortInfo(
            DummySerial.DEVICE_NAME,
            skip_link_detection=True,
        )
        ports.append(dummy_port_info)
    return ports + comports()


def get_serial(port: typing.Union[str, ListPortInfo], baudrate: int = 9600) -> Serial:
    """시리얼 포트를 연결하고, 시리얼 객체를 반환합니다."""
    if isinstance(port, ListPortInfo):
        device = port.device
    else:
        device = port

    if device == DummySerial.DEVICE_NAME:
        ser = DummySerial()
        logging.info('더미 시리얼 포트가 성공적으로 연결되었습니다.')
    else:
        ser = Serial(
            port=device,
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0,
        )
        logging.info('시리얼 포트가 성공적으로 연결되었습니다.')
    return ser
