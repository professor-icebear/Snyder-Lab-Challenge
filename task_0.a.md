# Task 0.a – Data Volume Estimation

> 📅 Date: 2025-07-06  
> 🧑 Author: Mohammad Abdullah  

---

## 🎯 Objective

The goal of this task is to perform **back-of-the-envelope data estimations** to understand:
- How much data will be generated
- What kind of storage we’ll need
- Whether the system might struggle with performance or scalability

This helps us make better technical decisions for data ingestion, querying, and storage.

---

## ✅ Chosen Metrics

We picked **6 realistic Fitbit metrics** that are useful for a **physical activity affecting sleep** study. These metrics were chosen based on:
- Their relevance to either physical activity or sleep quality
- Their availability from Fitbit’s Web API
- Different data resolutions to reflect a variety of ingestion rates

| Metric                  | Resolution | Why This Metric?                                                                                            |
|-------------------------|------------|-------------------------------------------------------------------------------------------------------------|
| **Heart Rate**          | 1s         | Most precise and important for detecting exertion and rest. Used to measure both activity and sleep state.  |
| **Steps**               | 1min       | Basic movement data. Easily correlated with general physical activity and energy expenditure.               |
| **Active Zone Minutes** | 5min       | Shows time spent in high effort zones like Cardio and Peak. Useful to understand exercise quality.          |
| **Sleep Stages**        | 1min       | Tracks light, deep, REM stages to assess sleep quality.                                                     |
| **SpO₂**                | 1min       | Measures blood oxygen levels, especially useful for detecting disturbances during sleep (e.g., sleep apnea).|
| **HRV**                 | 5min       | Indicator of recovery and stress. Important for sleep + post-activity analysis.                             |

---

## 🧮 Data Estimations

### 1. Theoretical Maximum (All 4 metrics @ 1-second resolution)
This section is theoretical – only **heart rate** has 1-second granularity in real Fitbit data.

#### a. How many data points?
- 4 metrics × 86,400 seconds/day = **345,600 data points per day per user**
- Per year (365 days):  
  - **n = 1**: 126.14 million  
  - **n = 1,000**: 126.14 billion  
  - **n = 10,000**: 1.26 trillion  

#### b. Over time (n=1)
- 1 year: 126.14M
- 2 years: 252.29M
- 5 years: 630.72M

---

### 2. Storage Calculation

#### a. Uncompressed Storage

Assume **25 bytes per data point** (8 bytes timestamp, 8 bytes float, 4 bytes user ID, 5 bytes overhead/indexing).

Scenario:  
- 1,000 users  
- 3 metrics  
- 2 years  
- 1-second resolution

**3 × 86,400 × 365 × 2 × 1,000 = 189 billion data points**  
→ 189B × 25 = **4.72 TB**

#### b. Compressed Storage (80% reduction)
- 4.72 TB × 0.2 = **944 GB**

#### c. Why is this compressible?

Time-series data often has:
- Repeating timestamps and values (e.g., sleep periods)
- Small differences between consecutive values (good for delta encoding)
- Consistent schemas

**Fitbit data is ideal for compression**, especially at rest or during sleep.

---

### 3. Realistic Study Scenario with 6 Metrics

#### a. Metrics and Frequency

| Metric               | Resolution | Est. Points/Day |
|----------------------|------------|-----------------|
| Heart Rate           | 1s         | 86,400          |
| Steps                | 1min       | 1,440           |
| Active Zone Minutes  | 5min       | ~288            |
| Sleep Stages         | 1min       | ~480            |
| SpO₂ (night)         | 1min       | ~480            |
| HRV                  | 5min       | ~288            |

→ Total/day ≈ 89,376 points/user  
→ Yearly/user: ~32.6 million  
→ For 1,000 users: **~32.6 billion**

#### b. Storage

- Uncompressed: 32.6B × 25 = **812.5 GB**
- Compressed (80%): **162.5 GB**

---

### 4. Query Optimization

Querying raw 1-second data is expensive. We can:

- **Downsample** during ingestion:
  - Create pre-aggregated tables: `raw_data`, `data_1min`, `data_1hr`, `data_1day`
- **Choose the right resolution** based on the query:
  - e.g. For a 6-month chart → use 1-hour data instead of raw
- **Cache common queries** and date ranges
- **Use indexes** on timestamps and user_id

📌 These methods reduce query cost at the expense of extra storage.

---

### 5. Scaling Limits

#### a. Vertical Scaling (single machine)

| Component | Limit       |
|-----------|-------------|
| CPU       | 16–32 cores |
| RAM       | 128–256 GB  |
| SSD       | 5–10 TB     |

A powerful server can handle the dataset up to n ≈ 1,000 easily — beyond that, we’ll need to scale horizontally.

#### b. Horizontal Scaling (no cloud)

- **Shard by user ID** or **time range**
- Use a **coordinator node** to handle query routing
- Sync data across local machines via **replication**
- Use **Docker Swarm** or similar to manage multiple services locally

This makes querying faster and keeps ingestion scalable across trials.

---

## ✅ Summary

We selected 6 important metrics based on sleep and activity relevance and realistic API support. Using these, a clinical trial with 1,000 users for 1 year would generate:
- ~32.6 billion data points  
- ~812 GB uncompressed  
- ~162 GB compressed

This analysis will guide our ingestion and visualization system design in Tasks 1 and beyond.

---
