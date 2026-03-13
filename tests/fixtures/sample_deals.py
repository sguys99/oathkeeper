"""Sample deal texts for E2E testing — 5 scenarios with varied characteristics."""

CLEAR_GO_DEAL = {
    "title": "xx철강 AI 비전 검사 시스템",
    "raw_input": (
        "고객사: xx철강 (대한민국 철강 대기업, 연매출 20조)\n"
        "프로젝트: 고로 라인 AI 비전 기반 불량 자동 탐지 시스템\n\n"
        "요구사항:\n"
        "- 실시간 이미지 분석을 통한 불량 자동 감지\n"
        "- 딥러닝 기반 결함 분류 (균열, 표면 흠, 두께 이상)\n"
        "- 엣지 디바이스 배포 (공장 내 실시간 처리 필요)\n"
        "- 기존 MES 시스템과 API 연동\n\n"
        "기술 스택: 컴퓨터 비전, PyTorch, TensorRT, FastAPI\n"
        "예상 금액: 5억 원\n"
        "납기: 2026년 9월 (6개월)\n"
        "투입 인력: PM 1, MLE 2, BE 1\n"
        "담당자: 김영수 이사"
    ),
}

CLEAR_NO_GO_DEAL = {
    "title": "스타트업 Z 전사 AI 플랫폼",
    "raw_input": (
        "고객사: 스타트업 Z (설립 6개월, 자본금 1억)\n"
        "프로젝트: 전사 AI 플랫폼 구축 (챗봇 + 추천 + 예측 + 자동화)\n\n"
        "요구사항:\n"
        "- GPT 기반 고객 상담 챗봇\n"
        "- 상품 추천 엔진\n"
        "- 매출 예측 대시보드\n"
        "- 업무 자동화 워크플로우\n"
        "- 모바일 앱 개발\n\n"
        "예산: 5천만 원\n"
        "납기: 1개월\n"
        "비고: 요구사항 변경 가능성 높음, 내부 데이터 없음"
    ),
}

CONDITIONAL_GO_DEAL = {
    "title": "금융사 A 사기 탐지 ML 시스템",
    "raw_input": (
        "고객사: A금융 (중견 카드사, 연 거래 50만건)\n"
        "프로젝트: 실시간 카드 사기 탐지 ML 파이프라인\n\n"
        "요구사항:\n"
        "- 실시간 이상 거래 탐지 (지연 200ms 이내)\n"
        "- ML 모델 학습/서빙 파이프라인\n"
        "- 기존 FDS 시스템 연동\n"
        "- 관리자 대시보드\n\n"
        "기술: Python, Kafka, Spark, MLflow\n"
        "예상 금액: 3억 원\n"
        "납기: 4개월 (타이트)\n"
        "인력 가용: PM/MLE 확보, 스트리밍 전문가 미확보\n"
        "담당: 박민지 팀장"
    ),
}

HOLD_DEAL = {
    "title": "프로젝트 문의",
    "raw_input": "AI 관련 프로젝트 진행하고 싶은데 상담 가능한가요?",
}

FILE_UPLOAD_DEAL = {
    "title": "유통사 B 수요예측 시스템",
    "raw_input": (
        "고객사: B유통 (국내 대형 유통기업)\n"
        "프로젝트: AI 기반 SKU별 수요 예측 시스템 구축\n\n"
        "요구사항:\n"
        "- 10만 SKU 대상 일별 수요 예측\n"
        "- 시계열 ML 모델 (Prophet, LightGBM 등)\n"
        "- 프로모션/날씨/이벤트 외부 변수 반영\n"
        "- 기존 ERP 연동 (SAP)\n"
        "- 바이어용 대시보드\n\n"
        "기술: Python, Airflow, BigQuery, Looker\n"
        "예상 금액: 4억 원\n"
        "납기: 5개월\n"
        "담당: 최지연 부장"
    ),
}

ALL_SCENARIOS = [
    ("clear_go", CLEAR_GO_DEAL),
    ("clear_no_go", CLEAR_NO_GO_DEAL),
    ("conditional_go", CONDITIONAL_GO_DEAL),
    ("hold", HOLD_DEAL),
    ("file_upload", FILE_UPLOAD_DEAL),
]
