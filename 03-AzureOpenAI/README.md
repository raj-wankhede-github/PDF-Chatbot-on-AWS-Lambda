# Create PDF Chatbot using OpenAI and fetch PDF files from S3 bucket

## Overview

This guide outlines the steps to set up a PDF Chatbot using OpenAI and PDF files from an S3 bucket. The process involves creating a VPC, setting up an RDS PostgreSQL DB, creating Lambda functions, layers, and interacting with the system using Postman.

## Steps

### 1. Create VPC 

- Create a VPC with Private and Public Subnet.
- Provide internet access to the Private Subnet via NAT Gateway.

### 2. Create RDS PostgreSQL DB

- Create an RDS PostgreSQL DB in the previously created VPC.
- Note down the DB Name, DB User, and DB Password for future Lambda function configuration.

### 3. Clone GitHub Repository

- Clone the [GitHub folder](https://github.com/manipuraco/askcybexAPIs/) (or Download) and navigate to the AzureOpenAI folder, where 4 zip files are available.

### 4. Create Lambda Function

- Create a Lambda function from the AWS Console with python3.11 runtime and x86_64 architecture.
  - Under the "Code" tab, click on "Upload from" and select the option ".zip file".
  - Select "Deployment-Azure-OpenAI.zip" from your local machine and click on "Save".

### 5. Create Lambda Layer (Skip this step if you already have below Lambda layers)

- Go to Lambda Layers (in the same region as the created Lambda function) and click on "Create Layer".
- Provide Name, Description (optional), and select "Upload a .zip file" option (or use S3). Choose "Layer-01-Flask-langchain-openai.zip".
- Tick x86_64.
- Under Compatible Runtime, select Python3.11.
- Click Create.
- epeat these steps for a total of 3 layers by selecting the other 2 zip files: "Layer-02-pinecone-psycopg2-PyPDF2-tqdm-Werkzeug-tiktoken.tzip" and "Layer-03-PyMuPDF.zip".

### 6. Add Layers to Lambda Function

- In the Lambda function -> “Code” section, scroll down to the “Layers” section and click on “Add a layer”.
- Select “Custom layers” and choose the layers created in the previous step.
  - If the layer name is not shown in the dropdown, select “Specify an ARN” and provide the ARN of the Lambda Layer version.

### 7. Create S3 Bucket

- Create an S3 bucket (e.g., `use-s3-bucket-as-input`) and create 2 folders: `processed_files/` and `uploaded_files/`.

### 8. Organize Files in S3

- Under `S3://uploaded_files` folder, create a folder and a sub-folder within that correspond to “user_id” and “deployment_id” (sent via request body/form-data).

  Example: 
  ```
  s3://use-s3-bucket-as-input/uploaded_files/user-1234/dep-1234/
  ```

### 9. Upload PDF Files to S3

- Upload the PDF files under `s3://<bucket-name>/uploaded_files/<user_id>/<deployment_id>`.

### 10. Train the Chatbot

#### Using Postman

- Obtain the OpenAI Lambda function URL from Function -> Configuration -> Function URL.

- Use the POST method on the URL (add /train at the end): `https://<ID>.lambda-url.<region>.on.aws/train`

- Request body:
   - `user_id`: <use the same user_id as the folder name created in folder s3://<bucket-name>/uploaded_files/>
   - `deployment_id`: <use the same deployment_id as the folder name created in folder s3://<bucket-name>/uploaded_files/<user_id>/>
   - Example:
        ```
        user_id: user-1234
        deployment_id: dep-1234
        ```

- Optionally, use Query String parameters (known as “params” in Postman):
   - `AI-KEY: <use-ai-key-here>`
   - Example: 
        ```
        AI-KEY: sk-abcd1234567890
        ```

- Click on Send and wait for the request to Finish. The time depends on the number of PDFs in the S3 folder and the time taken by the operation.

### 11. Query the Chatbot

#### Using Postman

- Use the POST method on the URL (add /query at the end): `https://<ID>.lambda-url.<region>.on.aws/query`

- Request body:
   - `user_id`: <use the same user_id as the folder name created in S3 in point (b) above>
   - `deployment_id`: <use the same deployment_id as the folder name created in S3 in point (b) above>
   - Example:
        ```
        user_id: user-1234
        deployment_id: dep-1234
        ```
        
- Click on Send and wait for the API response.
