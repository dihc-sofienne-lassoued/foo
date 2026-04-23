const Queue = require("bull");

const videoQueue = new Queue("video-processing", {
  redis: {
    host: process.env.REDIS_HOST || "redis",
    port: process.env.REDIS_PORT || 6379,

    // 🔥 FIXES all your issues
    maxRetriesPerRequest: null,
    enableReadyCheck: false,
  },
});

videoQueue.on("error", (err) => {
  console.error("❌ Queue error:", err);
});

module.exports = videoQueue;