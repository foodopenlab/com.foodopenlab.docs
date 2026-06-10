# MFDS Backend ERD (Database Schema Specification)

이 문서는 백엔드 시스템(`SQLAlchemy` 및 `SQLModel`)의 실제 테이블과 외래키 관계를 바탕으로 정리된 핵심 ERD 사양서입니다. 

본 사양서는 **제1정규형(1NF)부터 제3정규형(3NF)까지의 데이터베이스 정규화 규칙** 및 **조인 테이블 상속(Joined Table Inheritance)** 구조를 완벽하게 적용한 **ERD v10 사양**입니다.

---

## 1. 관계 다이어그램 (ERD)

```mermaid
erDiagram
    %% 3NF/상속: 공통 사용자 부모 테이블에서 자식 테이블로의 1:1 식별 상속 관계
    users ||--|| admins : "inherits (1:1)"
    users ||--|| expert_users : "inherits (1:1)"
    users ||--|| anonymous : "inherits (1:1)"

    %% 3NF/다형성해소: 다형성 참조 제거 및 FK 물리적 제약 연결
    users ||--o{ agent_sessions : "starts"
    admins ||--o{ expert_whitelist : "registers"
    expert_users ||--o{ expert_user_sessions : "has"
    agent_sessions ||--o{ agent_messages : "contains"
    
    agent_messages ||--o{ satisfaction_feedbacks : "receives"
    agent_messages ||--o{ expert_feedbacks : "receives"
    expert_users ||--o{ expert_feedbacks : "labels"

    %% 1NF: 원자성 보장을 위한 Array 다중값 속성의 1:N 분리 테이블
    agent_messages ||--o{ agent_message_sources : "has"
    industry_category ||--o{ category_keywords : "has"
    report_feedback ||--o{ report_feedback_sections : "has"

    %% 일일 리포트 및 카테고리 관계
    industry_category ||--o{ industry_category : "references parent"
    expert_users ||--o{ expert_user_industry : "selects"
    industry_category ||--o{ expert_user_industry : "references category"
    expert_users ||--o{ daily_report : "has reports"
    daily_report ||--o{ report_feedback : "has feedback"
    expert_users ||--o{ report_feedback : "submits feedback"
    industry_category ||--o{ report_feedback_analysis : "analyzes"

    users {
        uuid id PK
        string user_type "admin | expert | anonymous"
        timestamptz created_at
    }

    admins {
        uuid user_id PK_FK "references users.id"
        string email UNIQUE
        string name
        string hashed_password
        timestamptz last_login
    }

    expert_whitelist {
        string email PK
        string invited_name
        string role_desc
        uuid added_by FK "references admins.user_id"
        timestamptz added_at
    }

    expert_users {
        uuid user_id PK_FK "references users.id"
        string email UNIQUE
        string name
        string picture
        string auth_provider "google | email"
        string hashed_password
        timestamptz last_login
    }

    expert_user_sessions {
        uuid id PK
        uuid expert_user_id FK "references expert_users.user_id"
        string access_token
        string refresh_token
        timestamptz created_at
        timestamptz expires_at
    }

    anonymous {
        uuid user_id PK_FK "references users.id"
        string cookie_id
        timestamptz last_seen
    }

    agent_sessions {
        uuid id PK
        uuid actor_id FK "references users.id"
        timestamptz started_at
        timestamptz last_active_at
    }

    agent_messages {
        uuid id PK
        uuid session_id FK "references agent_sessions.id"
        string role "user | assistant"
        string query_pattern
        text content
        timestamptz created_at
    }

    agent_message_sources {
        uuid id PK
        uuid message_id FK "references agent_messages.id"
        text source_url
    }

    satisfaction_feedbacks {
        uuid id PK
        uuid message_id FK "references agent_messages.id"
        boolean is_positive
        timestamptz submitted_at
    }

    expert_feedbacks {
        uuid id PK
        uuid message_id FK "references agent_messages.id"
        uuid expert_user_id FK "references expert_users.user_id"
        string label
        text memo
        timestamptz submitted_at
    }

    industry_category {
        string code PK
        string type "media | foodtype"
        string parent_code FK "self-reference"
        int2 depth
        boolean is_flat
        string name_ko
        string crawler_param
        timestamptz created_at
    }

    category_keywords {
        uuid id PK
        string category_code FK "references industry_category.code"
        string keyword
    }

    expert_user_industry {
        uuid id PK
        uuid expert_user_id FK "references expert_users.user_id"
        string category_code FK "references industry_category.code"
        timestamptz created_at
    }

    daily_report {
        uuid id PK
        uuid expert_user_id FK "references expert_users.user_id"
        date report_date
        timestamptz generated_at
        timestamptz expires_at
        boolean is_saved
        text summary "formatted HTML"
        string summary_preview "150 chars plain text"
        jsonb raw_news "NoSQL style pragmatism"
        jsonb raw_recalls
        jsonb raw_laws
        jsonb raw_mfds
        jsonb raw_research
        jsonb raw_stats
        jsonb raw_risk
    }

    report_feedback {
        uuid id PK
        uuid report_id FK "references daily_report.id"
        uuid expert_user_id FK "references expert_users.user_id"
        timestamptz created_at
        text content_feedback
        text missing_feedback
        text improvement_feedback
        int2 usefulness_score
    }

    report_feedback_sections {
        uuid id PK
        uuid feedback_id FK "references report_feedback.id"
        string section_type "NEWS | RECALL | LAW | MFDS | RISK | RESEARCH | STATS"
    }

    report_feedback_analysis {
        uuid id PK
        string industry_code FK "references industry_category.code"
        timestamptz analyzed_at
        int4 feedback_count
        date period_start
        date period_end
        jsonb missing_topics
        jsonb improvement_keys
        jsonb useful_sections
        text summary
        jsonb action_items
    }
```

