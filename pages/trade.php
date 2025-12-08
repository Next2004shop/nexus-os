<div class="flex h-full">
    <!-- CHART SECTION -->
    <div class="flex-1 flex flex-col p-4 h-full relative">
        <div class="flex justify-between items-center mb-4">
            <div class="flex items-center gap-4">
                <div class="logo-container"
                    style="width: 40px; height: 40px; margin: 0; background: rgba(255,149,0,0.1); border-color: rgba(255,149,0,0.2);">
                    <i data-lucide="bitcoin" style="color: #F7931A;"></i>
                </div>
                <div>
                    <h1 class="text-2xl font-bold">BTC/USD</h1>
                    <div class="text-nexus-subtext text-xs font-mono">BITCOIN SPOT MARKET</div>
                </div>
            </div>

            <div class="text-right">
                <div id="live-price" class="text-3xl font-bold font-mono text-green">$98,124.50</div>
                <div class="text-xs text-nexus-subtext flex justify-end items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-nexus-green animate-pulse"></span>
                    MARKET OPEN
                </div>
            </div>
        </div>

        <!-- CHART (MOCK FOR VISUALS) -->
        <div
            class="chart-wrapper flex-1 relative bg-black/40 backdrop-blur-md rounded-2xl border border-white/5 overflow-hidden">
            <!-- Simulated Chart Lines using CSS gradients for now, or lightweight charts later -->
            <div id="tv-chart" style="width: 100%; height: 100%;"></div>
        </div>
    </div>

    <!-- SIDE PANEL (OPERATIONS) -->
    <div style="width: 360px;" class="h-full border-l border-white/5 bg-black/20 backdrop-blur-xl p-6 flex flex-col">

        <div class="mb-8 p-4 rounded-xl bg-nexus-blue/10 border border-nexus-blue/20">
            <div class="flex justify-between items-center mb-2">
                <span class="text-xs font-bold text-nexus-blue uppercase">Connection Status</span>
                <span id="bridge-status" class="text-xs font-mono text-white">CONNECTING...</span>
            </div>
            <div class="h-1 bg-black/50 rounded-full overflow-hidden">
                <div id="status-bar" class="h-full w-full bg-nexus-blue animate-pulse origin-left"></div>
            </div>
        </div>

        <!-- NEW: AI INTELLIGENCE PANEL -->
        <div class="p-4 mb-6 rounded-xl bg-black/40 border border-white/10 relative overflow-hidden">
            <div class="absolute top-0 right-0 p-2 opacity-50"><i data-lucide="brain-circuit"></i></div>
            <h3 class="text-xs font-bold text-nexus-subtext uppercase mb-4">Nexus Intelligence</h3>

            <!-- Direction Meter -->
            <div class="flex items-center gap-4 mb-4">
                <div class="w-12 h-12 rounded-full border-4 border-white/10 flex items-center justify-center relative group"
                    id="meter-container">
                    <i id="dir-icon" data-lucide="minus" class="text-white"></i>
                </div>
                <div>
                    <div class="text-xs text-nexus-subtext font-mono">DIRECTION</div>
                    <div id="ai-direction" class="text-xl font-bold text-white">WAIT</div>
                </div>
            </div>

            <!-- Smart Money Badges -->
            <div class="space-y-2 mb-4">
                <div class="flex justify-between text-xs">
                    <span class="text-nexus-subtext">Smart Money</span>
                    <span id="smc-status" class="font-bold text-white">SCANNING...</span>
                </div>
                <div class="flex justify-between text-xs">
                    <span class="text-nexus-subtext">Confidence</span>
                    <span id="ai-conf" class="font-bold text-nexus-blue">0%</span>
                </div>
                <div class="flex justify-between text-xs">
                    <span class="text-nexus-subtext">Risk Rating</span>
                    <span id="risk-rating" class="font-bold text-white">---</span>
                </div>
            </div>

            <button id="btn-refresh-ai"
                class="w-full py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-bold transition-all">
                <i data-lucide="refresh-cw" class="w-3 h-3 inline mr-1"></i> UPDATE ANALYSIS
            </button>
        </div>

        <!-- STEALTH CONTROL -->
        <div class="mb-4">
            <button id="btn-burn"
                class="w-full py-3 rounded-xl bg-red-900/20 border border-red-500/30 text-red-500 hover:bg-red-900/40 transition-all font-mono text-xs uppercase flex items-center justify-center gap-2 group">
                <i data-lucide="flame" class="group-hover:text-red-400"></i> BURN LOGS (STEALTH)
            </button>
        </div>

        <div class="flex-1">
            <div class="flex gap-2 mb-6 p-1 bg-white/5 rounded-xl border border-white/5">
                <button id="mode-buy"
                    class="flex-1 py-3 rounded-lg font-bold text-sm bg-nexus-green text-black shadow-[0_0_15px_rgba(0,221,128,0.3)] transition-all">BUY</button>
                <button id="mode-sell"
                    class="flex-1 py-3 rounded-lg font-bold text-sm text-nexus-subtext hover:text-white transition-all">SELL</button>
            </div>

            <div class="space-y-4">
                <div class="input-group">
                    <label class="text-xs text-nexus-subtext font-bold block mb-2 uppercase">Amount (Lots)</label>
                    <input type="number" id="trade-amount" class="input-field text-xl font-bold" value="0.01"
                        step="0.01">
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div class="input-group">
                        <label class="text-xs text-nexus-subtext font-bold block mb-2 uppercase">Stop Loss</label>
                        <input type="number" id="trade-sl" class="input-field" placeholder="0.00">
                    </div>
                    <div class="input-group">
                        <label class="text-xs text-nexus-subtext font-bold block mb-2 uppercase">Take Profit</label>
                        <input type="number" id="trade-tp" class="input-field" placeholder="0.00">
                    </div>
                </div>
            </div>
        </div>

        <button id="btn-execute"
            class="w-full py-4 text-lg font-bold rounded-xl bg-nexus-green text-black hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_0_30px_rgba(0,221,128,0.2)]">
            EXECUTE BUY
        </button>
    </div>
