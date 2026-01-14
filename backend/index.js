const express = require("express");
const app = express();

// Middleware
app.use(express.json());

// Port (Render uses process.env.PORT)
const PORT = process.env.PORT || 3000;

// Test route
app.get("/", (req, res) => {
  res.send("Placement Portal Backend is running 🚀");
});

// Example API route
app.get("/api/students", (req, res) => {
  res.json([
    { id: 1, name: "Student One", branch: "CSE" },
    { id: 2, name: "Student Two", branch: "ECE" }
  ]);
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
