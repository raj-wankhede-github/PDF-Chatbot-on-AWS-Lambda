# PDF Chatbot 

# Pre-requisite mandatory steps for ManualUpload/openAI/AzureOpenAI

## Overview

This guide outlines the steps to set up a PDF Chatbot using OpenAI. The process involves creating a VPC, setting up an RDS PostgreSQL DB, creating Lambda functions, layers, and interacting with the application using Postman.

### 1. Create VPC 

- Create a VPC with Private and Public Subnet.
- Provide internet access to the Private Subnet via NAT Gateway.

### 2. Create RDS PostgreSQL DB

- Create an RDS PostgreSQL DB with the created VPC in Private subnet.
- Note down the "DB name", "Master username", "Master password" and "Endpoint URL" for Lambda function configuration.

### 3. Clone GitHub Repository

- Clone the [GitHub folder](https://github.com/manipuraco/askcybexAPIs/) (or Download) and navigate to the AzureOpenAI folder, where 4 zip files are available.

### 4. Create Lambda Layer

- Go to Lambda Layers (in the same region as the created Lambda function) and click on "Create Layer".
- Provide Name, Description (optional), and select "Upload a .zip file" option (or use S3). Choose "Layer-01-Flask-langchain-openai.zip".
- Tick x86_64.
- Under Compatible Runtime, select Python3.11.
- Click Create.
- Repeat these steps for a total of 3 layers by selecting the other 2 zip files: "Layer-02-pinecone-psycopg2-PyPDF2-tqdm-Werkzeug-tiktoken.tzip" and "Layer-03-PyMuPDF.zip".