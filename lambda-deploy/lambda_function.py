import json
import requests
from bs4 import BeautifulSoup
from jinja2 import Template
import boto3
import PyPDF2
import io
from urllib.parse import urljoin
import logging
from datetime import datetime
import config

# strands-agents import (fallback 처리)
try:
    from strands_agents import BedrockAgent
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False
    logging.warning("strands-agents를 사용할 수 없습니다. 기본 Bedrock 클라이언트를 사용합니다.")

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(getattr(logging, config.LOG_LEVEL))

def lambda_handler(event, context):
    """
    Lambda 핸들러 함수
    정부 고시 데이터를 가져와서 분석하고 HTML 이메일 콘텐츠를 생성합니다.
    """
    try:
        # 1. HTML 데이터 가져오기
        url = config.SOURCE_URL
        html_content = fetch_html_content(url)
        
        # 2. 테이블에서 최신 데이터 추출
        notice_data = extract_latest_notice(html_content)
        
        if not notice_data:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': '고시 데이터를 찾을 수 없습니다.'})
            }
        
        # 3. PDF 파일 다운로드 및 분석 (가능한 경우)
        pdf_content = None
        if notice_data.get('pdf_link'):
            pdf_content = download_and_analyze_pdf(url, notice_data['pdf_link'])
        
        # 4. Bedrock Agent를 사용한 분석
        analyzed_content = analyze_with_bedrock(notice_data, pdf_content)
        
        # 5. HTML 이메일 생성
        html_email = generate_html_email(notice_data, analyzed_content)
        
        # 6. S3에 HTML 파일 업로드
        s3_key = upload_html_to_s3(html_email, notice_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'HTML 이메일이 성공적으로 생성되고 S3에 업로드되었습니다.',
                'html_content': html_email,
                'notice_data': notice_data,
                's3_key': s3_key,
                's3_bucket': config.S3_BUCKET_NAME
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Lambda 실행 중 오류 발생: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }

def fetch_html_content(url):
    """웹사이트에서 HTML 콘텐츠를 가져옵니다."""
    try:
        response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"HTML 콘텐츠 가져오기 실패: {str(e)}")
        raise

