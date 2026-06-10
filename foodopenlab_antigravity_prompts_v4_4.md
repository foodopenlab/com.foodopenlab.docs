# foodopsagent — 안티그래비티 작업 지시서 v4.4
> 작성일: 2026-06-10
> 아키텍처: 헥사고날 + 클린 + DDD + 프랙탈 슬라이스
> 프레임워크: FastAPI + PostgreSQL (NeonDB) + SQLAlchemy 2.0 (async)
> LLM: Gemini 3.0 Flash
> v3 → v4 변경: 일일 리포트 시스템 + 전문가 피드백 루프 추가
> v4 → v4.1 변경: 최신 연구 동향 섹션 추가 (PubMed API + RISS API)
> v4.1 → v4.2 변경: 뉴스 소스 확장 (식품저널·푸드아이콘 크롤러) + FIS 식품산업통계 섹션 추가 (Open API + 뉴스레터 크롤러)
> v4.2 → v4.3 변경: RissAdapter → ScienceOnAdapter 교체 (KISTI ScienceON API Gateway, 티켓: ARTI) + FisApiAdapter 제외 (사업자 전용) + FisNewsletterCrawlerAdapter 단독 운영
> v4.3 → v4.4 변경: summary HTML 저장 + summary_preview 컬럼 추가 / LLM 역할 포맷터로 변경 + 섹션별 항목 수 제한 / 식품유형축 공식분류 기반 25개 재편 + 대분류·중분류 2단계 계층 구조 / 카테고리 선택 미디어 3개 + 식품유형 대분류 3개×중분류 3개 / flat 카테고리 4개(특수영양·특수의료·알가공·벌꿀화분) 중분류 없음 / 신규 가입자 당일 발송 제외 / 빈 섹션 "당일 특이사항 없음" 처리 / 배치 스케줄 2단계 분리(09:40 크롤링, 10:30 생성)

---

## 설계 원칙 (반드시 숙지)

```
1. 프랙탈 원칙
   슬라이스 1개 = router + interactor + domain + adapter + repository 풀세트
   라우터 없는 슬라이스는 존재하지 않음

2. 헥사고날 포트-어댑터
   Interactor는 Port(인터페이스)만 의존
   외부 시스템(API, 크롤러, LLM)은 모두 Adapter로 구현

3. DDD
   도메인 로직은 Entity / VO 안에
   Interactor는 조율만, 비즈니스 규칙은 도메인 객체가 책임

4. AI가 활용하는 객체지향
   모든 외부 의존성은 생성자 주입
   단위 테스트 시 Mock Adapter 교체 가능 구조
```

---

## 전체 슬라이스 목록 (총 20개)

| # | 슬라이스 | 라우터 | 비고 |
|---|---|---|---|
| 1 | admins | POST /auth/admin/login | |
| 2 | expert_whitelist | POST /admin/whitelist, GET /admin/whitelist | |
| 3 | expert_users | POST /auth/signup, POST /auth/login | |
| 4 | expert_user_session | POST /auth/refresh, DELETE /auth/logout | |
| 5 | anonymous | POST /anonymous | 쿠키 자동 발급 |
| 6 | agent_session | POST /sessions, GET /sessions/{id} | |
| 7 | agent_message | POST /sessions/{id}/messages | |
| 8 | satisfaction_feedback | POST /messages/{id}/feedback/satisfaction | |
| 9 | expert_feedback | POST /messages/{id}/feedback/expert | |
| 10 | recall | GET /recall | 식품안전나라 API |
| 11 | enforcement | GET /enforcement | 식품안전나라 API |
| 12 | regulation | GET /regulation | 법제처 API + Gemini |
| 13 | haccp_certification | GET /haccp | 식품안전나라 API |
| 14 | admin_dashboard | GET /admin/feedback/summary 외 | |
| 15 | expert_user_industry | GET /mypage/industry, PUT /mypage/industry | 업종 선택 |
| 16 | industry_category | GET /admin/industry-categories | 카테고리 마스터 |
| 17 | daily_report | GET /mypage/reports, GET /mypage/reports/{id}, POST /mypage/reports/{id}/save, GET /mypage/reports/{id}/download | |
| 18 | report_scheduler | POST /admin/reports/generate | 배치 트리거 |
| 19 | report_feedback | POST /mypage/reports/{id}/feedback, GET /mypage/reports/{id}/feedback | |
| 20 | report_feedback_analysis | GET /admin/report-feedback/analysis, POST /admin/report-feedback/analyze | |

> 총 라우터 26개

---

## ERD v9 (v8 + 일일 리포트 시스템 추가)

```
v8 기존 테이블 (변경 없음)
├── ADMINS
├── EXPERT_WHITELIST
├── EXPERT_USERS          ← industry_code 컬럼 제거 (EXPERT_USER_INDUSTRY로 분리)
├── EXPERT_USER_SESSION
├── ANONYMOUS
├── AGENT_SESSION
├── AGENT_MESSAGE
├── SATISFACTION_FEEDBACK
├── EXPERT_FEEDBACK
├── API_USAGE_LOG
└── SEARCH_LOG

v9 신규 테이블
├── INDUSTRY_CATEGORY
├── EXPERT_USER_INDUSTRY
├── DAILY_REPORT
├── REPORT_FEEDBACK
└── REPORT_FEEDBACK_ANALYSIS
```

### INDUSTRY_CATEGORY

