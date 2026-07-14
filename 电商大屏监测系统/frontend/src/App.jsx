import React, { useEffect, useRef, useState, useCallback } from "react";
import * as echarts from "echarts";
import { io } from "socket.io-client";

const CHART_COLORS = ["#00d4ff", "#00ff88", "#ff6b6b", "#ffd93d", "#c084fc", "#fb923c"];

function formatMoney(v) {
  if (v >= 1e8) return (v / 1e8).toFixed(2) + " 亿";
  if (v >= 1e4) return (v / 1e4).toFixed(2) + " 万";
  return v.toFixed(0);
}

function formatNum(v) {
  if (v >= 1e8) return (v / 1e8).toFixed(1) + "亿";
  if (v >= 1e4) return (v / 1e4).toFixed(1) + "万";
  return v.toLocaleString();
}

function StatCard({ label, value, unit, color }) {
  return (
    <div style={{
      background: "linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%)",
      border: `1px solid ${color}33`,
      borderRadius: 12,
      padding: "20px 24px",
      display: "flex",
      flexDirection: "column",
      gap: 8,
      position: "relative",
      overflow: "hidden",
    }}>
      <div style={{
        position: "absolute", top: -20, right: -20,
        width: 80, height: 80, borderRadius: "50%",
        background: `${color}15`,
      }} />
      <div style={{ fontSize: 14, color: "#8892b0" }}>{label}</div>
      <div style={{ fontSize: 32, fontWeight: 700, color, fontFamily: "DIN, monospace" }}>
        {value}
        {unit && <span style={{ fontSize: 14, marginLeft: 4, color: "#8892b0" }}>{unit}</span>}
      </div>
    </div>
  );
}

const TrendChart = React.memo(function TrendChart({ data }) {
  const domRef = useRef(null);
  const chartRef = useRef(null);

  // init chart once
  useEffect(() => {
    if (!domRef.current) return;
    const chart = echarts.init(domRef.current, null, { renderer: "canvas" });
    chartRef.current = chart;
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  // update data
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    if (!data || data.length === 0) {
      chart.clear();
      return;
    }

    const times = data.map((d) => {
      const t = new Date(d.timestamp || d.windowStart);
      return `${String(t.getHours()).padStart(2, "0")}:${String(t.getMinutes()).padStart(2, "0")}:${String(t.getSeconds()).padStart(2, "0")}`;
    });
    const sales = data.map((d) => d.sales || 0);
    const orders = data.map((d) => d.orders || 0);

    chart.setOption({
      tooltip: { trigger: "axis", backgroundColor: "#1a1f3a", borderColor: "#334" },
      legend: { data: ["Sales", "Orders"], textStyle: { color: "#8892b0" }, top: 0 },
      grid: { left: 55, right: 55, top: 35, bottom: 25 },
      xAxis: {
        type: "category", data: times,
        axisLine: { lineStyle: { color: "#334" } },
        axisLabel: { color: "#8892b0", fontSize: 10, rotate: 45 },
      },
      yAxis: [
        {
          type: "value", name: "Sales(Yuan)", nameTextStyle: { color: "#8892b0", fontSize: 10 },
          axisLabel: { color: "#8892b0", formatter: (v) => formatMoney(v), fontSize: 10 },
          splitLine: { lineStyle: { color: "#1a1f3a" } },
        },
        {
          type: "value", name: "Orders", nameTextStyle: { color: "#8892b0", fontSize: 10 },
          axisLabel: { color: "#8892b0", fontSize: 10 },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: "Sales", type: "line", smooth: true, data: sales,
          yAxisIndex: 0,
          lineStyle: { color: CHART_COLORS[0], width: 2 },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(0,212,255,0.4)" },
            { offset: 1, color: "rgba(0,212,255,0.02)" },
          ])},
          itemStyle: { color: CHART_COLORS[0] },
          symbol: "none",
        },
        {
          name: "Orders", type: "bar", data: orders,
          yAxisIndex: 1,
          itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(0,255,136,0.8)" },
            { offset: 1, color: "rgba(0,255,136,0.1)" },
          ]), borderRadius: [4, 4, 0, 0] },
        },
      ],
    }, true);
    chart.resize();
  }, [data]);

  return <div ref={domRef} style={{ width: "100%", height: 280 }} />;
}, (prevProps, nextProps) => {
  if (prevProps.data === nextProps.data) return true;
  if (!prevProps.data && !nextProps.data) return true;
  if (prevProps.data?.length === 0 && nextProps.data?.length === 0) return true;
  return false;
});

