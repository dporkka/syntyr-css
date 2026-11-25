<?php
/**
 * Example for a WordPress child theme's functions.php.
 * Copy dist/syntyr.embed.css into the child theme's assets directory.
 * This is source guidance, not a standalone WordPress plugin.
 */
add_action('wp_enqueue_scripts', function () {
    $relative = '/assets/syntyr.embed.css';
    $absolute = get_stylesheet_directory() . $relative;
    if (!is_readable($absolute)) {
        return;
    }
    wp_enqueue_style(
        'syntyr-embed',
        get_stylesheet_directory_uri() . $relative,
        array(),
        (string) filemtime($absolute)
    );
});
