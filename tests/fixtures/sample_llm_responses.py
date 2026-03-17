"""Canned LLM responses for integration tests — one per agent node."""

import json

# ── Deal Structuring ────────────────────────────────────────────────────

STRUCTURED_DEAL = {
    "project_summary": "xx철강 AI 비전 검사 시스템 — 제조 라인 불량 자동 탐지",
    "customer_name": "xx철강",
    "customer_industry": "제조",
    "expected_amount": 500_000_000,
    "tech_requirements": ["컴퓨터 비전", "딥러닝", "엣지 디바이스"],
    "duration_months": 6,
    "additional_info": "고로 라인 실시간 이미지 분석, 기존 MES 연동",
    "missing_fields": [],
}

STRUCTURED_DEAL_RESPONSE = json.dumps(STRUCTURED_DEAL, ensure_ascii=False)

STRUCTURED_DEAL_HOLD = {
    "project_summary": "",
    "customer_name": "",
    "customer_industry": "",
    "tech_requirements": [],
    "missing_fields": ["customer_name", "project_summary", "tech_requirements"],
}

STRUCTURED_DEAL_HOLD_RESPONSE = json.dumps(STRUCTURED_DEAL_HOLD, ensure_ascii=False)

# ── Scoring ─────────────────────────────────────────────────────────────

SCORING_RESPONSE_DATA = {
    "scores": [
        {
            "criterion": "기술 적합성",
            "score": 85,
            "weight": 0.20,
            "rationale": "CV/DL 역량 보유, 엣지 경험 일부 있음",
        },
        {
            "criterion": "수익성",
            "score": 75,
            "weight": 0.20,
            "rationale": "5억 규모 적절한 마진 확보 가능",
        },
        {
            "criterion": "리소스 가용성",
            "score": 70,
            "weight": 0.15,
            "rationale": "MLE 2명 가용, PM 1명 확보 필요",
        },
        {
            "criterion": "납기 리스크",
            "score": 60,
            "weight": 0.15,
            "rationale": "6개월 일정 약간 타이트",
        },
        {
            "criterion": "요구사항 명확성",
            "score": 80,
            "weight": 0.10,
            "rationale": "검사 기준 명확, MES 연동 스펙 확인 필요",
        },
        {
            "criterion": "전략적 가치",
            "score": 90,
            "weight": 0.10,
            "rationale": "제조 AI 레퍼런스 확보 기회",
        },
        {
            "criterion": "고객 리스크",
            "score": 80,
            "weight": 0.10,
            "rationale": "대기업, 지불 안정성 높음",
        },
    ],
}

SCORING_RESPONSE = json.dumps(SCORING_RESPONSE_DATA, ensure_ascii=False)

# ── Resource Estimation ─────────────────────────────────────────────────

RESOURCE_ESTIMATION_DATA = {
    "team_composition": [
        {"role": "PM", "count": 1, "months": 6},
        {"role": "MLE", "count": 2, "months": 6},
        {"role": "BE", "count": 1, "months": 4},
    ],
    "duration_months": 6,
    "total_cost": 350_000_000,
    "expected_margin": 30.0,
    "rationale": "MLE 중심 투입, 백엔드 MES 연동 4개월",
}

RESOURCE_ESTIMATION_RESPONSE = json.dumps(RESOURCE_ESTIMATION_DATA, ensure_ascii=False)

# ── Risk Analysis ───────────────────────────────────────────────────────

RISK_ANALYSIS_DATA = {
    "risks": [
        {
            "category": "기술",
            "item": "엣지 디바이스 호환성",
            "level": "HIGH",
            "description": "공장 환경의 엣지 디바이스 성능 제한",
            "mitigation": "사전 PoC로 모델 최적화 검증",
        },
        {
            "category": "일정",
            "item": "MES 연동 지연",
            "level": "MEDIUM",
            "description": "고객 측 MES API 제공 일정 불확실",
            "mitigation": "모의 인터페이스 병행 개발",
        },
        {
            "category": "고객",
            "item": "요구사항 변경",
            "level": "LOW",
            "description": "검사 기준 추가 가능성",
            "mitigation": "변경 관리 프로세스 사전 합의",
        },
    ],
}

RISK_ANALYSIS_RESPONSE = json.dumps(RISK_ANALYSIS_DATA, ensure_ascii=False)

# ── Similar Projects ────────────────────────────────────────────────────

SIMILAR_PROJECTS_DATA = {
    "similar_projects": [
        {
            "project_name": "A사 용접 품질 검사 AI",
            "similarity_score": 0.87,
            "industry": "제조",
            "tech_stack": ["YOLOv8", "TensorRT", "FastAPI"],
            "duration_months": 5,
            "result": "성공",
            "lessons_learned": "초기 데이터 수집이 가장 중요",
        },
        {
            "project_name": "B사 반도체 외관 검사",
            "similarity_score": 0.72,
            "industry": "반도체",
            "tech_stack": ["ResNet", "OpenCV", "Edge TPU"],
            "duration_months": 8,
            "result": "성공",
            "lessons_learned": "조명 환경 표준화 필수",
        },
        {
            "project_name": "C사 식품 이물질 탐지",
            "similarity_score": 0.65,
            "industry": "식품",
            "tech_stack": ["EfficientNet", "ONNX Runtime"],
            "duration_months": 4,
            "result": "성공",
            "lessons_learned": "클래스 불균형 처리 전략 중요",
        },
    ],
}

SIMILAR_PROJECTS_RESPONSE = json.dumps(SIMILAR_PROJECTS_DATA, ensure_ascii=False)

# ── Final Verdict (markdown, not JSON) ──────────────────────────────────

FINAL_REPORT_MARKDOWN = """\
# xx철강 AI 비전 검사 시스템 — 분석 리포트

## 종합 판단: **Go**

### 종합 점수: 77.5 / 100

## 평가 요약
제조 AI 비전 검사 프로젝트로, 기술 적합성과 전략적 가치가 높습니다.

## 주요 리스크
- 엣지 디바이스 호환성 (HIGH)
- MES 연동 일정 (MEDIUM)

## 권고사항
1. 사전 PoC를 통해 엣지 디바이스 성능 검증
2. MES 연동 스펙 조기 확보
3. 변경 관리 프로세스 수립
"""
