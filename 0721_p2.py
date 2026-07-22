"""
════════════════════════════════════════════════════════════════════
════════════════════════════════════════════════════════════════════

머리말
[실습 2] 파일 I/O, 예외 처리, Pydantic 검증 파이프라인
- 설명:  Python_Practice2_Data.json을 로딩해
        Pydantic v2로 검증하고 valid는 CSV, errors는 JSON으로 저장 후
        재로딩까지 확인
- 작성자: 정한결
- 변경내역:
        v1 뼈대 + 데이터 로딩
        v2 오류 데이터 3종, 정상 데이터 4건 삽입
        v3 실행시간 데코레이터 추가
        v4 주석 수정 및 가독성 향상
        
════════════════════════════════════════════════════════════════════
════════════════════════════════════════════════════════════════════
"""

import csv
import json
import logging
from pathlib import Path

# logging 설정 — print 대신 레벨(info, error)과 시각을 같이 찍음
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

#
import time
from functools import wraps


def timer(func):
    """함수 실행 시간을 찍어주는 데코레이터 (p.34)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} 실행 시간: {time.perf_counter() - t:.4f}초")
        return result
    return wrapper



# 파일 위치 기준 절대경로로 잡기
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "Python_Practice2_Data.json"






# ══════════════════════════════════
# 1) 예외 처리 + 파일 읽기
# ══════════════════════════════════


@timer
def safe_load_csv(path):
    """파일 읽어서 dict 리스트 반환. 실패하면 None.
    성공은 logger.info, 실패는 logger.error, finally에서 '로딩 종료' 출력"""
    try:
        with open(path, encoding="utf-8") as f:
            # 데이터2 사용으로 json.load로 바로 읽힘
            if str(path).endswith(".json"):
                rows = json.load(f)
            else:
                rows = list(csv.DictReader(f))
        logger.info(f"{len(rows)}건 로딩 성공: {path}")
        return rows
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없음: {path}")
        
        return None
    except json.JSONDecodeError as e:
        logger.error(f"파일 형식 오류: {e}")
        return None
    finally:
        print("로딩 종료")


# checkpoint: 없는 파일이면 None 나오는지 먼저 확인
assert safe_load_csv(BASE_DIR / "없는파일.json") is None
print("assert None 통과")

# 진짜 데이터 로딩
raw_data = safe_load_csv(DATA_PATH)
print("로딩 건수:", len(raw_data))
print("첫 행:", raw_data[0])




# ══════════════════════════════════
# 2) Pydantic v2 스키마 정의
# ══════════════════════════════════

from typing import Optional
from pydantic import BaseModel, Field, ValidationError


class SalesRecord(BaseModel):
    """매출 한 건의 스키마. 규칙에 안 맞으면 생성 시점에 ValidationError 발생"""
    month: str = Field(min_length=1)     # 빈 문자열 금지
    region: str = Field(min_length=1)    # 빈 문자열 금지
    amount: float = Field(gt=0)          # 0 초과
    category: Optional[str] = None       # 없어도 됨


# 동작 미리 확인 — 정상 1건, 오류 1건
ok = SalesRecord(**raw_data[0])
print("정상 레코드:", ok)

try:
    SalesRecord(month="2024-01", region="서울", amount=0)  # amount 0 → 규칙 위반
except ValidationError as e:
    print("검증 실패 (의도된 테스트):")
    print(e)
    
    
    
    
# ══════════════════════════════════
# 3) 검증 파이프라인 (valid, errors 분리)
# ══════════════════════════════════

def validate_records(rows):
    """rows를 순회하며 SalesRecord로 변환.
    성공은 valid, 실패는 errors({row, error})에 나눠 담아서 반환"""
    valid, errors = [], []
    for row in rows:
        try:
            valid.append(SalesRecord(**row))
        except ValidationError as e:   # exception으로 안잡고 정확히 지정
            print(f"검증 실패: {e}")     # checkpoint: 오류 내용 출력
            errors.append({"row": row, "error": str(e)})
    return valid, errors


valid, errors = validate_records(raw_data)
print("─── 검증 결과 ───")
print(f"valid: {len(valid)}건 / errors: {len(errors)}건")




# ══════════════════════════════════
# 4) 결과 파일 저장 + 재로딩 확인
# ══════════════════════════════════

VALID_CSV = BASE_DIR / "valid.csv"
ERRORS_JSON = BASE_DIR / "errors.json"

# valid 레코드를 CSV로 저장
# 모델 dict 변환 model_dump 사용
with open(VALID_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["month", "region", "amount", "category"])
    writer.writeheader()
    for rec in valid:
        writer.writerow(rec.model_dump())

# errors를 JSON으로 저장

with open(ERRORS_JSON, "w", encoding="utf-8") as f:          # ensure_ascii=False로 한글 깨짐 방지
    json.dump(errors, f, ensure_ascii=False, indent=2)

logger.info(f"저장 완료: valid {len(valid)}건 -> {VALID_CSV.name}, errors {len(errors)}건 -> {ERRORS_JSON.name}")

# 건수 검증 — 1번 safe_load_csv 재사용 (csv 분기 여기서 쓰임)
reloaded = safe_load_csv(VALID_CSV)
print("─── 재로딩 검증 ───")
print(f"재로딩 건수: {len(reloaded)}")
assert len(reloaded) == len(valid)
print("재로딩 건수 assert 통과")




# ══════════════════════════════════
# 5) Checkpoint 내용 추가 — 오류 데이터 삽입
# ══════════════════════════════════

# 배포 데이터 100건은 전부 정상이라 실패 데이터 삽입
# 규칙 3개를 하나씩 위반하는 행 삽입
test_raw_data = [
    {"month": "2024-01", "region": "서울", "amount": 1500, "category": "전자"},  # 정상
    {"month": "2024-01", "region": "부산", "amount": 800, "category": "의류"},   # 정상
    {"month": "2024-02", "region": "대구", "amount": 1200},                     # 정상 (category 없음 - 허용)
    {"month": "2024-02", "region": "인천", "amount": 500, "category": "식품"},   # 정상
    {"month": "", "region": "광주", "amount": 900, "category": "전자"},          # 오류: month 빈 값
    {"month": "2024-03", "region": "", "amount": 700, "category": "의류"},       # 오류: region 빈 값
    {"month": "2024-03", "region": "대전", "amount": 0, "category": "식품"},     # 오류: amount 0
]

# 3번 검증 함수 재사용
test_valid, test_errors = validate_records(test_raw_data)

print("─── Checkpoint 검증 (테스트 데이터) ───")
print(f"valid: {len(test_valid)}건 / errors: {len(test_errors)}건")
assert len(test_valid) == 4 and len(test_errors) == 3
print("valid 4건 / errors 3건 assert 통과")


# 데이터가 100건으로 작아서 코드 방식에 따른 실행시간 차이는 오차범위 수준이라 판단하였스빈다.
# 성능 최적화보다 가독성을 높이는 방향으로 함수를 분리하여 작성했습니다.
# 실행시간은 @timer 데코레이터로 로딩 구간마다 측정해 확인했습니다.