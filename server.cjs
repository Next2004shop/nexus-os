const express = require('express');
const path = require('path');
const compression = require('compression');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const cluster = require('cluster');
const os = require('os');

const PORT = process.env.PORT || 3000;
const BRIDGE_TARGET = process.env.BRIDGE_TARGET || 'http://35.239.252.226:5000';
const RATE_LIMIT_WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS || 5 * 60 * 1000); // default 5 minutes
const RATE_LIMIT_MAX = Number(process.env.RATE_LIMIT_MAX || 300); // default 300 requests / window / IP
const MAINTENANCE_TOKEN = process.env.MAINTENANCE_TOKEN || '';
const TRUST_PROXY = process.env.TRUST_PROXY || 'loopback';
const CSP_ENABLED = process.env.CSP_ENABLED !== 'false';
const BRIDGE_BASIC_USER = process.env.BRIDGE_BASIC_USER || 'danmutemi2023';
const BRIDGE_BASIC_PASS = process.env.BRIDGE_BASIC_PASS || '\\-JR0-0bEGRP.IS';
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

    cluster.on('exit', (worker) => {
        console.log(`⚠️ Worker ${worker.process.pid} died. Auto-Respawning...`);
        cluster.fork(); // Self-Healing: Respawn worker
    });

} else {
    // WORKER PROCESS
    const app = express();

    // 1. Advanced Security & Optimization
    app.set('trust proxy', TRUST_PROXY);
    app.use(helmet({
        contentSecurityPolicy: CSP_ENABLED ? {
            directives: {
                defaultSrc: ["'self'"],
                connectSrc: ["'self'", BRIDGE_TARGET],
                imgSrc: ["'self'", 'data:'],
                scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                styleSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                objectSrc: ["'none'"],
            }
        } : false,
        crossOriginEmbedderPolicy: false,
    }));
    app.use(compression());
    app.use(cors());
    app.use(express.json());
    app.use(morgan('tiny')); // Request logging

    // Routes
    const walletRoutes = require('./src/routes/wallet.cjs');
    app.use('/api/wallet', walletRoutes);

    // Rate Limiting (DDoS Protection)
    const limiter = rateLimit({
        windowMs: RATE_LIMIT_WINDOW_MS,
        max: RATE_LIMIT_MAX,
        standardHeaders: true,
        legacyHeaders: false,
        message: { error: "Security Alert: Rate limit exceeded. Cooldown initiated." }
    });
    app.use(limiter);

    // 2. Serve Static Files
    app.use(express.static(path.join(__dirname, 'dist')));

    // 2.1 Proxy to Python Bridge (MetaTrader 5)
    const httpProxy = require('http-proxy');
    const apiProxy = httpProxy.createProxyServer();
    apiProxy.on('error', (e, req, res) => {
        console.error("Bridge Proxy Error:", e.message);
        if (!res.headersSent) {
            res.status(502).json({ error: "Bridge Unreachable", details: e.message });
        }
    });

    app.all('/api/bridge/*', (req, res) => {
        // Remove /api/bridge prefix when forwarding to Python (which expects /status, /trade, etc.)
        req.url = req.url.replace('/api/bridge', '');
        const headers = {};
        if (BRIDGE_BASIC_USER && BRIDGE_BASIC_PASS) {
            const token = Buffer.from(`${BRIDGE_BASIC_USER}:${BRIDGE_BASIC_PASS}`).toString('base64');
            headers.Authorization = `Basic ${token}`;
        }
        apiProxy.web(req, res, { target: BRIDGE_TARGET, changeOrigin: true, headers });
    });

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

    const requireAdminToken = (req, res, next) => {
        if (!MAINTENANCE_TOKEN) return next(); // allow if not configured
        if (req.get('x-admin-token') === MAINTENANCE_TOKEN) return next();
        return res.status(401).json({ error: 'Unauthorized' });
    };

    // API: Toggle Maintenance Mode (Admin Only)
    app.post('/api/admin/maintenance', requireAdminToken, (req, res) => {
        const { enabled } = req.body;
        maintenanceMode = enabled;
        console.log(`[SYSTEM] Maintenance Mode set to: ${maintenanceMode}`);
        res.json({ success: true, maintenance: maintenanceMode });
    });

    // Serve React App (Catch all for SPA)
    app.get('*', (req, res) => {
        res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });

    app.listen(PORT, () => {
        console.log(`[NEXUS HOST] Server running on port ${PORT} | Worker: ${cluster.isWorker ? cluster.worker.id : 'MASTER'}`);
    });
}
