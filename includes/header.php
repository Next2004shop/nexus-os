<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus AI | Enterprise Trading</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;700&display=swap">
    <link rel="stylesheet" href="/assets/css/style.css">
    <!-- Lucide Icons via CDN (Simple fix for icons) -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
</head>
<body>
    <div id="sidebar">
        <div class="logo-container">
            <img src="/legacy_react/src/assets/logo.png" alt="Nexus"> <!-- Pointing to legacy logo for now -->
        </div>
        <nav style="display: flex; flex-direction: column; width: 100%; align-items: center;">
            <a href="/?page=trade" class="nav-item <?php echo $page === 'trade' ? 'active' : ''; ?>" title="Trade">
                <i data-lucide="terminal"></i>
            </a>
            <a href="/?page=stocks" class="nav-item <?php echo $page === 'stocks' ? 'active' : ''; ?>" title="Stocks">
                <i data-lucide="globe"></i>
            </a>
            <a href="/?page=ai" class="nav-item <?php echo $page === 'ai' ? 'active' : ''; ?>" title="AI Bot">
                <i data-lucide="bot"></i>
            </a>
            <a href="/?page=wallet" class="nav-item <?php echo $page === 'wallet' ? 'active' : ''; ?>" title="Wallet">
                <i data-lucide="wallet"></i>
            </a>
        </nav>
    </div>
    <div id="main-content">
