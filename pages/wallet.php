<div class="p-6 h-full overflow-y-auto">
    <!-- Header -->
    <div class="mb-8">
        <h1 class="text-3xl font-bold mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Wallet
        </h1>
        <p class="text-nexus-subtext">Manage your assets and portfolio</p>
    </div>

    <!-- Total Balance Card -->
    <div class="nexus-card p-8 mb-8 relative overflow-hidden">
        <div class="absolute top-0 right-0 w-64 h-64 bg-nexus-green/5 rounded-full blur-3xl"></div>
        <div class="relative z-10">
            <div class="flex justify-between items-start mb-6">
                <div>
                    <div class="text-nexus-subtext uppercase text-xs font-bold mb-3">Total Balance</div>
                    <div class="font-mono text-white text-5xl font-bold mb-4">$124,592.40</div>
                    <div class="text-green flex items-center gap-2">
                        <i data-lucide="trending-up" class="w-5 h-5"></i>
                        +$2,490.10 (2.1%) Today
                    </div>
                </div>
                <div class="flex gap-3">
                    <button class="btn btn-primary flex items-center gap-2">
                        <i data-lucide="plus" class="w-4 h-4"></i> Deposit
                    </button>
                    <button class="btn bg-white/10 hover:bg-white/20 text-white border-0 flex items-center gap-2">
                        <i data-lucide="arrow-up-right" class="w-4 h-4"></i> Withdraw
                    </button>
                </div>
            </div>

            <!-- Quick Stats -->
            <div class="grid grid-cols-3 gap-4 pt-6 border-t border-white/10">
                <div>
                    <div class="text-nexus-subtext text-xs mb-1">Available</div>
                    <div class="text-xl font-bold font-mono">$98,234.50</div>
                </div>
                <div>
                    <div class="text-nexus-subtext text-xs mb-1">In Orders</div>
                    <div class="text-xl font-bold font-mono text-nexus-yellow">$26,357.90</div>
                </div>
                <div>
                    <div class="text-nexus-subtext text-xs mb-1">Total P&L</div>
                    <div class="text-xl font-bold font-mono text-nexus-green">+$12,450.20</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Assets Grid -->
    <div class="mb-6">
        <h2 class="text-xl font-bold mb-4">Assets</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <?php
            $assets = [
                ['USDT', 'Tether', 45000.00, '$45,000.00', '+0.01%', 'stablecoin'],
                ['BTC', 'Bitcoin', 1.24, '$121,700.00', '+2.5%', 'crypto'],
                ['ETH', 'Ethereum', 14.5, '$28,450.00', '+1.8%', 'crypto'],
                ['EUR', 'Euro', 25000.00, '$26,250.00', '+0.5%', 'forex'],
                ['AAPL', 'Apple Stock', 120.00, '$26,460.00', '+0.8%', 'stock'],
                ['GOLD', 'Gold (oz)', 10.5, '$24,780.00', '+1.2%', 'commodity'],
            ];

            foreach ($assets as $asset):
                $isPositive = strpos($asset[4], '+') !== false;
                $colorClass = $isPositive ? 'text-green' : 'text-red';
                $iconClass = $isPositive ? 'trending-up' : 'trending-down';
                ?>
                <div class="nexus-card p-5 hover:scale-[1.02] transition-all cursor-pointer group">
                    <div class="flex justify-between items-start mb-4">
                        <div class="flex items-center gap-3">
                            <div
                                class="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center font-bold text-lg border border-white/20">
                                <?php echo $asset[0][0]; ?>
                            </div>
                            <div>
                                <div class="font-bold text-lg"><?php echo $asset[0]; ?></div>
                                <div class="text-nexus-subtext text-xs"><?php echo $asset[1]; ?></div>
                            </div>
                        </div>
                        <span class="px-2 py-1 rounded-md text-xs font-bold uppercase bg-white/10 text-nexus-subtext">
                            <?php echo $asset[5]; ?>
                        </span>
                    </div>

                    <div class="mb-3">
                        <div class="text-nexus-subtext text-xs mb-1">Holdings</div>
                        <div class="font-mono text-2xl font-bold"><?php echo number_format($asset[2], 2); ?></div>
                    </div>

                    <div class="flex justify-between items-center pt-3 border-t border-white/10">
                        <div>
                            <div class="text-nexus-subtext text-xs">Value</div>
                            <div class="font-mono font-bold"><?php echo $asset[3]; ?></div>
                        </div>
                        <div class="<?php echo $colorClass; ?> flex items-center gap-1 text-sm font-bold">
                            <i data-lucide="<?php echo $iconClass; ?>" class="w-4 h-4"></i>
                            <?php echo $asset[4]; ?>
                        </div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>

    <!-- Recent Transactions -->
    <div class="nexus-card p-6">
        <h3 class="text-lg font-bold mb-4">Recent Transactions</h3>
        <div class="space-y-3">
            <?php
            $transactions = [
                ['Deposit', 'USDT', '+5,000.00', '2 hours ago', 'deposit'],
                ['Buy', 'BTC', '-0.05', '5 hours ago', 'buy'],
                ['Sell', 'ETH', '+2.5', '1 day ago', 'sell'],
                ['Withdrawal', 'USD', '-10,000.00', '2 days ago', 'withdrawal'],
            ];

            foreach ($transactions as $tx):
                $isPositive = strpos($tx[2], '+') !== false;
                $colorClass = $isPositive ? 'text-green' : $tx[4] === 'buy' ? 'text-nexus-blue' : 'text-red';
                $icon = $tx[4] === 'deposit' ? 'arrow-down-left' : ($tx[4] === 'withdrawal' ? 'arrow-up-right' : ($tx[4] === 'buy' ? 'shopping-cart' : 'dollar-sign'));
                ?>
                <div
                    class="flex justify-between items-center p-4 bg-black/20 rounded-xl border border-white/5 hover:bg-black/30 transition-all">
                    <div class="flex items-center gap-4">
                        <div class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
                            <i data-lucide="<?php echo $icon; ?>" class="w-5 h-5 <?php echo $colorClass; ?>"></i>
                        </div>
                        <div>
                            <div class="font-bold"><?php echo $tx[0]; ?></div>
                            <div class="text-nexus-subtext text-xs"><?php echo $tx[3]; ?></div>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="font-mono font-bold <?php echo $colorClass; ?>"><?php echo $tx[2]; ?>
                            <?php echo $tx[1]; ?></div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
</div>

<script>
    // Update balance animation
    function animateValue(id, start, end, duration) {
        const obj = document.querySelector(id);
        if (!obj) return;
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = progress * (end - start) + start;
            obj.textContent = '$' + value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Simulate balance updates
    setInterval(() => {
        const currentBalance = parseFloat($('.font-mono.text-white.text-5xl').text().replace('$', '').replace(',', ''));
        const change = (Math.random() - 0.5) * 100;
        const newBalance = currentBalance + change;
        $('.font-mono.text-white.text-5xl').text('$' + newBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
    }, 5000);

    // Initialize icons
    lucide.createIcons();
</script>