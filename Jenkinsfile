pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins-kaniko-sa 
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command:
    - sleep
    args:
    - 99d
    volumeMounts:
    - name: aws-secret
      mountPath: /kaniko/.aws/
    - name: docker-config
      mountPath: /kaniko/.docker/
  - name: aws-cli
    image: amazon/aws-cli:latest
    command:
    - sleep
    args:
    - 99d
  volumes:
  - name: aws-secret
    secret:
      secretName: aws-credentials
  - name: docker-config
    configMap:
      name: docker-config
"""
        }
    }
    
    environment {
        ECR_REGISTRY = "177716289679.dkr.ecr.ap-northeast-2.amazonaws.com"
        ECR_REPOSITORY = "izza/email"
        AWS_DEFAULT_REGION = "ap-northeast-2"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "✅ 코드 체크아웃 완료"
            }
        }
        
        stage('Checkout GitOps Repository') {
            steps {
                script {
                    sh '''
                        if [ -d "izza-cd" ]; then
                            rm -rf izza-cd
                        fi
                        git clone https://github.com/aws-izza/izza-cd.git
                    '''
                }
            }
        }

        stage('Generate Image Tag') {
            steps {
                script {
                    def timestamp = new Date().format('yyyyMMdd-HHmmss')
                    def shortCommit = env.GIT_COMMIT.take(7)
                    def branchName = env.GIT_BRANCH.replaceAll('origin/', '')
                    env.IMAGE_TAG = "${branchName}-${timestamp}-${shortCommit}"
                    env.FULL_IMAGE_NAME = "${ECR_REGISTRY}/${ECR_REPOSITORY}:${env.IMAGE_TAG}"
                    
                    echo "🏷️ Generated image tag: ${env.IMAGE_TAG}"
                    echo "📍 Full image name: ${env.FULL_IMAGE_NAME}"
                }
            }
        }
        stage('Debug AWS Credentials') {
            steps {
                container('kaniko') {
                    script {
                        sh '''
                            echo "=== AWS Credentials Check ==="
                            ls -la /kaniko/.aws/
                            echo "=== AWS Config Content ==="
                            cat /kaniko/.aws/config || echo "Config file not found"
                            echo "=== AWS Credentials Content (첫 줄만) ==="
                            head -1 /kaniko/.aws/credentials || echo "Credentials file not found"
                        '''
                    }
                }
            }
        }

        stage('Build and Push with Kaniko') {
            steps {
                container('kaniko') {
                    script {
                        sh """
                            /kaniko/executor \
                                --dockerfile=Dockerfile \
                                --context=dir://. \
                                --destination=${env.FULL_IMAGE_NAME}
                        """
                    }
                }
            }
        }
        
        stage('Update Deployment YAML') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'github-pat', 
                                                    usernameVariable: 'GIT_USERNAME', 
                                                    passwordVariable: 'GIT_PASSWORD')]) {
                        dir('izza-cd') {
                            sh '''
                                git config user.name "jenkins"
                                git config user.email "jenkins@company.com"
                            '''
                            
                            sh """
                                rm -rf environments/email/email-deployment.yaml
                                cp ../deployment/email-deployment.yaml environments/email/email-deployment.yaml
                                sed -i 's|image: .*|image: ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}|' environments/email/email-deployment.yaml
                            """
                            
                            sh """
                                git add environments/email/email-deployment.yaml
                                git commit -m "Update: dev image tag to ${IMAGE_TAG}"
                                git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/aws-izza/izza-cd.git main
                            """
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo """
            🎉 빌드 성공!
            
            📊 빌드 정보:
            - 브랜치: ${env.GIT_BRANCH}
            - 이미지: ${env.FULL_IMAGE_NAME}
            - 커밋: ${env.GIT_COMMIT}
            """
        }
        
        failure {
            echo "❌ 빌드 실패! 로그를 확인하세요."
        }
    }
}