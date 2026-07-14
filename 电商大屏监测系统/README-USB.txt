═══════════════════════════════════════════════
  实时电商数据大屏监测系统
  Real-time E-commerce Dashboard
═══════════════════════════════════════════════

【如何使用】

  方式一（推荐）：电脑已安装 Node.js
    → 双击 "start.bat"

  方式二：电脑已安装 Node.js + Java + Python
    → 双击 "start.bat" 自动启用完整数据管道

  方式三：电脑没有安装任何环境
    → 将 Node.js / Java / Python 放入 runtime\ 目录
    → 双击 "start.bat"

【启动后访问】

  大屏地址: http://localhost:5173
  后端地址: http://localhost:3001/health

【停止所有服务】

  双击 "start.bat --stop"
  或在命令行执行: start.bat --stop

【项目结构】

  start.bat            ← 统一起停脚本（支持 --stop 参数）
  runtime/            ← 便携运行环境（可选）
    node/             ← Node.js 便携版
    python/           ← Python 嵌入式版
    java/             ← JDK 便携版
  redis/              ← Redis Windows 版（已自带）
  backend/            ← Express + Socket.IO 后端
  frontend/           ← React + Vite + ECharts 前端大屏
  data-generator/     ← Python 模拟数据生成器
  flink-job/          ← Flink 流计算作业
  kafka_2.13-3.9.2/   ← Kafka（KRaft 模式，已自带）

【服务端口】

  :5173  前端大屏 (React + Vite)
  :3001  后端 API (Express + Socket.IO)
  :6379  Redis 缓存
  :9092  Kafka Broker

【数据管道架构】

  Generator → Kafka → Flink → Redis → Backend → WebSocket → Frontend
    200订单/s   4分区   4窗口   4 keys    :3001     实时推送    :5173
    1000PV/s           1s+1min                     1 tick/s    ECharts

【常见问题】

  Q: 端口被占用怎么办？
  A: 先执行 start.bat --stop 清理，再重新启动

  Q: 前端显示"正在加载实时数据..."？
  A: 等待几秒，Flink 需要时间连接 Kafka 并开始向 Redis 写入数据

  Q: 大屏显示 Mock 数据而非实时数据？
  A: 确保 Kafka + Flink + 数据生成器 正常运行（需要 Java + Python）
