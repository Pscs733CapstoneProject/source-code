// backend/src/index.js
const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const path = require("path");
const { v4: uuidv4 } = require("uuid");
const natural = require("natural");

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors()); // open for dev, adjust for production
app.use(bodyParser.json());

// load training data
const trainingDataPath = path.join(__dirname, "config", "trainingData.json");
let trainingData = require(trainingDataPath);

// Build TF-IDF
const TfIdf = natural.TfIdf;
let tfidf = new TfIdf();
trainingData.forEach((item) => tfidf.addDocument(item.text));

// helper - compute scores for a query
function scoreQuery(query) {
  const scores = []; // { idx, score }
  // tfidf.tfidfs calculates score per document for the query
  tfidf.tfidfs(query, function(i, measure) {
    scores.push({ idx: i, score: measure });
  });
  return scores;
}

// normalize and compute final scoring with optional role boost
function findBestMatch(query, role = "") {
  const lowerRole = (role || "").toLowerCase().trim();
  const scores = scoreQuery(query);

  // attach meta info and role boost
  const results = scores.map((s) => {
    const doc = trainingData[s.idx];
    let finalScore = s.score;

    // if role is provided and matches doc.role or doc.role == 'All', boost
    if (lowerRole) {
      const docRole = (doc.role || "").toLowerCase();
      if (docRole && (docRole === lowerRole || docRole === "all" || lowerRole.includes(docRole))) {
        finalScore = finalScore * 1.4 + 0.2; // boost
      }
    }

    return {
      id: doc.id,
      title: doc.title,
      role: doc.role,
      department: doc.department,
      text: doc.text,
      score: finalScore
    };
  });

  // sort descending by score
  results.sort((a, b) => b.score - a.score);
  return results;
}

// Chat endpoint
app.post("/chat", (req, res) => {
  try {
    let { message, role, sessionId } = req.body || {};
    if (!message) return res.status(400).json({ error: "Missing 'message' in body" });

    console.log(`[${sessionId || uuidv4()}] query:`, message, " role:", role || "none");

    // find matches
    const matches = findBestMatch(message, role);

    // pick top match if score above threshold
    const top = matches[0] || null;
    const threshold = 0.05; // tune this threshold if needed

    if (top && top.score >= threshold) {
      return res.json({
        reply: top.text,
        id: top.id,
        title: top.title,
        role: top.role,
        score: top.score,
      });
    } else {
      // fallback: show a helpful generic message and top suggestions
      const suggestions = matches.slice(0, 3).map(m => ({ id: m.id, title: m.title, score: m.score }));
      return res.json({
        reply: "Sorry, I couldn't find an exact match. Please rephrase or try keywords like: clerk, approval, report, password.",
        suggestions
      });
    }
  } catch (err) {
    console.error("Server error:", err);
    return res.status(500).json({ error: "Server error" });
  }
});

// A simple endpoint to list available training topics (for frontend to show quick options)
app.get("/topics", (req, res) => {
  const list = trainingData.map(d => ({ id: d.id, title: d.title, role: d.role }));
  res.json(list);
});

app.listen(PORT, "127.0.0.1", () => {
  console.log(`NLP server running on http://127.0.0.1:${PORT}`);
});
