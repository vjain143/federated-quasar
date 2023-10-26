# WARN java.lang.reflect.InvocationTargetException: null
INFO [2023-10-22 06:51:21,899] [main] o.o.s.c.p.PipelineServiceClientFactory - Registering PipelineServiceClient: org.openmetadata.service.clients.pipeline.noop.NoopClient"
WARN [2023-10-22 06:51:21,926] [main] o.o.s.r.CollectionRegistry - Encountered exception
java.lang.reflect.InvocationTargetException: null
at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
at java.base/java.lang.reflect.Method.invoke(Method.java:568)
at org.openmetadata.service.resources.CollectionRegistry.createResource(CollectionRegistry.java:260)
at org.openmetadata.service.resources.CollectionRegistry.registerResources(CollectionRegistry.java:172)
at org.openmetadata.service.OpenMetadataApplication.registerResources(OpenMetadataApplication.java:436)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:189)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:123)
at io.dropwizard.cli.EnvironmentCommand.run(EnvironmentCommand.java:67)
at io.dropwizard.cli.ConfiguredCommand.run(ConfiguredCommand.java:98)
at io.dropwizard.cli.Cli.run(Cli.java:78)
at io.dropwizard.Application.run(Application.java:94)
at org.openmetadata.service.OpenMetadataApplication.main(OpenMetadataApplication.java:480)
Caused by: org.openmetadata.sdk.exception.PipelineServiceClientException: Error trying to load PipelineServiceClient org.openmetadata.service.clients.pipeline.noop.NoopClient": org.openmetadata.service.clients.pipeline.noop.NoopClient"
at org.openmetadata.service.clients.pipeline.PipelineServiceClientFactory.createPipelineServiceClient(PipelineServiceClientFactory.java:52)
at org.openmetadata.service.resources.automations.WorkflowResource.initialize(WorkflowResource.java:105)
... 14 common frames omitted

# WARN - java.lang.reflect.InvocationTargetException: null
INFO [2023-10-22 06:51:22,141] [main] o.q.i.StdSchedulerFactory - Quartz scheduler 'DefaultQuartzScheduler' initialized from default resource file in Quartz package: 'quartz.properties'
INFO [2023-10-22 06:51:22,141] [main] o.q.i.StdSchedulerFactory - Quartz scheduler version: 2.3.2
INFO [2023-10-22 06:51:22,141] [main] o.q.c.QuartzScheduler - Scheduler DefaultQuartzScheduler_$_NON_CLUSTERED started.
INFO [2023-10-22 06:51:22,150] [main] o.o.s.r.CollectionRegistry - Registering org.openmetadata.service.resources.events.subscription.EventSubscriptionResource with order 9
INFO [2023-10-22 06:51:22,152] [main] o.o.s.r.CollectionRegistry - Registering org.openmetadata.service.resources.analytics.ReportDataResource with order 9
INFO [2023-10-22 06:51:22,156] [main] o.o.s.Entity - Registering entity class org.openmetadata.schema.entity.data.Container container
INFO [2023-10-22 06:51:22,157] [main] o.o.s.r.CollectionRegistry - Registering org.openmetadata.service.resources.storages.ContainerResource with order 9
INFO [2023-10-22 06:51:22,161] [main] o.o.s.Entity - Registering entity class org.openmetadata.schema.entity.data.Chart chart
INFO [2023-10-22 06:51:22,162] [main] o.o.s.r.CollectionRegistry - Registering org.openmetadata.service.resources.charts.ChartResource with order 9
INFO [2023-10-22 06:51:22,166] [main] o.o.s.Entity - Registering entity class org.openmetadata.schema.entity.services.ingestionPipelines.IngestionPipeline ingestionPipeline
INFO [2023-10-22 06:51:22,167] [main] o.o.s.c.p.PipelineServiceClientFactory - Registering PipelineServiceClient: org.openmetadata.service.clients.pipeline.noop.NoopClient"
WARN [2023-10-22 06:51:22,167] [main] o.o.s.r.CollectionRegistry - Encountered exception
java.lang.reflect.InvocationTargetException: null
at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
at java.base/java.lang.reflect.Method.invoke(Method.java:568)
at org.openmetadata.service.resources.CollectionRegistry.createResource(CollectionRegistry.java:260)
at org.openmetadata.service.resources.CollectionRegistry.registerResources(CollectionRegistry.java:172)
at org.openmetadata.service.OpenMetadataApplication.registerResources(OpenMetadataApplication.java:436)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:189)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:123)
at io.dropwizard.cli.EnvironmentCommand.run(EnvironmentCommand.java:67)
at io.dropwizard.cli.ConfiguredCommand.run(ConfiguredCommand.java:98)
at io.dropwizard.cli.Cli.run(Cli.java:78)
at io.dropwizard.Application.run(Application.java:94)
at org.openmetadata.service.OpenMetadataApplication.main(OpenMetadataApplication.java:480)
Caused by: org.openmetadata.sdk.exception.PipelineServiceClientException: Error trying to load PipelineServiceClient org.openmetadata.service.clients.pipeline.noop.NoopClient": org.openmetadata.service.clients.pipeline.noop.NoopClient"
at org.openmetadata.service.clients.pipeline.PipelineServiceClientFactory.createPipelineServiceClient(PipelineServiceClientFactory.java:52)
at org.openmetadata.service.resources.services.ingestionpipelines.IngestionPipelineResource.initialize(IngestionPipelineResource.java:130)
... 14 common frames omitted