```sql
CREATE TABLE industry_category (
    code           VARCHAR PRIMARY KEY,
    -- media 대분류: 'media_meat' 등
    -- foodtype 대분류: 'ft_meat' 등
    -- foodtype 중분류: 'ft_meat_ham' 등
    type           VARCHAR NOT NULL CHECK (type IN ('media', 'foodtype')),
    parent_code    VARCHAR REFERENCES industry_category(code),
    -- NULL: 대분류 / 값 있음: 중분류
    depth          SMALLINT NOT NULL DEFAULT 1,
    -- 1=대분류, 2=중분류
    is_flat        BOOLEAN NOT NULL DEFAULT false,
    -- true: 중분류 없이 대분류만 운영 (특수영양·특수의료·알가공·벌꿀화분)
    name_ko        VARCHAR NOT NULL,
    crawler_param  VARCHAR,
    -- media 타입: 'S2N5' (식품음료신문 섹션코드)
    -- foodtype 타입: NULL
    keywords       TEXT[] NOT NULL DEFAULT '{}',
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### EXPERT_USER_INDUSTRY

```sql
CREATE TABLE expert_user_industry (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_user_id   UUID NOT NULL REFERENCES expert_users(id) ON DELETE CASCADE,
    category_type    VARCHAR NOT NULL CHECK (category_type IN ('media', 'foodtype')),
    category_code    VARCHAR NOT NULL REFERENCES industry_category(code),
    -- media: 대분류 코드 (depth=1)
    -- foodtype flat: 대분류 코드 (depth=1, is_flat=true)
    -- foodtype 일반: 중분류 코드 (depth=2)
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (expert_user_id, category_type, category_code)
);
-- 애플리케이션 레벨 제한:
-- media: 대분류 최대 3개
-- foodtype 일반: 대분류당 중분류 최대 3개, 대분류 최대 3개 → 최대 9개 row
-- foodtype flat: 대분류 직접 저장, 대분류 3개 카운트에 포함
```

### DAILY_REPORT

```sql
CREATE TABLE daily_report (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_user_id   UUID NOT NULL REFERENCES expert_users(id) ON DELETE CASCADE,
    report_date      DATE NOT NULL,
    generated_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at       TIMESTAMP NOT NULL,
    -- generated_at + 7일, is_saved=true면 만료 무시
    is_saved         BOOLEAN NOT NULL DEFAULT false,

    -- LLM 포맷팅 결과 (HTML 저장)
    -- 프론트: dangerouslySetInnerHTML + DOMPurify.sanitize() 필수
    summary          TEXT NOT NULL,

    -- 목록 미리보기용 plain text (HTML 태그 제거 후 150자)
    -- summary 저장 직전 백엔드에서 추출
    summary_preview  VARCHAR(150) NOT NULL DEFAULT '',

    -- 섹션별 원본 수집 데이터 (LLM 입력 소스)
    raw_news         JSONB NOT NULL DEFAULT '[]',
    -- [{title, url, published_at, source}]
    raw_recalls      JSONB NOT NULL DEFAULT '[]',
    raw_laws         JSONB NOT NULL DEFAULT '[]',
    raw_mfds         JSONB NOT NULL DEFAULT '[]',
    -- 식약처 보도자료
    raw_research     JSONB NOT NULL DEFAULT '[]',
    -- [{title, title_en, url, source, abstract_keywords}]
    raw_stats        JSONB NOT NULL DEFAULT '[]',
    -- [{title, url, source}]
    raw_risk         JSONB NOT NULL DEFAULT '{}',
    -- {level: 'high'|'medium'|'low', reason, weather}

    UNIQUE (expert_user_id, report_date)
    -- 하루 1개만 생성
);
```

### REPORT_FEEDBACK

```sql
CREATE TABLE report_feedback (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id             UUID NOT NULL REFERENCES daily_report(id) ON DELETE CASCADE,
    expert_user_id        UUID NOT NULL REFERENCES expert_users(id) ON DELETE CASCADE,
    created_at            TIMESTAMP NOT NULL DEFAULT NOW(),

    -- 섹션별 유용성 체크 (복수 선택)
    useful_sections       TEXT[] NOT NULL DEFAULT '[]',
    -- ['NEWS', 'RECALL', 'LAW', 'MFDS', 'RISK', 'RESEARCH', 'STATS']

    -- 서술형 피드백 3종 (최소 1개 필수)
    content_feedback      TEXT,
    -- "오늘 소시지 관련 회수 정보가 누락됐어요"
    missing_feedback      TEXT,
    -- "원료 가격 동향이 있으면 좋겠어요"
    improvement_feedback  TEXT,
    -- "식약처 요약이 너무 길어요"

    -- 전반적 유용성 점수
    usefulness_score      SMALLINT NOT NULL CHECK (usefulness_score BETWEEN 1 AND 5),

    UNIQUE (report_id, expert_user_id)
    -- 리포트당 1회만 제출
);
```

### REPORT_FEEDBACK_ANALYSIS

```sql
CREATE TABLE report_feedback_analysis (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    industry_code    VARCHAR NOT NULL,
    -- INDUSTRY_CATEGORY.code 참조 (FK 없음, 복합 업종 분석 가능)
    analyzed_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    feedback_count   INTEGER NOT NULL,
    period_start     DATE NOT NULL,
    period_end       DATE NOT NULL,

    -- LLM 분석 결과
    missing_topics   JSONB NOT NULL DEFAULT '[]',
    -- ["원료 가격 동향", "수입산 비중", ...]
    improvement_keys JSONB NOT NULL DEFAULT '[]',
    -- ["요약 너무 길다", "링크 깨짐", ...]
    useful_sections  JSONB NOT NULL DEFAULT '{}',
    -- {"NEWS": 0.85, "RECALL": 0.92, "MFDS": 0.71, ...}
    summary          TEXT NOT NULL,
    action_items     JSONB NOT NULL DEFAULT '[]'
    -- ["MFDS 보도자료 요약 2줄로 축소", ...]
);
```

---

## 도메인 객체 전체 목록

### Value Objects (VO)

```python
class ActorType(str, Enum):
    EXPERT    = "expert"
    ANONYMOUS = "anonymous"

class AuthProvider(str, Enum):
    EMAIL  = "email"
    GOOGLE = "google"

class QueryPattern(str, Enum):
    LAW        = "law"
    INGREDIENT = "ingredient"
    HACCP      = "haccp"
    GENERAL    = "general"

class CategoryType(str, Enum):
    MEDIA    = "media"
    FOODTYPE = "foodtype"

class SectionType(str, Enum):
    NEWS     = "NEWS"
    RECALL   = "RECALL"
    LAW      = "LAW"
    MFDS     = "MFDS"
    RISK     = "RISK"
    RESEARCH = "RESEARCH"   # 최신 연구 동향 (PubMed + RISS)
    STATS    = "STATS"      # 식품산업통계 (FIS Open API + 뉴스레터)

