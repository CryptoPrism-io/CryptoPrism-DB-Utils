# CryptoPrism Database Monitoring Dashboard - PRD

**Product Requirements Document**  
**Version:** 1.0  
**Date:** September 8, 2025  
**Owner:** Yogesh Sahu  

---

## Executive Summary

This PRD outlines the implementation of a comprehensive Streamlit-based monitoring dashboard for the CryptoPrism database ecosystem. The dashboard will provide real-time visibility into ETL pipeline health, data quality assurance, performance metrics, and operational alerts, reducing the need for manual code-level monitoring.

## Project Context

### Background
- **Project Path:** `c:\cpio_db\CryptoPrism-DB-Utils`
- **Development History:** 9 months of production crypto feature engineering
- **Current State:** Production pipelines for crypto ratios, signals, and OHLCV data
- **Pain Points:** No centralized monitoring, manual QA checks, missing observability

### Recent Achievements
- Database performance issues resolved (91.7% test success rate)
- Modular optimization toolkits implemented
- Multi-table JOIN fixes completed
- Schema validation and primary key analysis tools ready

## Problem Statement

**Primary Issues:**
1. **Lack of Observability** - No central dashboard for ETL pipeline monitoring
2. **Manual QA Processes** - Time-consuming manual validation of data quality
3. **Performance Blind Spots** - No real-time query performance monitoring
4. **Reactive Maintenance** - Issues discovered after failures occur
5. **Operational Friction** - Requires deep code knowledge for health checks

**Business Impact:**
- Increased operational overhead
- Delayed issue detection and resolution
- Risk of data quality degradation
- Reduced team productivity

## Solution Overview

### Proposed Solution
A lightweight, real-time Streamlit dashboard that provides:
- **ETL Pipeline Monitoring** - Job status, runtime tracking, failure alerts
- **Data Quality Assurance** - Automated validation rules and reports
- **Performance Analytics** - Query optimization and index usage analysis  
- **Operational Controls** - Guided remediation and maintenance actions
- **Business Intelligence** - Signal analysis and strategy metrics

### Architecture Decision

**Selected: Lightweight Real-time Dashboard**

**Rationale:**
- Minimal deployment friction (Docker + Streamlit)
- Leverages existing database infrastructure
- Integrates with completed performance toolkits
- Provides immediate value without complex enterprise overhead

**Architecture Components:**
```
[ETL Scripts] ──writes──> [PostgreSQL]
     │                        │
     │                        │
     └──logs──> [reportlog.md] │
                               │
[Streamlit App] ──reads────────┘
     │
     ├─> [Slack Alerts]
     ├─> [Email Notifications]  
     └─> [Action Buttons] ──> [CLI Scripts]
```

## Requirements Specification

### Functional Requirements

#### FR1: ETL Pipeline Monitoring
- **FR1.1:** Display real-time ETL job status and execution history
- **FR1.2:** Track job duration, row counts, and success/failure rates
- **FR1.3:** Show runtime trend analysis and performance percentiles
- **FR1.4:** Provide job re-run capabilities with audit logging
- **FR1.5:** Filter jobs by status, date range, and job type

#### FR2: Data Quality Assurance
- **FR2.1:** Execute automated validation rules on data completeness
- **FR2.2:** Display schema compliance and primary key coverage
- **FR2.3:** Show data freshness and row count deltas
- **FR2.4:** Integrate existing comprehensive validation suite results
- **FR2.5:** Allow QA rule exceptions with documented approval

#### FR3: Performance Monitoring
- **FR3.1:** Display database query performance metrics
- **FR3.2:** Show index usage statistics and optimization recommendations
- **FR3.3:** Provide one-click index creation with safety confirmations
- **FR3.4:** Monitor table sizes and growth trends
- **FR3.5:** Execute EXPLAIN analysis on critical queries

#### FR4: Business Intelligence
- **FR4.1:** Display crypto signal distribution and performance metrics
- **FR4.2:** Show top-performing assets by alpha, beta, and Sharpe ratios
- **FR4.3:** Track binary signal counts and win rate distributions
- **FR4.4:** Provide historical backtest summary (if available)

#### FR5: Operational Controls
- **FR5.1:** Provide secure action buttons for maintenance tasks
- **FR5.2:** Display searchable logs with filtering capabilities
- **FR5.3:** Enable reportlog.md editing and changelog management
- **FR5.4:** Support file downloads for audit and analysis

#### FR6: Alerting and Notifications
- **FR6.1:** Send Slack notifications for ETL failures and performance issues
- **FR6.2:** Support configurable alert thresholds and cooldown periods
- **FR6.3:** Provide email escalation for critical failures
- **FR6.4:** Log all alerts with timestamps and recipients

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1:** Dashboard page load time < 5 seconds
- **NFR1.2:** Database query response time < 3 seconds for 95% of requests
- **NFR1.3:** Support concurrent users up to 10 without degradation

