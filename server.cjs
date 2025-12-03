const express = require('express');
const path = require('path');
const compression = require('compression');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const cluster = require('cluster');
const os = require('os');

const PORT = process.env.PORT || 3001;
const numCPUs = os.cpus().length;

if (cluster.isPrimary) {
    console.log(`
    🚀 NEXUS HOST: MAXIMUM POWER
    ----------------------------
    > Master Process: ${process.pid}
    > Detected Cores: ${numCPUs}
    > Mode: CLUSTER (Multi-Core)
    > Security: ACTIVE
    `);

    // Fork workers for each CPU core
    for (let i = 0; i < numCPUs; i++) {
        cluster.fork();
    }

    cluster.on('exit', (worker, code, signal) => {
        console.log(`⚠️ Worker ${worker.process.pid} died. Auto-Respawning...`);
        cluster.fork(); // Self-Healing: Respawn worker
    });

} else {
    // WORKER PROCESS
    const app = express();

    // 1. Advanced Security & Optimization
    app.use(helmet({
        contentSecurityPolicy: false,
    }));
    app.use(compression());
    app.use(cors());
    app.use(express.json());
    app.use(morgan('tiny')); // Request logging

    // Rate Limiting (DDoS Protection)
    const limiter = rateLimit({
        windowMs: 15 * 60 * 1000, // 15 minutes
        max: 1000, // Limit each IP to 1000 requests per windowMs
        message: { error: "Security Alert: Rate limit exceeded. Cooldown initiated." }
    });
    app.use(limiter);

    // 2. Serve Static Files
    app.use(express.static(path.join(__dirname, 'dist')));

    // 3. "Server Agent" API Endpoint (Enhanced)
    app.get('/api/server-agent/status', (req, res) => {
        const memory = process.memoryUsage();

        res.json({
            status: 'ONLINE',
            agent: 'Nexus Host Agent (Elite)',
            mode: 'CLUSTER',
            workerId: process.pid,
            totalCores: numCPUs,
            memory: {
                rss: Math.round(memory.rss / 1024 / 1024) + ' MB',
                heapTotal: Math.round(memory.heapTotal / 1024 / 1024) + ' MB',
            },
            uptime: process.uptime(),
            timestamp: new Date().toISOString()
        });
    });

    // MAINTENANCE MODE STATE
    let maintenanceMode = false;

    // API: Get System Status (Poll this from Frontend)
    app.get('/api/status', (req, res) => {
        res.json({
            status: 'ONLINE',
            maintenance: maintenanceMode,
            version: '2.5.0',
            cluster: {
                isWorker: cluster.isWorker,
                id: cluster.isWorker ? cluster.worker.id : 'MASTER'
            }
        });
    });

    // API: Toggle Maintenance Mode (Admin Only - Simulated)
    app.post('/api/admin/maintenance', (req, res) => {
        const { enabled } = req.body;
        maintenanceMode = enabled;
        console.log(`[SYSTEM] Maintenance Mode set to: ${maintenanceMode}`);
        res.json({ success: true, maintenance: maintenanceMode });
    });

    // 4. NEXUS BRIDGE GATEWAY (Reverse Proxy to Python)
    // Forwards requests from /api/bridge/* -> http://127.0.0.1:5000/*
    const httpProxy = require('http-proxy');
    const apiProxy = httpProxy.createProxyServer();

    app.use('/api/bridge', (req, res) => {
        console.log(`[GATEWAY] Proxying request: ${req.method} ${req.url} -> Python Bridge`);
        // req.url is already relative to the mount point in app.use
        apiProxy.web(req, res, { target: 'http://127.0.0.1:5001' }, (e) => {
            console.error("[GATEWAY] Bridge Error:", e.message);
            if (!res.headersSent) {
                res.status(502).json({ error: "Nexus Bridge Unreachable. Is the Python Core running?" });
            }
        });
    });

    // Serve React App (Catch-All)
    app.get(/(.*)/, (req, res) => {
        res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });

    app.listen(PORT, () => {
        console.log(`[NEXUS HOST] Server running on port ${PORT} | Worker: ${cluster.isWorker ? cluster.worker.id : 'MASTER'}`);
    });
}