const HotProductsChart = React.memo(function HotProductsChart({ products }) {
  const domRef = useRef(null);
  const chartRef = useRef(null);

  // init chart once
  useEffect(() => {
    if (!domRef.current) return;
    const chart = echarts.init(domRef.current, null, { renderer: "canvas" });
    chartRef.current = chart;
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  // update data
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    if (!products || products.length === 0) {
      chart.clear();
      return;
    }

    const names = products.map((p) => p.productName).reverse();
    const counts = products.map((p) => p.count).reverse();

    chart.setOption({
      tooltip: { trigger: "axis", backgroundColor: "#1a1f3a", borderColor: "#334",
        formatter: (params) => {
          const i = params[0]?.dataIndex;
          if (i === undefined) return "";
          const idx = products.length - 1 - i;
          const p = products[idx];
          return `<b>${p.productName}</b><br/>Sold: ${p.count}<br/>Sales: ${formatMoney(p.sales)}`;
        },
      },
      grid: { left: 110, right: 50, top: 10, bottom: 20 },
      xAxis: {
        type: "value", name: "Qty",
        axisLabel: { color: "#8892b0", fontSize: 10 },
        splitLine: { lineStyle: { color: "#1a1f3a" } },
      },
      yAxis: {
        type: "category", data: names,
        axisLabel: { color: "#e0e0e0", fontSize: 11, width: 100, overflow: "truncate" },
        axisLine: { lineStyle: { color: "#334" } },
      },
      series: [{
        type: "bar", data: counts,
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: (p) => CHART_COLORS[p.dataIndex % CHART_COLORS.length],
        },
        label: { show: true, position: "right", color: "#8892b0", fontSize: 11 },
      }],
    }, true);
    chart.resize();
  }, [products]);

  return <div ref={domRef} style={{ width: "100%", height: 280 }} />;
}, (prevProps, nextProps) => {
  if (prevProps.products === nextProps.products) return true;
  if (!prevProps.products && !nextProps.products) return true;
  if (prevProps.products?.length === 0 && nextProps.products?.length === 0) return true;
  return false;
});

