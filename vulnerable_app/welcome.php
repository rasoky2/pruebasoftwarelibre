<?php
session_start();
if (!isset($_SESSION['user'])) {
    header('Location: index.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Panel de Usuario</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; text-align: center; padding-top: 100px; }
        .welcome-msg { font-size: 2rem; color: #38bdf8; }
        a { color: #f472b6; text-decoration: none; }
    </style>
</head>
<body>
    <div class="welcome-msg">¡Bienvenido, <?php echo htmlspecialchars($_SESSION['user']); ?>!</div>
    <p>Has iniciado sesión exitosamente.</p>
    <p><a href="logout.php">Cerrar Sesión</a></p>
</body>
</html>