class RiskLevel(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"

class ReportItem:
    title:        str
    url:          str
    source:       str
    published_at: date

class ReportSection:
    type:     SectionType
    items:    list[ReportItem]
    is_empty: bool  # 수집 결과 없음 여부

    @property
    def empty_message(self) -> str:
        return "당일 특이사항 없음" if self.is_empty else ""

class IndustryFilter:
    media_codes:        list[str]  # media 대분류 최대 3개
    foodtype_mid_codes: list[str]  # foodtype 중분류 최대 9개 (대분류 3 × 중분류 3)
    #                              # flat 카테고리(is_flat=true)는 대분류 코드 직접 포함

    def to_section_codes(self) -> list[str]:
        # media_codes → crawler_param 목록
        # ['S2N5', 'S2N10', 'S2N2']
        ...

    def to_keywords(self) -> list[str]:
        # foodtype_mid_codes의 keywords 합집합 반환
        # 중분류 9개 × 평균 3개 키워드 = 약 27개
        ...
```

### Entities

```python
class Admin:
    id:           UUID
    email:        str
    password_hash: str
    created_at:   datetime

class ExpertUser:
    id:            UUID
    email:         str
    password_hash: str
    invited_name:  str
    auth_provider: AuthProvider
    created_at:    datetime

class Anonymous:
    id:         UUID
    created_at: datetime

class ExpertUserIndustry:
    id:             UUID
    expert_user_id: UUID
    category_type:  CategoryType
    category_code:  str
    created_at:     datetime

class IndustryCategory:
    code:          str
    type:          CategoryType
    name_ko:       str
    crawler_param: str | None
    keywords:      list[str]

class DailyReport:
    id:             UUID
    expert_user_id: UUID
    report_date:    date
    generated_at:   datetime
    expires_at:     datetime
    is_saved:       bool
    summary:        str
    sections:       list[ReportSection]

    def is_expired(self) -> bool:
        return not self.is_saved and datetime.now() > self.expires_at

class ReportFeedback:
    id:                   UUID
    report_id:            UUID
    expert_user_id:       UUID
    created_at:           datetime
    useful_sections:      list[SectionType]
    content_feedback:     str | None
    missing_feedback:     str | None
    improvement_feedback: str | None
    usefulness_score:     int

    def is_valid(self) -> bool:
        return bool(
            self.usefulness_score and
            any([
                self.content_feedback,
                self.missing_feedback,
                self.improvement_feedback,
            ])
        )

class FeedbackAnalysis:
    id:               UUID
    industry_code:    str
    analyzed_at:      datetime
    feedback_count:   int
    period_start:     date
    period_end:       date
    missing_topics:   list[str]
    improvement_keys: list[str]
    useful_sections:  dict[str, float]
    summary:          str
    action_items:     list[str]
```

---

## 슬라이스별 상세 명세

---

### Slice 15 — expert_user_industry

**라우터**
```
GET /mypage/industry   → 내 업종 선택 현황 조회
PUT /mypage/industry   → 업종 선택 수정
```

**Interactor**
```python
class ExpertUserIndustryInteractor:
    MAX_MEDIA    = 3   # 미디어 대분류 최대 3개
    MAX_FT_PARENT = 3  # 식품유형 대분류 최대 3개
    MAX_FT_CHILD  = 3  # 대분류당 중분류 최대 3개

    async def get_my_industry(self, expert_user_id: UUID) -> list[ExpertUserIndustry]:
        return await self.repo.find_by_user(expert_user_id)

    async def update(
        self,
        expert_user_id: UUID,
        media_codes: list[str],
        foodtype_selections: list[dict],
        # foodtype_selections 구조:
        # [
        #   {"code": "ft_meat_ham",   "parent_code": "ft_meat"},   # 일반 중분류
        #   {"code": "ft_egg",        "parent_code": None},         # flat 대분류
        # ]
    ):
        # 미디어 최대 3개 검증
        if len(media_codes) > self.MAX_MEDIA:
            raise BusinessRuleViolation("뉴스소스는 최대 3개까지 선택 가능합니다.")

        # 식품유형 대분류 최대 3개 검증
        parent_codes = {
            s["parent_code"] if s["parent_code"] else s["code"]
            for s in foodtype_selections
        }
        if len(parent_codes) > self.MAX_FT_PARENT:
            raise BusinessRuleViolation("식품유형 대분류는 최대 3개까지 선택 가능합니다.")

        # 대분류별 중분류 최대 3개 검증
        for parent in parent_codes:
            children = [
                s for s in foodtype_selections
                if s["parent_code"] == parent
            ]
            if len(children) > self.MAX_FT_CHILD:
                raise BusinessRuleViolation(
                    f"대분류당 중분류는 최대 3개까지 선택 가능합니다."
                )

        # 기존 전체 삭제 후 재저장 (PUT 시맨틱)
        await self.repo.delete_by_user(expert_user_id)

        for code in media_codes:
            await self.repo.save(ExpertUserIndustry(
                expert_user_id=expert_user_id,
                category_type=CategoryType.MEDIA,
                category_code=code,
            ))

        for sel in foodtype_selections:
            # flat 대분류: 대분류 코드 직접 저장
            # 일반 중분류: 중분류 코드 저장 (parent_code로 대분류 역추적)
            await self.repo.save(ExpertUserIndustry(
                expert_user_id=expert_user_id,
                category_type=CategoryType.FOODTYPE,
                category_code=sel["code"],
            ))
```

---

### Slice 16 — industry_category

**라우터**
```
GET /admin/industry-categories        → 카테고리 마스터 전체 조회
PUT /admin/industry-categories/{code} → 키워드 수정 (피드백 분석 후 튜닝용)
```

**초기 시드 데이터 (migrations에 포함)**
```python
# ─────────────────────────────────────────
# MEDIA 대분류 (17개) — depth=1, is_flat=False
# (code, name_ko, crawler_param, keywords)
# ─────────────────────────────────────────
MEDIA_CATEGORIES = [
    ("media_meat",        "육가공",          "S2N5",       ["햄", "소시지", "육가공", "돈육", "베이컨"]),
    ("media_dairy",       "유가공",          "S2N10",      ["우유", "치즈", "버터", "유가공", "낙농"]),
    ("media_beverage",    "음료·주류",       "S2N6",       ["음료", "주류", "두유", "맥주", "소주"]),
    ("media_bakery",      "제과·베이커리",   "S2N12",      ["빵", "케이크", "과자", "베이커리"]),
    ("media_ramen",       "라면·면류",       "S2N15",      ["라면", "면류", "국수", "파스타"]),
    ("media_sauce",       "간편식·소스",     "S2N16",      ["간편식", "소스", "즉석", "HMR"]),
    ("media_additive",    "소재·첨가물",     "S2N4",       ["첨가물", "소재", "보존료", "당류"]),
    ("media_fermented",   "전통·발효식품",   "S2N13",      ["장류", "김치", "발효", "된장"]),
    ("media_agri",        "농수산·펫푸드",   "S2N3",       ["농산물", "수산물", "펫푸드"]),
    ("media_foodservice", "외식·프랜차이즈", "S2N7",       ["외식", "프랜차이즈", "급식"]),
    ("media_distribution","급식·유통",       "S2N9",       ["유통", "급식", "물류"]),
    ("media_packaging",   "포장·기계",       "S2N18",      ["포장", "기계", "용기"]),
    ("media_health",      "건기식",          "S2N2",       ["건강기능식품", "건기식", "홍삼"]),
    ("media_foodtech",    "푸드테크",        "S2N1",       ["푸드테크", "대체육", "배양육"]),
    ("media_esg",         "ESG",             "S2N19",      ["ESG", "친환경", "탄소중립"]),
    ("media_foodjournal", "식품저널",        "FOODJOURNAL",["식품", "식품산업", "식품정책", "원료", "가공"]),
    ("media_foodicon",    "푸드아이콘",      "FOODICON",   ["식품", "유통", "외식", "트렌드", "신제품"]),
]

# ─────────────────────────────────────────
# FOODTYPE 대분류 (25개) — depth=1
# (code, name_ko, is_flat, keywords)
# is_flat=True: 중분류 없이 대분류만 운영
# ─────────────────────────────────────────
FOODTYPE_PARENT_CATEGORIES = [
    ("ft_confectionery", "과자류·빵류·떡류",      False, ["과자", "빵", "떡", "케이크", "쿠키"]),
    ("ft_ice",           "빙과류",                False, ["아이스크림", "빙과", "샤베트"]),
    ("ft_chocolate",     "코코아·초콜릿류",       False, ["초콜릿", "코코아", "초콜릿가공품"]),
    ("ft_sugar",         "당류",                  False, ["설탕", "시럽", "올리고당", "물엿", "과당"]),
    ("ft_jam",           "잼류",                  False, ["잼", "마멀레이드"]),
    ("ft_soy",           "두부류·묵류",           False, ["두부", "묵", "유바", "가공두부"]),
    ("ft_oil",           "식용유지류",            False, ["식용유", "참기름", "들기름", "마가린", "쇼트닝"]),
    ("ft_noodle",        "면류",                  False, ["라면", "국수", "파스타", "당면", "생면"]),
    ("ft_beverage",      "음료류",                False, ["음료", "탄산", "주스", "두유", "차", "커피"]),
    ("ft_infant",        "특수영양식품",           True,  ["분유", "이유식", "조제유", "성장기조제식", "임산부식품"]),
    ("ft_medical",       "특수의료용도식품",       True,  ["환자식", "영양조제식품", "당뇨환자식", "연하곤란식"]),
    ("ft_fermented_soy", "장류",                  False, ["된장", "간장", "고추장", "청국장", "메주"]),
    ("ft_seasoning",     "조미식품",              False, ["소스", "케첩", "마요네즈", "식초", "카레", "향신료", "식염"]),
    ("ft_pickle",        "절임류·조림류·김치류",  False, ["김치", "장아찌", "피클", "절임", "조림"]),
    ("ft_liquor",        "주류",                  False, ["맥주", "소주", "와인", "막걸리", "위스키"]),
    ("ft_agri",          "농산가공식품류",         False, ["전분", "밀가루", "쌀", "시리얼", "견과류"]),
    ("ft_meat",          "식육가공품류·포장육",   False, ["햄", "소시지", "베이컨", "양념육", "포장육"]),
    ("ft_egg",           "알가공품류",             True,  ["달걀", "계란", "전란액", "난황", "알가공품"]),
    ("ft_dairy",         "유가공품류",            False, ["우유", "치즈", "버터", "발효유", "요거트", "분유"]),
    ("ft_fish",          "수산가공식품류",         False, ["어묵", "젓갈", "건어물", "어육소시지", "액젓"]),
    ("ft_animal",        "동물성가공식품류",       False, ["곤충가공", "자라", "기타동물성가공"]),
    ("ft_honey",         "벌꿀·화분가공품류",     True,  ["벌꿀", "꿀", "로열젤리", "화분", "프로폴리스"]),
    ("ft_instant",       "즉석식품류",            False, ["즉석밥", "HMR", "레토르트", "밀키트", "만두"]),
    ("ft_etc",           "기타식품류",            False, ["기타가공품", "효소식품"]),
    ("ft_health",        "건강기능식품",           False, ["홍삼", "비타민", "프로바이오틱스", "오메가3", "건강기능식품"]),
    # 건강기능식품은 식품위생법이 아닌 건강기능식품법 별도 관리
]

# ─────────────────────────────────────────
# FOODTYPE 중분류 — depth=2, is_flat=False
# (code, parent_code, name_ko, keywords)
# is_flat=True 대분류(ft_infant, ft_medical, ft_egg, ft_honey)는 중분류 없음
# ─────────────────────────────────────────
FOODTYPE_CHILD_CATEGORIES = [
    # 1. 과자류·빵류·떡류
    ("ft_confectionery_snack",  "ft_confectionery", "과자·캔디류",  ["과자", "캔디", "추잉껌"]),
    ("ft_confectionery_bread",  "ft_confectionery", "빵류",         ["빵", "케이크", "쿠키"]),
    ("ft_confectionery_rice",   "ft_confectionery", "떡류",         ["떡", "떡볶이떡", "인절미"]),

    # 2. 빙과류
    ("ft_ice_cream",    "ft_ice", "아이스크림류",  ["아이스크림", "저지방아이스크림", "아이스밀크"]),
    ("ft_ice_mix",      "ft_ice", "아이스크림믹스류", ["아이스크림믹스"]),
    ("ft_ice_other",    "ft_ice", "빙과·얼음류",  ["빙과", "샤베트", "식용얼음"]),

    # 3. 코코아·초콜릿류
    ("ft_chocolate_cocoa", "ft_chocolate", "코코아가공품류", ["코코아매스", "코코아버터", "코코아분말"]),
    ("ft_chocolate_choco", "ft_chocolate", "초콜릿류",       ["초콜릿", "밀크초콜릿", "화이트초콜릿", "준초콜릿"]),

    # 4. 당류
    ("ft_sugar_sugar",   "ft_sugar", "설탕류",    ["설탕", "기타설탕"]),
    ("ft_sugar_oligo",   "ft_sugar", "올리고당류", ["올리고당", "올리고당가공품"]),
    ("ft_sugar_syrup",   "ft_sugar", "당시럽·엿류",["물엿", "덱스트린", "과당"]),

    # 5. 잼류 (중분류 1개 — 선택 시 바로 확정)
    ("ft_jam_jam",  "ft_jam", "잼",  ["잼", "기타잼"]),

    # 6. 두부류·묵류
    ("ft_soy_tofu", "ft_soy", "두부류", ["두부", "유바", "가공두부"]),
    ("ft_soy_muk",  "ft_soy", "묵류",   ["묵", "도토리묵", "청포묵"]),

    # 7. 식용유지류
    ("ft_oil_plant",   "ft_oil", "식물성유지류",  ["콩기름", "올리브유", "참기름", "들기름", "채종유"]),
    ("ft_oil_animal",  "ft_oil", "동물성유지류",  ["식용우지", "식용돈지", "어유"]),
    ("ft_oil_process", "ft_oil", "식용유지가공품",["혼합식용유", "마가린", "쇼트닝", "식물성크림"]),

    # 8. 면류
    ("ft_noodle_fresh", "ft_noodle", "생면·숙면",  ["생면", "숙면"]),
    ("ft_noodle_dry",   "ft_noodle", "건면",        ["건면", "국수", "파스타"]),
    ("ft_noodle_fried", "ft_noodle", "유탕면",      ["라면", "유탕면"]),

    # 9. 음료류
    ("ft_beverage_carbonate", "ft_beverage", "탄산음료류",  ["탄산음료", "탄산수"]),
    ("ft_beverage_tea",       "ft_beverage", "다류",         ["침출차", "액상차", "고형차", "녹차", "홍차"]),
    ("ft_beverage_fruit",     "ft_beverage", "과채음료류",   ["과채주스", "농축과채즙", "과채음료"]),
    ("ft_beverage_fermented", "ft_beverage", "발효음료류",   ["유산균음료", "효모음료", "기타발효음료"]),
    ("ft_beverage_soymilk",   "ft_beverage", "두유류",       ["두유", "원액두유", "가공두유"]),
    ("ft_beverage_coffee",    "ft_beverage", "커피류",       ["원두", "인스턴트커피", "커피믹스", "액상커피"]),
    ("ft_beverage_other",     "ft_beverage", "기타음료",     ["혼합음료", "음료베이스", "이온음료"]),

    # 12. 장류
    ("ft_fermented_soy_soy",    "ft_fermented_soy", "간장류",  ["한식간장", "양조간장", "혼합간장"]),
    ("ft_fermented_soy_paste",  "ft_fermented_soy", "된장·고추장류", ["된장", "고추장", "춘장"]),
    ("ft_fermented_soy_other",  "ft_fermented_soy", "청국장·혼합장", ["청국장", "혼합장", "기타장류"]),

    # 13. 조미식품
    ("ft_seasoning_sauce",   "ft_seasoning", "소스류",         ["소스", "마요네즈", "케첩", "복합조미식품"]),
    ("ft_seasoning_vinegar", "ft_seasoning", "식초류",         ["발효식초", "희석초산"]),
    ("ft_seasoning_spice",   "ft_seasoning", "향신료·고춧가루",["고춧가루", "카레", "천연향신료", "후추"]),
    ("ft_seasoning_salt",    "ft_seasoning", "식염류",         ["천일염", "정제소금", "가공소금"]),

    # 14. 절임류·조림류·김치류
    ("ft_pickle_kimchi", "ft_pickle", "김치류",  ["김치", "깍두기", "총각김치", "김칫속"]),
    ("ft_pickle_pickle", "ft_pickle", "절임류",  ["절임식품", "당절임", "장아찌", "피클"]),
    ("ft_pickle_jorim",  "ft_pickle", "조림류",  ["조림"]),

    # 15. 주류
    ("ft_liquor_fermented",  "ft_liquor", "발효주류",  ["탁주", "막걸리", "약주", "청주", "맥주", "과실주"]),
    ("ft_liquor_distilled",  "ft_liquor", "증류주류",  ["소주", "위스키", "브랜디", "리큐르"]),
    ("ft_liquor_other",      "ft_liquor", "기타주류",  ["기타주류", "주정"]),

    # 16. 농산가공식품류
    ("ft_agri_starch",  "ft_agri", "전분·밀가루류",    ["전분", "밀가루", "영양강화밀가루"]),
    ("ft_agri_cereal",  "ft_agri", "시리얼·곡류가공",  ["시리얼", "쌀가공품", "곡류가공품"]),
    ("ft_agri_nut",     "ft_agri", "견과·과채가공품",  ["땅콩버터", "견과류가공품", "과채가공품", "건과"]),

    # 17. 식육가공품류·포장육
    ("ft_meat_ham",      "ft_meat", "햄류",      ["햄", "생햄", "프레스햄"]),
    ("ft_meat_sausage",  "ft_meat", "소시지류",  ["소시지", "발효소시지", "혼합소시지"]),
    ("ft_meat_양념",     "ft_meat", "양념육·포장육", ["양념육", "분쇄가공육", "포장육", "갈비가공품", "베이컨"]),

    # 19. 유가공품류
    ("ft_dairy_milk",     "ft_dairy", "우유·가공유류",  ["우유", "강화우유", "유산균첨가우유", "가공유"]),
    ("ft_dairy_fermented","ft_dairy", "발효유류",       ["발효유", "요거트", "농후발효유", "크림발효유"]),
    ("ft_dairy_cheese",   "ft_dairy", "치즈·버터류",    ["치즈", "가공치즈", "버터", "가공버터"]),
    ("ft_dairy_powder",   "ft_dairy", "분유·농축유류",  ["전지분유", "탈지분유", "가당연유", "유청"]),

    # 20. 수산가공식품류
    ("ft_fish_paste",   "ft_fish", "어육가공품류", ["어묵", "어육소시지", "연육", "어육살"]),
    ("ft_fish_salted",  "ft_fish", "젓갈류",       ["젓갈", "양념젓갈", "액젓", "조미액젓"]),
    ("ft_fish_dried",   "ft_fish", "건포·기타",    ["건어포", "조미건어포", "조미김", "한천"]),

    # 21. 동물성가공식품류
    ("ft_animal_insect", "ft_animal", "곤충가공식품",     ["곤충가공식품", "식용곤충"]),
    ("ft_animal_other",  "ft_animal", "기타동물성가공품", ["자라가공식품", "기타식육", "기타동물성"]),

    # 23. 즉석식품류
    ("ft_instant_ready",  "ft_instant", "즉석섭취·편의식품", ["즉석섭취식품", "신선편의식품", "간편조리세트"]),
    ("ft_instant_cook",   "ft_instant", "즉석조리식품",      ["즉석조리식품", "레토르트", "즉석밥", "HMR", "밀키트"]),
    ("ft_instant_mandu",  "ft_instant", "만두류",            ["만두", "만두피"]),

    # 24. 기타식품류
    ("ft_etc_enzyme",  "ft_etc", "효소식품",  ["효소식품"]),
    ("ft_etc_other",   "ft_etc", "기타가공품",["기타가공품"]),

    # 25. 건강기능식품
    ("ft_health_recognized", "ft_health", "개별인정형",  ["개별인정형원료", "기능성원료"]),
    ("ft_health_listed",     "ft_health", "고시형",      ["홍삼", "비타민", "프로바이오틱스", "오메가3", "루테인", "콜라겐"]),
    ("ft_health_other",      "ft_health", "기타건기식",  ["EPA", "DHA", "식이섬유", "칼슘", "마그네슘"]),
]
```

---

### Slice 17 — daily_report

**라우터**
```
GET  /mypage/reports              → 내 리포트 목록 (최대 7개, 만료 미저장 제외)
GET  /mypage/reports/{id}         → 리포트 상세
POST /mypage/reports/{id}/save    → 저장 플래그 설정 (만료 방지)
GET  /mypage/reports/{id}/download → PDF/텍스트 다운로드
```

**Ports (인터페이스)**
```python
class ThinkfoodPort(Protocol):
    async def fetch(self, section_codes: list[str]) -> list[ReportItem]: ...

# v4.2: 뉴스 소스가 3개(ThinkfoodCrawler, FoodJournalCrawler, FoodIconCrawler)로 확장됨
# DailyReportInteractor는 CompositeNewsAdapter 하나만 주입받음
# class CompositeNewsAdapter(ThinkfoodPort):
#     adapters: list[ThinkfoodPort]
#     async def fetch(self, section_codes) -> list[ReportItem]:
#         results = await asyncio.gather(*[a.fetch(section_codes) for a in self.adapters])
#         return deduplicate(flatten(results))

class MfdsPressPort(Protocol):
    async def fetch(self, keywords: list[str]) -> list[ReportItem]: ...

class RecallReportPort(Protocol):
    async def fetch(self, keywords: list[str]) -> list[ReportItem]: ...

class RegulationReportPort(Protocol):
    async def fetch(self, keywords: list[str]) -> list[ReportItem]: ...

class FoodRiskPort(Protocol):
    async def fetch(self, keywords: list[str]) -> dict: ...
    # {"level": "high"|"medium"|"low", "reason": "...", "weather": "..."}

class ResearchPort(Protocol):
    async def fetch(
        self,
        keywords: list[str],
        days_back: int = 30,
    ) -> list[ReportItem]: ...
    # 최근 N일 논문 제목 + 원본 링크 (최대 5건)
    # 영문 제목 그대로 반환 (LLM이 리포트 생성 시 한국어 번역 포함)
    # 구현체: PubMedAdapter (해외) + ScienceOnAdapter (국내, KISTI ARTI 티켓)

class FoodStatsPort(Protocol):
    async def fetch(
        self,
        keywords: list[str],
    ) -> list[ReportItem]: ...
    # FIS Open API 통계 지표 + 뉴스레터 크롤링 결과 통합 반환
    # ReportItem.source = "fis_api" | "fis_newsletter"

class ReportLLMPort(Protocol):
    async def generate_summary(
        self,
        sections: list[ReportSection],
        industry_filter: IndustryFilter,
        report_date: date,
    ) -> str: ...
```

**Adapters**
```python
class ThinkfoodCrawlerAdapter(ThinkfoodPort):
    BASE_URL = "https://www.thinkfood.co.kr"

    async def fetch(self, section_codes: list[str]) -> list[ReportItem]:
        items = []
        for code in section_codes:
            url = f"{self.BASE_URL}/news/articleList.html?sc_sub_section_code={code}&view_type=sm"
            # requests + BeautifulSoup
            # a[href*="articleView"] 파싱
            # title + url + published_at 추출
            ...
        return items

class MfdsPressAdapter(MfdsPressPort):
    BASE_URL = "https://www.mfds.go.kr/brd/m_99/list.do"

    async def fetch(self, keywords: list[str]) -> list[ReportItem]:
        # 식약처 보도자료 목록 크롤링
        # 제목에 keywords 포함 여부로 필터링
        ...

class PubMedAdapter(ResearchPort):
    # NCBI E-utilities 공식 무료 API
    # API 키: NCBI 계정 생성 후 발급 (무료)
    # https://www.ncbi.nlm.nih.gov/account/
    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    async def fetch(self, keywords: list[str], days_back: int = 30) -> list[ReportItem]:
        # 1. ESearch → 최근 N일 논문 PMID 목록 조회
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])
        query += f' AND ("last {days_back} days"[PDat])'
        query += ' AND (food[MeSH Terms] OR food safety[MeSH Terms])'

        search_res = await self._get(
            f"{self.BASE}/esearch.fcgi",
            params={
                "db":      "pubmed",
                "term":    query,
                "retmax":  5,
                "sort":    "pub date",
                "api_key": self.api_key,
                "retmode": "json",
            }
        )
        pmids = search_res["esearchresult"]["idlist"]
        if not pmids:
            return []

        # 2. ESummary → 제목 + 날짜 조회
        summary_res = await self._get(
            f"{self.BASE}/esummary.fcgi",
            params={
                "db":      "pubmed",
                "id":      ",".join(pmids),
                "api_key": self.api_key,
                "retmode": "json",
            }
        )
        return [
            ReportItem(
                title=item["title"],
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                source="pubmed",
                published_at=parse_pubmed_date(item["pubdate"]),
            )
            for pmid, item in summary_res["result"].items()
            if pmid != "uids" and item.get("title")
        ]

