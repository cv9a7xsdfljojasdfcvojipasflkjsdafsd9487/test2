
# =============================================================
# 셀 4: NIA 웹 크롤링 및 데이터 수집 로직
# =============================================================

# 필요한 라이브러리가 명시적으로 import되어 있지 않아, 실행을 위해 추가합니다.
# (원래 노트북 코드 셀 내부에서 import 되었을 수 있습니다.)
# from bs4 import BeautifulSoup # 이미 import 됨
# import re # 이미 import 됨

# NIA 메인 페이지 요청
response = requests.get("https://nia.or.kr/site/nia_kor/main.do;jsessionid=6EACE24EADAB8A749EFCC1293267C284.33f82d3a14ca06361270")
html = response.text
soup = BeautifulSoup(html, 'html.parser')

data = []
# '.article.know' 요소는 메인 페이지의 특정 섹션을 가리킵니다.
items=soup.select(".article.know")

# 상위 5개 항목 순회
for i in range(1, 6):
    # 제목, 분류, 링크 생성에 필요한 코드 추출
    try:
        selector_base = f".article.know > ul > li:nth-child({i}) > a"
        
        name = soup.select_one(selector_base).attrs['title']
        category = soup.select_one(f"{selector_base} > span.category").text
        code0 = soup.select_one(selector_base).attrs['onclick']
        
        # onclick 속성에서 3개의 숫자 인자 추출
        pattern = re.compile(r"'([^']*)'")
        raw_arguments = pattern.findall(code0)
        extracted_numbers = [arg for arg in raw_arguments if arg.isdigit()]
        
        # 인자 추출 및 링크 생성
        code1 = extracted_numbers[0]
        code2 = extracted_numbers[1]
        code3 = extracted_numbers[2]
        link = f'https://nia.or.kr/site/nia_kor/ex/bbs/View.do?cbIdx={code1}&bcIdx={code2}&parentSeq={code3}'
        
        # 상세 페이지 접속하여 날짜 추출
        response = requests.get(link)
        html3 = response.text
        soup3 = BeautifulSoup(html3, 'html.parser')
        
        # 날짜 정보가 있는 텍스트 추출 (예: '2025.12.08')
        html_string = soup3.select_one(".src>em").text
        date_parts = html_string.split('.')
        year = date_parts[0]
        month = date_parts[1]
        day = date_parts[2]
        
        # 데이터 리스트에 추가
        data.append([name, category, link, year, month, day])
        
    except AttributeError as e:
        print(f"항목 {i} 처리 중 셀렉터 오류 발생: {e}")
    except IndexError as e:
        print(f"항목 {i} 처리 중 인자 추출 오류 발생: {e}")
    except Exception as e:
        print(f"항목 {i} 처리 중 예상치 못한 오류 발생: {e}")


# =============================================================
# 셀 5: DataFrame 생성 및 출력
# =============================================================
df3 = pd.DataFrame(data, columns=['제목', '분류', '링크', '년', '월', '일'])
# df3 # (스크립트에서는 DataFrame을 명시적으로 print 해야 출력이 남습니다.)
# print(df3.head()) # 필요하다면 데이터 확인을 위해 사용

# =============================================================
# 셀 6: JSON 파일 이어 붙이기 및 저장 로직
# =============================================================

full_path = 'nia.json' # 경로를 nia.json으로 변경 (원래 코드가 실행된 후 변경된 이름)
new_data = df3.to_dict('records')

existing_data = []

# 1. 기존 JSON 파일 로드
if os.path.exists(full_path):
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content:
                existing_data = json.loads(content)
            else:
                print("기존 JSON 파일은 존재하지만 비어 있습니다. 새 데이터만 저장합니다.")
    except Exception as e:
        print(f"기존 JSON 파일 로드 중 오류 발생 ({e}). 새 데이터만 저장합니다.")
        existing_data = []

# 2. 새 데이터와 기존 데이터를 합치기
combined_data = existing_data + new_data

# 3. 중복 제거 (가장 중요한 단계)
# '링크'를 기준으로 중복 제거를 위한 Set을 생성합니다.
seen_links = set()
final_data = []

for item in combined_data:
    link = item.get('링크')
    
    # '링크'가 None이거나 비어있지 않고, 아직 처리하지 않은 링크인 경우에만 추가
    if link and link not in seen_links:
        final_data.append(item)
        seen_links.add(link)
        
print(f"총 {len(existing_data)}개의 기존 데이터와 {len(new_data)}개의 새 데이터를 합쳤습니다.")
print(f"중복을 제거한 후 최종 데이터는 총 {len(final_data)}개입니다.")

# 4. 최종 데이터를 JSON 파일로 저장 (덮어쓰기)
with open(full_path, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

print(f"\n최종 데이터가 '{full_path}'에 성공적으로 저장되었습니다.")