</div>

<script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
<script src="/assets/js/api.js"></script>
<script>
    $(document).ready(function () {
        console.log("Nexus Trade V2");
        let currentMode = 'BUY';

        // 1. Check Backend Status Loop
        setInterval(async () => {
            const status = await NexusAPI.getStatus();
            $('#bridge-status').text(status.mt5_status || 'OFFLINE');

            if (status.mt5_status === 'CONNECTED') {
                $('#bridge-status').removeClass('text-red').addClass('text-green');
                $('#status-bar').removeClass('animate-pulse').addClass('bg-green-500');
            } else {
                $('#bridge-status').removeClass('text-green').addClass('text-red');
            }

            // Update Price (Mock for Vibe if offline, use real if available)
            if (Math.random() > 0.5) {
                let p = parseFloat($('#live-price').text().replace('$', '').replace(',', ''));
                p += (Math.random() - 0.5) * 50;
                $('#live-price').text('$' + p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
            }
        }, 2000);

        // 2. Mode Switch
        $('#mode-buy').click(() => {
            currentMode = 'BUY';
            $('#mode-buy').addClass('bg-nexus-green text-black shadow-[0_0_15px_rgba(0,221,128,0.3)]').removeClass('text-nexus-subtext hover:text-white bg-transparent');
            $('#mode-sell').removeClass('bg-nexus-red text-white shadow-[0_0_15px_rgba(255,59,48,0.3)]').addClass('text-nexus-subtext hover:text-white bg-transparent');
            $('#btn-execute').removeClass('bg-nexus-red shadow-[0_0_30px_rgba(255,59,48,0.2)]').addClass('bg-nexus-green shadow-[0_0_30px_rgba(0,221,128,0.2)]').text('EXECUTE BUY');
        });

        $('#mode-sell').click(() => {
            currentMode = 'SELL';
            $('#mode-sell').addClass('bg-nexus-red text-white shadow-[0_0_15px_rgba(255,59,48,0.3)]').removeClass('text-nexus-subtext hover:text-white bg-transparent');
            $('#mode-buy').removeClass('bg-nexus-green text-black shadow-[0_0_15px_rgba(0,221,128,0.3)]').addClass('text-nexus-subtext hover:text-white bg-transparent');
            $('#btn-execute').removeClass('bg-nexus-green shadow-[0_0_30px_rgba(0,221,128,0.2)]').addClass('bg-nexus-red shadow-[0_0_30px_rgba(255,59,48,0.2)]').text('EXECUTE SELL');
        });

        // 3. Execution Logic
        $('#btn-execute').click(async function () {
            const btn = $(this);
            const originalText = btn.text();
            const amount = $('#trade-amount').val();

            // Visual Interaction
            btn.addClass('opacity-50 cursor-not-allowed').text('PROCESSING...');

            // Call API
            const result = await NexusAPI.placeTrade('BTCUSD', currentMode, amount);

            if (result.status === 'Trade Executed' || result.ticket) {
                alert(`✅ ORDER FILLED\nTicket: ${result.ticket}\nVolume: ${amount}`);
            } else {
                alert(`❌ ERROR: ${result.error || 'Unknown Error'}`);
            }

            btn.removeClass('opacity-50 cursor-not-allowed').text(originalText);
        });

        // 4. Update AI Panel
        async function updateAI() {
            $('#btn-refresh-ai').find('i').addClass('animate-spin');

            try {
                // Call the Analyze Endpoint
                const res = await fetch('http://localhost:5001/ai/analyze', {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Basic ' + btoa('admin:securepassword'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ symbol: 'BTCUSD', timeframe: 'M15' })
                });
                const data = await res.json();

                // Parse AI Signal (Blueprint Format)
                if (data.ai_signal) {
                    const signal = data.ai_signal;

                    // Direction
                    $('#ai-direction').text(signal.direction || 'WAIT');
                    if (signal.direction === 'UP') {
                        $('#ai-direction').removeClass('text-red-500 text-white').addClass('text-green-400');
                        $('#meter-container').addClass('border-green-400/50').removeClass('border-red-500/50 border-white/10');
                        $('#dir-icon').replaceWith('<i id="dir-icon" data-lucide="arrow-up" class="text-green-400"></i>');
                    } else if (signal.direction === 'DOWN') {
                        $('#ai-direction').removeClass('text-green-400 text-white').addClass('text-red-500');
                        $('#meter-container').addClass('border-red-500/50').removeClass('border-green-400/50 border-white/10');
                        $('#dir-icon').replaceWith('<i id="dir-icon" data-lucide="arrow-down" class="text-red-500"></i>');
                    }

                    // Confidence
                    $('#ai-conf').text((signal.confidence || 0) + '%');

                    // Risk
                    $('#risk-rating').text(signal.risk_rating || 'MEDIUM');
                    if (signal.risk_rating === 'High') $('#risk-rating').addClass('text-red-500');
                    else if (signal.risk_rating === 'Low') $('#risk-rating').addClass('text-green-400');

                    // Mode
                    // $('#ai-mode').text(signal.mode || 'Hunt');
                }

                // Parse Smart Money
                if (data.smart_money) {
                    const smc = data.smart_money;
                    $('#smc-status').text(smc.status.replace(/_/g, ' '));
                    if (smc.status.includes('WHALE') || smc.status.includes('GRAB')) {
                        $('#smc-status').addClass('text-yellow-400 animate-pulse');
                    } else {
                        $('#smc-status').removeClass('text-yellow-400 animate-pulse').addClass('text-white');
                    }
                }

                lucide.createIcons();

            } catch (e) {
                console.error("AI Update Failed", e);
            } finally {
                $('#btn-refresh-ai').find('i').removeClass('animate-spin');
            }
        }

        $('#btn-refresh-ai').click(updateAI);

        // Initial Poll
        setTimeout(updateAI, 3000);

        // Simple Chart (Lightweight Charts)
        const chart = LightweightCharts.createChart(document.getElementById('tv-chart'), {
            layout: { background: { color: 'transparent' }, textColor: '#888' },
            grid: { vertLines: { color: 'rgba(255,255,255,0.05)' }, horzLines: { color: 'rgba(255,255,255,0.05)' } },
            width: document.getElementById('tv-chart').clientWidth,
            height: document.getElementById('tv-chart').clientHeight
        });
        const lineSeries = chart.addLineSeries({ color: '#00DD80' });
        // Mock Data Generation
        let data = [];
        let price = 98000;
        let time = new Date().getTime() / 1000 - (1000 * 60);
        for (let i = 0; i < 1000; i++) {
            price += (Math.random() - 0.5) * 100;
            time += 60;
            data.push({ time: time, value: price });
        }
        lineSeries.setData(data);
    });
</script>