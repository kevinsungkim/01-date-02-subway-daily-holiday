"""공휴일 master를 기존 subway_daily에 덧씌워 date_type을 보정한다."""

from pathlib import Path

import pandas as pd


# 파일 경로 설정
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"

SUBWAY_INPUT_FILE = SAMPLE_DIR / "subway_daily_sample.csv"
HOLIDAY_INPUT_FILE = SAMPLE_DIR / "Gonghyuil_2015_2026.xlsx"
OUTPUT_FILE = SAMPLE_DIR / "subway_daily_with_holiday_sample.csv"

EXPECTED_SUBWAY_COLUMNS = [
    "date",
    "year",
    "month",
    "day",
    "date_type",
    "line_name",
    "station_name",
    "daily_in_passengers",
    "daily_out_passengers",
    "daily_total_passengers",
]
EXPECTED_HOLIDAY_COLUMNS = ["date", "day_type"]
VALID_DATE_TYPES = {"평일", "주말", "공휴일"}


# subway_daily 샘플 데이터 불러오기
subway_daily = pd.read_csv(SUBWAY_INPUT_FILE)
subway_daily_before = subway_daily.copy()


# 공휴일 master 불러오기
holiday_df = pd.read_excel(
    HOLIDAY_INPUT_FILE,
    usecols=EXPECTED_HOLIDAY_COLUMNS,
    engine="openpyxl",
)


# 입력 데이터 구조 검증
missing_subway_columns = set(EXPECTED_SUBWAY_COLUMNS) - set(
    subway_daily.columns
)
missing_holiday_columns = set(EXPECTED_HOLIDAY_COLUMNS) - set(
    holiday_df.columns
)

if missing_subway_columns:
    raise ValueError(
        f"subway_daily 필수 컬럼 누락: {sorted(missing_subway_columns)}"
    )
if missing_holiday_columns:
    raise ValueError(
        f"공휴일 master 필수 컬럼 누락: {sorted(missing_holiday_columns)}"
    )
if holiday_df["date"].duplicated().any():
    raise ValueError("공휴일 master의 date 컬럼에 중복 날짜가 있습니다.")
if not holiday_df["day_type"].eq("공휴일").all():
    raise ValueError("공휴일 master의 day_type은 모두 '공휴일'이어야 합니다.")


# 날짜 형식 통일
subway_daily["date"] = pd.to_datetime(
    subway_daily["date"],
    format="%Y-%m-%d",
    errors="raise",
)
holiday_df["date"] = pd.to_datetime(
    holiday_df["date"],
    errors="raise",
)


# 기존 데이터와 공휴일 master의 날짜 범위 기록
subway_dates_before = set(subway_daily["date"])
holiday_only_dates = set(holiday_df["date"]) - subway_dates_before
holiday_dates_in_subway = subway_dates_before & set(holiday_df["date"])


# subway_daily와 공휴일 master를 date 기준으로 결합
# subway_daily를 왼쪽에 두므로 공휴일 master에만 있는 날짜는 추가되지 않는다.
subway_daily = subway_daily.merge(
    holiday_df,
    on="date",
    how="left",
    validate="many_to_one",
)


# 공휴일인 날짜는 date_type을 공휴일로 보정
subway_daily["date_type"] = subway_daily["day_type"].fillna(
    subway_daily["date_type"]
)


# 최종 분석용 컬럼 정리
subway_daily = subway_daily.drop(columns=["day_type"])
subway_daily["date"] = subway_daily["date"].dt.strftime("%Y-%m-%d")
subway_daily = subway_daily[EXPECTED_SUBWAY_COLUMNS]


# 결과 데이터 검증
if len(subway_daily) != len(subway_daily_before):
    raise AssertionError("공휴일 보정 전후 row 수가 다릅니다.")
if "day_type" in subway_daily.columns:
    raise AssertionError("최종 결과에 day_type 임시 컬럼이 남아 있습니다.")
if not set(subway_daily["date_type"]).issubset(VALID_DATE_TYPES):
    raise AssertionError(
        "date_type에 평일, 주말, 공휴일 이외의 값이 있습니다."
    )

result_dates = set(pd.to_datetime(subway_daily["date"]))
if result_dates != subway_dates_before:
    raise AssertionError("기존 subway_daily에 없던 날짜가 추가되었습니다.")
if result_dates & holiday_only_dates:
    raise AssertionError("공휴일 master에만 있는 날짜가 결과에 추가되었습니다.")

corrected_holiday_rows = subway_daily[
    pd.to_datetime(subway_daily["date"]).isin(holiday_dates_in_subway)
]
if not corrected_holiday_rows["date_type"].eq("공휴일").all():
    raise AssertionError("일부 공휴일의 date_type이 보정되지 않았습니다.")


# 결과 파일 저장
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
subway_daily.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
)


# 실행 결과 검증
print("기존 subway_daily row 수:", len(subway_daily_before))
print("공휴일 보정 후 row 수:", len(subway_daily))
print("date_type 값:", sorted(subway_daily["date_type"].unique()))
print("공휴일로 보정된 row 수:", len(corrected_holiday_rows))
print("결과 파일:", OUTPUT_FILE)