class ScienceOnAdapter(ResearchPort):
    # KISTI ScienceON API Gateway
    # API 키: https://scienceon.kisti.re.kr → 인증키 신청 (무료, 승인 1~3 영업일)
    # 사용 티켓: ARTI (국내외 학술지·학회논문·학위논문·저널·프로시딩)
    # 환경변수: SCIENCEON_API_KEY
    BASE = "https://scienceon.kisti.re.kr/api"   # ← 실제 엔드포인트는 승인 후 매뉴얼 확인

    async def fetch(self, keywords: list[str], days_back: int = 30) -> list[ReportItem]:
        query = " ".join(keywords[:3])
        start_date = (date.today() - timedelta(days=days_back)).strftime("%Y%m%d")
        end_date = date.today().strftime("%Y%m%d")

        res = await self._get(
            f"{self.BASE}/article/search",   # ARTI 티켓 논문 검색 엔드포인트
            params={
                "apiKey":    self.api_key,
                "query":     query,
                "startDt":   start_date,
                "endDt":     end_date,
                "pageSize":  5,
                "sort":      "date",
                # 실제 파라미터명은 승인 후 ScienceON API 매뉴얼 확인 후 보정
            }
        )
        return [
            ReportItem(
                title=item.get("title", ""),
                url=item.get("url") or f"https://scienceon.kisti.re.kr/srch/selectPORSrchArticle.do?cn={item.get('cn','')}",
                source="scienceon",
                published_at=parse_scienceon_date(item.get("pubYear", "")),
            )
            for item in res.get("items", [])
            if item.get("title")
        ]

