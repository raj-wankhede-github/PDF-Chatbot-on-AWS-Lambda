# Create PDF Chatbot using OpenAI by using the PDF files from S3 bucket

## Overview

This guide outlines the steps to set up a PDF Chatbot using OpenAI by using the PDF files from S3 bucket. The process involves updating code from Deployment.zip and test the API.

## Steps

### 1. Upload Deployment.zip to Lambda Function

- Go to respective Lambda function created for this folder `02-OpenAI`.
- Under the "Code" tab, click on "Upload from" and select the option ".zip file".
- Kindly make sure you are under `02-OpenAI` folder on your local machine.
- Select "Deployment.zip" from respective folder on your local machine and click on "Save". 
- Wait for function to deploy.


### 2. Train the Chatbot

#### Using Postman

- Obtain the OpenAI Lambda function URL from `Function -> Configuration -> Function URL`.

- Use the POST method on the URL (add /train at the end): `https://<ID>.lambda-url.<region>.on.aws/train`

- Request body in form-data:
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

- Click on Send and wait for the request to Finish. The time for request to finish depends on the number of PDFs/size of PDFs in the S3 folder.

### 3. Query the Chatbot

#### Using Postman

- Obtain the OpenAI Lambda function URL from `Function -> Configuration -> Function URL`.

- Use the POST method on the URL (add /query at the end): `https://<ID>.lambda-url.<region>.on.aws/query`

- Request body in form-data:
   - `user_id`: <use the same user_id as the folder name created in folder s3://<bucket-name>/uploaded_files/>
   - `deployment_id`: <use the same deployment_id as the folder name created in folder s3://<bucket-name>/uploaded_files/<user_id>/>
   - `question`: <ask query related to PDFs in S3 bucket>
   - `prompt`: You are given a paragraph and a query. You need to answer the query on the basis of paragraph. If the answer is not contained within the text below, say Sorry, I don't know. Please try again. P:{documents} Q: {query} A: 
   - Example:
        ```
        user_id: user-1234
        deployment_id: dep-1234
        question: what are Some of the key elements of focus group research? 
        prompt: You are given a paragraph and a query. You need to answer the query on the basis of paragraph. If the answer is not contained within the text below, say Sorry, I don't know. Please try again. P:{documents} Q: {query} A: 
        ```
        
- Click on Send and wait for the API response.

