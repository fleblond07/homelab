<?php

if (!defined('ABSPATH') || !defined('HOMELAB_SMTP_HOST')) {
    return;
}

add_action('phpmailer_init', static function ($phpmailer) {
    $original_from = $phpmailer->From;

    $phpmailer->isSMTP();
    $phpmailer->Host = HOMELAB_SMTP_HOST;
    $phpmailer->Port = HOMELAB_SMTP_PORT;
    $phpmailer->SMTPSecure = HOMELAB_SMTP_ENCRYPTION;
    $phpmailer->SMTPAutoTLS = HOMELAB_SMTP_ENCRYPTION === 'tls';
    $phpmailer->SMTPAuth = true;
    $phpmailer->Username = HOMELAB_SMTP_USERNAME;
    $phpmailer->Password = HOMELAB_SMTP_PASSWORD;
    $phpmailer->Timeout = 15;

    $phpmailer->From = HOMELAB_SMTP_FROM_EMAIL;
    $phpmailer->Sender = HOMELAB_SMTP_FROM_EMAIL;
    if (defined('HOMELAB_SMTP_FROM_NAME')) {
        $phpmailer->FromName = HOMELAB_SMTP_FROM_NAME;
    }

    if (
        $original_from
        && strcasecmp($original_from, HOMELAB_SMTP_FROM_EMAIL) !== 0
        && stripos($original_from, 'wordpress@') !== 0
        && !$phpmailer->getReplyToAddresses()
    ) {
        $phpmailer->addReplyTo($original_from);
    }
}, PHP_INT_MAX);

add_action('wp_mail_failed', static function ($error) {
    error_log('homelab-smtp: ' . $error->get_error_message());
});
