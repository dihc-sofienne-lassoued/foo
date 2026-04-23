const Queue = require("bull");
const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");

const videoQueue = new Queue("video-processing", {
  redis: {
    host: process.env.REDIS_HOST || "redis",
    port: process.env.REDIS_PORT || 6379,
  },
});

console.log("👷 Worker started...");

videoQueue.process(async (job) => {
  console.log("🔥 Processing job:", job.id);

  const form = new FormData();
  form.append("file", fs.createReadStream(job.data.file));

  try {
    const response = await axios.post(
      "http://video-python:8000/process",
      form,
      {
        headers: form.getHeaders(),
        responseType: "stream",
      },
    );

    return new Promise((resolve, reject) => {
      let result = "";
      let buffer = ""; // ✅ for safe streaming parsing

      response.data.on("data", (chunk) => {
        const text = chunk.toString();
        console.log("TEXT: " + text);
        result += text;
        buffer += text;

        // ✅ extract ALL progress values (not just one)
        const matches = [...buffer.matchAll(/PROGRESS:(\d+)/g)];

        for (const m of matches) {
          const progress = parseInt(m[1], 10);
          console.log("📊 Progress:", progress);
          job.progress(progress);
        }

        // ✅ keep only last part to avoid broken chunks
        buffer = buffer.slice(-50);
      });

      response.data.on("end", () => {
        try {
          // ✅ Extract ONLY the JSON part (ignore PROGRESS lines)
          const jsonMatch = result.match(/\{.*\}/s);

          if (!jsonMatch) {
            throw new Error("No JSON found in response:\n" + result);
          }

          const parsed = JSON.parse(jsonMatch[0]);

          // ✅ ensure final progress
          job.progress(100);

          console.log("✅ Done:", parsed.output);
          resolve(parsed.output);
        } catch (e) {
          console.error("❌ Parse error:\n", result);
          reject(e);
        }
      });

      response.data.on("error", (err) => {
        console.error("❌ Stream error:", err);
        reject(err);
      });
    });
  } catch (err) {
    console.error("❌ Failed:", err.message);
    throw err;
  }
});
