const express = require("express");
const multer = require("multer");
const cors = require("cors");
const bodyParser = require("body-parser");

const { ApolloServer } = require("@apollo/server");
const { expressMiddleware } = require("@as-integrations/express5");

const typeDefs = require("./schema");
const videoQueue = require("./shared/queue");

const app = express();
const upload = multer({ dest: "uploads/" });
const KSUID = require("ksuid");

/* =========================
   ✅ REST upload endpoint
========================= */
app.post("/upload", upload.single("video"), async (req, res) => {
  try {
    console.log("📥 Upload received");

    if (!req.file) {
      return res.status(400).json({ error: "No file uploaded" });
    }

    const id = (await KSUID.random()).string;

    const job = await videoQueue.add(
      {
        file: req.file.path,
      },
      {
        jobId: id,
      },
    );

    console.log("✅ Job added:", job.id);

    res.json({ jobId: job.id });
  } catch (err) {
    console.error("❌ Upload error:", err);
    res.status(500).json({ error: "Upload failed" });
  }
});

/* =========================
   ✅ Static outputs
========================= */
app.use("/outputs", express.static("outputs"));

/* =========================
   ✅ GraphQL resolvers
========================= */
const resolvers = {
  Query: {
    jobStatus: async (_, { id }) => {
      try {
        // ✅ ALWAYS fetch fresh job from Redis
        const job = await videoQueue.getJob(id);
        if (!job) return null;

        const state = await job.getState();

        // ⚠️ Bull quirk: sometimes progress is stored differently
        let progress = 0;

        try {
          progress = await job.progress();
        } catch {
          progress = job._progress || 0; // fallback (Bull internal)
        }

        console.log("📊 Job", id, "progress:", progress, "state:", state);

        return {
          id,
          status: state,
          progress: progress ?? 0,
          outputUrl: state === "completed" ? job.returnvalue : null,
        };
      } catch (err) {
        console.error("❌ jobStatus error:", err);
        return null;
      }
    },
  },
};

/* =========================
   ✅ Start server
========================= */
async function start() {
  const server = new ApolloServer({ typeDefs, resolvers });
  await server.start();

  app.use("/graphql", cors(), bodyParser.json(), expressMiddleware(server));

  app.listen(4000, () => {
    console.log("🚀 Server running on http://localhost:4000");
  });
}

start();
