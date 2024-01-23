# Create PDF Chatbot using OpenAI and PDF files from S3 bucket

1)	Create VPC with Private and Public Subnet. Provide internet access to Private Subnet via NAT Gateway.

2)	Create RDS PostgreSQL DB in above created VPC with DB Name, DB User and DB Password. Kindly make note of the same as we will require this during Lambda function configuration.

3)	Clone Github repo (or Download) and move to OpenAI folder, where you will find 4 zip files.

4) Create Lambda function from AWS Console with python3.11 runtime with x86_64 architecture.
   &emsp;&emsp;a) Go to newly created function and under "Code" tab click on "Upload from" and select option ".zip file".
   b) Select Deployment-OpenAI.zip from your local machine and click on "Save".

4) Create Lambda layer:\n
    \t(a)	Go to Lambda Layers (in same region as that of created Lambda function) and click on Create Layer.\n
    \t(b)	Give Name, Description (optional), and make sure “Upload a .zip file” option (or use S3) and select a file Layer-01-Flask-langchain-openai.zip" \n
    \t(c)	Tick x86_64\n
    \t(d)	Under Compatible Runtime, select Python3.11. This is important because the package/module dependencies were created from pip3.11 (that uses python3.11).\n
    \t(e)	Click Create\n
    \t(f)	Repeat these steps for creating total 3 layers by selecting other 2 zip files "Layer-02-pinecone-psycopg2-PyPDF2-tqdm-Werkzeug-tiktoken.\tzip" and "Layer-03-PyMuPDF.zip".

5)	Go to Lambda function -> “Code” and scroll down to “Layers” section and click on “Add a layer”. Select “Custom layers” and from drop down select the Layer that we created in previous step. \n
    a)	In case the layer name is not shown in drop down, select “Specify an ARN” and provide ARN of Lambda Layer version.

6) 
