# Application

This repository contains components for a logging service using FastAPI and AWS services.

## Components

### 1. FastAPI Application

The FastAPI application receives log messages and forwards them to an SQS queue. It is designed to handle incoming requests efficiently.

### 2. Worker

The worker component consumes log messages from the SQS queue and stores them in a PostgreSQL database. It ensures that messages are processed and stored reliably.

### 3. Stress Testing with k6

A stress testing script using k6 is provided to simulate traffic to the FastAPI application:

- **Ramp-up:** Increases Virtual Users (VUs) to a specified amount over 1 minute.
- **Steady-state:** Maintains a constant load (specified VUs) for 3 minutes.
- **Ramp-down:** Decreases VUs to 0 over 1 minute.

The VUs send one log after another to the service as soon as they receive a response from it.

### 4. CDK (AWS Cloud Development Kit)

The CDK script automates the deployment of the entire system. It includes provisions for deploying the FastAPI application, Worker, SQS, and PostgreSQL, along with a CloudWatch dashboard for monitoring key metrics.

## Running the Application Locally

### Requirements

Ensure you have the following installed on your local machine:

- [Docker](https://www.docker.com/)
- [docker-compose](https://docs.docker.com/compose/)

### Steps to Run

1. **Clone the Repository:**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Run docker-compose**

    Navigate to the root directory of your project where docker-compose.yml is located, and execute the following command:

    ```bash
    docker-compose build
    ```
    ```bash
    docker-compose up
    ```
    This command will start all the services required. The API will be available at localhost:8000/


## Deploying the Application to AWS

### Requirements

Ensure you have the following installed and configured:
- [Docker](https://www.docker.com/)
- [AWS CLI](https://aws.amazon.com/cli/)
- [CDK (AWS Cloud Development Kit)](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)

### Steps to Deploy

1. **Set AWS Credentials:**

   Export your AWS credentials as environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=<your-access-key-id>
   export AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
   export AWS_DEFAULT_REGION=<your-aws-region>
   ```

2. **Navigate to CDK Folder:**

   Go to the directory where the CDK project is located:
   ```bash
   cd cdk
   ```

3. **Bootstrap your AWS environment:**
   ```bash
   cdk bootstrap
   ```

4. **Set Docker Platform (for Mac M1/M2):**
   If you are using a Mac M1 or M2 with Docker, export the Docker default platform.
   ```bash
   export DOCKER_DEFAULT_PLATFORM="linux/amd64"
   ```

5. **Create and Activate Virtual Environment:**

   Create a virtual environment and activate it:
   ```bash
   python3 -m venv .env
   source .env/bin/activate
   ```

6. **Install Requirements:**

   Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

7. **Deploy Using CDK:**

   Deploy your application using CDK:
   ```bash
   cdk deploy
   ```

8. **To know the IP of the FastAPI application:**

    Run the following command
    ```bash
    aws elbv2 describe-load-balancers --query "LoadBalancers[*].[LoadBalancerName,DNSName]" --output table
    ```
    Look for the load balancer associated with your CDK stack and resolve the DNS name with
    ```bash
    nslookup <your-load-balancer-dns-name>
    ```


## Stress Test
   Refer to [the stress-test README](stress-test/README.md)


## Missing Features and Improvements

### 1. Better Subnetting in the CDK

Currently, the CDK setup includes only one public subnet. For better security and architecture design:
- The Load Balancer for the FastAPI application should be in a public subnet.
- All other resources, including the ECS tasks and the database, should be placed in private subnets.

### 2. Write Unit and Integration Tests

To ensure the reliability and maintainability of the application:
- **Unit Tests**: Write unit tests for individual functions and components to verify their behavior in isolation.
- **Integration Tests**: Write integration tests to ensure that different parts of the application work together as expected. This includes testing the FastAPI endpoints, the SQS integration, and the database interactions.

### 3. Thresholds and Alerts for Auto Scaling Services

To maintain performance and reliability under varying loads:
- Define thresholds for CPU, memory usage and messages in the SQS to trigger auto-scaling actions for the FastAPI and worker services.
- Set up CloudWatch alarms to monitor these metrics and trigger scaling policies.
- Configure notifications to alert when thresholds are breached or scaling actions are performed.


### 4. Optional Read Endpoint for Logs Using Redis as Cache

#### Overview

The current project lacks an endpoint to retrieve logs after they have been processed and stored. Implementing a read endpoint for logs with Redis as a cache can provide fast access to recent logs, reducing the load on the PostgreSQL database.


##### Simplest Approach: Get Log by ID

The simplest read endpoint would allow fetching a log by its ID. However, this approach may not be very practical since the endpoint to create logs currently does not return an ID.

##### Realistic Approach: Get Last N Logs Sorted by Timestamp

A more practical solution would be to retrieve the last N logs sorted by timestamp in descending order. Additionally, the endpoint could support an offset parameter for pagination.

Possible solutions may involve:

##### Caching last N minutes of logs

To optimize performance:
- Store the last N minutes of logs in Redis with keys that expire when the log timestamp is greater than N minutes from now.
- Use Redis to fetch logs based on timestamp ranges.
- If Redis does not contain the complete dataset, fall back to querying PostgreSQL.

##### Caching last N logs

Another approach is to maintain a sorted set in Redis where each log entry is scored by its timestamp. This allows efficient retrieval of the last M logs without needing to query PostgreSQL unless necessary.