---

## 2. 정규화 및 상속 적용 상세 명세

### ① 1NF (제1정규형) 적용 사항
모든 다중값 속성(Array)을 자식 테이블로 완전히 정규화하여 데이터 원자성을 확보했습니다.
* **`agent_message_sources`**: 기존 `agent_messages` 테이블 내 `source_urls` (TEXT[]) 컬럼을 분리한 1:N 맵핑 테이블
* **`category_keywords`**: 기존 `industry_category` 테이블 내 `keywords` (TEXT[]) 컬럼을 분리한 1:N 맵핑 테이블
* **`report_feedback_sections`**: 기존 `report_feedback` 테이블 내 `useful_sections` (TEXT[]) 컬럼을 분리한 1:N 맵핑 테이블
* *Note: `daily_report` 테이블 내 수집 데이터(`raw_news` 등 JSONB)의 경우, 외부 스키마 변화가 잦아 구조적 편의를 위해 NoSQL형 JSONB 타입을 비정규화 형태로 유지했습니다.*

### ② 3NF (제3정규형) 및 상속(Inheritance) 적용 사항
* **공통 계정 상속 구조 (`users`)**:
  * 공통 행위자 메타정보(PK, 생성일, 계정타입)를 담은 `users` 테이블을 상위에 생성했습니다.
  * `admins`, `expert_users`, `anonymous` 테이블은 `users.id`를 외래키이자 고유키(PK_FK)로 가지며 1:1 상속을 받습니다.
  * 이로써 `agent_sessions.actor_id`는 어떤 유형의 행위자든 가상 참조가 아닌 **실제 데이터베이스 외래키(FK) 제약조건**을 통해 관계 무결성을 확보합니다.
* **`expert_user_industry` 중복 제거**:
  * 기존 구조에서 이행적 종속성(Transitive Dependency, `id -> category_code -> category_type`)을 유발하던 `category_type` 컬럼을 완전히 제거하고 `category_code`만을 남겼습니다. 카테고리 타입은 JOIN 조회를 통해 가져옵니다.


