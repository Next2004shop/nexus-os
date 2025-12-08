<?php
// Simple PHP Router
$page = isset($_GET['page']) ? $_GET['page'] : 'trade';

// Whitelist pages for security
$allowed_pages = ['trade', 'stocks', 'ai', 'wallet'];
if (!in_array($page, $allowed_pages)) {
    $page = 'trade';
}

require_once 'includes/header.php';

// Include the requested page
$page_file = "pages/{$page}.php";
if (file_exists($page_file)) {
    include $page_file;
} else {
    echo "<div style='color: white; padding: 2rem;'>Page not found: {$page}</div>";
}

require_once 'includes/footer.php';
?>