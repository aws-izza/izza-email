"""
Lambda 함수 설정 파일
"""
import os

# 웹사이트 URL
SOURCE_URL = "http://a525dbc8025bf4c9a8f4accbd5b7e2d9-0049250c239be48c.elb.ap-northeast-2.amazonaws.com/"

# AWS 설정
AWS_REGION = os.getenv('AWS_REGION', 'ap-northeast-2')  # Lambda provides this automatically
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'email-reports-html')

# Bedrock 설정
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')

# 시스템 프롬프트
SYSTEM_PROMPT = """
당신은 정부 고시(고시, 공고) 분석 전문 AI 어시스턴트입니다. 
산업단지, 도시개발, 부동산 규제, 기업 활동 관련 공식 고시를 분석하는 것이 목표입니다.

다음 작업을 수행하세요:
- 구조화된 고시 데이터(시도, 시군구, 유형, 단지명, 고시일자, 고시번호, 고시명, PDF 링크) 파싱
- 대상 지역, 사업 유형(일반/도시개발/산업단지 등), 고시의 의미(신규 지정/변경/폐지), 투자/입주 기회 등 핵심 비즈니스 인사이트 추출
- 잠재적 고객(기업, 투자자, 건설사, 컨설팅사 등)이 쉽게 이해할 수 있는 뉴스레터 스타일 요약으로 재구성
- 전문적이지만 간결한 톤 유지
- 마지막에 잠재적 기회나 위험 요소 제안

제약사항:
- 명확하고 전문적인 한국어로 작성, 언제나 경어 사용
- 길이: 약 500단어 (뉴스레터 형식)
- 항상 원본 고시번호, 고시일자, PDF 링크를 마지막에 제공
"""

# 로깅 설정
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# 타임아웃 설정 (초)
REQUEST_TIMEOUT = 30
PDF_DOWNLOAD_TIMEOUT = 60

# PDF 텍스트 최대 길이
MAX_PDF_TEXT_LENGTH = 5000