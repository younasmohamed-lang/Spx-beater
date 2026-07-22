# Lufthansa AWS Migration: Non-Sticky Competitor Service Analysis

## Executive Summary

This document identifies 14 third-party cloud and SaaS services that Lufthansa likely operates, ranked by migration feasibility to AWS-native equivalents. "Non-sticky" services are those where switching costs are manageable, AWS has a mature equivalent, data portability is reasonable, and no deep proprietary lock-in exists.

**Excluded (sticky):** SAP ERP (deeply customized), mainframe/legacy systems, heavily customized Salesforce CRM.

---

## Migration Candidate Matrix

| Current Service | AWS Target | Domain | Complexity | Stickiness |
|---|---|---|---|---|
| Snowflake | Amazon Redshift Serverless | Data Warehouse | Low | Low |
| Confluent Cloud (Kafka) | Amazon MSK Serverless | Event Streaming | Low | Low |
| Elastic Cloud | Amazon OpenSearch Service | Search & Logs | Low | Low |
| Datadog | CloudWatch + X-Ray + Managed Grafana | Observability | Low | Low |
| MongoDB Atlas | Amazon DocumentDB | NoSQL Database | Low | Low |
| Cloudflare CDN/WAF | CloudFront + AWS WAF + Shield | Edge / Security | Low | Low |
| HashiCorp Vault | AWS Secrets Manager + KMS | Secrets & Encryption | Medium | Low |
| Terraform Cloud | CloudFormation / CDK | Infrastructure as Code | Medium | Medium |
| Databricks | Amazon EMR + SageMaker | Data Engineering / ML | Medium | Medium |
| Twilio | Amazon Connect + SNS + SES + Pinpoint | Communications | Medium | Low |
| GitHub Actions | CodePipeline + CodeBuild | CI/CD | Medium | Medium |
| Okta | IAM Identity Center (SSO) | Identity / SSO | High | Medium |
| Azure SQL / Cosmos DB | Amazon Aurora / DynamoDB | Managed Database | High | Medium |
| Google BigQuery | Amazon Athena + Redshift | Ad-hoc Analytics | High | Medium |

---

## Detailed Analysis by Domain

### 1. Data & Analytics

#### Snowflake -> Amazon Redshift Serverless (Low Effort)
- **Migration path:** UNLOAD -> S3 -> COPY
- **Cost impact:** 25-40% savings
- **Why non-sticky:** Standard SQL workloads, BI tool integrations (Tableau, Looker) port with minimal refactoring. Tight S3/Glue/Lake Formation integration eliminates cross-cloud data transfer costs.
- **Risk:** Snowflake-specific functions need SQL translation.

#### Databricks -> Amazon EMR + SageMaker (Medium Effort)
- **Migration path:** Delta -> Iceberg on S3
- **Cost impact:** 20-35% savings
- **Why non-sticky:** Standard Spark/Python notebooks are portable. Predictive maintenance models for aircraft fleets and demand forecasting pipelines work on EMR.
- **Risk:** Unity Catalog governance, Delta-specific features.

#### Google BigQuery -> Amazon Athena + Redshift (Higher Effort)
- **Migration path:** Export -> S3 Parquet -> Athena
- **Cost impact:** Varies by query pattern
- **Why non-sticky at surface level:** SQL-on-data pattern is standard. However, BigQuery ML, nested schemas, and proprietary functions add friction.
- **Risk:** Proprietary SQL dialect, BigQuery ML -> SageMaker rewrite.

### 2. Event Streaming & Messaging

#### Confluent Cloud (Kafka) -> Amazon MSK Serverless (Low Effort)
- **Migration path:** MirrorMaker 2.0 replication
- **Cost impact:** 30-45% savings
- **Why non-sticky:** MSK runs Apache Kafka natively - same protocol, same client libraries, same consumer groups. Flight event producers/consumers need only endpoint reconfiguration.
- **Risk:** ksqlDB -> Amazon Managed Flink migration.

### 3. Search, Logging & Observability

#### Elastic Cloud -> Amazon OpenSearch Service (Low Effort)
- **Migration path:** Snapshot -> S3 -> restore
- **Cost impact:** 20-30% savings
- **Why non-sticky:** OpenSearch is API-compatible with Elasticsearch 7.x. Kibana dashboards port to OpenSearch Dashboards. Log ingestion pipelines require only endpoint changes.
- **Risk:** ES 8.x feature gap.

#### Datadog -> CloudWatch + X-Ray + Managed Grafana (Low Effort)
- **Migration path:** Agent swap + dashboard rebuild
- **Cost impact:** 40-60% savings
- **Why non-sticky:** Metrics standards (StatsD, OpenTelemetry) are portable. Datadog's per-host pricing becomes prohibitive at Lufthansa's fleet scale (700+ aircraft, thousands of services).
- **Risk:** Custom dashboard rebuild effort.

### 4. Managed Databases

#### MongoDB Atlas -> Amazon DocumentDB (Low Effort)
- **Migration path:** DMS or mongodump/restore
- **Cost impact:** 15-25% savings
- **Why non-sticky:** DocumentDB is wire-compatible with MongoDB 5.0+. Application code using the MongoDB driver works without changes.
- **Risk:** Atlas-specific aggregation features.

