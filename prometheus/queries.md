# TodoSphere Monitoring Queries

This document contains pre-built Prometheus queries to monitor system load and application metrics.

## 1. System Resource Monitoring (CPU, RAM, Network)

### Container CPU Usage (in % of a CPU core)
* **Query:**
  ```promql
  sum by (name) (rate(container_cpu_usage_seconds_total{name=~"todosphere.+"}[1m])) * 100
  ```
* **Description:** Displays CPU usage percentage for each TodoSphere container.

### Container RAM (Memory) Usage (in MB)
* **Query:**
  ```promql
  sum by (name) (container_memory_working_set_bytes{name=~"todosphere.+"}) / 1024 / 1024
  ```
* **Description:** Displays the active memory usage of each container.

### Container Network Download (in KB/s)
* **Query:**
  ```promql
  sum by (name) (rate(container_network_receive_bytes_total{name=~"todosphere.+"}[1m])) / 1024
  ```
* **Description:** Shows incoming network traffic.

### Container Network Upload (in KB/s)
* **Query:**
  ```promql
  sum by (name) (rate(container_network_transmit_bytes_total{name=~"todosphere.+"}[1m])) / 1024
  ```
* **Description:** Shows outgoing network traffic.

---

## 2. FastAPI Application Metrics

### Total Requests Per Second (RPS)
* **Query:**
  ```promql
  sum(rate(http_requests_total[1m]))
  ```
* **Description:** Shows the overall request throughput of the backend server.

### Requests Per Second by Route (RPS Breakdown)
* **Query:**
  ```promql
  sum by (handler, method) (rate(http_requests_total[1m]))
  ```
* **Description:** Shows RPS split by HTTP method and endpoint path.

### Average Response Latency (in Milliseconds)
* **Query:**
  ```promql
  (sum by (handler) (rate(http_request_duration_seconds_sum[1m])) / sum by (handler) (rate(http_request_duration_seconds_count[1m]))) * 1000
  ```
* **Description:** Average response times for all API endpoints.

### Tail Latency - 95th Percentile Response Time (in Milliseconds)
* **Query:**
  ```promql
  histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler)) * 1000
  ```
* **Description:** Tail latencies (p95 response times).

### Server Error Rate (HTTP 500s)
* **Query:**
  ```promql
  sum(rate(http_requests_total{status=~"5.."}[1m]))
  ```
* **Description:** Rate of server-side internal errors.