#### NFR2: Reliability
- **NFR2.1:** 99.5% uptime during business hours
- **NFR2.2:** Graceful handling of database connection failures
- **NFR2.3:** Automatic recovery from transient errors

#### NFR3: Security
- **NFR3.1:** Basic authentication for dashboard access
- **NFR3.2:** Read-only database access by default
- **NFR3.3:** Elevated permissions required for write operations
- **NFR3.4:** Audit logging for all administrative actions

#### NFR4: Usability
- **NFR4.1:** Intuitive navigation requiring minimal training
- **NFR4.2:** Mobile-responsive design for tablet access
- **NFR4.3:** Export capabilities for reports and data

#### NFR5: Maintainability
- **NFR5.1:** Containerized deployment with Docker
- **NFR5.2:** Environment-based configuration
- **NFR5.3:** Comprehensive error logging and monitoring

## Technical Specifications

### Technology Stack
- **Frontend:** Streamlit 1.28+
- **Backend:** Python 3.10+ with SQLAlchemy
- **Database:** PostgreSQL (existing)
- **Visualization:** Plotly/Altair for interactive charts
- **Deployment:** Docker + Docker Compose
- **Authentication:** Streamlit-Authenticator or basic auth

### Database Schema Changes

#### New Tables
```sql
-- ETL execution tracking
CREATE TABLE etl_runs (
    run_id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds NUMERIC(10,2),
    status VARCHAR(20) NOT NULL,
    rows_processed INTEGER DEFAULT 0,
    rows_failed INTEGER DEFAULT 0,
    error_message TEXT,
    script_version VARCHAR(50),
    git_commit_hash VARCHAR(40),
    created_by VARCHAR(50),
    metadata JSONB
);
```

#### New Indexes
```sql
-- Performance optimizations
CREATE INDEX idx_etl_runs_start_time ON etl_runs (start_time DESC);
CREATE INDEX idx_fe_ratios_signals_slug_ts ON "FE_RATIOS_SIGNALS" (slug, timestamp);
CREATE INDEX idx_fe_dmv_all_timestamp ON "FE_DMV_ALL" (timestamp DESC);
```

### Integration Points

#### Existing Toolkits Integration
- **query_optimization_toolkit.py** - Integrated into Performance page
- **schema_correction_toolkit.py** - Used for QA validation
- **primary_key_completion_toolkit.py** - Automated PK analysis
- **comprehensive_validation_suite.py** - Core QA engine

### Dashboard Pages Specification

#### Page 1: Overview Dashboard
**Purpose:** High-level health check and key metrics

**Components:**
- Key performance indicators (last run status, duration, row counts)
- Runtime trend sparkline (last 30 runs)
- Recent failures table (limit 10)
- Quick navigation links

**Metrics:**
- Last ETL run status and duration
- Primary key coverage percentage
- Average query performance
- Alert summary

#### Page 2: ETL Runs Monitor
**Purpose:** Detailed job execution tracking and controls

**Components:**
- Filterable job history table
- Runtime trend visualization
- Job detail modals with logs
- Re-run action buttons

**Features:**
- Server-side filtering and pagination
- Export to CSV functionality
- Job comparison capabilities
- Status-based color coding

#### Page 3: QA Checks & Validation
**Purpose:** Data quality monitoring and validation

**Components:**
- Validation rule status dashboard
- Schema compliance reports
- Data freshness indicators
- Exception management interface

**Integration:**
- Real-time execution of validation suite
- Historical QA trend analysis
- Automated report generation

#### Page 4: Performance & Indexing
**Purpose:** Database optimization and monitoring

**Components:**
- Query performance metrics
- Index usage statistics
- Optimization recommendations
- One-click index creation

**Features:**
- EXPLAIN plan analysis
- Slow query identification
- Performance trend tracking
- Automated recommendations

#### Page 5: Business Signals
**Purpose:** Crypto strategy and signal analysis

**Components:**
- Signal distribution charts
- Asset performance rankings
- Strategy metric summaries
- Historical trend analysis

**Metrics:**
- Alpha/Beta/Sharpe ratio distributions
- Win rate analysis
- Signal count trends
- Performance attribution

#### Page 6: Logs & Artifacts
**Purpose:** Log management and operational artifacts

**Components:**
- Searchable log viewer
- reportlog.md editor
- Changelog management
- File download capabilities

**Features:**
- Real-time log tailing
- Advanced filtering options
- Artifact versioning
- Audit trail maintenance

## Implementation Plan

### Phase 1: Foundation (Sprint 1 - 4 days)
**Priority:** CRITICAL

**Deliverables:**
- Database schema setup (etl_runs table)
- Basic Streamlit application structure
- Authentication implementation
- Overview and ETL Runs pages
- Initial integration with existing toolkits

