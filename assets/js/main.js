// Main Nexus JS
$(document).ready(function () {
    console.log("Nexus Core Online");

    // Sidebar Hover Effects (already handled by CSS, but adds sound or extra interaction)
    $('.nav-item').mouseenter(function () {
        // Optional: Play tick sound
    });

    // Global "Vibe" Animations
    $('body').css('opacity', 0).animate({ opacity: 1 }, 500);
});
