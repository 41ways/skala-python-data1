"""
════════════════════════════════════════════════════════════════════
════════════════════════════════════════════════════════════════════

머리말
[실습 1] 자료구조 집계 · 컴프리헨션 · 제너레이터
- 설명: Python_Practice1_Data.json(매출 100건)을 로딩해
        컴프리헨션/Counter/defaultdict/제너레이터로 집계·분석
- 작성자: 정한결
- 변경내역:
        v1 시작
        v2 주석 다듬기
        
════════════════════════════════════════════════════════════════════
════════════════════════════════════════════════════════════════════
"""

import ast
import sys


def load_sales(path):
    """데이터 읽어서 매출 dict 리스트 반환. 실패 시 None. 결과 상관없이 finally에서 종료 메시지 출력"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
             # 파일이 "sales = [...]" 형태의 파이썬 코드라서
             # json.load 대신 앞부분 떼고 ast.literal_eval로 파싱함
        return ast.literal_eval(text.split("=", 1)[1].strip())
    except FileNotFoundError:
        print(f"파일을 찾을 수 없음: {path}")
        return None
    except (ValueError, SyntaxError, IndexError) as e:
        print(f"데이터 형식 오류: {e}")
        return None
    finally:
        print("데이터 로딩 시도 종료")


sales = load_sales("Python_Practice1_Data.json")
if sales is None:
    sys.exit(1)
    
print(sales[0])
print(len(sales))

from collections import Counter, defaultdict




# ══════════════════════════════════
# 1) 리스트/딕셔너리 컴프리헨션
# ══════════════════════════════════

# amount 1000 이상만 (리스트 컴프리헨셔ㅑㄴ)
high = [r for r in sales if r["amount"] >= 1000]

# 위에서 거른 거래 기준으로 지역별 매출 합계 (딕셔너리 컴프리헨션)
# 지역 목록을 set 컴프리헨션으로 뽑고, 지역마다 sum
region_total = {
    region: sum(r["amount"] for r in high if r["region"] == region)
    for region in {r["region"] for r in high}
}

# top3 금액 큰순서
top3 = sorted(high, key=lambda r: r["amount"], reverse=True)[:3]

print("─── 1번 결과 ───")
print(f"필터링 건수: {len(high)}")
print(f"지역별 총매출: {region_total}")
print(f"top3: {[(r['region'], r['amount']) for r in top3]}")





# ══════════════════════════════════
# 2) Counter + defaultdict
# ══════════════════════════════════

# 지역별 거래가 몇 건인지 세기 (카운터)
region_count = Counter(r["region"] for r in sales)

# 카테고리별 amount 리스트 — defaultdict 키 없을때 빈 리스트
cat_amounts = defaultdict(list)
for r in sales:
    cat_amounts[r["category"]].append(r["amount"])

print("─── 2번 결과 ───")
print(f"지역별 건수 top3: {region_count.most_common(3)}")
print(f"카테고리 종류: {list(cat_amounts.keys())}")
print(f"'전자' amount 개수: {len(cat_amounts['전자'])}")





# ══════════════════════════════════
# 3) 제너레이터 — 메모리 비교
# ══════════════════════════════════

# amount 1000 초과인 행만 yield
# 한 행씩 거내는 방식, 대용량 처리에 유리함
def high_sales(rows):
    for r in rows:
        if r["amount"] > 1000:
            yield r

gen = high_sales(sales)                          
lst = [r for r in sales if r["amount"] > 1000]   

print("─── 3번 결과 ───")
print("generator 크기:", sys.getsizeof(gen), "bytes")
print("list 크기     :", sys.getsizeof(lst), "bytes")
assert sys.getsizeof(gen) < sys.getsizeof(lst)
print("메모리 비교 assert 통과")






# ══════════════════════════════════
# 4) 종합 — 월별, 카테고리별 매출 집계
#    (컴프리헨션 + defaultdict)
# ══════════════════════════════════
# defaultdict로 월별, 카테고리별 총매출 누적
month_cat = defaultdict(float)
for r in sales:
    month_cat[(r["month"], r["category"])] += r["amount"]

# 컴프리헨션으로 최종 dict 정리 
# 보기 좋게 월>카테고리합계 형태로 덩리 (컴프리헨션)
months = {m for m, c in month_cat}
month_cat_total = {
    m: {c: total for (mm, c), total in month_cat.items() if mm == m}
    for m in sorted(months)
}

print("─── 4번 결과 ───")
for m, cats in month_cat_total.items():
    print(m, cats)