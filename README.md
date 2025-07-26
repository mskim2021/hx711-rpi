# Raspberry Pi용 HX711 Python 모듈 (한국어)
이 Python 모듈은 `RPi.GPIO` 라이브러리를 사용하여 Raspberry Pi에서 HX711 로드셀의 무게를 측정합니다.  
GPIO 핀을 제어하여 HX711에서 데이터를 읽고 로드셀의 무게를 측정할 수 있습니다.  
Raspberry Pi 4에서 작동 확인했습니다.

## 주요 메소드
메소드에 대한 더 자세한 설명은 해당 메소드의 docstring을 참고해주세요.

### `HX711.__init__(dt_pin: int, sck_pin: int, gain: Literal[128, 64, 32] = 128) -> None`
- HX711 객체를 생성하고, 데이터 핀, 클럭 핀, 게인을 설정합니다.
  - `dt_pin` (int): 데이터 GPIO 핀 번호.
  - `sck_pin` (int): 클럭 GPIO 핀 번호.
  - `gain` (Literal[128, 64, 32], optional): 게인 값 (기본값: `128`).
- 예시:
  ```python
  from hx711-rpi import HX711

  hx = HX711(5, 6)
  print(f"데이터 핀: {hx.dt}, 클럭 핀: {hx.sck}, 게인: {hx.gain})
  ```

### `HX711.gain` (속성)
- 게인 값을 설정하거나 조회합니다.
- 반환값: 현재 설정된 게인 값.
- 예시:
    ```python
    current_gain = hx.gain
    print(f"이전 게인: {current_gain}")

    hx.gain = 64  # 게인 값 변경
    print(f"신규 게인: {hx.gain}")
    ```

### `HX711.tare(samples: int = 10) -> int`
- 로드셀의 영점(`offset`)을 자동으로 설정합니다.
  - `samples` (int, optional): 영점 설정에 사용할 샘플 개수 (기본값: `10`).
- 반환값: 영점 설정 후 결정된 오프셋 값.
- 예시:
    ```python
    result = hx.tare()
    print(f"영점 오프셋 자동 설정: {result}")

    hx.offset = 321123  # 인스턴스 변수 직접 설정
    print(f"영점 오프셋 수동 설정: {hx.offset}")
    ```

### `HX711.calibrate(reference_weight: float, samples: int = 10) -> float`
- 기준 무게를 사용해 로드셀의 보정 계수(`scale`)를 자동으로 설정합니다.
  - `reference_weight` (float): 기준 물체의 무게 (그램 단위).
  - `samples` (int, optional): 보정에 사용할 샘플 개수 (기본값: `10`).
- 반환값: 단위 보정 후 결정된 계수 값.
- 예시:
    ```python
    result = hx.calibrate(600)
    print(f"보정 계수 자동 설정: {result}")

    hx.scale = 402  # 인스턴스 변수 직접 설정
    print(f"보정 계수 수동 설정: {hx.scale}")
    ```

### `HX711.get_weight() -> float`
- 영점 오프셋과 보정 계수에 따라 현재 무게를 반환합니다.
- 반환값: 현재 측정된 무게.
- 예시:
    ```python
    weight = hx.get_weight()
    print(f"현재 무게: {weight} g")
    ```

### `HX711.power_down` (속성)
- 절전 모드를 설정하거나 해제합니다. 절전 모드는 HX711을 사용하면 자동으로 해제됩니다.
- 반환값: 현재 절전 모드 상태.
- 예시:
    ```python
    hx.power_down = True
    print(f"절전 모드 상태: {hx.power_down}")
    ```

### `HX711.cleanup() -> None`
- HX711에 사용한 GPIO 핀을 정리합니다.
- 예시:
    ```python
    hx.cleanup()
    ```

## 전체 사용 예시
아래는 `HX711` 객체를 생성하고, 영점 설정, 보정, 무게 측정을 순차적으로 하는 예시 코드입니다.
```python
from hx711-rpi import HX711

# 1. HX711 객체 생성
hx = HX711(5, 6)

# 2. 영점 설정
offset = hx.tare()
print(f"영점 오프셋 값: {offset}")

# 3. 단위 보정
# 예: 기준 무게 600g으로 보정
scale = hx.calibrate(600)
print(f"보정 계수 값: {scale}")

# 4. 무게 측정
weight = hx.get_weight()
print(f"현재 측정된 무게: {weight} g")

# 5. 사용 종료 후 핀 정리
hx.cleanup()
```
