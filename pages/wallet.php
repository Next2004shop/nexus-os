<div class="page-container">
    <h1 style="font-size: 2rem; margin-bottom: 2rem; font-weight: bold;">Wallet</h1>

    <div class="card p-4"
        style="background: linear-gradient(135deg, #00DD8022 0%, #000 100%); margin-bottom: 2rem; border-color: var(--nexus-green);">
        <div class="text-subtext uppercase text-xs font-bold mb-2">Total Balance</div>
        <div class="font-mono text-white" style="font-size: 3rem; font-weight: bold;">$124,592.40</div>
        <div class="text-green flex items-center gap-2 mt-2">
            <i data-lucide="trending-up"></i> +$2,490.10 (2.1%)
        </div>
    </div>

    <h2 style="font-size: 1.2rem; margin-bottom: 1rem;">Assets</h2>
    <div class="card">
        <?php
        $assets = [
            ['USDT', 'Tether', 45000.00],
            ['BTC', 'Bitcoin', 1.24],
            ['ETH', 'Ethereum', 14.5],
        ];
        foreach ($assets as $asset):
            ?>
            <div class="p-4 flex justify-between items-center" style="border-bottom: 1px solid var(--nexus-border);">
                <div class="flex items-center gap-4">
                    <div
                        style="width: 32px; height: 32px; background: rgba(255,255,255,0.1); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem;">
                        <?php echo $asset[0][0]; ?>
                    </div>
                    <div>
                        <div class="font-bold"><?php echo $asset[0]; ?></div>
                        <div class="text-subtext text-xs"><?php echo $asset[1]; ?></div>
                    </div>
                </div>
                <div class="text-right font-mono">
                    <?php echo number_format($asset[2], 2); ?>
                </div>
            </div>
        <?php endforeach; ?>
    </div>
</div>