# ─────────────────────────────────────────
# v4.2 신규 Adapter (4개)
# ─────────────────────────────────────────

class FoodJournalCrawlerAdapter(ThinkfoodPort):
    """식품저널 (https://www.foodnjournal.com) 크롤러
    - ThinkfoodPort를 재사용: section_codes → 카테고리 URL 매핑
    - crawler_param 값("FOODJOURNAL")은 내부 라우팅 식별자로만 사용
    """
    BASE_URL = "https://www.foodnjournal.com"

    # 카테고리 URL 매핑 (실제 사이트 구조 확인 후 보정 필요)
    SECTION_MAP: dict[str, str] = {
        "FOODJOURNAL": "/news/articleList.html",
        # 필요 시 세부 카테고리 추가:
        # "FOODJOURNAL_POLICY": "/news/articleList.html?sc_section_code=S1N1",
    }

    async def fetch(self, section_codes: list[str]) -> list[ReportItem]:
        items = []
        for code in section_codes:
            path = self.SECTION_MAP.get(code)
            if not path:
                continue
            url = f"{self.BASE_URL}{path}"
            # requests + BeautifulSoup
            # 선택자: 사이트 구조에 맞게 조정 (thinkfood와 유사한 뉴스 목록 패턴 예상)
            # a[href*="articleView"] → title + url + published_at 추출
            ...
        return items


class FoodIconCrawlerAdapter(ThinkfoodPort):
    """푸드아이콘 (https://www.foodicon.co.kr) 크롤러
    - ThinkfoodPort를 재사용
    - crawler_param 값("FOODICON")은 내부 라우팅 식별자로만 사용
    """
    BASE_URL = "https://www.foodicon.co.kr"

    SECTION_MAP: dict[str, str] = {
        "FOODICON": "/news/articleList.html",
        # 필요 시 세부 카테고리 추가
    }

    async def fetch(self, section_codes: list[str]) -> list[ReportItem]:
        items = []
        for code in section_codes:
            path = self.SECTION_MAP.get(code)
            if not path:
                continue
            url = f"{self.BASE_URL}{path}"
            # requests + BeautifulSoup
            # 선택자: 사이트 구조 확인 후 보정
            ...
        return items


