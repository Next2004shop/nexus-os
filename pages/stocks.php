<div class="p-6 h-full overflow-y-auto">
    <!-- Header -->
    <div class="mb-8">
        <h1 class="text-3xl font-bold mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Global
            Markets</h1>
        <p class="text-nexus-subtext">Real-time stock prices and market data</p>
    </div>

    <!-- Market Overview Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <?php
        $stocks = [
            ['AAPL', 'Apple Inc.', 220.50, '+0.8%', '+1.75', 'tech'],
            ['TSLA', 'Tesla Inc.', 175.20, '-1.2%', '-2.15', 'automotive'],
            ['NVDA', 'NVIDIA Corp.', 120.00, '+3.4%', '+3.96', 'tech'],
            ['MSFT', 'Microsoft Corp.', 415.30, '+0.5%', '+2.08', 'tech'],
            ['GOOGL', 'Alphabet Inc.', 140.25, '-0.3%', '-0.42', 'tech'],
            ['AMZN', 'Amazon.com', 178.90, '+1.1%', '+1.95', 'ecommerce'],
        ];

        foreach ($stocks as $stock):
            $isPositive = strpos($stock[3], '+') !== false;
            $colorClass = $isPositive ? 'text-green' : 'text-red';
            $borderGlow = $isPositive ? 'border-nexus-green/20' : 'border-nexus-red/20';
            $bgGlow = $isPositive ? 'bg-nexus-green/5' : 'bg-nexus-red/5';
            ?>
            <div
                class="nexus-card p-6 hover:scale-[1.02] transition-transform cursor-pointer group relative overflow-hidden">
                <!-- Background glow effect -->
                <div class="absolute inset-0 <?php echo $bgGlow; ?> opacity-0 group-hover:opacity-100 transition-opacity">
                </div>

                <div class="relative z-10">
                    <!-- Stock Symbol & Change -->
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <div class="flex items-center gap-2 mb-1">
                                <h3 class="text-2xl font-bold font-mono"><?php echo $stock[0]; ?></h3>
                                <span
                                    class="px-2 py-0.5 rounded-md text-xs font-bold uppercase bg-white/10 text-nexus-subtext"><?php echo $stock[5]; ?></span>
                            </div>
                            <p class="text-sm text-nexus-subtext"><?php echo $stock[1]; ?></p>
                        </div>
                        <div class="text-right">
                            <div class="<?php echo $colorClass; ?> text-xl font-bold font-mono"><?php echo $stock[3]; ?>
                            </div>
                            <div class="<?php echo $colorClass; ?> text-sm font-mono"><?php echo $stock[4]; ?></div>
                        </div>
                    </div>

                    <!-- Current Price -->
                    <div class="flex items-baseline gap-2 mb-4">
                        <span class="text-4xl font-bold font-mono">$<?php echo number_format($stock[2], 2); ?></span>
                    </div>

                    <!-- Mini Chart Placeholder -->
                    <div class="h-16 relative">
                        <div class="absolute inset-0 flex items-end justify-between gap-1">
                            <?php for ($i = 0; $i < 20; $i++):
                                $height = rand(20, 100);
                                ?>
                                <div class="flex-1 <?php echo $isPositive ? 'bg-nexus-green/30' : 'bg-nexus-red/30'; ?> rounded-t transition-all hover:opacity-80"
                                    style="height: <?php echo $height; ?>%"></div>
                            <?php endfor; ?>
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="mt-4 flex gap-2">
                        <button
                            class="flex-1 py-2 bg-nexus-green/10 hover:bg-nexus-green/20 border border-nexus-green/30 text-nexus-green rounded-lg text-sm font-bold transition-all">
                            BUY
                        </button>
                        <button
                            class="flex-1 py-2 bg-nexus-red/10 hover:bg-nexus-red/20 border border-nexus-red/30 text-nexus-red rounded-lg text-sm font-bold transition-all">
                            SELL
                        </button>
                    </div>
                </div>
            </div>
        <?php endforeach; ?>
    </div>

    <!-- Market Indices -->
    <div class="nexus-card p-6">
        <h3 class="text-lg font-bold mb-4">Market Indices</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <?php
            $indices = [
                ['S&P 500', '5,200.50', '+0.45%', '+23.25'],
                ['NASDAQ', '16,400.20', '+0.82%', '+133.50'],
                ['DOW JONES', '40,100.75', '-0.12%', '-48.50'],
            ];
            foreach ($indices as $index):
                $isPositive = strpos($index[2], '+') !== false;
                $colorClass = $isPositive ? 'text-green' : 'text-red';
                ?>
                <div class="flex justify-between items-center p-4 bg-black/20 rounded-xl border border-white/5">
                    <div>
                        <div class="text-nexus-subtext text-sm mb-1"><?php echo $index[0]; ?></div>
                        <div class="text-2xl font-bold font-mono"><?php echo $index[1]; ?></div>
                    </div>
                    <div class="text-right">
                        <div class="<?php echo $colorClass; ?> text-lg font-bold"><?php echo $index[2]; ?></div>
                        <div class="<?php echo $colorClass; ?> text-sm font-mono"><?php echo $index[3]; ?></div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
</div>

<style>
    .card {
        background: var(--nexus-card);
        border: 1px solid var(--nexus-border);
        backdrop-filter: blur(10px);
        border-radius: 16px;
    }
</style>

<script>
    // Add real-time price updates
    setInterval(() => {
        // Simulate price changes
        document.querySelectorAll('.font-mono').forEach(el => {
            if (el.textContent.includes('$') && !el.textContent.includes('%')) {
                const price = parseFloat(el.textContent.replace('$', '').replace(',', ''));
                const change = (Math.random() - 0.5) * 2;
                const newPrice = price + change;
                el.textContent = '$' + newPrice.toFixed(2);
            }
        });
    }, 3000);
</script>