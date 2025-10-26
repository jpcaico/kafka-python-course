# ShopStream - Real-Time E-Commerce Data Streaming Pipeline

## Project Overview

ShopStream is an educational data streaming pipeline that simulates a global e-commerce platform processing purchase events in real-time. The project demonstrates modern data engineering patterns using Apache Kafka, Avro schema management, and data lake architecture.

## Learning Objectives

### Primary Goals
- **Stream Processing Fundamentals**: Understand Kafka producers, consumers, and topics
- **Schema Management**: Learn Avro serialization and Schema Registry patterns
- **Data Lake Architecture**: Implement medallion architecture (Bronze/Silver/Gold layers) (Only Bronze implemented in this step)
- **Distributed Systems**: Explore fault tolerance, replication, and partitioning strategies
- **Real-World Patterns**: Apply production-ready configuration and monitoring practices

### Technical Skills Developed
- Kafka cluster setup and administration
- Avro schema design and evolution
- Stream-to-batch processing patterns
- Object storage integration (MinIO/S3)
- Parquet columnar format optimization
- Consumer group coordination and offset management

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SHOPSTREAM ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌──────────────────────────────────────────────────────┐
│  EVENT PRODUCER │    │                 KAFKA CLUSTER                        │
│                 │    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│ ┌─────────────┐ │    │  │   BROKER 1  │ │   BROKER 2  │ │   BROKER 3  │    │
│ │ Faker Data  │ │───▶│  │   :9094     │ │   :9095     │ │   :9096     │    │
│ │ Generator   │ │    │  └─────────────┘ └─────────────┘ └─────────────┘    │
│ └─────────────┘ │    │         │              │              │             │
│                 │    │    ┌─────────────────────────────────────────┐       │
│ ┌─────────────┐ │    │    │        TOPIC: shopstream-purchases      │       │
│ │ Avro        │ │    │    │                                         │       │
│ │ Serializer  │ │    │    │  ┌─────────┐ ┌─────────┐ ┌─────────┐   │       │
│ └─────────────┘ │    │    │  │ PART 0  │ │ PART 1  │ │ PART 2  │   │       │
└─────────────────┘    │    │  │         │ │         │ │         │   │       │
                       │    │  │[US,EU,  │ │[US,EU,  │ │[US,EU,  │   │       │
┌─────────────────┐    │    │  │ ASIA]   │ │ ASIA]   │ │ ASIA]   │   │       │
│ SCHEMA REGISTRY │    │    │  └─────────┘ └─────────┘ └─────────┘   │       │
│                 │    │    └─────────────────────────────────────────┘       │
│ ┌─────────────┐ │    └──────────────────────────────────────────────────────┘
│ │ Avro Schema │ │                          │
│ │ Management  │ │                          ▼
│ └─────────────┘ │    ┌──────────────────────────────────────────────────────┐
│                 │    │                EVENT CONSUMER                        │
│ ┌─────────────┐ │    │                                                      │
│ │ Schema      │ │    │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│ │ Validation  │ │    │ │ Regional    │ │ Batch       │ │ Parquet     │    │
│ └─────────────┘ │    │ │ Batching    │ │ Processing  │ │ Conversion  │    │
└─────────────────┘    │ └─────────────┘ └─────────────┘ └─────────────┘    │
                       └──────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAKE (MinIO)                               │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │ BRONZE      │    │ SILVER      │    │ GOLD        │                    │
│  │ (Raw Data)  │    │ (Cleaned)   │    │ (Business)  │                    │
│  │             │    │             │    │             │                    │
│  │ region=US/  │    │ [Future]    │    │ [Future]    │                    │
│  │ region=EU/  │    │ Validation  │    │ Aggregated  │                    │
│  │ region=ASIA/│    │ & Quality   │    │ Metrics     │                    │
│  │             │    │ Rules       │    │ & KPIs      │                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Infrastructure Components

### Kafka Cluster Configuration

#### Brokers
- **Count**: 3 brokers for fault tolerance
- **Replication Factor**: 3 (every message stored on all brokers)
- **Ports**: 9094, 9095, 9096 (external access)
- **Mode**: KRaft (no Zookeeper dependency)

#### Topics
- **Name**: `shopstream-purchases`
- **Partitions**: 3 (enables parallel consumer processing)
- **Retention**: 7 days (balances storage cost vs replay capability)
- **Compression**: Snappy (balance of speed vs size)

#### Partitioning Strategy
```
Message Key: user_id (string)
Partition Assignment: hash(user_id) % 3

Example Distribution:
- user_id "1234" → Partition 1
- user_id "5678" → Partition 0  
- user_id "9999" → Partition 2

Result: Same user's events always in same partition (ordering preserved)
```

### Schema Registry
- **Purpose**: Centralized Avro schema management
- **URL**: http://localhost:8082
- **Subject**: `shopstream-purchases-value`
- **Compatibility**: Backward compatible schema evolution