class FisNewsletterCrawlerAdapter(FoodStatsPort):
    """FIS 식품산업통계정보 뉴스레터 크롤링
    - 대상: https://www.atfis.or.kr → 뉴스레터 / 간행물 목록
    - 주기: 월간 발행 → 최신 1건만 수집
    - source="fis_newsletter"
    - FIS Open API는 사업자 회원 전용으로 현재 제외 (v4.3)
      → 향후 사업자 등록 후 FisApiAdapter 추가 예정
    """
    BASE_URL = "https://www.atfis.or.kr"
    NEWSLETTER_PATH = "/article/newsletter/list.do"  # ← 실제 경로 확인 필요

    async def fetch(self, keywords: list[str]) -> list[ReportItem]:
        url = f"{self.BASE_URL}{self.NEWSLETTER_PATH}"
        # requests + BeautifulSoup
        # 뉴스레터 목록에서 최신 1~3건 제목 + URL + 발행일 추출
        # keywords 필터: 제목에 keywords 중 하나라도 포함된 것만 수집
        items = []
        # ... 파싱 구현
        return items
```

**Interactor**
```python
# 섹션별 최대 항목 수 (글자수 제한 대신 항목 수로 관리)
SECTION_ITEM_LIMITS = {
    SectionType.NEWS:     10,
    SectionType.RECALL:    5,
    SectionType.LAW:       5,
    SectionType.MFDS:      5,
    SectionType.RISK:      1,
    SectionType.RESEARCH:  5,  # PubMed 3 + ScienceON 2
    SectionType.STATS:     3,
}

# 전체 섹션 비었을 때 출력할 HTML
EMPTY_REPORT_HTML = """
<article class="daily-report empty">
  <p class="empty-notice">오늘은 선택하신 업종 관련 특이사항이 없습니다.</p>
</article>
"""

import re

def extract_preview(html: str, length: int = 150) -> str:
    plain = re.sub(r'<[^>]+>', '', html)
    return plain[:length]

class DailyReportInteractor:
    thinkfood_port:   ThinkfoodPort
    mfds_port:        MfdsPressPort
    recall_port:      RecallReportPort
    regulation_port:  RegulationReportPort
    risk_port:        FoodRiskPort
    research_port:    ResearchPort   # PubMed(해외) + ScienceON(국내) 통합
    stats_port:       FoodStatsPort  # FIS 뉴스레터 크롤러 단독 운영 (v4.3~)
    llm_port:         ReportLLMPort
    report_repo:      DailyReportRepository
    industry_repo:    ExpertUserIndustryRepository
    category_repo:    IndustryCategoryRepository

    async def get_my_reports(self, expert_user_id: UUID) -> list[DailyReport]:
        await self.report_repo.delete_expired_unsaved(expert_user_id)
        return await self.report_repo.find_by_user(expert_user_id)

    async def generate(self, expert_user_id: UUID) -> DailyReport:
        # 오늘 이미 생성됐으면 기존 반환
        existing = await self.report_repo.find_by_user_and_date(
            expert_user_id, today()
        )
        if existing:
            return existing

        # 1. 업종 필터 구성
        industries = await self.industry_repo.find_by_user(expert_user_id)
        categories = await self.category_repo.find_by_codes(
            [i.category_code for i in industries]
        )
        industry_filter = IndustryFilter.from_categories(industries, categories)

        # 2. 병렬 수집
        news, recalls, laws, mfds, risk, research, stats = await asyncio.gather(
            self.thinkfood_port.fetch(industry_filter.to_section_codes()),
            self.recall_port.fetch(industry_filter.to_keywords()),
            self.regulation_port.fetch(industry_filter.to_keywords()),
            self.mfds_port.fetch(industry_filter.to_keywords()),
            self.risk_port.fetch(industry_filter.to_keywords()),
            self.research_port.fetch(industry_filter.to_keywords(), days_back=30),
            self.stats_port.fetch(industry_filter.to_keywords()),
        )

        # 3. 섹션별 항목 수 제한 + 빈 여부 판단
        def make_section(type_, items):
            limited = items[:SECTION_ITEM_LIMITS[type_]]
            return ReportSection(
                type=type_,
                items=limited,
                is_empty=len(limited) == 0,
            )

        sections = [
            make_section(SectionType.NEWS,     news),
            make_section(SectionType.RECALL,   recalls),
            make_section(SectionType.LAW,      laws),
            make_section(SectionType.MFDS,     mfds),
            make_section(SectionType.RISK,     [risk] if risk else []),
            make_section(SectionType.RESEARCH, research),
            make_section(SectionType.STATS,    stats),
        ]

        # 4. 전체 섹션이 모두 비어있으면 LLM 호출 없이 처리
        if all(s.is_empty for s in sections):
            summary = EMPTY_REPORT_HTML
        else:
            summary = await self.llm_port.generate_summary(
                sections=sections,
                industry_filter=industry_filter,
                report_date=today(),
            )

        # 5. 저장
        report = DailyReport(
            expert_user_id=expert_user_id,
            report_date=today(),
            expires_at=now() + timedelta(days=7),
            is_saved=False,
            summary=summary,
            summary_preview=extract_preview(summary),
            sections=sections,
        )
        return await self.report_repo.save(report)

    async def save(self, expert_user_id: UUID, report_id: UUID) -> DailyReport:
        report = await self.report_repo.find(report_id)
        if report.expert_user_id != expert_user_id:
            raise Forbidden()
        report.is_saved = True
        return await self.report_repo.update(report)
