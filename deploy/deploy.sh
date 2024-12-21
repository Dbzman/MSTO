#!/bin/bash
set -e

# Configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
ECR_REPOSITORY_NAME="msto"
ECS_CLUSTER_NAME="msto-cluster"
ECS_SERVICE_NAME="msto-service"

# Build the Docker image
echo "Building Docker image..."
docker build -t ${ECR_REPOSITORY_NAME}:latest .

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Create ECR repository if it doesn't exist
echo "Creating ECR repository if it doesn't exist..."
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY_NAME} || \
    aws ecr create-repository --repository-name ${ECR_REPOSITORY_NAME}

# Tag and push the image
echo "Tagging and pushing image to ECR..."
ECR_REPOSITORY_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"
docker tag ${ECR_REPOSITORY_NAME}:latest ${ECR_REPOSITORY_URI}:latest
docker push ${ECR_REPOSITORY_URI}:latest

# Update task definition
echo "Updating ECS task definition..."
TASK_DEFINITION_FILE="deploy/ecs-task-definition.json"
sed -i.bak "s|\${AWS_ACCOUNT_ID}|${AWS_ACCOUNT_ID}|g" ${TASK_DEFINITION_FILE}
sed -i.bak "s|\${AWS_REGION}|${AWS_REGION}|g" ${TASK_DEFINITION_FILE}
sed -i.bak "s|\${ECR_REPOSITORY_URI}|${ECR_REPOSITORY_URI}|g" ${TASK_DEFINITION_FILE}

TASK_DEFINITION_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://${TASK_DEFINITION_FILE} \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

# Update ECS service
echo "Updating ECS service..."
aws ecs update-service \
    --cluster ${ECS_CLUSTER_NAME} \
    --service ${ECS_SERVICE_NAME} \
    --task-definition ${TASK_DEFINITION_ARN} \
    --force-new-deployment

echo "Deployment completed successfully!"
echo "Task Definition ARN: ${TASK_DEFINITION_ARN}"
echo "Monitor deployment status:"
echo "aws ecs describe-services --cluster ${ECS_CLUSTER_NAME} --services ${ECS_SERVICE_NAME}" 