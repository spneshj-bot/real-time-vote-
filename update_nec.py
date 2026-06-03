#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
중앙선관위 제9회 지방선거(2026-06-03) 부산광역시장 개표 현황을 수집해
같은 폴더에 data.json 으로 저장한다.  GitHub Action이 5분마다 실행한다.
브라우저는 CORS로 선관위를 직접 못 부르므로, 서버(Action)에서 받아 커밋하고
페이지는 같은 출처의 data.json만 읽는다.
"""
import urllib.request, re, html, json, sys
from datetime import datetime, timedelta, timezone

URL = ("https://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?"
       "electionId=0020260603&requestURI=/electioninfo/0020260603/vc/vccp09.jsp&"
       "topMenuId=VC&secondMenuId=VCCP09&menuId=VCCP09&"
       "statementId=VCCP09_%233&electionCode=3&cityCode=2600&townCode=-1")

NAMES = ['중구','서구','동구','영도구','부산진구','동래구','남구','북구',
         '해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군']

def cells(r):
    cs = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, re.S)
    return [html.unescape(re.sub(r'<[^>]+>', '', c)).replace('\xa0', ' ').strip() for c in cs]

def to_int(x):
    try: return int(float(x.replace(',', '')))
    except: return 0

def to_float(x):
    try: return float(x.replace(',', ''))
    except: return 0.0

def main():
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Mozilla/5.0 (election-dashboard)",
        "Referer": "https://info.nec.go.kr/"
    })
    raw = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', raw, re.S)

    # 컬럼 순서(선관위): 구,선거인,투표,더불어민주당 전재수,국민의힘 박형준,개혁신당 정이한,계,무효,기권,개표율
    districts, total = {}, None
    for r in rows:
        cs = cells(r)
        if len(cs) >= 10 and cs[0].replace(' ', '') in (NAMES + ['합계']):
            nm = cs[0].replace(' ', '')
            rec = {"jeon": to_int(cs[3]), "bak": to_int(cs[4]), "etc": to_int(cs[5]),
                   "valid": to_int(cs[6]), "rate": to_float(cs[9])}
            if nm == '합계':
                total = rec
            else:
                districts[nm] = rec

    # 안전장치: 파싱 실패 시 기존 data.json 을 덮어쓰지 않는다
    if total is None or len(districts) < 16:
        print("parse failed: districts=%d total=%s" % (len(districts), total))
        sys.exit(1)

    kst = (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
    out = {"updated_kst": kst, "rate": total["rate"], "total": total, "districts": districts}
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("ok %s  개표 %.2f%%  전재수 %d  박형준 %d" % (kst, total["rate"], total["jeon"], total["bak"]))

if __name__ == "__main__":
    main()
