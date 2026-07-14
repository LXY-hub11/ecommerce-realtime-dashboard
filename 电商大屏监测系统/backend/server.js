const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const cors = require("cors");

const PORT = 3001;

const app = express();
app.use(cors());
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

// ─── Redis (optional) ───
let redis = null;
let redisConnected = false;

async function connectRedis() {
  try {
    const { createClient } = require("redis");
    redis = createClient({
      url: "redis://localhost:6379",
      socket: {
        connectTimeout: 3000,
        reconnectStrategy: (retries) => {
          if (retries > 3) {
            console.log("⚠️  Redis not available after 3 retries — using built-in mock data");
            return false; // stop reconnecting
          }
          return Math.min(retries * 200, 1000);
        },
      },
    });
    redis.on("error", (err) => {
        console.error(`❌ Redis connection error: ${err.message}`);
        redisConnected = false;
    });
    await redis.connect();
    redisConnected = true;
    console.log("✅ Redis connected on localhost:6379");
  } catch (err) {
    console.log(`⚠️  Redis not available: ${err.message} — using built-in mock data generator`);
    redisConnected = false;
  }
}

// ─── Rolling trend buffer ───
const trendBuffer = [];
const MAX_TREND = 120;
let pollCount = 0;

// ─── Mock data generator (used when Redis is unavailable) ───
const PRODUCTS = [
  { name: "iPhone 15 Pro Max", category: "electronics", price: 8999 },
  { name: "MacBook Air M3", category: "electronics", price: 10999 },
  { name: "AirPods Pro", category: "electronics", price: 1899 },
  { name: "iPad Air", category: "electronics", price: 4799 },
  { name: "Apple Watch S9", category: "electronics", price: 3199 },
  { name: "Nike Air Max", category: "sports", price: 899 },
  { name: "Adidas Ultraboost", category: "sports", price: 1099 },
  { name: "Lululemon Yoga Pants", category: "sports", price: 599 },
  { name: "North Face Jacket", category: "sports", price: 1599 },
  { name: "YSL Lipstick", category: "beauty", price: 380 },
  { name: "Estee Lauder Serum", category: "beauty", price: 890 },
  { name: "SK-II Facial Essence", category: "beauty", price: 1299 },
  { name: "Dyson Vacuum V15", category: "home", price: 4999 },
  { name: "IKEA Standing Desk", category: "home", price: 2499 },
  { name: "Philips Air Purifier", category: "home", price: 1999 },
  { name: "Nintendo Switch OLED", category: "games", price: 2299 },
  { name: "PS5 Slim", category: "games", price: 3499 },
  { name: "LEGO Star Wars", category: "games", price: 699 },
  { name: "Moutai Feitian 53", category: "liquor", price: 1499 },
  { name: "Tsingtao Beer 24-pack", category: "liquor", price: 89 },
];