#### Azure SQL / Cosmos DB -> Aurora / DynamoDB (Higher Effort)
- **Migration path:** AWS DMS continuous replication
- **Cost impact:** 20-30% savings
- **Why partially non-sticky:** Azure SQL migrates cleanly via DMS. Cosmos DB multi-model APIs require splitting: documents -> DynamoDB, graph -> Neptune.
- **Risk:** Stored procedures, Cosmos multi-model split.

### 5. Security, Identity & Edge

#### Cloudflare CDN/WAF -> CloudFront + AWS WAF + Shield (Low Effort)
- **Migration path:** DNS cutover + rule migration
- **Cost impact:** 15-25% savings
- **Why non-sticky:** Standard CDN caching and WAF rules. No egress cost between AWS services. Lufthansa.com benefits from reduced latency to AWS-hosted backends.
- **Risk:** Cloudflare Workers -> Lambda@Edge rewrite.

#### HashiCorp Vault -> Secrets Manager + KMS (Medium Effort)
- **Migration path:** Export + API migration script
- **Cost impact:** 30-50% savings (operational cost)
- **Why non-sticky:** Secret storage and encryption-as-a-service are well-abstracted behind API layers. Eliminates Vault cluster operations and unseal key management.
- **Risk:** Dynamic secrets policies, transit engine custom workflows.

#### Okta -> IAM Identity Center (Higher Effort)
- **Migration path:** Phased SAML app migration
- **Cost impact:** 50-70% savings on licensing
- **Why non-sticky:** SAML/OIDC are standard protocols. SCIM provisioning from existing directories is supported.
- **Risk:** Custom MFA flows, lifecycle hooks, deep third-party integrations.

### 6. DevOps & Infrastructure

#### Terraform Cloud -> CloudFormation / CDK (Medium Effort)
- **Migration path:** Incremental cdktf -> CDK
- **Cost impact:** Terraform Cloud license eliminated
- **Why non-sticky (for AWS-only infra):** CDK provides type-safe IaC with built-in state tracking. Multi-cloud Terraform modules remain valid if other clouds are retained.
- **Risk:** HCL rewrite effort for large module libraries.

#### GitHub Actions -> CodePipeline + CodeBuild (Medium Effort)
- **Migration path:** Workflow -> buildspec.yml conversion
- **Cost impact:** 10-20% savings
- **Why non-sticky:** Build logic (scripts, tests, deploys) is CI-agnostic. CodeBuild runs within VPC with IAM roles - better for regulated aviation software (DO-178C).
- **Risk:** Community action ecosystem loss.

### 7. Customer Communications

#### Twilio -> Amazon Connect + SNS + SES + Pinpoint (Medium Effort)
- **Migration path:** API abstraction layer swap
- **Cost impact:** 30-50% savings at volume
- **Why non-sticky:** Messaging APIs (SMS, email, voice) are commodity interfaces behind abstraction layers. High-volume airline messaging benefits from AWS's bulk pricing.
- **Risk:** Twilio Flex contact center -> Amazon Connect rebuild.

---

## Recommended Phasing

### Phase 1: Quick Wins (Months 1-3)
Near-zero application changes. Immediate cost reduction.
- Confluent Cloud -> Amazon MSK Serverless
- Elastic Cloud -> Amazon OpenSearch Service
- Cloudflare -> CloudFront + AWS WAF
- MongoDB Atlas -> Amazon DocumentDB

### Phase 2: Cost Optimization (Months 3-6)
Replace high-cost SaaS licensing with AWS-native equivalents.
- Datadog -> CloudWatch + X-Ray + Managed Grafana
- Snowflake -> Amazon Redshift Serverless
- HashiCorp Vault -> Secrets Manager + KMS
- Twilio -> SNS + SES + Amazon Connect

### Phase 3: Platform Consolidation (Months 6-12)
Services requiring code changes, schema adaptation, or workflow rewrites.
- Terraform Cloud -> CloudFormation / CDK
- GitHub Actions -> CodePipeline + CodeBuild
- Databricks -> EMR + SageMaker

### Phase 4: Strategic Migration (Months 12-18)
Deeply integrated services requiring phased cutover and parallel running.
- Okta -> IAM Identity Center
- Azure SQL / Cosmos DB -> Aurora / DynamoDB
- Google BigQuery -> Athena + Redshift

---

## Services Deliberately Excluded (Sticky)

| Service | Reason |
|---|---|
| SAP S/4HANA | Deeply customized ERP with years of airline-specific configuration. Migration risk outweighs benefit. Consider SAP on AWS instead. |
| Salesforce CRM | Heavy customization, Apex code, Lightning components. Replacement with AWS services not practical. |
| Amadeus/SITA | Industry-standard GDS and airline messaging - no AWS equivalent exists. |
| IBM Mainframe (TPF) | Legacy reservation/DCS systems. Modernization is a multi-year program, not a migration. |

---

## Key Principles

1. **Non-sticky = low switching cost.** We target services built on open standards (SQL, Kafka protocol, MongoDB wire protocol, SAML/OIDC, OpenTelemetry) where AWS has API-compatible or functionally equivalent offerings.

2. **Cost is not the only driver.** Consolidation reduces credential sprawl, simplifies compliance (GDPR, PCI-DSS), and enables unified IAM policies across all services.

3. **Parallel running for databases.** All database migrations should run source and target in parallel with DMS continuous replication before cutover.

4. **Preserve multi-cloud optionality.** Some services (Terraform, GitHub) provide multi-cloud value. Migrate only the AWS-specific workflows; keep the tools if other clouds remain in play.
