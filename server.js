const express = require('express');
const path = require('path');
const compression = require('compression');
const helmet = require('helmet');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// 1. Security & Optimization
app.use(helmet({
    contentSecurityPolicy: false, // Disabled for flexibility with external images/scripts
}));
app.use(compression()); // Gzip compression
app.use(cors());
app.use(express.json());

// 2. Serve Static Files (The React App)
app.use(express.static(path.join(__dirname, 'dist')));

// 3. "Server Agent" API Endpoint
// This allows the AI Command Center to monitor the host's health
app.get('/api/server-agent/status', (req, res) => {
    const uptime = process.uptime();
    const memory = process.memoryUsage();

    res.json({
        status: 'ONLINE',
        agent: 'Nexus Host Agent',
        uptime: uptime,
        memory: {
            rss: Math.round(memory.rss / 1024 / 1024) + ' MB',
            heapTotal: Math.round(memory.heapTotal / 1024 / 1024) + ' MB',
            heapUsed: Math.round(memory.heapUsed / 1024 / 1024) + ' MB',
        },
        load: 'OPTIMAL',
        timestamp: new Date().toISOString()
    });
});

// 4. Catch-All Route (SPA Support)
// Sends all other requests to index.html so React Router handles them
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

// 5. Start the Host
app.listen(PORT, () => {
    console.log(`
    🚀 NEXUS HOST ONLINE
    --------------------
    > Port: ${PORT}
    > Mode: Production
    > Agent: Active
    > URL:  http://localhost:${PORT}
    `);
});
