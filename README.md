# 双十一实时电商数据大屏监测系统

高并发实时数据处理与可视化大屏系统，模拟双十一电商场景下的秒级数据流转和实时看板展示。

## 技术栈

`Kafka` `Flink (Java)` `Redis` `Node.js/Express` `Socket.IO` `React/Vite` `ECharts` `Docker` `Python`

## 全链路架构

```
Python 数据生成器 → Kafka → Flink 流计算 → Redis → Node.js 后端 → WebSocket → React 前端
        ↓               ↓           ↓            ↓            ↓              ↓
   订单+浏览事件    消息队列    窗口聚合     实时缓存      数据推送       大屏展示
```

## 核心特性

### 数据模拟器（Python）
- 双通道并发：订单 200条/s + 页面浏览 1000条/s
- 突发流量模式：5% 概率触发 3-8 倍瞬时激增，模拟秒杀场景

### 流计算引擎（Flink / Java）
- Tumbling Window 秒级+分钟级双粒度聚合（销售额/订单量/PV/UV）
- HashSet UV 精确去重（非 HyperLogLog 近似）
- AggregateFunction + ProcessWindowFunction 分离，增量聚合降低内存
- 5s Checkpoint 容错机制

### Redis Sink
- Jedis 连接池管理（maxTotal=8）
- TTL 差异化策略（秒级 10s / 分钟级 120s）
- 3 次重试机制

### 后端（Node.js / Express）
- Socket.IO 实时推送，自动重连
- Redis 优先 + Mock 降级双模式自动切换
- setTimeout 链式调度防重叠
- 优雅关闭（SIGINT/SIGTERM）

### 前端（React / Vite）
- 深色大屏风格，四组实时指标卡片
- ECharts 双轴趋势图 + 热销商品 TOP 10 排行榜
- 连接状态实时指示，加载/错误/空数据三态覆盖

### 运维部署
- Docker Compose 一键编排（Kafka + Redis）
- 健康检查 + 自动创建 Topic

## 项目结构

```
电商大屏监测系统/
├── data-generator/       # Python 数据模拟器
│   └── generator.py      # Kafka Producer（订单/PV 双通道）
├── flink-job/            # Flink 流计算任务（Java）
│   └── src/main/java/.../OrderStatsJob.java
├── backend/              # Node.js 后端
│   └── server.js         # Express + Socket.IO + Redis
├── frontend/             # React 前端
│   └── src/App.jsx       # ECharts 大屏组件
└── docker-compose.yml    # Kafka + Redis 容器编排
```

## 快速开始

```bash
# 1. 启动基础设施
docker-compose up -d

# 2. 启动 Flink 任务（需 Maven + JDK 11）
cd flink-job && mvn package && flink run target/*.jar

# 3. 启动数据生成器
cd data-generator && pip install -r requirements.txt && python generator.py

# 4. 启动后端
cd backend && npm install && node server.js

# 5. 启动前端
cd frontend && npm install && npm run dev
```

## 开发说明

全程采用 Vibe Coding 模式开发，Claude Code 辅助完成 Flink 窗口逻辑、Redis 容错、React 组件优化。

---

🤖 部分代码由 Claude Code 辅助生成
