<?php
include 'db_setup.php';
session_start();

$error = '';
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $username = $_POST['username'];
    $password = $_POST['password'];

    // VULNERABILIDAD: Inyección SQL clásica
    // No se usan sentencias preparadas, se concatena directamente la entrada del usuario
    $query = "SELECT * FROM users WHERE username = '$username' AND password = '$password'";
    
    try {
        $result = $db->query($query);
        $user = $result->fetch(PDO::FETCH_ASSOC);

        if ($user) {
            $_SESSION['user'] = $user['username'];
            header('Location: welcome.php');
            exit;
        } else {
            $error = "Usuario o contraseña incorrectos.";
        }
    } catch (Exception $e) {
        $error = "Error en la consulta: " . $e->getMessage();
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login | SecureApp (Vulnerable)</title>
    <!-- Usamos Tailwind para emular Shadcn/UI rápidamente sin dependencias complejas -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #020817; }
        .shadcn-card { background-color: #020817; border: 1px solid #1e293b; color: #f8fafc; }
        .shadcn-input { background-color: #020817; border: 1px solid #1e293b; color: #f8fafc; }
        .shadcn-input:focus { border-color: #3b82f6; outline: none; ring: 2px; ring-color: #3b82f6; }
        .shadcn-primary { background-color: #f8fafc; color: #020817; }
        .shadcn-primary:hover { background-color: #e2e8f0; }
        .shadcn-secondary { background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; }
        .shadcn-secondary:hover { background-color: #334155; }
    </style>
</head>
<body class="flex min-h-screen items-center justify-center p-4">
    <div class="shadcn-card w-full max-w-md rounded-xl p-8 shadow-2xl">
        <div class="mb-8 text-center">
            <h1 class="text-2xl font-bold tracking-tight text-white">Ingresar al Sistema</h1>
            <p class="text-sm text-slate-400 mt-2">Introduce tus credenciales para acceder al panel.</p>
        </div>

        <form method="POST" class="space-y-6" id="loginForm">
            <div class="space-y-2">
                <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70" for="username">Usuario</label>
                <input type="text" name="username" id="username" placeholder="admin" required
                       class="shadcn-input flex h-10 w-full rounded-md px-3 py-2 text-sm">
            </div>
            
            <div class="space-y-2">
                <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70" for="password">Contraseña</label>
                <input type="password" name="password" id="password" placeholder="••••••••" required
                       class="shadcn-input flex h-10 w-full rounded-md px-3 py-2 text-sm">
            </div>

            <?php if ($error): ?>
                <div class="rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-500">
                    <?php echo $error; ?>
                </div>
            <?php endif; ?>

            <button type="submit" class="shadcn-primary flex h-10 w-full items-center justify-center rounded-md px-4 py-2 text-sm font-semibold transition-colors">
                Continuar
            </button>
        </form>

        <div class="mt-8 pt-6 border-t border-slate-800">
            <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-4">Herramientas de Auditoría</h3>
            <div class="grid grid-cols-1 gap-3">
                <button onclick="injectSQL()" class="shadcn-secondary flex h-10 w-full items-center justify-center rounded-md px-4 py-2 text-xs font-medium transition-colors">
                    🚀 Cargar Bypass SQL Injection
                </button>
                <a href="search.php" class="text-center text-xs text-slate-400 hover:text-white transition-colors mt-2">
                    Probar Inyección en Búsqueda (XSS/SQL) →
                </a>
            </div>
        </div>
    </div>

    <script>
        function injectSQL() {
            // El payload ' OR 1=1 -- comenta el resto de la consulta SQL (incluyendo el AND de la contraseña)
            document.getElementById('username').value = "' OR 1=1 --";
            document.getElementById('password').value = "hack";
            // Resaltar para feedback visual
            document.getElementById('username').classList.add('border-blue-500');
            setTimeout(() => {
                document.getElementById('loginForm').submit();
            }, 500);
        }
    </script>
</body>
</html>
