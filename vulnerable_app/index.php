<?php
include 'db_setup.php';
require_once 'auth_ldap.php'; // Integración con el proyecto de Agustín
session_start();

$error = '';
$login_method = 'DB'; // Método por defecto

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $username = $_POST['username'];
    $password = $_POST['password'];
    $method = $_POST['auth_method']; // Detectamos el botón presionado

    if ($method === 'LDAP') {
        // --- LOGIN CORPORATIVO (LDAP) ---
        if (autenticar_con_ldap($username, $password)) {
            $_SESSION['user'] = $username;
            $_SESSION['auth_type'] = 'LDAP (Corporativo)';
            header('Location: welcome.php');
            exit;
        } else {
            $error = "Error: Autenticación LDAP fallida. (Hable con Agustín)";
        }
    } else {
        // --- LOGIN TRADICIONAL (MySQL - VULNERABLE) ---
        $query = "SELECT * FROM users WHERE username = '$username' AND password = '$password'";
        try {
            $result = $db->query($query);
            $user = $result->fetch(PDO::FETCH_ASSOC);

            if ($user) {
                $_SESSION['user'] = $user['username'];
                $_SESSION['auth_type'] = 'Base de Datos (Tradicional)';
                header('Location: welcome.php');
                exit;
            } else {
                $error = "Usuario o contraseña incorrectos.";
            }
        } catch (Exception $e) {
            $error = "Error en la consulta: " . $e->getMessage();
        }
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIA Login | Secure Infrastructure Access</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #020817; }
        .shadcn-card { background-color: #020817; border: 1px solid #1e293b; color: #f8fafc; }
        .shadcn-input { background-color: #0c1117; border: 1px solid #30363d; color: #f8fafc; }
        .shadcn-input:focus { border-color: #3b82f6; outline: none; }
        .btn-primary { background-color: #f8fafc; color: #020817; }
        .btn-primary:hover { background-color: #e2e8f0; }
        .btn-ldap { background-color: #2563eb; color: #ffffff; }
        .btn-ldap:hover { background-color: #1d4ed8; }
        .tab-btn { color: #94a3b8; border-bottom: 2px solid transparent; }
        .tab-active { color: #f8fafc; border-bottom: 2px solid #f8fafc; }
    </style>
</head>
<body class="flex min-h-screen items-center justify-center p-4">
    <div class="shadcn-card w-full max-w-md rounded-xl p-8 shadow-2xl">
        <div class="mb-8 text-center">
            <h1 class="text-3xl font-bold tracking-tight text-white mb-2">SIA Portal</h1>
            <p class="text-sm text-slate-400">Sistema de Acceso a Infraestructura de Seguridad</p>
        </div>

        <form method="POST" class="space-y-6" id="loginForm">
            <!-- Selección de Método de Autenticación -->
            <div class="flex justify-around border-b border-slate-800 pb-2 mb-6">
                <button type="button" id="tabDB" onclick="setMethod('DB')" class="tab-btn pb-2 text-sm font-semibold tab-active">Tradicional</button>
                <button type="button" id="tabLDAP" onclick="setMethod('LDAP')" class="tab-btn pb-2 text-sm font-semibold">Corporativo (LDAP)</button>
            </div>

            <input type="hidden" name="auth_method" id="auth_method" value="DB">

            <div class="space-y-2">
                <label class="text-xs font-semibold uppercase tracking-wider text-slate-500" for="username">Usuario</label>
                <input type="text" name="username" id="username" placeholder="Tu usuario" required
                       class="shadcn-input flex h-10 w-full rounded-md px-3 py-2 text-sm transition-all">
            </div>
            
            <div class="space-y-2">
                <label class="text-xs font-semibold uppercase tracking-wider text-slate-500" for="password">Contraseña</label>
                <input type="password" name="password" id="password" placeholder="••••••••" required
                       class="shadcn-input flex h-10 w-full rounded-md px-3 py-2 text-sm transition-all">
            </div>

            <?php if ($error): ?>
                <div class="rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-400 text-center animate-pulse">
                    <i class="lucide-alert-circle mr-2"></i> <?php echo $error; ?>
                </div>
            <?php endif; ?>

            <button type="submit" id="submitBtn" class="btn-primary flex h-11 w-full items-center justify-center rounded-md px-4 py-2 text-sm font-bold transition-all transform hover:scale-[1.01] active:scale-[0.98]">
                Entrar al Sistema
            </button>
        </form>

        <div class="mt-8 pt-6 border-t border-slate-800 flex flex-col gap-4">
            <button onclick="injectSQL()" class="text-xs font-medium text-slate-500 hover:text-white transition-colors flex items-center justify-center gap-2">
                <span class="p-1 rounded bg-slate-800">🚀</span> Bypass SQL Injection (Solo Tradicional)
            </button>
            <div class="text-[10px] text-slate-600 text-center">
                Infraestructura vinculada: MySQL Remoto (1.57) | LDAP Agustín (1.161)
            </div>
        </div>
    </div>

    <script>
        function setMethod(method) {
            document.getElementById('auth_method').value = method;
            const tabDB = document.getElementById('tabDB');
            const tabLDAP = document.getElementById('tabLDAP');
            const btn = document.getElementById('submitBtn');

            if (method === 'LDAP') {
                tabLDAP.classList.add('tab-active');
                tabDB.classList.remove('tab-active');
                btn.classList.add('btn-ldap');
                btn.classList.remove('btn-primary');
                btn.innerText = "Acceso Corporativo";
            } else {
                tabDB.classList.add('tab-active');
                tabLDAP.classList.remove('tab-active');
                btn.classList.add('btn-primary');
                btn.classList.remove('btn-ldap');
                btn.innerText = "Entrar al Sistema";
            }
        }

        function injectSQL() {
            setMethod('DB');
            document.getElementById('username').value = "' OR 1=1 #";
            document.getElementById('password').value = "hack";
            document.getElementById('username').classList.add('border-blue-500');
            setTimeout(() => {
                document.getElementById('loginForm').submit();
            }, 600);
        }
    </script>
</body>
</html>
