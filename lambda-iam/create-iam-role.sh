#!/bin/bash

# IAM 역할 생성 스크립트

set -e

ROLE_NAME="lambda-execution-role"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🔐 Lambda 실행 IAM 역할을 생성합니다..."

# 1. IAM 역할 생성
echo "📝 IAM 역할 생성 중..."
if aws iam get-role --role-name $ROLE_NAME 2>/dev/null; then
    echo "⚠️  IAM 역할이 이미 존재합니다: $ROLE_NAME"
else
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://lambda-trust-policy.json
    
    echo "✅ IAM 역할이 생성되었습니다: $ROLE_NAME"
fi

# 2. 정책 연결
echo "📋 정책 연결 중..."
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name lambda-execution-policy \
    --policy-document file://iam-role-policy.json

echo "✅ 정책이 연결되었습니다."

# 3. 기본 Lambda 실행 역할 정책 연결
echo "📋 기본 Lambda 실행 정책 연결 중..."
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

echo "✅ 기본 Lambda 실행 정책이 연결되었습니다."

echo ""
echo "🎉 IAM 역할 설정이 완료되었습니다!"
echo "역할 ARN: arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"
echo ""
echo "이제 deploy-simple.sh를 실행하여 Lambda 함수를 배포할 수 있습니다."