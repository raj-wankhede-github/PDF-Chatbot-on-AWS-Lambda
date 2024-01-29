# PDF Chatbot on AWS Lambda

## Overview

This guide outlines the steps to set up a PDF Chatbot using OpenAI. The process involves creating a VPC, setting up an RDS PostgreSQL DB, creating Lambda functions, layers, and interacting with the application using Postman.

## Pre-requisite mandatory steps to use this repository

### 1. Create VPC 

- Create a VPC with Private and Public Subnet.
- [Provide internet access to the Private Subnet via NAT Gateway](https://repost.aws/knowledge-center/nat-gateway-vpc-private-subnet).

### 2. Create RDS PostgreSQL DB

- Create an RDS PostgreSQL DB with the created VPC in Private subnet.
- Note down the "DB name", "Master username", "Master password" and "Endpoint URL" for Lambda function configuration.

### 3. Clone GitHub Repository

- Clone the [GitHub folder](https://github.com/manipuraco/askcybexAPIs/) (or Download) and navigate to the `00-Lambda-Layers` folder, where 3 zip files are available.

### 4. Create Lambda Layer

- Go to Lambda Layers (in the same region as the created Lambda function) and click on "Create Layer".
- Provide Name, Description (optional), and select "Upload a .zip file" option (or use S3). Choose `Layer-01-Flask-langchain-openai.zip`.
- Tick x86_64.
- Under Compatible Runtime, select Python3.11.
- Click Create.
- Repeat above steps and select the other 2 zip files: `Layer-02-pinecone-psycopg2-PyPDF2-tqdm-Werkzeug-tiktoken.tzip` and `Layer-03-PyMuPDF.zip`.
- This process shall create 3 Lambda layers.

### 5. Create Lambda Function

- Create 3 Lambda functions from the AWS Console with python3.11 runtime and x86_64 architecture. Leave everything else to default.

### 6. Add Layers to Lambda Function

- From Lambda function go to -> “Code” section, scroll down to the “Layers” section and click on “Add a layer”.
- Select “Custom layers” and choose the layers created in previous step.
  - If the layer name is not shown in the dropdown, select “Specify an ARN” and provide the ARN of the Lambda Layer version.
  - Repeat this step and add all 3 layers to a function.
- Perform the same for other 2 Lambda functions. 

### 7. Configuration on all 3 Lambda Functions

- Change timeout to 15min and RAM to 512MB:
    - Lambda -> Configuration -> General configuration

- Create Environment Variables:
    - Lambda -> Configuration -> Environment variables:
        - `DBHOST`: <Endpoint URL from step 2>
        - `DBNAME`: <DB name from step 2>
        - `DBPASSWORD`: <DB password from step 2>
        - `DBUSER`: <DB user from step 2>
        - `ENVIRONMENT`: <Environment from Pinecone. E.g., gcp-starter>
        - `PINECONE_API_KEYS`: < Pinecone api key >
        - `PINECONE_INDEX_NAME`: < Pinecone index name >

- Additional Environment Variable for OpenAI Lambda function:
    - `OPEN_API_KEYS`: < Key for OpenAI >
    - `S3_BUCKET_NAME`: < S3 bucket where the PDF files are present >

- Additional Environment Variables for Azure OpenAI Lambda function:
    - `AZURE_OPENAI_ENDPOINT`: < Custom Azure OpenAI Endpoint >
    - `AZURE_OPEN_API_KEYS`: < Key for Azure OpenAI >
    - `S3_BUCKET_NAME`: < S3 bucket where the PDF files are present >

- Additional Environment Variable for Bedrock Lambda function:
    - `S3_BUCKET_NAME`: < S3 bucket where the PDF files are present >

- Enable Function URL:
    - Lambda -> Configuration -> Function URL
    - Choose authentication as NONE, since the Environment variables of Lambda contains the API Key for OpenAI/Azure OpenAI/Pinecone. Without these, the function will return an error.
    - This is the URL to send requests on /train, /query, /remove etc.

- Change the Lambda handler
    - Function -> Code -> scroll down to "Runtime settings" and click Edit -> Change the "Handler" to `app.lambda_handler`
    
- Provide Lambda Execution Role access to EC2/S3/RDS:
    - Lambda -> Configuration -> Permissions -> Click on Role name and it will open IAM console in new browser tab with Role in it.
    - Drop down on Add Permissions and click Attach policies
    - Select `AWSLambdaVPCAccessExecutionRole, AmazonRDSFullAccess, AmazonS3FullAccess` and add permission to the Execution Role.

- Configure VPC access to Lambda function:
    - Lambda -> Configuration -> VPC -> Select VPC -> Choose Private Subnets ONLY (where default route is not directed to IGW) -> Select SG (mentioned below) and click Save. This takes some time to create ENIs that Lambda uses to access the VPC resources (like RDS).

        - Choose Security Group (e.g., Lambda-SG) such that it gives OUTBOUND access to RDS via port 5432 on Destination SG (e.g., RDS-SG)
        Similarly, Security Group assigned to RDS DB as “RDS-SG” that allows INBOUND access to Port 5432 from Source SG “Lambda-SG”. 

        OR follow below process to automatically handle ports on SG.

        In case you want to automatically handle this, first make sure Lambda is already in VPC with any SG assigned. Then go to Lambda -> Configuration -> RDS databases -> Connect to RDS Database -> Select the existing RDS Database -> Select “Do not use a database proxy” and click on Create. This will create/edit Security Group attached to Lambda/RDS accordingly.

### 8. Create S3 Bucket

- Create an S3 bucket (e.g., `use-s3-bucket-as-input`) and create 2 folders under it: `processed_files/` and `uploaded_files/`.
- Example:
    ```
    s3://uploaded_files/
    s3://processed_files/
    ```

### 9. Organize Files in S3 Bucket

- Under `S3://uploaded_files` folder, create a folder and a sub-folder within that folder. This correspond to “user_id” and “deployment_id” (sent via request body/form-data).

- Example: 
  ```
  s3://use-s3-bucket-as-input/uploaded_files/user-1234/dep-1234/
  ```

### 10. Upload PDF Files to S3 Bucket

- Upload the PDF files under folder `s3://<bucket-name>/uploaded_files/<user_id>/<deployment_id>/`.
- Example:
    ```
    s3://use-s3-bucket-as-input/uploaded_files/user-1234/dep-1234/test-1.pdf
    s3://use-s3-bucket-as-input/uploaded_files/user-1234/dep-1234/test-2.pdf
    s3://use-s3-bucket-as-input/uploaded_files/user-1234/dep-1234/test-3.pdf
    ```
### 11. Other Configurations

- Kindly refer README.md file of the respective folder `01-ManualUpload, 02-OpenAI, 03-AzureOpenAI` for additional Configuration related to specific application and test the same using Postman application.
