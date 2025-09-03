# 정부 고시 분석 Lambda 함수

이 프로젝트는 정부 고시 웹사이트에서 최신 산업단지 관련 고시를 가져와서 분석하고, HTML 이메일 뉴스레터를 생성하는 AWS Lambda 함수입니다.

## 주요 기능

1. **웹 스크래핑**: 지정된 URL에서 HTML 테이블 데이터 추출
2. **데이터 파싱**: 최신 고시 정보 (시도, 시군구, 유형, 단지명, 고시일자, 고시번호, 고시명, PDF 링크) 추출
3. **PDF 분석**: PDF 파일 다운로드 및 텍스트 추출 (선택사항)
4. **AI 분석**: Strands-Agents Bedrock을 사용한 고시 내용 분석
5. **HTML 생성**: Jinja2 템플릿을 사용한 뉴스레터 스타일 HTML 이메일 생성
6. **S3 업로드**: 생성된 HTML 파일을 자동으로 S3 버킷에 저장

## 프로젝트 구조

```
probin/
├── lambda_function.py      # 메인 Lambda 핸들러
├── config.py              # 설정 파일
├── templates/
│   └── email_template.html # HTML 이메일 템플릿
├── test_lambda.py         # 로컬 테스트 스크립트
├── deploy.sh              # 배포 스크립트
├── Dockerfile             # Docker 컨테이너 설정
├── requirements.txt       # Python 의존성
└── pyproject.toml         # 프로젝트 설정
```

## 설치 및 설정

### 1. 의존성 설치

```bash
# uv를 사용한 의존성 설치
uv pip install -r requirements.txt

# 또는 pip 사용
pip install -r requirements.txt
```

### 2. AWS 설정

AWS CLI가 설정되어 있어야 합니다:

```bash
aws configure
```

필요한 IAM 권한:
- Lambda 함수 생성/업데이트
- ECR 리포지토리 생성/푸시
- Bedrock 모델 접근
- S3 버킷 읽기/쓰기 (email-reports-html)
- CloudWatch Logs 쓰기

### 3. 환경 변수 설정

Lambda 함수에서 사용할 환경 변수:
- `AWS_REGION`: AWS 리전 (기본값: ap-northeast-2)
- `S3_BUCKET_NAME`: HTML 파일을 저장할 S3 버킷 (기본값: email-reports-html)
- `BEDROCK_MODEL_ID`: Bedrock 모델 ID
- `LOG_LEVEL`: 로그 레벨 (기본값: INFO)

## 사용 방법

### 로컬 테스트

```bash
python test_lambda.py
```

이 명령어는 Lambda 함수를 로컬에서 실행하고 결과를 `test_output.html` 파일로 저장합니다.

### 배포

#### 1단계: IAM 역할 생성 (최초 1회만)

```bash
./create-iam-role.sh
```

#### 2단계: Lambda 함수 배포

```bash
./deploy-simple.sh
```

또는 기존 스크립트 사용:

```bash
./deploy.sh
```

배포 스크립트는 다음 작업을 수행합니다:
1. Docker 이미지 빌드
2. ECR에 이미지 푸시
3. Lambda 함수 생성/업데이트
4. 환경 변수 설정

### Lambda 함수 호출

배포 후 AWS Lambda 콘솔에서 함수를 테스트하거나, AWS CLI를 사용할 수 있습니다:

```bash
aws lambda invoke \
    --function-name probin-notice-processor \
    --payload '{}' \
    --region ap-northeast-2 \
    response.json
```

## API 응답 형식

### 성공 응답 (200)

```json
{
    "statusCode": 200,
    "body": {
        "message": "HTML 이메일이 성공적으로 생성되고 S3에 업로드되었습니다.",
        "html_content": "<html>...</html>",
        "s3_key": "2025/01/notice_20250731_경남-사천시_축동일반산업단지.html",
        "s3_bucket": "email-reports-html",
        "notice_data": {
            "시도": "경남",
            "시군구": "사천시",
            "유형": "일반",
            "단지명": "축동일반산업단지",
            "고시일자": "2025-07-31",
            "고시번호": "사천시 고시 제2025-193호",
            "고시명": "사천 축동일반산업단지 관리기본계획 수립 고시",
            "pdf_link": "/download/..."
        }
    }
}
```

### 오류 응답

```json
{
    "statusCode": 500,
    "body": {
        "error": "오류 메시지"
    }
}
```

## 설정 커스터마이징

### HTML 템플릿 수정

`templates/email_template.html` 파일을 수정하여 이메일 디자인을 변경할 수 있습니다.

### 시스템 프롬프트 수정

`config.py` 파일의 `SYSTEM_PROMPT` 변수를 수정하여 AI 분석 방식을 조정할 수 있습니다.

### 소스 URL 변경

`config.py` 파일의 `SOURCE_URL` 변수를 수정하여 다른 웹사이트를 대상으로 할 수 있습니다.

### S3 파일 구조

업로드된 HTML 파일은 다음과 같은 구조로 S3에 저장됩니다:

```
email-reports-html/
├── 2025/
│   ├── 01/
│   │   ├── notice_20250131_경남-사천시_축동일반산업단지.html
│   │   └── notice_20250131_서울-강남구_테헤란밸리.html
│   └── 02/
│       └── notice_20250215_부산-해운대구_센텀시티.html
└── 2024/
    └── 12/
        └── notice_20241231_대구-수성구_수성알파시티.html
```

각 파일에는 다음 메타데이터가 포함됩니다:
- 시도, 시군구, 유형, 단지명, 고시일자, 고시번호
- 업로드 타임스탬프

## 문제 해결

### 일반적인 문제

1. **배포 시 환경 변수 오류**: `deploy-simple.sh` 사용 권장
2. **IAM 역할 오류**: `create-iam-role.sh`로 역할을 먼저 생성
3. **Bedrock 접근 권한 오류**: IAM 역할에 Bedrock 접근 권한이 있는지 확인
4. **S3 업로드 실패**: IAM 역할에 S3 버킷 권한이 있는지 확인
5. **PDF 다운로드 실패**: 네트워크 연결 및 PDF URL 확인
6. **HTML 파싱 오류**: 웹사이트 구조 변경 시 파싱 로직 업데이트 필요

### 로그 확인

CloudWatch Logs에서 Lambda 함수 실행 로그를 확인할 수 있습니다:

```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/probin-notice-processor"
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.