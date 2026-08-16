# subway_daily DATE PART 2: 공휴일 기준 덧씌우기

## 1. 프로젝트 개요

`01-date-02-subway-daily-holiday`는 서울 지하철 일별 이용 데이터인 `subway_daily`의 날짜 유형을 공휴일 기준으로 보정하는 전처리 프로젝트입니다.

DATE PART 1단계에서는 원본의 `사용일자`를 날짜 형식으로 변환하고, Python의 요일 정보를 기준으로 `평일`과 `주말`을 구분했습니다. 하지만 상권 유동인구 분석에서는 공휴일도 별도로 구분할 필요가 있습니다. 공휴일에는 일반적인 평일·주말과 다른 이동 목적과 이용 패턴이 나타날 수 있기 때문입니다.

이 단계에서는 한국천문연구원 API를 기반으로 생성한 공휴일 master를 기존 `subway_daily`에 결합합니다. 공휴일 master에 포함된 날짜는 기존 `date_type` 값이 `평일` 또는 `주말`이더라도 최종적으로 `공휴일`로 보정합니다.

## 2. 전처리 목적

요일 정보만으로는 평일에 지정된 공휴일과 주말에 겹친 공휴일을 구별할 수 없습니다. 이를 그대로 사용하면 공휴일의 지하철 이용량이 평일 또는 일반 주말에 포함되어 상권별 이동 패턴과 수요 변화를 정확하게 해석하기 어렵습니다.

이번 전처리의 목적은 기존 row 수와 승하차량을 그대로 유지하면서 `date_type`만 다음 세 가지 값으로 정리하는 것입니다.

* `평일`
* `주말`
* `공휴일`

## 3. 입력 데이터

### `subway_daily_sample.csv`

홍대입구역을 기준으로 구성한 포트폴리오용 미니 샘플입니다. 전체 Raw Data는 GitHub에 포함하지 않습니다.

| column                   | description            |
| ------------------------ | ---------------------- |
| `date`                   | 날짜                     |
| `year`                   | 연도                     |
| `month`                  | 월                      |
| `day`                    | 일                      |
| `date_type`              | 기존 날짜 유형인 `평일` 또는 `주말` |
| `line_name`              | 지하철 노선명                |
| `station_name`           | 지하철역명                  |
| `daily_in_passengers`    | 일별 승차 인원               |
| `daily_out_passengers`   | 일별 하차 인원               |
| `daily_total_passengers` | 일별 총 승하차 인원            |

### `Gonghyuil_2015_2026.xlsx`

한국천문연구원 API를 기반으로 생성한 2015~2026년 공휴일 기준 데이터입니다. 이번 저장소에는 API Key 없이도 전처리를 재현할 수 있도록 생성 완료된 공휴일 엑셀 파일을 샘플 입력으로 포함합니다.

API Key는 공휴일 데이터를 생성할 때 API 호출에 사용한 인증 정보이므로 코드나 파일, GitHub 저장소에는 포함하지 않습니다.

## 4. 공휴일 master 구조

`Gonghyuil_2015_2026.xlsx`는 기존 `subway_daily`의 `date_type`을 보정하는 기준 테이블입니다.

| column     | description             |
| ---------- | ----------------------- |
| `date`     | 공휴일 날짜, `yyyy-mm-dd` 형식 |
| `day_type` | 날짜 유형, 모든 값은 `공휴일`      |

파일에는 2015~2026년의 공휴일 날짜가 row 단위로 들어 있습니다.

## 5. 기존 subway_daily에 공휴일 기준을 덧씌우는 방식

결합 방향은 반드시 다음과 같습니다.

```text
subway_daily LEFT JOIN Gonghyuil_2015_2026.xlsx
```

두 데이터셋의 `date`를 `datetime`으로 통일한 뒤, 기존 `subway_daily`를 왼쪽 데이터로 사용합니다.

```python
subway_daily = subway_daily.merge(
    holiday_df,
    on="date",
    how="left",
)

subway_daily["date_type"] = subway_daily["day_type"].fillna(
    subway_daily["date_type"]
)

subway_daily = subway_daily.drop(columns=["day_type"])
```

공휴일 master에 일치하는 날짜가 있으면 기존 값이 `평일`인지 `주말`인지와 관계없이 `공휴일`로 덧씌웁니다. 일치하지 않으면 기존 값을 유지하고, merge에 사용한 임시 컬럼 `day_type`은 최종 결과에서 제거합니다.

