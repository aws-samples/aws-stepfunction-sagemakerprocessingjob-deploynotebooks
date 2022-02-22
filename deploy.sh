# Create Roles and ECR Repo
sam package --template-file template.yml --output-template-file packaged.yaml --force-upload --region us-west-1 --s3-bucket dev

sam deploy --template-file packaged.yaml --stack-name sfn-smprocessingjob-stack --region us-west-1 --no-fail-on-empty-changeset --force-upload --capabilities CAPABILITY_NAMED_IAM

# get current AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
# get current AWS REGION to use in URLs
REGION=$(aws configure get region)

docker build -t sagemaker-processing  .

docker tag sagemaker-processing ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/sagemaker-processing

aws ecr get-login-password --region ${REGION}| docker login -u AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/sagemaker-processing
docker push ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/sagemaker-processing

python3 ./cicd_utils/sfn-sagemakerprocessingjob.py -w . -e -i sagemaker-processing