export default function App() {
  const [stats, setStats] = useState({
    second: { sales: 0, orders: 0, pv: 0, uv: 0, hotProducts: [] },
    minute: { sales: 0, orders: 0, pv: 0, uv: 0, hotProducts: [] },
    trend: [],
  });
  const [connected, setConnected] = useState(false);
  const [initialLoad, setInitialLoad] = useState(true);
  const [error, setError] = useState(null);
  const [time, setTime] = useState(new Date());

  // Real-time clock
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Socket.IO connection with reconnection
  useEffect(() => {
    const socket = io("http://localhost:3001", {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 10000,
      timeout: 20000,
    });
    socket.on("connect", () => {
      setConnected(true);
      setError(null);
    });
    socket.on("disconnect", () => setConnected(false));
    socket.on("connect_error", (err) => {
      setError(`连接失败: ${err.message}`);
      setConnected(false);
    });
    socket.on("stats", (data) => {
      if (initialLoad) setInitialLoad(false);
      setError(null);
      setStats(data);
    });
    return () => socket.disconnect();
  }, []);

  return (
    <div style={{ minHeight: "100vh", padding: "16px 24px" }}>
      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 16, padding: "0 8px",
      }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, background: "linear-gradient(90deg, #00d4ff, #c084fc)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            双十一实时电商数据大屏
          </h1>
          <div style={{ fontSize: 13, color: "#5a6080", marginTop: 4 }}>
            数据来源: Kafka → Flink → Redis → WebSocket &nbsp;|&nbsp; 窗口统计: 每秒 / 每分钟
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            background: connected ? "rgba(0,255,136,0.12)" : "rgba(255,107,107,0.12)",
            padding: "6px 14px", borderRadius: 20, fontSize: 13,
            color: connected ? "#00ff88" : "#ff6b6b",
          }}>
            <div style={{
              width: 8, height: 8, borderRadius: "50%",
              background: connected ? "#00ff88" : "#ff6b6b",
              boxShadow: `0 0 8px ${connected ? "#00ff88" : "#ff6b6b"}`,
            }} />
            {connected ? "数据实时连接中" : "连接断开"}
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, fontFamily: "DIN, monospace", color: "#e0e0e0" }}>
            {String(time.getHours()).padStart(2, "0")}:
            {String(time.getMinutes()).padStart(2, "0")}:
            {String(time.getSeconds()).padStart(2, "0")}
          </div>
        </div>
      </div>

      {/* Loading overlay */}
      {(initialLoad || error) && (
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "center",
          flexDirection: "column", gap: 16, padding: "60px 0",
        }}>
          {!error && (
            <>
              <div style={{
                width: 48, height: 48, border: "3px solid rgba(255,255,255,0.1)",
                borderTopColor: "#00d4ff", borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
              }} />
              <div style={{ color: "#8892b0", fontSize: 15 }}>
                {connected ? "正在加载实时数据..." : "正在连接后端服务..."}
              </div>
            </>
          )}
          {error && (
            <div style={{
              background: "rgba(255,107,107,0.12)", border: "1px solid rgba(255,107,107,0.3)",
              borderRadius: 12, padding: "20px 32px", color: "#ff6b6b", fontSize: 15, textAlign: "center",
            }}>
              ⚠️ {error}
              <div style={{ marginTop: 8, fontSize: 13, color: "#8892b0" }}>
                正在自动重连...
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stat cards — per-second */}
      <div style={{ marginBottom: 12, fontSize: 13, color: "#5a6080", padding: "0 8px" }}>
        每秒实时指标 (1s Tumbling Window)
      </div>
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 20,
      }}>
        <StatCard label="💰 销售额/秒" value={`¥${formatMoney(stats.second.sales)}`} color="#00d4ff" />
        <StatCard label="📦 订单量/秒" value={formatNum(stats.second.orders)} unit="单" color="#00ff88" />
        <StatCard label="👁 PV/秒" value={formatNum(stats.second.pv)} unit="次" color="#ffd93d" />
        <StatCard label="👤 UV/秒" value={formatNum(stats.second.uv)} unit="人" color="#c084fc" />
      </div>

      {/* Stat cards — per-minute */}
      <div style={{ marginBottom: 12, fontSize: 13, color: "#5a6080", padding: "0 8px" }}>
        每分钟累计指标 (1min Tumbling Window)
      </div>
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 20,
      }}>
        <StatCard label="💰 累计销售额/分钟" value={`¥${formatMoney(stats.minute.sales)}`} color="#fb923c" />
        <StatCard label="📦 累计订单/分钟" value={formatNum(stats.minute.orders)} unit="单" color="#f472b6" />
        <StatCard label="👁 累计PV/分钟" value={formatNum(stats.minute.pv)} unit="次" color="#38bdf8" />
        <StatCard label="👤 累计UV/分钟" value={formatNum(stats.minute.uv)} unit="人" color="#a78bfa" />
      </div>

      {/* Charts row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Sales trend */}
        <div style={{
          background: "rgba(255,255,255,0.03)", borderRadius: 12,
          border: "1px solid rgba(255,255,255,0.06)", padding: 16, height: 350,
        }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: "#e0e0e0", marginBottom: 8 }}>
            销售趋势 (近2分钟)
          </div>
          <TrendChart data={stats.trend} />
        </div>

        {/* Hot products */}
        <div style={{
          background: "rgba(255,255,255,0.03)", borderRadius: 12,
          border: "1px solid rgba(255,255,255,0.06)", padding: 16, height: 350,
        }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: "#e0e0e0", marginBottom: 8 }}>
            热销商品 TOP 10 (每分钟)
          </div>
          <HotProductsChart
            products={stats.minute.hotProducts?.length > 0 ? stats.minute.hotProducts : stats.second.hotProducts}
          />
        </div>
      </div>
    </div>
  );
}