# java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
INFO [2023-10-22 06:51:22,377] [main] o.o.s.r.CollectionRegistry - Registering org.openmetadata.service.resources.services.connections.TestConnectionDefinitionResource with order 9
INFO [2023-10-22 06:51:22,380] [main] o.o.s.e.EventFilter - Added event handler org.openmetadata.service.events.ChangeEventHandler
INFO [2023-10-22 06:51:22,380] [main] o.o.s.e.EventFilter - Added event handler org.openmetadata.service.events.WebAnalyticEventHandler
INFO [2023-10-22 06:51:22,381] [main] o.o.s.e.EventFilter - Added event handler org.openmetadata.service.events.AuditEventHandler
ERROR [2023-10-22 06:51:22,465] [main] o.o.s.s.e.ElasticSearchClientImpl - Failed to create Elastic Search indexes due to
org.elasticsearch.ElasticsearchException: java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
at org.elasticsearch.client.RestHighLevelClient.performClientRequest(RestHighLevelClient.java:2695)
at org.elasticsearch.client.RestHighLevelClient.internalPerformRequest(RestHighLevelClient.java:2171)
at org.elasticsearch.client.RestHighLevelClient.performRequest(RestHighLevelClient.java:2154)
at org.elasticsearch.client.IndicesClient.exists(IndicesClient.java:1279)
at org.openmetadata.service.search.elasticSearch.ElasticSearchClientImpl.createIndex(ElasticSearchClientImpl.java:198)
at org.openmetadata.service.search.SearchIndexDefinition.createIndexes(SearchIndexDefinition.java:76)
at org.openmetadata.service.search.SearchEventPublisher.<init>(SearchEventPublisher.java:58)
at org.openmetadata.service.OpenMetadataApplication.registerEventPublisher(OpenMetadataApplication.java:417)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:195)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:123)
at io.dropwizard.cli.EnvironmentCommand.run(EnvironmentCommand.java:67)
at io.dropwizard.cli.ConfiguredCommand.run(ConfiguredCommand.java:98)
at io.dropwizard.cli.Cli.run(Cli.java:78)
at io.dropwizard.Application.run(Application.java:94)
at org.openmetadata.service.OpenMetadataApplication.main(OpenMetadataApplication.java:480)
Caused by: java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
at org.elasticsearch.common.util.concurrent.BaseFuture$Sync.getValue(BaseFuture.java:257)
at org.elasticsearch.common.util.concurrent.BaseFuture$Sync.get(BaseFuture.java:244)
at org.elasticsearch.common.util.concurrent.BaseFuture.get(BaseFuture.java:75)
at org.elasticsearch.client.RestHighLevelClient.performClientRequest(RestHighLevelClient.java:2692)
... 14 common frames omitted
Caused by: java.net.ConnectException: Connection refused
at java.base/sun.nio.ch.Net.pollConnect(Native Method)
at java.base/sun.nio.ch.Net.pollConnectNow(Net.java:672)
at java.base/sun.nio.ch.SocketChannelImpl.finishConnect(SocketChannelImpl.java:946)
at org.apache.http.impl.nio.reactor.DefaultConnectingIOReactor.processEvent(DefaultConnectingIOReactor.java:174)
at org.apache.http.impl.nio.reactor.DefaultConnectingIOReactor.processEvents(DefaultConnectingIOReactor.java:148)
at org.apache.http.impl.nio.reactor.AbstractMultiworkerIOReactor.execute(AbstractMultiworkerIOReactor.java:351)
at org.apache.http.impl.nio.conn.PoolingNHttpClientConnectionManager.execute(PoolingNHttpClientConnectionManager.java:221)
at org.apache.http.impl.nio.client.CloseableHttpAsyncClientBase$1.run(CloseableHttpAsyncClientBase.java:64)
at java.base/java.lang.Thread.run(Thread.java:833)
ERROR [2023-10-22 06:51:22,472] [main] o.o.s.s.e.ElasticSearchClientImpl - Failed to create Elastic Search indexes due to
org.elasticsearch.ElasticsearchException: java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
at org.elasticsearch.client.RestHighLevelClient.performClientRequest(RestHighLevelClient.java:2695)
at org.elasticsearch.client.RestHighLevelClient.internalPerformRequest(RestHighLevelClient.java:2171)
at org.elasticsearch.client.RestHighLevelClient.performRequest(RestHighLevelClient.java:2154)
at org.elasticsearch.client.IndicesClient.exists(IndicesClient.java:1279)
at org.openmetadata.service.search.elasticSearch.ElasticSearchClientImpl.createIndex(ElasticSearchClientImpl.java:198)
at org.openmetadata.service.search.SearchIndexDefinition.createIndexes(SearchIndexDefinition.java:76)
at org.openmetadata.service.search.SearchEventPublisher.<init>(SearchEventPublisher.java:58)
at org.openmetadata.service.OpenMetadataApplication.registerEventPublisher(OpenMetadataApplication.java:417)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:195)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:123)
at io.dropwizard.cli.EnvironmentCommand.run(EnvironmentCommand.java:67)
at io.dropwizard.cli.ConfiguredCommand.run(ConfiguredCommand.java:98)
at io.dropwizard.cli.Cli.run(Cli.java:78)
at io.dropwizard.Application.run(Application.java:94)
at org.openmetadata.service.OpenMetadataApplication.main(OpenMetadataApplication.java:480)
Caused by: java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
at org.elasticsearch.common.util.concurrent.BaseFuture$Sync.getValue(BaseFuture.java:257)
at org.elasticsearch.common.util.concurrent.BaseFuture$Sync.get(BaseFuture.java:244)
at org.elasticsearch.common.util.concurrent.BaseFuture.get(BaseFuture.java:75)
at org.elasticsearch.client.RestHighLevelClient.performClientRequest(RestHighLevelClient.java:2692)
... 14 common frames omitted
Caused by: java.net.ConnectException: Connection refused
at java.base/sun.nio.ch.Net.pollConnect(Native Method)
at java.base/sun.nio.ch.Net.pollConnectNow(Net.java:672)
at java.base/sun.nio.ch.SocketChannelImpl.finishConnect(SocketChannelImpl.java:946)
at org.apache.http.impl.nio.reactor.DefaultConnectingIOReactor.processEvent(DefaultConnectingIOReactor.java:174)
at org.apache.http.impl.nio.reactor.DefaultConnectingIOReactor.processEvents(DefaultConnectingIOReactor.java:148)
at org.apache.http.impl.nio.reactor.AbstractMultiworkerIOReactor.execute(AbstractMultiworkerIOReactor.java:351)
at org.apache.http.impl.nio.conn.PoolingNHttpClientConnectionManager.execute(PoolingNHttpClientConnectionManager.java:221)
at org.apache.http.impl.nio.client.CloseableHttpAsyncClientBase$1.run(CloseableHttpAsyncClientBase.java:64)
at java.base/java.lang.Thread.run(Thread.java:833)
ERROR [2023-10-22 06:51:22,478] [main] o.o.s.s.e.ElasticSearchClientImpl - Failed to create Elastic Search indexes due to
org.elasticsearch.ElasticsearchException: java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
at org.elasticsearch.client.RestHighLevelClient.performClientRequest(RestHighLevelClient.java:2695)
at org.elasticsearch.client.RestHighLevelClient.internalPerformRequest(RestHighLevelClient.java:2171)
at org.elasticsearch.client.RestHighLevelClient.performRequest(RestHighLevelClient.java:2154)
at org.elasticsearch.client.IndicesClient.exists(IndicesClient.java:1279)
at org.openmetadata.service.search.elasticSearch.ElasticSearchClientImpl.createIndex(ElasticSearchClientImpl.java:198)
at org.openmetadata.service.search.SearchIndexDefinition.createIndexes(SearchIndexDefinition.java:76)
at org.openmetadata.service.search.SearchEventPublisher.<init>(SearchEventPublisher.java:58)
at org.openmetadata.service.OpenMetadataApplication.registerEventPublisher(OpenMetadataApplication.java:417)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:195)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:123)
at io.dropwizard.cli.EnvironmentCommand.run(EnvironmentCommand.java:67)
at io.dropwizard.cli.ConfiguredCommand.run(ConfiguredCommand.java:98)
at io.dropwizard.cli.Cli.run(Cli.java:78)
at io.dropwizard.Application.run(Application.java:94)
at org.openmetadata.service.OpenMetadataApplication.main(OpenMetadataApplication.java:480)
Caused by: java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
at org.elasticsearch.common.util.concurrent.BaseFuture$Sync.getValue(BaseFuture.java:257)
at org.elasticsearch.common.util.concurrent.BaseFuture$Sync.get(BaseFuture.java:244)
at org.elasticsearch.common.util.concurrent.BaseFuture.get(BaseFuture.java:75)
at org.elasticsearch.client.RestHighLevelClient.performClientRequest(RestHighLevelClient.java:2692)
... 14 common frames omitted
Caused by: java.net.ConnectException: Connection refused
at java.base/sun.nio.ch.Net.pollConnect(Native Method)
at java.base/sun.nio.ch.Net.pollConnectNow(Net.java:672)
at java.base/sun.nio.ch.SocketChannelImpl.finishConnect(SocketChannelImpl.java:946)
at org.apache.http.impl.nio.reactor.DefaultConnectingIOReactor.processEvent(DefaultConnectingIOReactor.java:174)
at org.apache.http.impl.nio.reactor.DefaultConnectingIOReactor.processEvents(DefaultConnectingIOReactor.java:148)
at org.apache.http.impl.nio.reactor.AbstractMultiworkerIOReactor.execute(AbstractMultiworkerIOReactor.java:351)
at org.apache.http.impl.nio.conn.PoolingNHttpClientConnectionManager.execute(PoolingNHttpClientConnectionManager.java:221)
at org.apache.http.impl.nio.client.CloseableHttpAsyncClientBase$1.run(CloseableHttpAsyncClientBase.java:64)
at java.base/java.lang.Thread.run(Thread.java:833)
ERROR [2023-10-22 06:51:22,484] [main] o.o.s.s.e.ElasticSearchClientImpl - Failed to create Elastic Search indexes due to
org.elasticsearch.ElasticsearchException: java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
at org.elasticsearch.client.RestHighLevelClient.performClientRequest(RestHighLevelClient.java:2695)
at org.elasticsearch.client.RestHighLevelClient.internalPerformRequest(RestHighLevelClient.java:2171)
at org.elasticsearch.client.RestHighLevelClient.performRequest(RestHighLevelClient.java:2154)
at org.elasticsearch.client.IndicesClient.exists(IndicesClient.java:1279)
at org.openmetadata.service.search.elasticSearch.ElasticSearchClientImpl.createIndex(ElasticSearchClientImpl.java:198)
at org.openmetadata.service.search.SearchIndexDefinition.createIndexes(SearchIndexDefinition.java:76)
at org.openmetadata.service.search.SearchEventPublisher.<init>(SearchEventPublisher.java:58)
at org.openmetadata.service.OpenMetadataApplication.registerEventPublisher(OpenMetadataApplication.java:417)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:195)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:123)
at io.dropwizard.cli.EnvironmentCommand.run(EnvironmentCommand.java:67)
at io.dropwizard.cli.ConfiguredCommand.run(ConfiguredCommand.java:98)
at io.dropwizard.cli.Cli.run(Cli.java:78)
at io.dropwizard.Application.run(Application.java:94)
at org.openmetadata.service.OpenMetadataApplication.main(OpenMetadataApplication.java:480)
Caused by: java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
at org.elasticsearch.common.util.concurrent.BaseFuture$Sync.getValue(BaseFuture.java:257)
at org.elasticsearch.common.util.concurrent.BaseFuture$Sync.get(BaseFuture.java:244)
at org.elasticsearch.common.util.concurrent.BaseFuture.get(BaseFuture.java:75)
at org.elasticsearch.client.RestHighLevelClient.performClientRequest(RestHighLevelClient.java:2692)
... 14 common frames omitted
Caused by: java.net.ConnectException: Connection refused
at java.base/sun.nio.ch.Net.pollConnect(Native Method)
at java.base/sun.nio.ch.Net.pollConnectNow(Net.java:672)
at java.base/sun.nio.ch.SocketChannelImpl.finishConnect(SocketChannelImpl.java:946)
at org.apache.http.impl.nio.reactor.DefaultConnectingIOReactor.processEvent(DefaultConnectingIOReactor.java:174)
at org.apache.http.impl.nio.reactor.DefaultConnectingIOReactor.processEvents(DefaultConnectingIOReactor.java:148)
at org.apache.http.impl.nio.reactor.AbstractMultiworkerIOReactor.execute(AbstractMultiworkerIOReactor.java:351)
at org.apache.http.impl.nio.conn.PoolingNHttpClientConnectionManager.execute(PoolingNHttpClientConnectionManager.java:221)
at org.apache.http.impl.nio.client.CloseableHttpAsyncClientBase$1.run(CloseableHttpAsyncClientBase.java:64)
at java.base/java.lang.Thread.run(Thread.java:833)
ERROR [2023-10-22 06:51:22,489] [main] o.o.s.s.e.ElasticSearchClientImpl - Failed to create Elastic Search indexes due to
org.elasticsearch.ElasticsearchException: java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
at org.elasticsearch.client.RestHighLevelClient.performClientRequest(RestHighLevelClient.java:2695)
at org.elasticsearch.client.RestHighLevelClient.internalPerformRequest(RestHighLevelClient.java:2171)
at org.elasticsearch.client.RestHighLevelClient.performRequest(RestHighLevelClient.java:2154)
at org.elasticsearch.client.IndicesClient.exists(IndicesClient.java:1279)
at org.openmetadata.service.search.elasticSearch.ElasticSearchClientImpl.createIndex(ElasticSearchClientImpl.java:198)
at org.openmetadata.service.search.SearchIndexDefinition.createIndexes(SearchIndexDefinition.java:76)
at org.openmetadata.service.search.SearchEventPublisher.<init>(SearchEventPublisher.java:58)
at org.openmetadata.service.OpenMetadataApplication.registerEventPublisher(OpenMetadataApplication.java:417)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:195)
at org.openmetadata.service.OpenMetadataApplication.run(OpenMetadataApplication.java:123)
at io.dropwizard.cli.EnvironmentCommand.run(EnvironmentCommand.java:67)
at io.dropwizard.cli.ConfiguredCommand.run(ConfiguredCommand.java:98)
at io.dropwizard.cli.Cli.run(Cli.java:78)
at io.dropwizard.Application.run(Application.java:94)
at org.openmetadata.service.OpenMetadataApplication.main(OpenMetadataApplication.java:480)
Caused by: java.util.concurrent.ExecutionException: java.net.ConnectException: Connection refused
at org.elasticsearch.common.util.concurrent.BaseFuture$Sync.getValue(BaseFuture.java:257)
at org.elasticsearch.common.util.concurrent.BaseFuture$Sync.get(BaseFuture.java:244)
at org.elasticsearch.common.util.concurrent.BaseFuture.get(BaseFuture.java:75)
at org.elasticsearch.client.RestHighLevelClient.performClientRequest(RestHighLevelClient.java:2692)
... 14 common frames omitted
