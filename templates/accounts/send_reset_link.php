<?php
$email = $_POST['email'];

// Generate token and save to database
$token = bin2hex(random_bytes(50));
// ... save to your users table ...

// Now just redirect or link to your EXISTING reset email HTML
$reset_link = "http://yourwebsite.com/your_existing_reset_email.html?token=" . $token;

// Send email with that link
mail($email, "Reset Password", "Click: $reset_link", "From: noreply@site.com");

echo "Reset link sent to your email!";
?>