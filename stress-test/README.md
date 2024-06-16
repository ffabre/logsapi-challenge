## Running the Stress Test

### Prerequisites

To run the stress test locally, you need to have [k6](https://k6.io/) installed. Follow these steps to install k6 and run the stress test.

### Running the Stress Test

The stress test script (`script.js`) can be configured and executed using the following steps:

1. **Configure the Test Script**

    Inside the `script.js` file, you can modify the `TARGET_VUS` variable to set the number of virtual users (VUs) for the test:

    ```javascript
    export let TARGET_VUS = 100; // Modify this value as needed
    ```

2. **Execute the Stress Test**
    Run the following command in your terminal to start the stress test:

    ```bash
    k6 run script.js
    ```

    The test will increase the number of VUs to the TARGET_VUS amount during the first minute, then run with TARGET_VUS for three minutes, and finally decrease the VUs to zero during the last minute. The entire test will take 5 minutes.


## Stress Testing Observations and Fixes

### Bottleneck: FastAPI Response Times and Timeouts

- **Issue:** Initial requests took around 750ms, leading to timeouts at 100VUs.
- **Fix:** Reuse a global boto session in FastAPI instead of creating a new one per request. This eliminated timeouts and improved response times significantly.

### Bottleneck: Worker CPU Saturation and Growing SQS Messages

- **Issue:** At 200VUs, SQS backlog grew, and worker CPU hit near 100%. A sign that the worker could not keep up with the workload.
- **Fix:** Changed the worker to use SQLAlchemy's `insert_all` to batch database writes, reducing write load and allowing the worker to handle 200VUs effectively.

### Bottleneck: FastAPI CPU Peaking 

- **Issue:** at 500VUs, CPU utilization spiked and response times increased.
- **Fix:** Vertically scaled the FastAPI instance and adjusted UVICORN worker processes to match available vCPUs, improving performance under load.

### Handling Increased Load: The Scalability Pattern

#### Observation

As the workload increased, both the FastAPI application and the worker processing log messages from SQS encountered difficulties in meeting the demand. This assessment was based on monitoring the number of messages in the SQS queue and observing CPU usage. While memory usage was not problematic during this testing phase, it could become a concern if log messages increase in size or if modifications to the FastAPI endpoint allow processing of multiple logs concurrently.

**FastAPI:**
- **CPU Usage:** As the number of incoming requests (Virtual Users, or VUs) increased, the CPU utilization of the FastAPI application peaked.
- **Response Times:** With increased CPU load, response times for handling requests also started to degrade.

**Worker:**
- **SQS Backlog:** Messages in the SQS queue began to accumulate, indicating that the worker was unable to process messages as quickly as they were being produced.
- **CPU Saturation:** The worker's CPU usage approached 100%, suggesting that it was operating at its processing capacity limit.

#### Solution

To address these issues and ensure the system could handle increased load effectively, a combination of vertical and horizontal scaling strategies has to be employed:

1. **Vertical Scaling:**
   - **FastAPI:** Increased the CPU allocated to individual instances of the FastAPI application. This approach helps in handling higher loads by providing more computational power and memory resources per instance.
   - **Worker:** Similarly, the worker was vertically scaled to add more resources (CPU, memory) per instance. This allows the worker to process messages more efficiently without hitting CPU bottlenecks.

2. **Horizontal Scaling:**
   - **FastAPI:** Deployed multiple instances of the FastAPI application to run concurrently. This horizontal scaling approach distributes incoming requests across multiple instances, allowing the system to handle a larger total volume of requests in parallel.
   - **Worker:** Similarly, horizontal scaling was applied to the worker component by deploying multiple worker instances. This allows the system to process messages from the SQS queue in parallel, reducing the backlog and improving overall processing throughput.



### Future Considerations: Database Scalability

- **Potential Bottleneck:** Database performance under increased write and read loads.
- **Scaling Strategy:** Plan for vertical scaling (more resources per node) initially, followed by horizontal scaling (partitioning for writes, replicas for reads) as needed.
