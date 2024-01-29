# Create PDF Chatbot using OpenAI by manually uploading PDF using /upload resource

## Overview

This guide outlines the steps to set up a PDF Chatbot using OpenAI by manually uploading PDF using /upload resource. The process involves updating code from Deployment.zip and test the API.

## Steps

### 1. Upload Deployment.zip to Lambda Function

- Go to respective Lambda function created for this folder `01-ManualUpload`.
- Under the "Code" tab, click on "Upload from" and select the option ".zip file".
- Kindly make sure you are under `01-ManualUpload` folder on your local machine.
- Select `Deployment.zip` from respective folder on your local machine and click on "Save". 
- Wait for function to deploy.

### 2. Remove permission for S3 from Lambda Execution Role

    - Lambda -> Configuration -> Permissions -> Click on Role name and it will open IAM console in new browser tab with Role in it.
    - From the Permissions policies, select `AmazonS3FullAccess` and click on Remove.

### 3. Upload PDF files

#### Using Postman

- Obtain the Lambda function URL from `Function -> Configuration -> Function URL`.

- Use the POST method on the URL (add /upoad at the end): `https://<ID>.lambda-url.<region>.on.aws/upload`

- Request body in form-data:
   - `user_id`: <put your user_id here>
   - `deployment_id`: <put your deployment_id here>
   - `files`: <use file(s) from local machine>
   - Example:
        ```
        user_id: user-4321
        deployment_id: user-4321
        files: test1.pdf
        ```
   - Here, `user_id, deployment_id` are of type `Text` and `files` is of type `File` under form-data.

- Click on Send and wait for the request to Finish. The time for request to finish depends on the number of PDFs/size of PDFs sent by user.

### 4. Train the Chatbot

#### Using Postman

- Obtain the Lambda function URL from `Function -> Configuration -> Function URL`.

- Use the POST method on the URL (add /train at the end): `https://<ID>.lambda-url.<region>.on.aws/train`

- Request body in form-data:
   - `user_id`: <use the same user_id as sent during /upload>
   - `deployment_id`: <use the same deployment_id as sent during /upload>
   - Example:
        ```
        user_id: user-4321
        deployment_id: user-4321
        ```

- Click on Send and wait for the request to Finish. The time for request to finish depends on the number of PDFs/size of PDFs in the S3 folder.

### 5. Query the Chatbot

#### Using Postman

- Obtain the Lambda function URL from `Function -> Configuration -> Function URL`.

- Use the POST method on the URL (add /query at the end): `https://<ID>.lambda-url.<region>.on.aws/query`

- Request body in form-data:
   - `user_id`: <use the same user_id as sent during /upload and /train>
   - `deployment_id`: <use the same deployment_id as sent during /upload and /train>
   - `question`: < ask query related to uploaded PDFs >
   - `prompt`: You are given a paragraph and a query. You need to answer the query on the basis of paragraph. If the answer is not contained within the text below, say Sorry, I don't know. Please try again. P:{documents} Q: {query} A: 
   - Example:
        ```
        user_id: user-4321
        deployment_id: user-4321
        question: What are Some of the key elements of focus group research? 
        prompt: You are given a paragraph and a query. You need to answer the query on the basis of paragraph. If the answer is not contained within the text below, say Sorry, I don't know. Please try again. P:{documents} Q: {query} A: 
        ```
        
- Click on Send and wait for the API response.

### 6. Chat with the Chatbot

#### Using Postman

- Obtain the Lambda function URL from `Function -> Configuration -> Function URL`.

- Use the POST method on the URL (add /chat at the end): `https://<ID>.lambda-url.<region>.on.aws/chat`

- Request body in form-data:
   - `user_id`: <use the same user_id as sent during /upload and /train>
   - `deployment_id`: <use the same deployment_id as sent during /upload and /train>
   - `question`: < ask query related to uploaded PDFs >
   - `prompt`: You are given a paragraph and a query. You need to answer the query on the basis of paragraph. If the answer is not contained within the text below, say Sorry, I don't know. Please try again. P:{documents} Q: {query} A: 
   - Example:
        ```
        user_id: user-4321
        deployment_id: user-4321
        question: What are Some of the key elements of focus group research? 
        prompt: You are given a paragraph and a query. You need to answer the query on the basis of paragraph. If the answer is not contained within the text below, say Sorry, I don't know. Please try again. P:{documents} Q: {query} A: 
        ```
        
- Click on Send and wait for the API response.

### 7. Remove the Pinecone namespace

#### Using Postman

- Obtain the Lambda function URL from `Function -> Configuration -> Function URL`.

- Use the POST method on the URL (add /remove at the end): `https://<ID>.lambda-url.<region>.on.aws/remove`

- Request body in form-data:
   - `user_id`: <use the same user_id as sent during /train>
   - `deployment_id`: <use the same deployment_id as sent during /train>
   - Example:
        ```
        user_id: user-4321
        deployment_id: user-4321
        ```

- Click on Send and wait for the request to Finish.