### Data Lake Storage (MinIO)
- **Object Storage**: S3-compatible API
- **Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Bucket Strategy**: `bronze-events` (raw ingestion layer)
- **Partitioning**: Hive-style (`region=US/date=2025-10-24/`)

## Data Flow Architecture

### Event Generation
```
Regional Purchase Events → Avro Serialization → Kafka Topic
         ↓                        ↓                  ↓
    [US, EU, ASIA]        [Schema Validation]   [3 Partitions]
```

### Regional Batching Strategy
```
Kafka Partitions (Mixed Regions)     Consumer Batching (Regional)
┌─────────────────────────────┐      ┌─────────────────────────────┐
│ Partition 0: [US,EU,ASIA]   │      │ US Batch: [All US events]  │
│ Partition 1: [EU,ASIA,US]   │ ──▶  │ EU Batch: [All EU events]  │
│ Partition 2: [ASIA,US,EU]   │      │ ASIA Batch: [ASIA events]  │
└─────────────────────────────┘      └─────────────────────────────┘
                                                    ↓
                                      ┌─────────────────────────────┐
                                      │ Data Lake Files:            │
                                      │ region=US/file1.parquet     │
                                      │ region=EU/file2.parquet     │
                                      │ region=ASIA/file3.parquet   │
                                      └─────────────────────────────┘
```

### Key Insight: Infrastructure vs Business Logic
- **Kafka Partitions**: Technical distribution (user_id based)
- **Regional Batching**: Business logic organization
- **Result**: Same region events from different partitions grouped together


## Configuration Deep Dive

### Critical Parameters

#### Batch Processing
```yaml
# Balances efficiency vs latency
BATCH_SIZE: 50                    # Events per file
BATCH_TIMEOUT_SECONDS: 30         # Max wait time
```

#### Consumer Groups
```yaml
group_id: purchase-ingestion-consumers
auto_offset_reset: earliest       # Process from beginning
enable_auto_commit: false         # Manual offset management
```

#### Topic Settings
```yaml
num_partitions: 3                 # Parallel processing capability
replication_factor: 3             # Fault tolerance level
min_insync_replicas: 2            # Write consistency requirement
retention_ms: 604800000           # 7 days retention
```

## Monitoring & Operations

### Key Metrics to Watch
- **Producer**: Throughput (events/second), error rate
- **Consumer**: Lag per partition, processing rate
- **Storage**: Files created, bytes written, regional distribution
- **Infrastructure**: Broker health, partition leadership

### Health Checks
```bash
# Kafka Cluster
docker-compose ps                              # Container status
curl http://localhost:8080                     # Kafka UI

# Schema Registry  
curl http://localhost:8082/subjects            # Available schemas

# MinIO Storage
curl http://localhost:9000/minio/health/ready  # Storage health
```

### Operational Commands
```bash
# View topic details
docker exec kafka-1 kafka-topics --describe --topic shopstream-purchases --bootstrap-server localhost:9092

# Monitor consumer group
docker exec kafka-1 kafka-consumer-groups --describe --group purchase-ingestion-consumers --bootstrap-server localhost:9092

# Check message flow
docker exec kafka-1 kafka-console-consumer --topic shopstream-purchases --from-beginning --max-messages 5 --bootstrap-server localhost:9092
```

## Deployment Sequence

### Development Environment Setup
1. **Infrastructure**: `docker-compose up -d`
2. **Topics**: `python admin/setup_topics.py`
3. **Schema**: `python schemas/verify_schema.py`
4. **Storage**: `python storage/test_storage.py`
5. **Producer**: `python services/event_generator.py`
6. **Consumer**: `python services/purchase_consumer.py`

### Production Considerations
- **Security**: TLS encryption, SASL authentication, ACLs
- **Monitoring**: Prometheus metrics, Grafana dashboards, alerting
- **Scaling**: Additional brokers, partition expansion, consumer instances
- **Backup**: Cross-region replication, schema versioning, data archival

## Educational Value

### Stream Processing Concepts
- **At-least-once delivery**: Message processing guarantees
- **Consumer groups**: Horizontal scaling and fault tolerance
- **Offset management**: Exactly-once processing patterns
- **Backpressure handling**: Flow control in streaming systems

### Data Engineering Patterns
- **Schema evolution**: Backward/forward compatibility strategies
- **Medallion architecture**: Bronze/Silver/Gold data progression
- **Partitioning strategies**: Query optimization and parallel processing
- **Stream-to-batch**: Real-time ingestion with analytical optimization

## Troubleshooting Guide

### Common Issues

#### Consumer Not Processing
- Check producer is generating events
- Verify topic exists and has messages
- Confirm schema compatibility
- Review consumer group assignment

#### Storage Failures
- Validate MinIO connectivity
- Check bucket permissions
- Verify Parquet serialization
- Monitor disk space

#### Performance Problems
- Tune batch sizes for throughput vs latency
- Scale consumer instances for higher throughput
- Optimize partition count for parallelism
- Monitor broker resource utilization
