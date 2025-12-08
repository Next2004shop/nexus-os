<div class="page-container">
    <h1 style="font-size: 2rem; margin-bottom: 2rem; font-weight: bold;">Global Markets</h1>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
        <!-- Generating mock cards for vibe -->
        <?php
        $stocks = [
            ['AAPL', 'Apple Inc.', 185.92, '+1.2%'],
            ['TSLA', 'Tesla Inc.', 240.50, '-0.5%'],
            ['NVDA', 'NVIDIA Corp.', 450.10, '+3.4%'],
            ['MSFT', 'Microsoft', 370.20, '+0.8%'],
            ['GOOGL', 'Alphabet', 130.40, '-0.2%'],
            ['AMZN', 'Amazon', 145.30, '+1.5%'],
        ];

        foreach ($stocks as $stock):
            $color = strpos($stock[3], '+') !== false ? 'text-green' : 'text-red';
            ?>
            <div class="card p-4">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold" style="font-size: 1.2rem;"><?php echo $stock[0]; ?></span>
                    <span class="<?php echo $color; ?> font-mono"><?php echo $stock[3]; ?></span>
                </div>
                <div class="text-subtext" style="font-size: 0.9rem; margin-bottom: 1rem;"><?php echo $stock[1]; ?></div>
                <div class="font-mono" style="font-size: 1.5rem; font-weight: bold;">
                    $<?php echo number_format($stock[2], 2); ?></div>
            </div>
        <?php endforeach; ?>
    </div>
</div>