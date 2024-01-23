# Create PDF Chatbot using OpenAI and fetch PDF files from S3 bucket

## Overview

This guide outlines the steps to set up a PDF Chatbot using OpenAI. The process involves creating a VPC, setting up an RDS PostgreSQL DB, creating Lambda functions, layers, and interacting with the application using Postman.

## Pre-requisite mandatory steps for initialWork/openAI/AzureOpenAI

### 1. Create VPC 

- Create a VPC with Private and Public Subnet.
- Provide internet access to the Private Subnet via NAT Gateway.

### 2. Create RDS PostgreSQL DB

- Create an RDS PostgreSQL DB in the previously created VPC.
- Note down the DB Name, DB User, and DB Password for future Lambda function configuration.

### 3. Clone GitHub Repository

- Clone the [GitHub folder](https://github.com/manipuraco/askcybexAPIs/) (or Download) and navigate to the AzureOpenAI folder, where 4 zip files are available.

### 4. Create Lambda Layer (Skip this step if you already have below Lambda layers)

- Go to Lambda Layers (in the same region as the created Lambda function) and click on "Create Layer".
- Provide Name, Description (optional), and select "Upload a .zip file" option (or use S3). Choose "Layer-01-Flask-langchain-openai.zip".
- Tick x86_64.
- Under Compatible Runtime, select Python3.11.
- Click Create.
- Repeat these steps for a total of 3 layers by selecting the other 2 zip files: "Layer-02-pinecone-psycopg2-PyPDF2-tqdm-Werkzeug-tiktoken.tzip" and "Layer-03-PyMuPDF.zip".