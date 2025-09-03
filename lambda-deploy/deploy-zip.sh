#!/bin/bash

# ZIP 기반 Lambda 함수 배포 스크립트 (테스트용)

set -e

# 변수 설정
FUNCTION_NAME="probin-notice-processor-zip"
REGION="ap-northeast-2"

echo "🚀 ZIP 기반 Lambda 함수 배포를 시작합니다..."

# Account ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1. 가상환경 생성 및 의존성 설치
echo "📦 의존성 설치 중..."
rm -rf lambda-package
mkdir lambda-package
mkdir tmp

# 의존성을 lambda-package 디렉토리에 설치
pip install -r requirements-minimal.txt -t lambda-package/

# 2. Lambda 함수 코드 복사
echo "📝 Lambda 함수 코드 복사 중..."
cp lambda_function.py lambda-package/
cp config.py lambda-package/
cp -r templates lambda-package/

# 3. ZIP 파일 생성
echo "🗜️ ZIP 파일 생성 중..."
cd lambda-package
zip -r ../lambda-function.zip .
cd ..

# 4. 환경 변수를 임시 파일로 생성
echo "📝 환경 변수 설정 중..."
cat > /tmp/lambda-env.json << EOF
{
    "Variables": {
        "S3_BUCKET_NAME": "email-reports-html",
        "LOG_LEVEL": "INFO"
    }
}
EOF

# 5. Lambda 함수 생성 또는 업데이트
echo "⚡ Lambda 함수 배포 중..."
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "기존 Lambda 함수 업데이트 중..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda-function.zip \
        --region $REGION
    
    # 환경 변수 업데이트
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment file:///tmp/lambda-env.json \
        --region $REGION
else
    echo "새 Lambda 함수 생성 중..."
    
    # IAM 역할 ARN (수동으로 생성된 역할 사용)
    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/lambda-execution-role"
    
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://lambda-function.zip \
        --timeout 300 \
        --memory-size 512 \
        --region $REGION \
        --environment file:///tmp/lambda-env.json
fi

# 6. 임시 파일 정리
rm -f /tmp/lambda-env.json
rm -rf lambda-package
rm -f lambda-function.zip

echo "✅ 배포가 완료되었습니다!"
echo "함수 이름: $FUNCTION_NAME"
echo ""
echo "테스트 명령어:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --region $REGION --payload '{}' response.json"