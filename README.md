# PDF Chatbot on AWS Lambda

## Overview

This guide outlines the steps to set up a PDF Chatbot using OpenAI/Azure OpenAI/Amazon Bedrock. The process involves creating a VPC, setting up an RDS PostgreSQL DB and DynamoDB, creating Lambda functions, layers, and interacting with the application using Postman.

## Pre-requisite mandatory steps to use this repository

### 1. Create VPC 

- Create a VPC with Private and Public Subnet.
- [Provide internet access to the Private Subnet via NAT Gateway](https://repost.aws/knowledge-center/nat-gateway-vpc-private-subnet).

### 2. Create RDS PostgreSQL DB and DynamoDB

- PostgreSQL:
    - Create an RDS PostgreSQL DB with the created VPC in Private subnet.
    - Note down the "DB name", "Master username", "Master password" and "Endpoint URL" for Lambda function configuration.

- DynamoDB:
    - Create DynamoDB Table with "Partition key" (part of the table's primary key) set as String to "SessionId" (Kindly do not change this)

### 3. Clone GitHub Repository

- Clone the [GitHub folder](https://github.com/manipuraco/askcybexAPIs/) (or Download) and navigate to the `00-Lambda-Layers` folder on local machine.

### 4. Create Lambda Layer

- Upload a file from `00-Lambda-Layers` to Amazon S3 Bucket - `Layer-01-Lambda-layer-All-in-one-dependencies.zip`. Copy the URL for the object in S3 bucket.
- Go to Lambda Layers (in the same region as the created Lambda function) and click on "Create Layer".
- Provide Name, Description (optional), and select "Upload a file from Amazon S3" and use the URL copied in previous step.
- Tick x86_64.
- Under Compatible Runtime, select Python3.11. Do not select any other Python version as the dependencies in the zip file was created using pip3.11 that uses python3.11 version.
- Click Create.

### 5. Create Lambda Function

- Create one Lambda function for each directory in the Github repo - ManualUpload/OpenAI/AzureOpenAI/Amazon-Bedrock (except for Lambda-Layers) using python3.11 runtime and x86_64 architecture. Leave everything else to default.

### 6. Add Layers to Lambda Function

- From Lambda function go to -> “Code” section, scroll down to the “Layers” section and click on “Add a layer”.
- Select “Custom layers” and choose the layers created in previous step.
  - If the layer name is not shown in the dropdown, select “Specify an ARN” and provide the ARN of the Lambda Layer version.
- Perform the same for other Lambda functions created in step 5. 

### 7. Configuration on all the Lambda Functions (Unless specified for respective Lambda function)

- Change timeout to 15 min and RAM to 512MB:
    - Lambda -> Configuration -> General configuration

- Create Environment Variables common for all the functions
    - Lambda -> Configuration -> Environment variables:
        - `DBHOST`: <Endpoint URL from step 2>
        - `DBNAME`: <DB name from step 2>
        - `DBPASSWORD`: <DB password from step 2>
        - `DBUSER`: <DB user from step 2>
        - `ENVIRONMENT`: <Environment from Pinecone. E.g., gcp-starter>
        - `PINECONE_API_KEYS`: < Use the Pinecone api key >
        - `PINECONE_INDEX_NAME`: < Use the Pinecone index name >

- Additional Environment variables for `OpenAI` Lambda function:
    - `OPEN_API_KEYS`: < Use Key for OpenAI >
    - `S3_BUCKET_NAME`: < S3 bucket where the PDF files are present >

- Additional Environment variables for `AzureOpenAI` Lambda function:
    - `AZURE_OPENAI_ENDPOINT`: < Use Custom Azure OpenAI Endpoint >
    - `AZURE_OPEN_API_KEYS`: < Use the Key for Azure OpenAI >
    - `S3_BUCKET_NAME`: < S3 bucket where the PDF files are present >

- Additional Environment variables for `Amazon-Bedrock` Lambda function:
    - `MEMORY_TABLE`: <use the DynamoDB Table name from step 2 >
    - `S3_BUCKET_NAME`: < S3 bucket where the PDF files are present >
    - Remove below Environment variables (if added) for Bedrock Lambda function (as we use DynamoDB Table instead of RDS PostgreSQL):
        - `DBHOST`
        - `DBNAME`
        - `DBPASSWORD`
        - `DBUSER`

- Enable Function URL:
    - Lambda -> Configuration -> Function URL
    - Choose authentication as NONE, since the Environment variables of Lambda contains the API Key for OpenAI/Azure OpenAI/Pinecone. Without these, the function will return an error.
    - This is the URL to send requests on /train, /query, /remove etc.

- Change the Lambda handler
    - Function -> Code -> scroll down to "Runtime settings" and click Edit -> Change the "Handler" to `app.lambda_handler`
    
- Provide Lambda Execution Role access to EC2/S3/RDS/Bedrock:
    - Lambda -> Configuration -> Permissions -> Click on Role name and it will open IAM console in new browser tab with Role in it.
    - Drop down on Add Permissions and click Attach policies
    - Select `AWSLambdaVPCAccessExecutionRole, AmazonRDSFullAccess, AmazonS3FullAccess` and add permission to the Execution Role.

    - For `ManualUpload` Lambda function:
        - Remove `AmazonS3FullAccess` permissions (if added). We do not need S3 access as we will upload the file manually using Postman.

    - For `Amazon-Bedrock` Lambda function:
        - Add Policy `AmazonBedrockFullAccess`
        - Remove `AWSLambdaVPCAccessExecutionRole, AmazonRDSFullAccess` permissions (if added). We do not need RDS access because we are using DynamoDB and similarly, we do not put Lambda in VPC and hence we do not need Lambda VPC Access.
        
- Configure VPC access to Lambda function: (IMPORTANT: Skip this VPC part for `Amazon-Bedrock` Lambda function)
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

- Kindly refer README.md file of the respective folder `01-ManualUpload, 02-OpenAI, 03-AzureOpenAI, 04-Amazon-Bedrock` for additional Configuration related to specific application and test the same using Postman application.
