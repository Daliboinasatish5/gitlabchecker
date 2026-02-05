const express = require("express");
const { exec } = require("child_process");

const app = express();
const PORT = 3000;

// Root route
app.get("/", (req, res) => {
  res.send("GitLab Compliance Checker running on Node (no Streamlit)");
});

// Run Python CLI (NO Streamlit)
app.get("/run", (req, res) => {
  exec("python cli.py", (error, stdout, stderr) => {
    if (error) {
      res.status(500).send(stderr || error.message);
      return;
    }
    res.type("text/plain").send(stdout);
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Node server running at http://localhost:${PORT}`);
});
