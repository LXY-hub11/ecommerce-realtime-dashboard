package com.example.flink;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.AggregateFunction;
import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.checkpoint.CheckpointConfig;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.functions.sink.RichSinkFunction;
import org.apache.flink.streaming.api.functions.windowing.ProcessAllWindowFunction;
import org.apache.flink.streaming.api.windowing.assigners.TumblingProcessingTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.util.Collector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;

import java.time.Duration;
import java.util.*;

/**
 * Flink streaming job: consumes orders + pageviews from Kafka,
 * computes per-second and per-minute window aggregations with precise UV dedup,
 * writes results to Redis for real-time dashboard consumption.
 *
 * Architecture:
 *   Kafka (order-events, pageview-events) → Flink → Redis → Backend → WebSocket → Frontend
 */
public class OrderStatsJob {

    // ---- Data models (must be public static for Flink serialization) ----

    public static class Order {
        public String orderId, userId, productId, productName, category;
        public double price;
        public int quantity;
        public long timestamp;

        public Order() {}
    }

    public static class PageView {
        public String userId, page;
        public long timestamp;

        public PageView() {}
    }

    public static class ProductRank {
        public String productName;
        public long count;
        public double sales;

        public ProductRank() {}

        public ProductRank(String productName, long count, double sales) {
            this.productName = productName;
            this.count = count;
            this.sales = sales;
        }
    }

    // ---- Accumulators ----

    public static class OrderStatsAccumulator {
        public double totalSales = 0.0;
        public long orderCount = 0;
        public Map<String, long[]> productStats = new HashMap<>();
    }

    public static class PvUvAccumulator {
        public long pv = 0;
        public Set<String> userIds = new HashSet<>();
    }

    // ---- Result types ----

    public static class OrderStatsResult {
        public String type;
        public double totalSales;
        public long orderCount;
        public List<ProductRank> hotProducts;
        public long windowStart;
        public long windowEnd;

        public OrderStatsResult() {}
    }

    public static class PvUvResult {
        public String type;
        public long pv;
        public long uv;
        public long windowStart;
        public long windowEnd;

        public PvUvResult() {}
    }

    // ---- Logger & JSON mapper ----

    private static final Logger LOG = LoggerFactory.getLogger(OrderStatsJob.class);
    private static final ObjectMapper MAPPER = new ObjectMapper();

    // ---- Order window aggregate (incremental, memory-efficient) ----

    public static class OrderAggregator
            implements AggregateFunction<Order, OrderStatsAccumulator, OrderStatsAccumulator> {

        @Override
        public OrderStatsAccumulator createAccumulator() {
            return new OrderStatsAccumulator();
        }

        @Override
        public OrderStatsAccumulator add(Order o, OrderStatsAccumulator acc) {
            acc.totalSales += o.price * o.quantity;
            acc.orderCount++;
            long[] stats = acc.productStats.computeIfAbsent(o.productName, k -> new long[2]);
            stats[0] += 1;
            stats[1] += (long) (o.price * o.quantity * 100); // store as cents to avoid float drift
            return acc;
        }

        @Override
        public OrderStatsAccumulator getResult(OrderStatsAccumulator acc) {
            return acc;
        }

        @Override
        public OrderStatsAccumulator merge(OrderStatsAccumulator a, OrderStatsAccumulator b) {
            a.totalSales += b.totalSales;
            a.orderCount += b.orderCount;
            for (Map.Entry<String, long[]> e : b.productStats.entrySet()) {
                long[] sa = a.productStats.computeIfAbsent(e.getKey(), k -> new long[2]);
                sa[0] += e.getValue()[0];
                sa[1] += e.getValue()[1];
            }
            return a;
        }
    }

    // ---- PageView window aggregate (precise UV dedup via HashSet) ----

    public static class PvUvAggregator
            implements AggregateFunction<PageView, PvUvAccumulator, PvUvAccumulator> {

        @Override
        public PvUvAccumulator createAccumulator() {
            return new PvUvAccumulator();
        }

        @Override
        public PvUvAccumulator add(PageView pv, PvUvAccumulator acc) {
            acc.pv++;
            acc.userIds.add(pv.userId);
            return acc;
        }

        @Override
        public PvUvAccumulator getResult(PvUvAccumulator acc) {
            return acc;
        }

        @Override
        public PvUvAccumulator merge(PvUvAccumulator a, PvUvAccumulator b) {
            a.pv += b.pv;
            a.userIds.addAll(b.userIds);
            return a;
        }
    }

