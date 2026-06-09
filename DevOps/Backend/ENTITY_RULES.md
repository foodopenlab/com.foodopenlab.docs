# 엔티티·ORM 필드 규칙 (SQLModel / SQLAlchemy)

> `@plan.docs/DevOps/Backend/ENTITY_RULES.md`  
> 전제: [FOUNDATIONS.md](../FOUNDATIONS.md) · [BACKEND_RULES.md](./BACKEND_RULES.md)

---

## 1. 적용 범위

- DB 테이블과 매핑되는 **SQLModel** (또는 동일 패턴의 SQLAlchemy declarative) 모델
- 비즈니스 식별자(사용자 ID, 주문 번호 등)와 별개인 **시스템 내부용 기본 키(surrogate PK)** 정의

---

## 2. 시스템 내부용 자동 증감 고유 번호 (기본 키)

### 목적

- 테이블마다 **단조 증가하는 정수형 기본 키**를 두어 조인·인덱스·ORM 로딩을 단순화한다.
- 외부에 노출하는 도메인 키(예: UUID, 사업자번호)와 분리해, 내부 참조용으로만 사용한다.

### 필드 규칙

| 항목 | 규칙 |
|------|------|
| Python 속성명 | `id` |
| DB 컬럼명 | `id` (`sa_column_kwargs`로 명시해 마이그레이션·리뷰 시 혼동 방지) |
| 타입 | `Optional[int]` — 생성 시에는 `None`을 두고 DB가 시퀀스·AUTO_INCREMENT로 채움 |
| 제약 | `primary_key=True` |
| 기본값 | `default=None` |

### 코드 예시 (SQLModel `Field`)

```python
from typing import Optional

from sqlmodel import Field, SQLModel


class ExampleEntity(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={"name": "id"},  # DB 컬럼명: id
    )
    # ... 이하 도메인 컬럼
```

### 구현 시 유의사항

- **INSERT** 시 `id`는 넣지 않거나 `None`으로 두어 DB가 자동 할당하도록 한다. 애플리케이션에서 임의 정수를 PK로 쓰지 않는다.
- 마이그레이션(Alembic 등)에서도 해당 컬럼은 **`autoincrement=True`**(또는 DB별 동등 설정)와 일치시킨다.
- 동일 테이블에 비즈니스 유니크 키가 있으면 **별도 컬럼 + `unique=True`**로 두고, `id`는 오직 내부 PK로만 쓴다.
- 문서·API 응답에서 외부 식별자로 `id`를 쓸지 여부는 **제품 보안·노출 정책**에 따르되, 가능하면 공개 식별자는 별도 필드로 노출한다.

---

## 3. 다른 문서와의 역할 분담

- HTTP 스키마·에러 코드: **BACKEND_RULES.md**
- 이 파일은 **테이블 매핑 모델의 필드 네이밍·PK 패턴**만 다룬다. 신규 엔티티 추가 시 본 절을 기본으로 따른다.