```

**LLM 프롬프트 템플릿**
```python
REPORT_PROMPT = """
아래 수집 데이터를 섹션별 HTML 형식으로 변환하세요.
요약·해석·권고 없이 지정된 필드만 추출·정제합니다.

[섹션별 출력 규칙]

NEWS / MFDS / STATS:
- 제목 (원문 그대로) + 하이퍼링크
- 1~2줄 핵심 내용 (수치·날짜 있으면 그대로 포함)
- 출처명 + 날짜

RECALL:
- 제품명 / 식품유형 / 위반사항 / 조치내용 / 유통기한 / 제조지역
- 수치·날짜 원문 그대로 유지
- 출처 하이퍼링크

LAW:
- 법령명 + 하이퍼링크 (조문 직링크 우선)
- 변경내용: 변경전 → 변경후 (수치 있으면 그대로)
- 시행일 / 대상품목

RESEARCH:
- 한국어 번역 제목 (영문 원제 병기)
- 초록 키워드 1~2줄
- 출처(PubMed / ScienceON) + 하이퍼링크

RISK:
- 위험등급 / 한줄 사유 / 날씨 수치

[빈 섹션 처리]
- 수집 데이터가 없는 섹션:
  <p class="empty">당일 특이사항 없음</p>
- 수집은 됐으나 선택 업종({industry_names})과 무관한 경우:
  <p class="empty">해당 업종 관련 특이사항 없음</p>

[공통 규칙]
- 해석·평가·권고 문장 금지 ("주의 필요", "검토 바람" 등 추가 금지)
- URL은 반드시 원본 그대로 유지
- 출력은 아래 HTML 구조만, 다른 텍스트 없이

<article class="daily-report">
  <section class="report-section" data-type="NEWS">
    <ul class="item-list">
      <li class="item-row">
        <a class="item-link" href="{{원본URL}}">{{제목}}</a>
        <p class="item-desc">{{1~2줄 내용}}</p>
        <span class="item-source">{{출처}} · {{날짜}}</span>
      </li>
    </ul>
  </section>

  <section class="report-section" data-type="RECALL">
    <ul class="item-list">
      <li class="item-row">
        <a class="item-link" href="{{원본URL}}">{{제품명}} → {{조치내용}}</a>
        <p class="item-desc">{{식품유형}} | {{위반사항}} | 유통기한 {{날짜}} | {{제조지역}}</p>
        <span class="item-source">{{출처}}</span>
      </li>
    </ul>
  </section>

  <section class="report-section" data-type="LAW">
    <ul class="item-list">
      <li class="item-row">
        <a class="item-link" href="{{조문URL}}">{{법령명}}</a>
        <p class="item-desc">{{변경전}} → {{변경후}} | {{시행일}} | 대상: {{품목}}</p>
        <span class="item-source">{{출처}}</span>
      </li>
    </ul>
  </section>

  <section class="report-section" data-type="MFDS">
    <ul class="item-list">
      <li class="item-row">
        <a class="item-link" href="{{원본URL}}">{{제목}}</a>
        <p class="item-desc">{{1~2줄 내용}}</p>
        <span class="item-source">식약처 · {{날짜}}</span>
      </li>
    </ul>
  </section>

  <section class="report-section" data-type="RISK">
    <div class="risk-block" data-level="{{high|medium|low}}">
      <span class="risk-level">{{위험등급}}</span>
      <span class="risk-desc">{{사유}} | {{날씨 수치}}</span>
    </div>
  </section>

  <section class="report-section" data-type="RESEARCH">
    <ul class="item-list">
      <li class="item-row">
        <a class="item-link" href="{{원본URL}}">{{한국어 번역 제목}}</a>
        <p class="item-desc research-en">{{영문 원제}}</p>
        <p class="item-desc">{{초록 키워드 1~2줄}}</p>
        <span class="item-source">{{PubMed|ScienceON}}</span>
      </li>
    </ul>
  </section>

  <section class="report-section" data-type="STATS">
    <ul class="item-list">
      <li class="item-row">
        <a class="item-link" href="{{원본URL}}">{{제목}}</a>
        <p class="item-desc">{{1~2줄 내용}}</p>
        <span class="item-source">FIS 뉴스레터</span>
      </li>
    </ul>
  </section>
</article>

[수집 데이터]
대상 업종: {industry_names}
수집일: {report_date}

## 업계 뉴스
{news_items}

## 회수·행정처분
{recall_items}

## 법규 변동
{law_items}

## 식약처 보도자료
{mfds_items}

## 식중독 위험 현황
{risk_info}

## 최신 연구 동향
{research_items}
-- PubMed(해외) + ScienceON(국내) 최근 30일 논문
-- 영문 제목은 한국어로 번역하여 원문 병기

## 식품산업 통계·동향
{stats_items}
-- FIS 뉴스레터 (월간, 최신 1~3건)
"""
```

---

### Slice 18 — report_scheduler

**라우터**
```
POST /admin/reports/generate
→ 전체 전문가회원 대상 오늘 리포트 배치 생성 트리거
→ 어드민 전용
```

**Interactor**
```python
class ReportSchedulerInteractor:
    expert_user_repo:        ExpertUserRepository
    industry_repo:           ExpertUserIndustryRepository
    daily_report_interactor: DailyReportInteractor

    async def generate_all(self) -> dict:
        users = await self.expert_user_repo.find_all_active()
        today = date.today()
        success, fail, skipped = 0, 0, 0

        for user in users:
            # 가입 당일 스킵
            if user.created_at.date() == today:
                skipped += 1
                continue

            # 업종 미설정 스킵
            industries = await self.industry_repo.find_by_user(user.id)
            if not industries:
                skipped += 1
                continue

            try:
                await self.daily_report_interactor.generate(user.id)
                success += 1
            except Exception as e:
                fail += 1
                logger.error(f"Report generation failed for {user.id}: {e}")

        return {
            "success": success,
            "fail":    fail,
            "skipped": skipped,
            "total":   len(users),
        }

# 배치 실행 방식 — 2단계 분리
# Step 1 (09:40): 크롤링·수집
# Step 2 (10:30): LLM 포맷팅 + 리포트 생성
# 백엔드 가동 시각: 09:30
```

---

## 배치 실행 설계

### Slice 19 — report_feedback

**라우터**
```
POST /mypage/reports/{id}/feedback → 피드백 제출
GET  /mypage/reports/{id}/feedback → 내 피드백 조회
```

**Interactor**
```python
class ReportFeedbackInteractor:
    feedback_repo: ReportFeedbackRepository
    report_repo:   DailyReportRepository

    async def submit(
        self,
        expert_user_id: UUID,
        report_id: UUID,
        dto: FeedbackCreateDTO,
    ) -> ReportFeedback:

        # 1. 리포트 존재 + 본인 소유 확인
        report = await self.report_repo.find(report_id)
        if not report:
            raise NotFound()
        if report.expert_user_id != expert_user_id:
            raise Forbidden()

        # 2. 중복 제출 방지
        existing = await self.feedback_repo.find_by_report_and_user(
            report_id, expert_user_id
        )
        if existing:
            raise BusinessRuleViolation("이미 피드백을 제출했습니다.")

        # 3. 도메인 유효성 검사
        feedback = ReportFeedback(
            report_id=report_id,
            expert_user_id=expert_user_id,
            **dto.to_domain(),
        )
        if not feedback.is_valid():
            raise ValidationError("점수와 최소 1개의 서술형 피드백이 필요합니다.")

        return await self.feedback_repo.save(feedback)

    async def get_my_feedback(
        self, expert_user_id: UUID, report_id: UUID
    ) -> ReportFeedback | None:
        return await self.feedback_repo.find_by_report_and_user(
            report_id, expert_user_id
        )
```

---

### Slice 20 — report_feedback_analysis

**라우터**
```
GET  /admin/report-feedback/analysis
→ 분석 결과 목록 조회 (업종별, 기간별 필터)

POST /admin/report-feedback/analyze
→ LLM 분석 트리거 (어드민 수동 실행)
Body: { industry_code, period_start, period_end }
```

**Port**
```python
class FeedbackAnalysisLLMPort(Protocol):
    async def analyze(
        self,
        feedbacks: list[ReportFeedback],
        industry_code: str,
    ) -> dict: ...
    # returns: {missing_topics, improvement_keys, useful_sections, summary, action_items}
```

**Interactor**
```python
class ReportFeedbackAnalysisInteractor:
    feedback_repo:  ReportFeedbackRepository
    analysis_repo:  ReportFeedbackAnalysisRepository
    llm_port:       FeedbackAnalysisLLMPort

    async def analyze(
        self,
        industry_code: str,
        period_start: date,
        period_end: date,
    ) -> FeedbackAnalysis:

        feedbacks = await self.feedback_repo.find_by_industry_period(
            industry_code, period_start, period_end
        )
        if len(feedbacks) < 5:
            raise BusinessRuleViolation(
                f"분석에 최소 5건의 피드백이 필요합니다. (현재 {len(feedbacks)}건)"
            )

        result = await self.llm_port.analyze(feedbacks, industry_code)

        analysis = FeedbackAnalysis(
            industry_code=industry_code,
            feedback_count=len(feedbacks),
            period_start=period_start,
            period_end=period_end,
            **result,
        )
        return await self.analysis_repo.save(analysis)
```

**LLM 분석 프롬프트**
```python
FEEDBACK_ANALYSIS_PROMPT = """
다음은 {industry_code} 업종 전문가들이 일일 브리핑에 남긴 피드백입니다.
기간: {period_start} ~ {period_end} (총 {count}건)

[피드백 원문]
{feedbacks_formatted}
-- 각 피드백: 유용성점수 / 유용한섹션 / 내용평가 / 누락정보 / 개선제안

[분석 지시]
아래 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력하세요.

{{
  "missing_topics": ["string", ...],
  // 자주 언급된 누락 정보 패턴 (최대 10개, 빈도 높은 순)

  "improvement_keys": ["string", ...],
  // 반복되는 개선 요청 패턴 (최대 10개)

  "useful_sections": {{
    "NEWS": 0.0~1.0,
    "RECALL": 0.0~1.0,
    "LAW": 0.0~1.0,
    "MFDS": 0.0~1.0,
    "RISK": 0.0~1.0,
    "RESEARCH": 0.0~1.0,
    "STATS": 0.0~1.0
  }},
  // 섹션별 언급 빈도 (유용한 섹션으로 선택된 비율)

  "summary": "string",
  // 전체 피드백 요약 (3~5줄, 핵심 인사이트 중심)

  "action_items": ["string", ...]
  // 다음 리포트 개선을 위한 구체적 액션 (최대 5개)
  // 예: "MFDS 보도자료 요약 2줄로 축소", "원료 가격 동향 섹션 추가"
}}
"""
```

---

## 배치 실행 설계

```python
# main.py lifespan에 APScheduler 등록
from apscheduler.schedulers.asyncio import AsyncIOScheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    # Step 1 — 09:40 크롤링·수집
    scheduler.add_job(
        crawl_and_collect,
        "cron",
        hour=9,
        minute=40,
    )

    # Step 2 — 10:30 LLM 포맷팅 + 리포트 생성
    scheduler.add_job(
        generate_daily_reports,
        "cron",
        hour=10,
        minute=30,
    )

    scheduler.start()
    yield
    scheduler.shutdown()