    // ---- Order window processor ----

    public static class OrderWindowProcessor
            extends ProcessAllWindowFunction<OrderStatsAccumulator, OrderStatsResult, TimeWindow> {

        private final String windowType;

        public OrderWindowProcessor(String windowType) {
            this.windowType = windowType;
        }

        @Override
        public void process(Context ctx, Iterable<OrderStatsAccumulator> elements,
                            Collector<OrderStatsResult> out) {
            OrderStatsAccumulator acc = elements.iterator().next();
            OrderStatsResult r = new OrderStatsResult();
            r.type = windowType;
            r.totalSales = Math.round(acc.totalSales * 100.0) / 100.0;
            r.orderCount = acc.orderCount;
            r.windowStart = ctx.window().getStart();
            r.windowEnd = ctx.window().getEnd();

            r.hotProducts = acc.productStats.entrySet().stream()
                    .map(e -> new ProductRank(e.getKey(), e.getValue()[0], e.getValue()[1] / 100.0))
                    .sorted((a, b) -> Long.compare(b.count, a.count))
                    .limit(10)
                    .collect(java.util.stream.Collectors.toList());
            out.collect(r);
        }
    }

    // ---- PageView window processor ----

    public static class PvUvWindowProcessor
            extends ProcessAllWindowFunction<PvUvAccumulator, PvUvResult, TimeWindow> {

        private final String windowType;

        public PvUvWindowProcessor(String windowType) {
            this.windowType = windowType;
        }

        @Override
        public void process(Context ctx, Iterable<PvUvAccumulator> elements,
                            Collector<PvUvResult> out) {
            PvUvAccumulator acc = elements.iterator().next();
            PvUvResult r = new PvUvResult();
            r.type = windowType;
            r.pv = acc.pv;
            r.uv = acc.userIds.size(); // precise dedup
            r.windowStart = ctx.window().getStart();
            r.windowEnd = ctx.window().getEnd();
            out.collect(r);
        }
    }

    // ---- Redis sink (connection pool, TTL, retry) ----

    public static class RedisSink extends RichSinkFunction<String> {
        private static final Logger LOG = LoggerFactory.getLogger(RedisSink.class);
        private static final int MAX_RETRIES = 3;
        private static final long RETRY_DELAY_MS = 100;

        private transient JedisPool pool;

        @Override
        public void open(org.apache.flink.configuration.Configuration parameters) {
            JedisPoolConfig poolConfig = new JedisPoolConfig();
            poolConfig.setMaxTotal(8);
            poolConfig.setMaxIdle(4);
            poolConfig.setMinIdle(2);
            poolConfig.setTestOnBorrow(true);
            poolConfig.setMaxWait(Duration.ofSeconds(2));
            pool = new JedisPool(poolConfig, "localhost", 6379, 3000);
            LOG.info("RedisSink connected — JedisPool (maxTotal=8) on localhost:6379");
        }

        @Override
        public void invoke(String value, Context ctx) {
            String[] parts = value.split(":::", 2);
            if (parts.length != 2) {
                LOG.warn("RedisSink: malformed value, expected 'key:::json' (len={})", value.length());
                return;
            }

            // Per-second keys TTL=10s (overwritten every second anyway)
            // Per-minute keys TTL=120s (overwritten every minute)
            int ttl = parts[0].contains(":second") ? 10 : 120;

            for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
                try (Jedis jedis = pool.getResource()) {
                    jedis.setex(parts[0], ttl, parts[1]);
                    return; // success
                } catch (Exception e) {
                    if (attempt == MAX_RETRIES) {
                        LOG.error("RedisSink: failed after {} attempts for key '{}': {}",
                                MAX_RETRIES, parts[0], e.getMessage());
                    } else {
                        LOG.warn("RedisSink: attempt {}/{} failed for key '{}', retrying...",
                                attempt, MAX_RETRIES, parts[0]);
                        try { Thread.sleep(RETRY_DELAY_MS); } catch (InterruptedException ignored) {}
                    }
                }
            }
        }