def extract_latest_notice(html_content):
    """HTML에서 최신 고시 정보를 추출합니다."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 테이블 찾기
        table = soup.find('table')
        if not table:
            logger.warning("테이블을 찾을 수 없습니다.")
            return None
        
        # tbody에서 마지막 tr 찾기 (최신 데이터)
        tbody = table.find('tbody')
        if not tbody:
            logger.warning("tbody를 찾을 수 없습니다.")
            return None
        
        rows = tbody.find_all('tr')
        if not rows:
            logger.warning("데이터 행을 찾을 수 없습니다.")
            return None
        
        # 마지막 행 (최신 데이터) 추출
        latest_row = rows[-1]
        cells = latest_row.find_all('td')
        
        if len(cells) < 8:
            logger.warning("충분한 데이터 셀이 없습니다.")
            return None
        
        # PDF 링크 추출
        pdf_link = None
        pdf_cell = cells[7].find('a')
        if pdf_cell and pdf_cell.get('href'):
            pdf_link = pdf_cell.get('href')
        
        notice_data = {
            '시도': cells[0].get_text(strip=True),
            '시군구': cells[1].get_text(strip=True),
            '유형': cells[2].get_text(strip=True),
            '단지명': cells[3].get_text(strip=True),
            '고시일자': cells[4].get_text(strip=True),
            '고시번호': cells[5].get_text(strip=True),
            '고시명': cells[6].get_text(strip=True),
            'pdf_link': pdf_link
        }
        
        logger.info(f"추출된 고시 데이터: {notice_data}")
        return notice_data
        
    except Exception as e:
        logger.error(f"고시 데이터 추출 실패: {str(e)}")
        raise

def download_and_analyze_pdf(base_url, pdf_link):
    """PDF 파일을 다운로드하고 텍스트를 추출합니다."""
    try:
        if not pdf_link:
            return None
        
        # 상대 경로를 절대 경로로 변환
        pdf_url = urljoin(base_url, pdf_link)
        
        response = requests.get(pdf_url, timeout=config.PDF_DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        
        # PDF 텍스트 추출
        pdf_file = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
        
        logger.info(f"PDF 텍스트 추출 완료: {len(text_content)} 문자")
        return text_content[:config.MAX_PDF_TEXT_LENGTH]
        
    except Exception as e:
        logger.error(f"PDF 다운로드/분석 실패: {str(e)}")
        return None

def analyze_with_bedrock(notice_data, pdf_content=None):
    """Bedrock Agent를 사용하여 고시 데이터를 분석합니다."""
    try:
        if STRANDS_AVAILABLE:
            # Strands-Agents 사용
            agent = BedrockAgent(
                region_name=config.AWS_REGION,
                model_id=config.BEDROCK_MODEL_ID
            )
        else:
            # 기본 Bedrock 클라이언트 사용
            bedrock = boto3.client('bedrock-runtime', region_name=config.AWS_REGION)
        
        # 분석할 데이터 준비
        analysis_data = f"""
        고시 정보:
        - 지역: {notice_data.get('시도')} {notice_data.get('시군구')}
        - 유형: {notice_data.get('유형')}
        - 단지명: {notice_data.get('단지명')}
        - 고시일자: {notice_data.get('고시일자')}
        - 고시번호: {notice_data.get('고시번호')}
        - 고시명: {notice_data.get('고시명')}
        """
        
        if pdf_content:
            analysis_data += f"\n\nPDF 내용 (일부):\n{pdf_content}"
        
        # Bedrock Agent로 분석 실행
        if STRANDS_AVAILABLE:
            response = agent.invoke(
                system_prompt=config.SYSTEM_PROMPT,
                user_message=f"다음 고시 데이터를 분석하여 뉴스레터 형식의 요약을 작성해주세요:\n\n{analysis_data}"
            )
            result = response.get('content', '분석 결과를 가져올 수 없습니다.')
        else:
            # 기본 Bedrock 클라이언트 사용
            prompt = f"{config.SYSTEM_PROMPT}\n\n다음 고시 데이터를 분석하여 뉴스레터 형식의 요약을 작성해주세요:\n\n{analysis_data}"
            
            response = bedrock.invoke_model(
                modelId=config.BEDROCK_MODEL_ID,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            result = response_body['content'][0]['text']
        
        logger.info("Bedrock 분석 완료")
        return result
        
    except Exception as e:
        logger.error(f"Bedrock 분석 실패: {str(e)}")
        # 기본 분석 결과 반환
        return generate_fallback_analysis(notice_data)

def generate_fallback_analysis(notice_data):
    """Bedrock 분석이 실패한 경우 기본 분석 결과를 생성합니다."""
    return f"""## 🔍 고시 개요
이번 고시는 {notice_data.get('단지명')} 관련 {notice_data.get('고시명')}입니다.
{notice_data.get('시도')} {notice_data.get('시군구')} 지역의 {notice_data.get('유형')} 관련 중요한 발표로, 해당 지역의 산업 발전과 기업 활동에 영향을 미칠 것으로 예상됩니다.

## 📊 주요 변경사항
- 고시일자: {notice_data.get('고시일자')}
- 고시번호: {notice_data.get('고시번호')}
- 해당 지역: {notice_data.get('시도')} {notice_data.get('시군구')}

## 💼 비즈니스 영향
해당 지역의 {notice_data.get('유형')} 관련 사업에 직접적인 영향을 미칠 것으로 예상되며, 관련 기업들의 사업 계획 수립에 중요한 참고 자료가 될 것입니다.

## 🎯 잠재적 기회
- 입주 기업: 새로운 투자 및 입주 기회 검토 필요
- 건설·엔지니어링사: 관련 프로젝트 발주 가능성
- 투자자: 지역 개발 계획 기반 투자 기회

