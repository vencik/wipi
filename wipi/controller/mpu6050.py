from typing import Dict, Iterator
from datetime import datetime, timedelta

import pause
from mpu6050 import mpu6050 as MPU6050

from wipi.controller import Controller


class mpu6050(Controller):
    """
    MPU6050 accelerometer & gyroscope
    """

    def __init__(self, name: str, address: int = 0x68, accel_range: float = MPU6050.ACCEL_RANGE_2G, gyro_range: float = MPU6050.GYRO_RANGE_250DEG):
        """
        :param name: Controller name
        :param address: MPU6050 module SMB address
        :param accel_range: Accelerometer measurement range/precision
        """
        super().__init__(name)
        self._dev = MPU6050(address)
        self._dev.set_accel_range(accel_range)
        self._dev.set_gyro_range(gyro_range)

    def get_state(self) -> Dict:
        """
        :return: Current state
        """
        return {
            "address" : self._dev.address,
            "accel_range" : self._dev.read_accel_range(),
            "gyro_range" : self._dev.read_gyro_range(),
        }

    def set_state(self, state: Dict) -> Dict:
        """
        :param state: State changes
        :return: Current state
        """
        accel_range = {
            2  : MPU6050.ACCEL_RANGE_2G,
            4  : MPU6050.ACCEL_RANGE_4G,
            8  : MPU6050.ACCEL_RANGE_8G,
            16 : MPU6050.ACCEL_RANGE_16G,
        }.get(state.get("accel_range", -1))
        if accel_range:
            self._dev.set_accel_range(accel_range)

        gyro_range = {
            250  : MPU6050.GYRO_RANGE_250DEG,
            500  : MPU6050.GYRO_RANGE_500DEG,
            1000 : MPU6050.GYRO_RANGE_1000DEG,
            2000 : MPU6050.GYRO_RANGE_2000DEG,
        }.get(state.get("gyro_range", -1))
        if gyro_range:
            self._dev.set_gyro_range(accel_range)

        return self.get_state()

    def downstream(self, query: Dict) -> Iterator[Dict]:
        """
        Downstream data from the accelerometer and gyroscope
        :param query: Query
        :return: Generator of data chunks
        """
        interval = timedelta(seconds=query.get("interval", 0.0))
        duration = timedelta(seconds=query.get("duration", 0.0))

        accel_data = query.get("accel_data", True)
        gyro_data = query.get("gyro_data", True)
        accel_unit_g = query.get("accel_unit_g", False)

        stop_at = datetime.now() + duration if duration else None
        while True:
            now = datetime.now()
            if stop_at and now >= stop_at:
                break

            data: Dict = {"timestamp" : now.strftime("%Y/%m/%d %H:%M:%S.%f")}
            if accel_data:
                data["accel_data"] = self._dev.get_accel_data(accel_unit_g)
            if gyro_data:
                data["gyro_data"] = self._dev.get_gyro_data()
            yield data

            if interval:
                pause.until(now + interval)
