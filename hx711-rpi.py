from typing import Literal, Final
import RPi.GPIO as GPIO
from time import sleep
from statistics import median
from threading import Lock


class HX711:
    """Raspberry Pi용 HX711 Python 모듈

    Attributes:
        dt (int): 설정된 데이터 GPIO 핀 번호.
        sck (int): 설정된 클럭 GPIO 핀 번호.
        offset (int): 설정된 영점 설정 오프셋 값.
        scale (float): 설정된 단위 보정 계수 값.
    """

    def __init__(self, dt_pin: int, sck_pin: int, gain: Literal[128, 64, 32] = 128) -> None:
        """HX711 객체를 생성합니다.

        Args:
            data_pin (int): 데이터 GPIO 핀 번호.
            clock_pin (int): 클럭 GPIO 핀 번호.
            gain (Literal[128, 64, 32], optional): 게인 값. 기본값은 `128`이며, A 채널은 `128`과 `64`를, B 채널은 `32`를 사용합니다.
        """
        self.dt: Final[int] = dt_pin
        self.sck: Final[int] = sck_pin
        if gain not in (128, 64, 32):
            raise ValueError("gain must be one of 128, 64, 32.")
        self._gain: Literal[128, 64, 32] = gain
        self.offset: int = 0
        self.scale: float = 1
        self._power_down: bool = False
        self._lock = Lock()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.dt, GPIO.IN)
        GPIO.setup(self.sck, GPIO.OUT, initial=GPIO.LOW)

        self._read_raw()  # 초기 쓰레기값 버리기 & 게인 설정

    def _is_ready(self) -> bool:
        """
        Returns:
            bool: HX711이 데이터를 준비했는 지 여부."""
        return GPIO.input(self.dt) == GPIO.LOW

    def _read_raw(self) -> int:
        """무게 데이터를 읽고 채널과 게인을 설정합니다.

        Returns:
            int: 2의 보수로 해석한 24비트 정수 무게 데이터.
        """
        while not self._is_ready():
            sleep(0.01)

        # 24비트 데이터 읽기
        value = 0
        for _ in range(24):
            GPIO.output(self.sck, GPIO.HIGH)
            GPIO.output(self.sck, GPIO.LOW)
            bit = GPIO.input(self.dt)
            value = (value << 1) | bit  # HX711이 MSB부터 전송하므로 왼쪽으로 밀면서 비트 저장

        # 채널 & 게인 설정
        match self._gain:
            case 64:
                gain_pulses = 3  # A 채널
            case 32:
                gain_pulses = 2  # B 채널
            case _:
                gain_pulses = 1  # A 채널
        for _ in range(gain_pulses):
            GPIO.output(self.sck, GPIO.HIGH)
            GPIO.output(self.sck, GPIO.LOW)

        # 24비트 값을 2의 보수로 해석
        value = -(value & 0x800000) + (value & 0x7fffff)

        return value

    def tare(self, samples: int = 10) -> int:
        """로드셀의 자체 오차와 위에 올려진 용기의 무게를 포함해 영점을 설정합니다.
        영점 설정 이후에 단위 보정을 해야 합니다.
        절전 모드를 자동으로 해제합니다.

        Args:
            samples (int, optional): 영점 설정에 사용할 샘플의 갯수. 기본값은 `10`입니다.

        Returns:
            int: 영점 설정 후 결졍된 오프셋 값.
        """
        if self._power_down:
            self.power_down = False  # 절전 모드 자동 해제
        with self._lock:
            values = [self._read_raw() for _ in range(samples)]
        self.offset = int(median(values))
        return self.offset

    def calibrate(self, reference_weight: float, samples: int = 10) -> float:
        """로드셀 위에 올려진 기준 물체의 무게에 따라 계산 단위를 보정합니다.
        영점 설정 이후에 단위 보정을 해야 합니다.
        절전 모드를 자동으로 해제합니다.

        Args:
            reference_weight (float): 기준 물체의 그램(g) 단위 무게.
            samples (int, optional): 단위 보정에 사용할 샘플의 갯수. 기본값은 `10`입니다.

        Returns:
            float: 단위 보정 후 결정된 계수 값.
        """
        if self._power_down:
            self.power_down = False  # 절전 모드 자동 해제
        with self._lock:
            values = [self._read_raw() - self.offset for _ in range(samples)]
        self.scale = median(values) / reference_weight
        return self.scale

    def get_weight(self) -> float:
        """절전 모드를 자동으로 해제합니다.

        Returns:
            float: 설정된 `offset`(영점 설정 오프셋)과 `scale`(단위 보정 계수)에 따라 변환된 무게.
        """
        if self._power_down:
            self.power_down = False  # 절전 모드 자동 해제
        with self._lock:
            return (self._read_raw() - self.offset) / self.scale

    @property
    def gain(self) -> Literal[128, 64, 32]:
        """A 채널은 `128`과 `64`를, B 채널은 `32`를 사용합니다.
        절전 모드를 자동으로 해제합니다.

        Returns:
            Literal[128, 64, 32]: 설정된 게인 값.

        Raises:
            ValueError: 새 게인 값이 `128`, `64`, `32` 중 하나가 아닐 경우 발생.
        """
        return self._gain

    @gain.setter
    def gain(self, value: Literal[128, 64, 32]) -> None:
        if value not in (128, 64, 32):
            raise ValueError("gain must be one of 128, 64, 32.")
        if value == self._gain:
            return
        self._gain = value
        if self._power_down:
            self.power_down = False  # 절전 모드 자동 해제
        with self._lock:
            self._read_raw()  # 초기 쓰레기값 버리기 & 게인 설정

    @property
    def power_down(self) -> bool:
        """기본값은 `False`이며, `True`로 설정 시 절전 모드가 켜집니다.
        절전 모드는 장치를 사용하는 경우 자동으로 해제됩니다.

        Returns:
            bool: 설정된 절전 모드의 상태.
        """
        return self._power_down

    @power_down.setter
    def power_down(self, value: bool) -> None:
        value = bool(value)
        if value == self._power_down:
            return
        if value:
            with self._lock:
                GPIO.output(self.sck, GPIO.LOW)
                GPIO.output(self.sck, GPIO.HIGH)
                sleep(0.00006)  # 최소 60 μs 이상 유지
        else:
            with self._lock:
                GPIO.output(self.sck, GPIO.LOW)
                self._read_raw()  # 초기 쓰레기값 버리기 & 게인 설정
        self._power_down = value

    def cleanup(self) -> None:
        """HX711이 사용한 GPIO 핀을 정리합니다."""
        GPIO.cleanup((self.dt, self.sck))