        @Override
        public void close() {
            if (pool != null) {
                pool.close();
                LOG.info("RedisSink: JedisPool closed");
            }
        }
    }

    // ---- Main ----

    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // Global parallelism is set to 1 because all windows use windowAll() for global
        // aggregation (total sales, global PV/UV across all products/users). windowAll
        // serializes all events through a single operator instance — using higher
        // parallelism would not improve throughput for this dashboard workload
        // (~1200 events/sec). If per-product or per-category windows were needed,
        // keyBy() + window() would allow parallel execution.
        env.setParallelism(1);

        // Checkpointing for fault tolerance and Kafka offset management
        env.enableCheckpointing(5000);
        CheckpointConfig ckConfig = env.getCheckpointConfig();
        ckConfig.setCheckpointTimeout(60000);
        ckConfig.setMinPauseBetweenCheckpoints(1000);
        ckConfig.setTolerableCheckpointFailureNumber(3);
        ckConfig.setExternalizedCheckpointCleanup(
                CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);

        // -- Kafka sources --
        KafkaSource<String> orderSource = KafkaSource.<String>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("order-events")
                .setGroupId("flink-order-consumer")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();

        KafkaSource<String> pvSource = KafkaSource.<String>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("pageview-events")
                .setGroupId("flink-pv-consumer")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();

        // -- Parse order stream with error handling --
        DataStream<Order> orders = env
                .fromSource(orderSource, WatermarkStrategy.noWatermarks(), "Kafka-Orders-Source")
                .flatMap((FlatMapFunction<String, Order>) (line, out) -> {
                    if (line == null || line.trim().isEmpty()) return;
                    try {
                        out.collect(MAPPER.readValue(line, Order.class));
                    } catch (Exception e) {
                        LOG.warn("Failed to parse order JSON (skipping): {}", e.getMessage());
                    }
                })
                .returns(Order.class)
                .name("Parse-Orders");

        // -- Parse pageview stream with error handling --
        DataStream<PageView> pageviews = env
                .fromSource(pvSource, WatermarkStrategy.noWatermarks(), "Kafka-PageViews-Source")
                .flatMap((FlatMapFunction<String, PageView>) (line, out) -> {
                    if (line == null || line.trim().isEmpty()) return;
                    try {
                        out.collect(MAPPER.readValue(line, PageView.class));
                    } catch (Exception e) {
                        LOG.warn("Failed to parse pageview JSON (skipping): {}", e.getMessage());
                    }
                })
                .returns(PageView.class)
                .name("Parse-PageViews");

        // -- Order statistics: 1-second tumbling window --
        orders
                .windowAll(TumblingProcessingTimeWindows.of(Time.seconds(1)))
                .aggregate(new OrderAggregator(), new OrderWindowProcessor("second"))
                .map(r -> "stats:orders:second:::" + MAPPER.writeValueAsString(r))
                .addSink(new RedisSink())
                .name("Orders-1s-Redis");

        // -- Order statistics: 1-minute tumbling window --
        orders
                .windowAll(TumblingProcessingTimeWindows.of(Time.minutes(1)))
                .aggregate(new OrderAggregator(), new OrderWindowProcessor("minute"))
                .map(r -> "stats:orders:minute:::" + MAPPER.writeValueAsString(r))
                .addSink(new RedisSink())
                .name("Orders-1min-Redis");

        // -- PageView statistics: 1-second window (PV + precise UV dedup) --
        pageviews
                .windowAll(TumblingProcessingTimeWindows.of(Time.seconds(1)))
                .aggregate(new PvUvAggregator(), new PvUvWindowProcessor("second"))
                .map(r -> "stats:pv:second:::" + MAPPER.writeValueAsString(r))
                .addSink(new RedisSink())
                .name("PV-1s-Redis");

        // -- PageView statistics: 1-minute window (PV + precise UV dedup) --
        pageviews
                .windowAll(TumblingProcessingTimeWindows.of(Time.minutes(1)))
                .aggregate(new PvUvAggregator(), new PvUvWindowProcessor("minute"))
                .map(r -> "stats:pv:minute:::" + MAPPER.writeValueAsString(r))
                .addSink(new RedisSink())
                .name("PV-1min-Redis");

        LOG.info("╔══════════════════════════════════════════════════════╗");
        LOG.info("║  Flink E-commerce Real-time Stats Job               ║");
        LOG.info("╠══════════════════════════════════════════════════════╣");
        LOG.info("║  Source:   Kafka localhost:9092                      ║");
        LOG.info("║  Topics:   order-events, pageview-events             ║");
        LOG.info("║  Sink:     Redis localhost:6379                      ║");
        LOG.info("║  Windows:  1-second + 1-minute tumbling (Processing) ║");
        LOG.info("║  UV dedup: HashSet (exact, in-window)                ║");
        LOG.info("╚══════════════════════════════════════════════════════╝");

        env.execute("E-commerce Real-time Stats Job (Kafka → Flink → Redis)");
    }
}
