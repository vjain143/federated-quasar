# Grafana - prometheus key metrics with trino
When monitoring Trino (formerly known as Presto) with Prometheus, it's important to collect relevant metrics to gain insights into the performance and health of your Trino cluster. Here are some key metrics to consider:

1. **Query Execution Metrics**:

   - `presto_query_stats`: Metrics related to query execution, including execution time, memory usage, and CPU time.
   - `presto_query_info`: Additional information about queries, such as query ID, state, and user.

2. **Worker Node Metrics**:

   - `presto_worker_memory`: Memory usage metrics for worker nodes.
   - `presto_worker_cpu`: CPU usage metrics for worker nodes.

3. **Coordinator Node Metrics**:

   - `presto_coordinator_memory`: Memory usage metrics for coordinator nodes.
   - `presto_coordinator_cpu`: CPU usage metrics for coordinator nodes.

4. **Cluster-wide Metrics**:

   - `presto_cluster_memory`: Total memory usage across the cluster.
   - `presto_cluster_cpu`: Total CPU usage across the cluster.

5. **Query Queuing and Execution Time Metrics**:

   - `presto_query_queued_time`: Time taken for queries to be queued before execution.
   - `presto_query_execution_time`: Total execution time of queries.

6. **Resource Utilization Metrics**:

   - `presto_resource_group_cpu`: CPU usage per resource group.
   - `presto_resource_group_memory`: Memory usage per resource group.

7. **Query Failure Metrics**:

   - `presto_query_failures`: Count of failed queries.
   - `presto_query_error_rate`: Rate of query failures.

8. **Worker Node Health Metrics**:

   - `presto_worker_health`: Metrics related to worker node health, such as connectivity and resource availability.

9. **JVM Metrics** (if applicable):

   - `jvm_memory_used`: JVM memory usage.
   - `jvm_gc_collection_seconds`: Garbage collection metrics.

10. **Network Metrics**:

    - `presto_network_received_bytes`: Bytes received on the network.
    - `presto_network_sent_bytes`: Bytes sent on the network.

11. **Disk Metrics** (if applicable):

    - `presto_disk_read_bytes`: Bytes read from disk.
    - `presto_disk_write_bytes`: Bytes written to disk.

Remember to configure Prometheus to scrape these metrics from your Trino cluster. You may need to set up a suitable exporter or instrument Trino to expose these metrics in a format that Prometheus understands.

Additionally, adjust the metric selection based on your specific monitoring goals and the aspects of Trino performance you're most interested in. Always refer to the Trino and Prometheus documentation for detailed information on metric names and configurations.