# Step 1: 크롤링 결과를 raw 테이블 또는 인메모리 캐시에 저장
async def crawl_and_collect():
    collector = RawDataCollector(...)
    result = await collector.collect_all()
    await raw_repo.save_today(result)
    logger.info(f"크롤링 완료: {result.item_count}건 수집")

# Step 2: 저장된 raw 데이터 기반으로 사용자별 리포트 생성
async def generate_daily_reports():
    raw_data = await raw_repo.find_today()
    if not raw_data:
        logger.error("크롤링 데이터 없음, 리포트 생성 스킵")
        return
    interactor = ReportSchedulerInteractor(...)
    result = await interactor.generate_all()
    logger.info(f"리포트 생성 완료: {result}")
```

---

## 마이페이지 UI 흐름 (프론트엔드 참고)

```
/mypage/reports (리포트 목록)
├── 리포트 카드 최대 7개
│   ├── 날짜 + 업종 태그
│   ├── summary_preview (150자, plain text — HTML 태그 없음)
│   ├── [저장] 버튼 (is_saved=false일 때)
│   └── [피드백] 버튼 (피드백 미제출 시)
│
├── 리포트 카드 클릭 → /mypage/reports/{id}
│   ├── 전체 브리핑 본문 (summary — HTML)
│   │   └── dangerouslySetInnerHTML + DOMPurify.sanitize() 필수
│   ├── [저장] / [다운로드] / [출력] 버튼
│   └── [피드백 작성] → 모달
│
└── 피드백 모달
    ├── 유용한 섹션 체크박스 (복수)
    ├── 내용 평가 텍스트에어리어
    ├── 누락 정보 텍스트에어리어
    ├── 개선 제안 텍스트에어리어
    └── 유용성 점수 1~5 선택

/mypage/industry (업종 설정)
├── 뉴스소스 선택 (최대 3개)
│   └── 17개 media 대분류 중 선택
│
└── 식품유형 선택
    ├── 대분류 선택 (최대 3개) — 25개 중 선택
    │   ├── is_flat=false: 대분류 선택 후 → 중분류 3개 추가 선택
    │   └── is_flat=true:  대분류 선택 즉시 확정 (중분류 UI 없음)
    │       (특수영양식품 / 특수의료용도식품 / 알가공품류 / 벌꿀·화분가공품류)
    └── 대분류당 중분류 최대 3개
```

---

## v3 → v4 → v4.1 → v4.2 → v4.3 → v4.4 변경사항 요약

| 항목 | v4.1 | v4.2 | v4.3 | v4.4 |
|---|---|---|---|---|
| 슬라이스 수 | 20개 | 20개 | 20개 | 20개 |
| 라우터 수 | 26개 | 26개 | 26개 | 26개 |
| SectionType | + RESEARCH | + STATS | 동일 | 동일 |
| 국내 논문 Adapter | RissAdapter (KERIS) | RissAdapter | → ScienceOnAdapter (KISTI) | 동일 |
| FIS Open API | 없음 | FisApiAdapter | ❌ 제외 (사업자 전용) | 동일 (제외) |
| FIS 뉴스레터 | 없음 | FoodStatsCombinedAdapter 내부 | → FisNewsletterCrawlerAdapter 단독 | 동일 |
| FoodStatsCombinedAdapter | 없음 | 있음 | ❌ 제거 | 동일 (없음) |
| 뉴스 소스 | ThinkfoodCrawler | + FoodJournal + FoodIcon | 동일 | 동일 |
| summary 저장 형식 | 평문 1200자 | 평문 1200자 | 평문 1200자 | **HTML 저장** |
| summary_preview | 없음 | 없음 | 없음 | **VARCHAR(150) 추가** |
| LLM 역할 | 브리핑 작성자 | 브리핑 작성자 | 브리핑 작성자 | **포맷터 (요약 금지)** |
| 글자수 제한 | 1000자 | 1200자 | 1200자 | **섹션별 항목 수 제한으로 교체** |
| 식품유형축 | 24개 flat | 24개 flat | 24개 flat | **공식분류 기반 25개 + 대/중분류 2단계** |
| flat 카테고리 | 없음 | 없음 | 없음 | **4개 (특수영양·특수의료·알가공·벌꿀화분)** |
| 카테고리 선택 구조 | media 3 + foodtype 3 | 동일 | 동일 | **media 3 + 대분류 3×중분류 3** |
| 신규 가입자 처리 | 없음 | 없음 | 없음 | **당일 발송 제외** |
| 빈 섹션 처리 | 없음 | 없음 | 없음 | **"당일 특이사항 없음"** |
| 배치 스케줄 | 05:00 단일 | 05:00 단일 | 05:00 단일 | **09:40 크롤링 / 10:30 생성 2단계** |
| 필요 API 키 | NCBI + RISS | + FIS | NCBI + SCIENCEON | 동일 |

### 신규 필요 환경변수 (v4.4 — 변경 없음)
```
NCBI_API_KEY=your_ncbi_api_key
SCIENCEON_API_KEY=your_scienceon_api_key
```

---

*v4.4 — 2026-06-10*
*레퍼런스: foodopsagent_설계결정_20260605.md / foodopsagent_erd_v8.md*
*v4.3 대비: summary HTML 저장 + summary_preview 추가 / LLM 포맷터 역할 변경 + 섹션별 항목 수 제한 / 식품유형축 공식분류 기반 25개 재편 + 2단계 계층 구조 / flat 카테고리 4개 / 신규 가입자 당일 발송 제외 / 빈 섹션 "당일 특이사항 없음" / 배치 09:40 크롤링·10:30 생성 2단계 분리*

---

## 진행 체크리스트

```
[ ] Phase 0-A: 패키지 골격 + 폴더 구조
[ ] Phase 0-B: ORM 모델 전체 (v9 ERD 기준 + summary_preview 컬럼 + INDUSTRY_CATEGORY 계층)
[ ] Phase 0-C: Domain Entity + VO 전체
[ ] Phase 0-D: 인증 슬라이스 (admins, expert_users, expert_user_session, anonymous)
[ ] Phase 1:   식품안전 슬라이스 (recall, enforcement, haccp_certification)
[ ] Phase 2:   AI 채팅 슬라이스 (agent_session, agent_message, satisfaction_feedback, expert_feedback)
[ ] Phase 3:   법령 슬라이스 (regulation)
[ ] Phase 4:   업종 슬라이스 (expert_user_industry, industry_category)
              └── 시드 데이터: MEDIA 17개 + FOODTYPE 대분류 25개 + 중분류 전체
              └── flat 카테고리 4개 (특수영양·특수의료·알가공·벌꿀화분) is_flat=True
[ ] Phase 5:   일일 리포트 슬라이스 (daily_report, report_scheduler)
              └── Adapter: ThinkfoodCrawler, MfdsPress, RecallReport, RegulationReport, FoodRisk
              └── Adapter: PubMedAdapter (NCBI E-utilities)
              └── Adapter: ScienceOnAdapter (KISTI ScienceON, ARTI 티켓)
              └── Adapter: FoodJournalCrawler, FoodIconCrawler
              └── Adapter: FisNewsletterCrawlerAdapter (크롤링 단독)
              └── Adapter: CompositeNewsAdapter (뉴스 3소스 통합)
              └── 배치 2단계: crawl_and_collect(09:40) + generate_daily_reports(10:30)
[ ] Phase 6:   피드백 루프 슬라이스 (report_feedback, report_feedback_analysis)
[ ] Phase 7:   어드민 슬라이스 (expert_whitelist, admin_dashboard)
[ ] Phase 8:   APScheduler 배치 등록 + main.py 통합
[ ] Phase 9:   스모크 테스트 전체 26개 라우터
```

---

*v4.4 — 2026-06-10*
*레퍼런스: foodopsagent_설계결정_20260605.md / foodopsagent_erd_v8.md*