이 과정은 공휴일 master를 기준으로 새로운 지하철 row를 만드는 작업이 아닙니다. 최종 결과는 기존 `subway_daily`의 row 수를 유지하면서, 이미 존재하는 날짜가 공휴일인지 여부만 덧씌운 데이터셋입니다.

## 6. 전처리 전후 비교

전처리 전 `subway_daily`:

| date       | date_type | station_name |
| ---------- | --------- | ------------ |
| 2026-03-01 | 주말        | 홍대입구역        |
| 2026-04-01 | 평일        | 홍대입구역        |

공휴일 master:

| date       | day_type |
| ---------- | -------- |
| 2026-03-01 | 공휴일      |
| 2026-05-05 | 공휴일      |

전처리 후 `subway_daily_with_holiday`:

| date       | date_type | station_name |
| ---------- | --------- | ------------ |
| 2026-03-01 | 공휴일       | 홍대입구역        |
| 2026-04-01 | 평일        | 홍대입구역        |

* `2026-03-01`은 Python 요일 기준으로 `주말`이었지만 공휴일 master에 포함되므로 `공휴일`로 보정됩니다.
* `2026-04-01`은 공휴일 master에 없으므로 기존 `평일` 값을 유지합니다.
* `2026-05-05`는 공휴일 master에는 있지만 기존 `subway_daily`에 없다면 최종 결과에 새로 추가되지 않습니다.

## 7. 2026년 데이터 범위 주의사항

메인 지하철 데이터 수집 시점이 2026년 5월이었기 때문에, 실제 `subway_daily` 데이터는 `2026-04-30`까지만 존재합니다.

반면 `Gonghyuil_2015_2026.xlsx`는 2026년 12월 25일까지의 공휴일 정보를 포함합니다. 따라서 `2026-05-05` 어린이날처럼 공휴일 master에는 존재하지만 기존 `subway_daily`에는 존재하지 않는 날짜가 있을 수 있습니다.

이 전처리는 공휴일 데이터를 기준으로 새로운 지하철 승하차량 row를 생성하는 작업이 아니라, 기존 `subway_daily`에 존재하는 날짜에 대해서만 `date_type`을 보정하는 작업입니다. `left join`을 사용하는 이유도 기존 지하철 데이터의 날짜 범위와 row 수를 보존하기 위해서입니다.

## 8. 실행 방법

Python 3.10 이상 환경을 권장합니다.

```bash
pip install -r requirements.txt
python src/preprocess_subway_daily_holiday.py
```

별도의 API 호출이나 API Key 입력 없이 저장소에 포함된 샘플 공휴일 master를 읽어 실행합니다.

## 9. 결과 파일

실행 결과는 다음 경로에 UTF-8 with BOM(`utf-8-sig`) CSV로 저장됩니다.

```text
data/sample/subway_daily_with_holiday_sample.csv
```

스크립트는 다음 항목을 함께 검증합니다.

* 보정 전후 row 수가 같은지
* 최종 결과에 `day_type`이 남아 있지 않은지
* `date_type`이 `평일`, `주말`, `공휴일` 중 하나인지
* 공휴일 master에만 있는 날짜가 새 row로 추가되지 않았는지
* 기존 지하철 데이터와 겹치는 공휴일이 `공휴일`로 보정되었는지

## 10. 포트폴리오 관점의 의미

이 프로젝트는 단순한 날짜 변환을 넘어 분석 목적에 맞는 기준 데이터를 기존 데이터셋에 결합하는 과정을 보여줍니다. 공휴일 master를 기준으로 새로운 row를 추가하는 대신, 기존 `subway_daily`를 기준으로 `left join`해 분석 대상의 날짜 범위와 row 수를 유지했습니다.

이를 통해 이후 상권 이동 분석에서 평일·주말·공휴일에 따른 지하철 이용량 차이를 비교할 수 있는 날짜 기준을 마련하고, 상권별 이동 패턴을 보다 세밀하게 해석할 수 있도록 구성했습니다.

## 파일 구조

```text
01-date-02-subway-daily-holiday/
├── README.md
├── requirements.txt
├── src/
│   └── preprocess_subway_daily_holiday.py
└── data/
    └── sample/
        ├── subway_daily_sample.csv
        ├── Gonghyuil_2015_2026.xlsx
        └── subway_daily_with_holiday_sample.csv
```
