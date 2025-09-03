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

다음 구조로 분석 결과를 작성하세요:

## 고시 개요
- 고시의 핵심 내용과 목적을 간단히 설명

## 주요 변경사항
- 이번 고시로 인한 주요 변경점이나 신규 사항
- 기존 대비 달라지는 점

## 비즈니스 영향
- 관련 기업들에게 미치는 영향
- 해당 지역 산업에 미치는 파급효과

## 잠재적 기회
- 투자 기회
- 입주 기회  
- 사업 확장 기회

## 주의사항
- 고려해야 할 리스크나 제약사항
- 준수해야 할 규정이나 절차

제약사항:
- 각 섹션은 ## 헤딩으로 시작
- 명확하고 전문적인 한국어로 작성, 언제나 경어 사용
- 전체 길이: 약 500단어 (뉴스레터 형식)
- 구체적이고 실용적인 정보 제공
"""

# 로깅 설정
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# 타임아웃 설정 (초)
REQUEST_TIMEOUT = 30
PDF_DOWNLOAD_TIMEOUT = 60

# PDF 텍스트 최대 길이
MAX_PDF_TEXT_LENGTH = 5000