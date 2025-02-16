# EC2 Subnet Details Cloudformation Custom Resource

A AWS Lambda-based CloudFormation Custom Resource for retrieving detailed subnet information, including associated route tables. This custom resource helps you access subnet properties that aren't directly available through standard CloudFormation resources.

## Overview

This custom resource allows you to:
- Retrieve detailed subnet properties during CloudFormation stack operations
- Access associated route table information for a given subnet
- Handle subnet information retrieval in a safe, CloudFormation-compatible way

## Prerequisites

- AWS Account
- IAM permissions for the Lambda function:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ec2:DescribeSubnets",
          "ec2:DescribeRouteTables"
        ],
        "Resource": "*"
      }
    ]
  }
  ```

## Installation

### Building the Lambda Container

1. Build the Docker image:
   ```bash
   docker build -t aws-cfn-subnet-details .
   ```

2. Tag and push to Amazon ECR:
   ```bash
   aws ecr get-login-password --region REGION | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com
   docker tag aws-cfn-subnet-details:latest ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/aws-cfn-subnet-details:latest
   docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/aws-cfn-subnet-details:latest
   ```

## Usage

### CloudFormation Template Example

```yaml
Resources:
  SubnetDetails:
    Type: Custom::SubnetDetails
    Properties:
      ServiceToken: !GetAtt SubnetDetailsFunction.Arn
      SubnetId: !Ref YourSubnetId

  SubnetDetailsFunction:
    Type: AWS::Lambda::Function
    Properties:
      Code:
        ImageUri: ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/aws-cfn-subnet-details:latest
      PackageType: Image
      Architectures:
        - arm64
      Role: !GetAtt LambdaExecutionRole.Arn
      Timeout: 30
      MemorySize: 128

  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: EC2Permissions
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - ec2:DescribeSubnets
                  - ec2:DescribeRouteTables
                Resource: '*'
```

### Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| SubnetId | String | The ID of the subnet to retrieve details for |

### Return Values

The custom resource returns the following subnet properties:

```json
{
  "AvailabilityZone": "us-east-1a",
  "CidrBlock": "10.0.0.0/24",
  "VpcId": "vpc-12345678",
  "SubnetId": "subnet-12345678",
  "RouteTable": "rtb-12345678"
}
```

You can reference these values in your CloudFormation template using `!GetAtt`:

```yaml
!GetAtt SubnetDetails.AvailabilityZone
!GetAtt SubnetDetails.CidrBlock
!GetAtt SubnetDetails.VpcId
```

## Development

### Local Development Setup

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix
   # or
   .\venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install boto3 urllib3
   ```

### Testing

To test locally with AWS credentials:

```bash
export AWS_PROFILE=your-profile
python -c "import src.index as lambda_function; lambda_function.handler({'RequestType': 'Create', 'ResourceProperties': {'SubnetId': 'subnet-12345678'}}, None)"
```

## License

This project is licensed under the terms of the LICENSE.md file included in the repository.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
