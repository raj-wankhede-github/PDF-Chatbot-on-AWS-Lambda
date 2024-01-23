# Create PDF Chatbot using OpenAI and PDF files from S3 bucket

1)	Create VPC with Private and Public Subnet. Provide internet access to Private Subnet via NAT Gateway.

2)	Create RDS PostgreSQL DB in above created VPC with DB Name, DB User and DB Password. Kindly make note of the same as we will require this during Lambda function configuration.

3)	Clone Github repo 

Create Lambda function from AWS Console with python3.11 runtime with x86_64 architecture.


4) Create Lambda layer:
    (1)	Go to Lambda Layers (in same region as that of created Lambda function) and click on Create Layer.
    (2)	Give Name, Description (optional), and make sure “Upload a .zip file” option (or use S3) and select a file “Flask-langchain-openai.zip” 
    (3)	Tick x86_64
    (4)	Under Compatible Runtime, select Python3.11. This is important because the package/module dependencies were created from pip3.11 (that uses python3.11).
    (5)	Click Create
    (6)	Repeat these steps for creating total 3 layers by selecting one zip file at a time.

5)	Go to Lambda function -> “Code” and scroll down to “Layers” section and click on “Add a layer”. Select “Custom layers” and from drop down select the Layer that we created in previous step. 
    a)	In case the layer name is not shown in drop down, select “Specify an ARN” and provide ARN of Lambda Layer version.