## ⚠️ 주의사항
정확한 내용은 원본 고시 문서를 반드시 확인하시기 바라며, 관련 법규 및 절차를 준수하여 진행하시기 바랍니다."""

def format_analyzed_content(analyzed_content):
    """분석 내용의 마크다운 헤딩과 리스트를 HTML로 변환합니다."""
    try:
        import re
        
        # ## 헤딩을 <h2> 태그로 변환
        formatted_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', analyzed_content, flags=re.MULTILINE)
        
        lines = formatted_content.split('\n')
        processed_lines = []
        in_list = False
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            if not stripped_line:
                # 빈 줄 처리
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                processed_lines.append('')
                continue
            
            if stripped_line.startswith('<h2>'):
                # 헤딩 처리 - 리스트가 열려있으면 닫기
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                processed_lines.append(stripped_line)
                
            elif stripped_line.startswith('- '):
                # 리스트 아이템 처리
                if not in_list:
                    processed_lines.append('<ul>')
                    in_list = True
                list_item = stripped_line[2:].strip()  # '- ' 제거
                processed_lines.append(f'<li>{list_item}</li>')
                
            else:
                # 일반 텍스트 처리
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                processed_lines.append(stripped_line)
        
        # 마지막에 리스트가 열려있으면 닫기
        if in_list:
            processed_lines.append('</ul>')
        
        return '\n'.join(processed_lines)
        
    except Exception as e:
        logger.error(f"분석 내용 포맷팅 실패: {str(e)}")
        return analyzed_content

def generate_html_email(notice_data, analyzed_content):
    """Jinja2를 사용하여 HTML 이메일을 생성합니다."""
    try:
        # 템플릿 파일 읽기
        with open('templates/email_template.html', 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        # 분석 내용을 HTML 형식으로 포맷팅
        formatted_analyzed_content = format_analyzed_content(analyzed_content)
        
        template = Template(template_str)
        html_content = template.render(
            notice_data=notice_data,
            analyzed_content=formatted_analyzed_content,
            base_url=config.SOURCE_URL
        )
        
        logger.info("HTML 이메일 생성 완료")
        return html_content
        
    except Exception as e:
        logger.error(f"HTML 이메일 생성 실패: {str(e)}")
        raise

def upload_html_to_s3(html_content, notice_data):
    """생성된 HTML 파일을 S3 버킷에 업로드합니다."""
    try:
        # S3 클라이언트 초기화
        s3_client = boto3.client('s3', region_name=config.AWS_REGION)
        
        # 파일명 생성 (고시일자와 단지명 기반)
        safe_date = notice_data.get('고시일자', '').replace('-', '')
        safe_name = notice_data.get('단지명', 'unknown').replace(' ', '_')
        safe_region = f"{notice_data.get('시도', '')}-{notice_data.get('시군구', '')}".replace(' ', '_')
        
        # S3 키 생성 (폴더 구조: year/month/filename)
        now = datetime.now()
        s3_key = f"{now.year}/{now.month:02d}/notice_{safe_date}_{safe_region}_{safe_name}.html"
        
        # HTML 콘텐츠를 S3에 업로드 (메타데이터는 ASCII만 허용되므로 영문 키와 값 사용)
        import base64
        s3_client.put_object(
            Bucket=config.S3_BUCKET_NAME,
            Key=s3_key,
            Body=html_content.encode('utf-8'),
            ContentType='text/html; charset=utf-8',
            Metadata={
                'region': base64.b64encode(notice_data.get('시도', '').encode('utf-8')).decode('ascii'),
                'city': base64.b64encode(notice_data.get('시군구', '').encode('utf-8')).decode('ascii'),
                'type': base64.b64encode(notice_data.get('유형', '').encode('utf-8')).decode('ascii'),
                'complex_name': base64.b64encode(notice_data.get('단지명', '').encode('utf-8')).decode('ascii'),
                'notice_date': notice_data.get('고시일자', ''),
                'notice_number': base64.b64encode(notice_data.get('고시번호', '').encode('utf-8')).decode('ascii'),
                'upload_timestamp': now.isoformat()
            }
        )
        
        logger.info(f"HTML 파일이 S3에 성공적으로 업로드되었습니다: s3://{config.S3_BUCKET_NAME}/{s3_key}")
        return s3_key
        
    except Exception as e:
        logger.error(f"S3 업로드 실패: {str(e)}")
        # S3 업로드 실패해도 전체 프로세스는 계속 진행
        return None