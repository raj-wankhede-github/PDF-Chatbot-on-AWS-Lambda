# Create PDF Chatbot using OpenAI and PDF files from S3 bucket

1)	Create VPC with Private and Public Subnet. Provide internet access to Private Subnet via NAT Gateway.

2)	Create RDS PostgreSQL DB in above created VPC with DB Name, DB User and DB Passwor. Kindly make note of the same as we will require this during Lambda function configuration.

3)	Create 2 Lambda functions from AWS Console with python3.11 runtime