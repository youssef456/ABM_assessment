# System Architecture Design

## Design Summary
The proposed system follows a **Decoupled Microservices Architecture** optimized for high-volume automation tasks. By using **RabbitMQ** as a central message broker, we ensure asynchronous task processing and resilience against worker failures. The **Worker Layer** is designed for horizontal scalability, allowing the system to handle spikes in demand by spinning up additional containerized Playwright instances. Data integrity is maintained via a **High-Availability SQL Cluster**, while a comprehensive **Observability Stack** (Prometheus/ELK) provides real-time health and error tracking. This design ensures that task execution is reliable, observable, and easily scalable.

## Architecture Diagram (Mermaid)

```mermaid
graph TD
    User((User/Client)) --> API[API Gateway / Load Balancer]
    
    subgraph "Messaging Layer"
        API -->|Task Submission| MQ[RabbitMQ Message Queue]
    }
    
    subgraph "Worker Layer (Scalable)"
        MQ -->|Task Distribution| W1[Worker Node 1]
        MQ -->|Task Distribution| W2[Worker Node 2]
        MQ -->|Task Distribution| WN[Worker Node N]
    }
    
    subgraph "Persistence Layer"
        W1 & W2 & WN -->|Data Storage| DB[(SQL Database)]
    end
    
    subgraph "Monitoring & Logging"
        W1 & W2 & WN -->|Metrics| MON[Monitoring Stack - Prometheus/Grafana]
        W1 & W2 & WN -->|Logs| LOG[Logging Stack - ELK/Loki]
        MON -->|Health Checks| Health[System Health]
        MON -->|Load Metrics| Load[System Current Load]
        LOG -->|Error Tracking| Errors[System Error Logging]
    end
    
    subgraph "Recovery & Failover"
        DB --- DB_Slave[(SQL Secondary)]
        MQ --- MQ_Cluster[RabbitMQ Cluster]
    end
```

## Component Details

### 1. Message Queue System (RabbitMQ)
- **Role**: Acts as a buffer and task distributor.
- **Benefits**: Decouples the API from the actual processing, enabling asynchronous task handling and persistence during worker downtime.
- **Failover**: Configured in a cluster with mirrored queues to prevent data loss.

### 2. Worker Node Architecture
- **Role**: Executes the automation and scraping logic (Playwright).
- **Horizontal Scaling**: New worker nodes can be spun up dynamically based on queue length (autoscale).
- **Isolation**: Each worker runs in a containerized environment to ensure clean states and security.

### 3. SQL Database
- **Role**: Stores task results, user metadata, and historical performance data.
- **Failover**: Implemented with primary-secondary replication for high availability.

### 4. Monitoring Stack
- **System Health**: Real-time heartbeat monitoring of all microservices.
- **System Current Load**: Tracks CPU/Memory usage of workers and MQ throughput.
- **System Error Logging**: Centralized error tracking for debugging and failover triggers.

### 5. Failover and Recovery Mechanisms
- **Retries**: Workers use exponential backoff for transient failures.
- **Dead Letter Queues (DLQ)**: Failed tasks are moved to a DLQ for manual inspection or automated retry with different parameters.
- **Load Balancing**: API Gateway redistributes traffic if a specific regional cluster fails.