// Simple seeded-ish random with variation
function rand(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randFloat(min, max) {
  return Math.random() * (max - min) + min;
}

// Mock accumulators for second and minute windows
let secondAcc = { sales: 0, orders: 0, pv: 0, uv: 0, productMap: {}, users: new Set(), windowStart: Date.now() };
let minuteAcc = { sales: 0, orders: 0, pv: 0, uv: 0, productMap: {}, users: new Set(), windowStart: Date.now() };
let lastSecondTick = Date.now();
let lastMinuteTick = Date.now();

function resetSecondAcc() {
  secondAcc = { sales: 0, orders: 0, pv: 0, uv: 0, productMap: {}, users: new Set(), windowStart: Date.now() };
}

function resetMinuteAcc() {
  minuteAcc = { sales: 0, orders: 0, pv: 0, uv: 0, productMap: {}, users: new Set(), windowStart: Date.now() };
  lastMinuteTick = Date.now();
}

function getHotProducts(productMap) {
  return Object.entries(productMap)
    .map(([name, stats]) => ({ productName: name, count: stats.count, sales: Math.round(stats.sales * 100) / 100 }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);
}

function generateMockTick() {
  const now = Date.now();

  // Check if we need to roll the second window
  if (now - lastSecondTick >= 1000) {
    // Push to trend before resetting
    const secondData = {
      sales: Math.round(secondAcc.sales * 100) / 100,
      orders: secondAcc.orders,
      pv: secondAcc.pv,
      uv: secondAcc.users.size,
      hotProducts: getHotProducts(secondAcc.productMap),
      windowStart: secondAcc.windowStart,
    };

    if (secondData.sales > 0 || secondData.pv > 0) {
      trendBuffer.push({ ...secondData, timestamp: now });
      if (trendBuffer.length > MAX_TREND) trendBuffer.shift();
    }

    resetSecondAcc();
    lastSecondTick = now;
  }

  // Check if we need to roll the minute window
  if (now - lastMinuteTick >= 60000) {
    resetMinuteAcc();
  }

  // Generate random orders (typically 5-30 per tick in burst mode)
  const burstMultiplier = Math.random() < 0.05 ? randFloat(3, 8) : 1;
  const orderCount = Math.floor(rand(3, 25) * burstMultiplier);
  for (let i = 0; i < orderCount; i++) {
    const product = PRODUCTS[rand(0, PRODUCTS.length - 1)];
    const quantity = [1,1,1,1,1,2,2,2,3,5][rand(0, 9)]; // weighted
    const saleAmount = product.price * quantity;

    secondAcc.sales += saleAmount;
    secondAcc.orders += 1;
    minuteAcc.sales += saleAmount;
    minuteAcc.orders += 1;

    // Track per-product
    for (const acc of [secondAcc, minuteAcc]) {
      if (!acc.productMap[product.name]) {
        acc.productMap[product.name] = { count: 0, sales: 0 };
      }
      acc.productMap[product.name].count += 1;
      acc.productMap[product.name].sales += saleAmount;
    }
  }

  // Generate random pageviews (typically 10-80 per tick)
  const pvCount = Math.floor(rand(6, 60) * burstMultiplier);
  for (let i = 0; i < pvCount; i++) {
    const userId = `user_${rand(1, 500000)}`;
    secondAcc.pv += 1;
    secondAcc.users.add(userId);
    minuteAcc.pv += 1;
    minuteAcc.users.add(userId);
  }
}

function buildMockPayload() {
  const now = Date.now();
  return {
    second: {
      sales: Math.round(secondAcc.sales * 100) / 100,
      orders: secondAcc.orders,
      pv: secondAcc.pv,
      uv: secondAcc.users.size,
      hotProducts: getHotProducts(secondAcc.productMap),
      windowStart: secondAcc.windowStart,
    },
    minute: {
      sales: Math.round(minuteAcc.sales * 100) / 100,
      orders: minuteAcc.orders,
      pv: minuteAcc.pv,
      uv: minuteAcc.users.size,
      hotProducts: getHotProducts(minuteAcc.productMap),
      windowStart: minuteAcc.windowStart,
    },
    trend: trendBuffer,
    timestamp: now,
  };
}

// ─── Redis polling ───
const REDIS_KEYS = [
  "stats:orders:second",
  "stats:orders:minute",
  "stats:pv:second",
  "stats:pv:minute",
];

// Whether the last Redis poll found actual data (used for fallback logic)
let redisHasData = false;

// ─── Unified data loop (Redis priority, mock fallback) ───
// Uses setTimeout chaining (NOT setInterval) to prevent overlapping ticks
// when Redis is slow. The tickRunning guard ensures only one tick at a time.
let tickRunning = false;
let tickTimer = null;
let redisPollCount = 0;

async function unifiedDataTick() {
  // Guard: prevent overlapping execution if previous tick is still in flight
  if (tickRunning) {
    console.log("⚠️  Skipping tick — previous tick still running (Redis may be slow)");
    tickTimer = setTimeout(unifiedDataTick, 1000);
    return;
  }
  tickRunning = true;

  try {
    // Try Redis first
    if (redisConnected) {
      try {
        const data = {};
        let rawFound = false;
        for (const key of REDIS_KEYS) {
          const raw = await redis.get(key);
          if (raw) {
            data[key] = JSON.parse(raw);
            rawFound = true;
          }
        }

        if (rawFound) {
          const second = {
            sales: data["stats:orders:second"]?.totalSales || 0,
            orders: data["stats:orders:second"]?.orderCount || 0,
            pv: data["stats:pv:second"]?.pv || 0,
            uv: data["stats:pv:second"]?.uv || 0,
            hotProducts: data["stats:orders:second"]?.hotProducts || [],
            windowStart: data["stats:orders:second"]?.windowStart || Date.now(),
          };

          const minute = {
            sales: data["stats:orders:minute"]?.totalSales || 0,
            orders: data["stats:orders:minute"]?.orderCount || 0,
            pv: data["stats:pv:minute"]?.pv || 0,
            uv: data["stats:pv:minute"]?.uv || 0,
            hotProducts: data["stats:orders:minute"]?.hotProducts || [],
            windowStart: data["stats:orders:minute"]?.windowStart || Date.now(),
          };

          if (second.sales > 0 || second.pv > 0 || second.orders > 0) {
            redisHasData = true;

            // Dedup: skip if same timestamp as last entry (avoids duplicate trend points)
            const lastTrend = trendBuffer.length > 0 ? trendBuffer[trendBuffer.length - 1] : null;
            if (!lastTrend || Math.abs(lastTrend.timestamp - Date.now()) > 500) {
              trendBuffer.push({ ...second, timestamp: Date.now() });
              if (trendBuffer.length > MAX_TREND) trendBuffer.shift();
            }

            io.emit("stats", { second, minute, trend: trendBuffer, timestamp: Date.now() });

            redisPollCount++;
            pollCount++;
            if (pollCount % 10 === 0) {
              console.log(`[Redis poll #${redisPollCount}] second: sales=${second.sales}, orders=${second.orders}, pv=${second.pv}, uv=${second.uv} | trend: ${trendBuffer.length} pts | clients: ${io.engine.clientsCount}`);
            }
            return; // Redis data sent — skip mock
          }
        }
      } catch (e) {
        console.error(`❌ Redis read error: ${e.message}`);
        redisConnected = false; // mark disconnected so we stop trying
        // fall through to mock
      }
    }

    // Fallback: generate mock data
    generateMockTick();
    const payload = buildMockPayload();
    io.emit("stats", payload);

    pollCount++;
    if (pollCount % 10 === 0) {
      console.log(`[Mock  poll #${pollCount}] second: sales=${payload.second.sales}, orders=${payload.second.orders}, pv=${payload.second.pv}, uv=${payload.second.uv} | trend: ${trendBuffer.length} pts | clients: ${io.engine.clientsCount}`);
    }
  } finally {
    tickRunning = false;
  }

  // Schedule next tick using setTimeout (chain, not interval)
  tickTimer = setTimeout(unifiedDataTick, 1000);
}

function startUnifiedLoop() {
  console.log("🎲 Starting data loop (Redis priority, mock fallback)...");
  // Reset accumulators
  resetSecondAcc();
  resetMinuteAcc();
  trendBuffer.length = 0;
  tickRunning = false;

  // Kick off first tick immediately, subsequent ticks via setTimeout chain
  tickTimer = setTimeout(unifiedDataTick, 100);
  console.log("✅ Data loop running (1 tick/sec, setTimeout chain)");
}

// ─── HTTP ───
app.get("/", (_req, res) => res.json({
  service: "E-commerce Dashboard Backend",
  version: "1.0",
  mode: redisConnected ? "redis" : "mock",
  endpoints: {
    health: "/health",
    debug: "/debug",
    socketio: "ws://localhost:3001 (Socket.IO)"
  }
}));

app.get("/health", (_req, res) => res.json({ status: "ok", mode: redisConnected ? "redis" : "mock" }));

app.get("/debug", (_req, res) => {
  res.json({
    mode: redisConnected ? "redis" : "mock",
    trendLength: trendBuffer.length,
    lastTrend: trendBuffer.length > 0 ? trendBuffer[trendBuffer.length - 1] : null,
    redisConnected,
    clients: io.engine.clientsCount,
    pollCount,
  });
});

// ─── Global error handlers ───
process.on("uncaughtException", (err) => {
  console.error("❌ UNCAUGHT EXCEPTION:", err);
  if (err.code === "EADDRINUSE") {
    console.error("Port already in use — exiting");
    process.exit(1);
  }
});

process.on("unhandledRejection", (reason) => {
  console.error("❌ UNHANDLED REJECTION:", reason);
});

// ─── Socket.IO ───
io.on("connection", (socket) => {
  console.log(`🔌 Client connected: ${socket.id} (total: ${io.engine.clientsCount})`);
  socket.on("disconnect", () => {
    console.log(`🔌 Client disconnected: ${socket.id} (total: ${io.engine.clientsCount})`);
  });
  socket.on("error", (err) => {
    console.error(`⚠️  Socket error (${socket.id}): ${err.message}`);
  });
});

// ─── Startup ───
server.listen(PORT, () => {
  console.log(`\n╔══════════════════════════════════════════════╗`);
  console.log(`║  🚀 Backend running on http://localhost:${PORT}  ║`);
  console.log(`║  📡 Socket.IO ready                         ║`);
  console.log(`╚══════════════════════════════════════════════╝\n`);

  // Start unified data loop immediately (mock data, auto-switches to Redis when available)
  startUnifiedLoop();

  // Try Redis in the background — if it connects, data loop will auto-switch to Redis source
  console.log("🔄 Checking for Redis in background...");
  connectRedis().then(() => {
    if (redisConnected) {
      console.log("✅ Redis connected — data loop will switch to Redis source when pipeline data is available");
    }
  });
});

// ─── Graceful shutdown ───
async function gracefulShutdown(signal) {
  console.log(`\n🛑 Received ${signal} — shutting down gracefully...`);

  // Stop the data loop
  if (tickTimer) {
    clearTimeout(tickTimer);
    tickTimer = null;
    console.log("✅ Data loop stopped");
  }

  // Close Redis connection
  if (redis && redisConnected) {
    try {
      await redis.quit();
      console.log("✅ Redis connection closed");
    } catch (e) {
      redis.disconnect();
    }
  }

  // Close HTTP server
  server.close(() => {
    console.log("✅ HTTP server closed");
    process.exit(0);
  });

  // Force exit after 5 seconds if graceful shutdown hangs
  setTimeout(() => {
    console.error("❌ Forced exit after 5s timeout");
    process.exit(1);
  }, 5000);
}

process.on("SIGINT", () => gracefulShutdown("SIGINT"));
process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