**Acceptance Criteria:**
- Dashboard accessible with authentication
- ETL runs displayed with basic filtering
- Database connection established and tested
- Key metrics visible on Overview page

### Phase 2: QA Integration (Sprint 2 - 5 days)
**Priority:** HIGH

**Deliverables:**
- QA Checks page implementation
- Performance monitoring page
- Business signals dashboard
- Existing toolkit integration completion
- SQL execution framework

**Acceptance Criteria:**
- Validation suite results displayed
- Performance metrics updated real-time
- Index recommendations actionable
- Business metrics accurately calculated

### Phase 3: Production Readiness (Sprint 3 - 3 days)
**Priority:** MEDIUM

**Deliverables:**
- Alert system implementation
- Logs & Artifacts page
- Action button functionality
- Container deployment
- Documentation completion

**Acceptance Criteria:**
- Alerts sent for configured thresholds
- Log viewing and searching functional
- Actions executed with proper authorization
- Application deployed via Docker
- Complete documentation delivered

## Success Metrics

### Primary KPIs
1. **Mean Time to Detection (MTTD)** - Target: < 15 minutes for ETL failures
2. **Mean Time to Resolution (MTTR)** - Target: < 60 minutes for common issues
3. **Dashboard Adoption Rate** - Target: 100% team usage within 2 weeks
4. **Manual QA Reduction** - Target: 80% reduction in manual checks

### Secondary Metrics
1. **Dashboard Response Time** - Target: < 3 seconds for 95% of queries
2. **Alert Accuracy** - Target: < 10% false positive rate
3. **User Satisfaction Score** - Target: > 4.0/5.0 rating
4. **Operational Efficiency** - Target: 50% reduction in monitoring overhead

## Risk Assessment

### Technical Risks
- **Database Performance Impact** - Mitigation: Read-only queries, connection pooling
- **Authentication Security** - Mitigation: Environment-based secrets, regular rotation
- **Scalability Limitations** - Mitigation: Caching, query optimization

### Operational Risks
- **User Adoption Resistance** - Mitigation: Training, gradual rollout
- **Alert Fatigue** - Mitigation: Configurable thresholds, smart alerting
- **Maintenance Overhead** - Mitigation: Automated deployment, comprehensive documentation

## Deployment Strategy

### Environment Setup
```bash
# Required environment variables
DB_HOST=your_database_host
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=dbcp
DASHBOARD_PASSWORD=secure_password
SLACK_WEBHOOK_URL=https://hooks.slack.com/your/webhook
```

### Deployment Options

#### Option 1: Local Development
```bash
# Quick start for development
pip install streamlit pandas plotly sqlalchemy psycopg2-binary
streamlit run streamlit_app.py
```

#### Option 2: Docker Production
```bash
# Production deployment
docker build -t cryptoprism-monitor .
docker-compose up -d
```

#### Option 3: Cloud Deployment
- Google Cloud Run
- AWS ECS/Fargate  
- Azure Container Instances

## Maintenance and Support

### Operational Procedures
- **Daily:** Review Overview page for failures and anomalies
- **Weekly:** Analyze Performance page for optimization opportunities
- **Monthly:** Review QA Checks for schema drift and validation rule updates
- **Quarterly:** Assess ETL runtime trends and capacity planning

### Backup and Recovery
- ETL runs metadata backed up daily
- reportlog.md versioned in git repository
- Configuration management through environment variables
- Disaster recovery documented with RTO < 2 hours

## Future Enhancements

### Phase 2 Roadmap
1. **Advanced Analytics** - Machine learning anomaly detection
2. **Mobile Application** - Native mobile app for alerts
3. **API Integration** - REST API for external systems
4. **Enterprise Features** - Role-based access control, audit logs

### Potential Integrations
- **Prometheus/Grafana** - Advanced metrics collection
- **PagerDuty** - Incident management integration
- **Jupyter Notebooks** - Interactive analysis capabilities
- **Apache Airflow** - Workflow orchestration integration

---

## Appendix

### Glossary
- **ETL:** Extract, Transform, Load data processing pipeline
- **QA:** Quality Assurance validation processes
- **MTTD:** Mean Time to Detection of issues
- **MTTR:** Mean Time to Resolution of issues
- **RTO:** Recovery Time Objective

### References
- CryptoPrism-DB repository structure
- Existing performance optimization toolkits
- Database schema documentation
- Streamlit best practices guide

### Contact Information
- **Product Owner:** Yogesh Sahu
- **Technical Lead:** Claude AI Assistant
- **Repository:** https://github.com/CryptoPrism-io/CryptoPrism-DB-Utils

---

**Document Status:** DRAFT  
**Next Review:** September 15, 2025  
**Approval Required:** Product Owner, Technical Lead