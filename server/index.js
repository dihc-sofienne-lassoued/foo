const express = require("express");
const multer = require("multer");
const cors = require("cors");
const bodyParser = require("body-parser");

const { ApolloServer } = require("@apollo/server");
const { expressMiddleware } = require("@as-integrations/express5");

const typeDefs = require("./schema");

const app = express();
const upload = multer({ dest: "uploads/" });

// ✅ REST endpoint (MUST be before app.listen)
const videoQueue = require("./shared/queue");

app.post("/upload", upload.single("video"), async (req, res) => {
  console.log("📥 Upload received");
  if (!req.file) {
    return res.status(400).json({ error: "No file uploaded" });
  }
  console.log("API => QUEUE NAME:", videoQueue.name);

  const job = await videoQueue.add({
    file: req.file.path,
  });
  console.log("✅ Job added:", job.id);

  res.json({ jobId: job.id });
});

app.use("/outputs", express.static("outputs"));

const resolvers = {
  Query: {
    jobStatus: async (_, { id }) => {
      return {
        id,
        status: "queued",
        outputUrl: null,
      };
    },
  },
};

async function start() {
  const server = new ApolloServer({ typeDefs, resolvers });
  await server.start();

  app.use("/graphql", cors(), bodyParser.json(), expressMiddleware(server));

  app.listen(4000, () => {
    console.log("🚀 Server running on http://localhost:4000");
  });
}

start();
