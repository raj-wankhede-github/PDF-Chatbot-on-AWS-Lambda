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

### 2. Upload PDF files

#### Using Postman

- Obtain the OpenAI Lambda function URL from `Function -> Configuration -> Function URL`.

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
   - Here, `user_id, deployment_id` are of type `Text` and `files` is of type `File`

- Click on Send and wait for the request to Finish. The time for request to finish depends on the number of PDFs/size of PDFs in the S3 folder.

### 3. Train the Chatbot

#### Using Postman

- Obtain the OpenAI Lambda function URL from `Function -> Configuration -> Function URL`.

- Use the POST method on the URL (add /train at the end): `https://<ID>.lambda-url.<region>.on.aws/train`

- Request body in form-data:
   - `user_id`: <use the same user_id as the folder name created in folder s3://<bucket-name>/uploaded_files/>
   - `deployment_id`: <use the same deployment_id as the folder name created in folder s3://<bucket-name>/uploaded_files/<user_id>/>
   - Example:
        ```
        user_id: user-4321
        deployment_id: user-4321
        ```

- Click on Send and wait for the request to Finish. The time for request to finish depends on the number of PDFs/size of PDFs in the S3 folder.

### 4. Query the Chatbot

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
        user_id: user-4321
        deployment_id: user-4321
        question: what are Some of the key elements of focus group research? 
        prompt: You are given a paragraph and a query. You need to answer the query on the basis of paragraph. If the answer is not contained within the text below, say Sorry, I don't know. Please try again. P:{documents} Q: {query} A: 
        ```
        
- Click on Send and wait for the API response.

