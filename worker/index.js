const Queue = require("bull");
const Redis = require("ioredis");
const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");

// 🔧 Redis connection (IMPORTANT: separate connections)
const redisConfig = {
  host: process.env.REDIS_HOST || "redis",
  port: process.env.REDIS_PORT || 6379,
  maxRetriesPerRequest: null, // 🔥 FIX subscriber error
};

// Create queue
const videoQueue = new Queue("video-processing", {
  redis: redisConfig,
});

console.log("👷 Worker started...");
console.log("Worker => QUEUE NAME: video-processing");

// ----------------------------------
// 🧠 Wait for Python service
// ----------------------------------
async function waitForPython() {
  for (let i = 0; i < 20; i++) {
    try {
      await axios.get("http://video-python:8000/");
      console.log("✅ Python service is ready");
      return;
    } catch (err) {
      console.log("⏳ Waiting for Python...");
      await new Promise((r) => setTimeout(r, 1000));
    }
  }

  throw new Error("❌ Python service not available");
}

// ----------------------------------
// 🚀 Send video to Python service
// ----------------------------------
async function sendToPython(filePath) {
  const form = new FormData();
  form.append("file", fs.createReadStream(filePath));

  for (let i = 0; i < 5; i++) {
    try {
      console.log(`📡 Sending to Python (attempt ${i + 1})`);

      const response = await axios.post(
        "http://video-python:8000/process",
        form,
        {
          headers: form.getHeaders(),
          maxContentLength: Infinity,
          maxBodyLength: Infinity,
          timeout: 0,
        },
      );

      return response.data;
    } catch (err) {
      console.log("❌ Python not ready / failed, retrying...");
      await new Promise((r) => setTimeout(r, 2000));
    }
  }

  throw new Error("❌ Failed to process video after retries");
}

// ----------------------------------
// 🔥 Main worker logic
// ----------------------------------
(async () => {
  // Wait until Python is ready BEFORE processing jobs
  await waitForPython();

  videoQueue.process(async (job) => {
    console.log(`🔥 Processing job: ${job.id}`);
    console.log("📂 File:", job.data.file);

    try {
      // Optional: progress start
      await job.progress(10);

      const result = await sendToPython(job.data.file, (p) => {
        // 👇 forward progress from Python
        job.progress(p);
      });

      await job.progress(90);

      console.log("✅ Processing complete:", result);

      await job.progress(100);

      return result.output;
    } catch (err) {
      console.error("❌ Failed:", err.message);
      throw err;
    }
  });
})();
