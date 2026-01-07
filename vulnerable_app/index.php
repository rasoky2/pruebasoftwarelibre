<?php
// Desactivar visualización de errores en producción
error_reporting(0);
ini_set('display_errors', 0);

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
            $_SESSION['role'] = 'corporate'; // Asignar rol corporativo
            $_SESSION['ldap_auth'] = true; // Marcar que la autenticación fue por LDAP
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
                $_SESSION['role'] = 'basic'; // Asignar rol básico
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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }
        
        .shadcn-card { 
            background-color: #ffffff; 
            border: 1px solid #e2e8f0; 
            color: #1e293b;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }
        
        .shadcn-input { 
            background-color: #f8fafc; 
            border: 1px solid #cbd5e1; 
            color: #1e293b; 
        }
        
        .shadcn-input:focus { 
            border-color: #667eea; 
            outline: none; 
            background-color: #ffffff;
        }
        
        .btn-primary { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff; 
        }
        
        .btn-primary:hover { 
            background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
        }
        
        .btn-ldap { 
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: #ffffff; 
        }
        
        .btn-ldap:hover { 
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        }
        
        .tab-btn { 
            color: #94a3b8; 
            border-bottom: 2px solid transparent; 
        }
        
        .tab-active { 
            color: #667eea; 
            border-bottom: 2px solid #667eea; 
        }
        
        .container-center {
            width: 100%;
            max-width: 28rem;
            margin: 0 auto;
        }
    </style>
</head>
<body>
    <div class="container-center">
        <div class="shadcn-card rounded-xl p-8">


        <div class="mb-8 text-center">
            <h1 class="text-3xl font-bold tracking-tight text-gray-800 mb-2">SIA Portal</h1>
            <p class="text-sm text-gray-600">Sistema de Acceso a Infraestructura de Seguridad</p>
        </div>

        <form method="POST" class="space-y-6" id="loginForm">
            <!-- Health Check Badges -->
            <div class="flex gap-2 justify-center mb-4">
                <?php if ($db_connection_error): ?>
                    <span class="inline-flex items-center rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700 border border-red-200" title="<?php echo $db_connection_error; ?>">
                        <span class="mr-1 h-1.5 w-1.5 rounded-full bg-red-500"></span> MySQL Offline
                    </span>
                <?php else: ?>
                    <span class="inline-flex items-center rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700 border border-green-200">
                        <span class="mr-1 h-1.5 w-1.5 rounded-full bg-green-500"></span> MySQL Online
                    </span>
                <?php endif; ?>

                <?php if (!$ldap_server_online): ?>
                    <span class="inline-flex items-center rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700 border border-red-200" title="<?php echo $ldap_connection_error; ?>">
                        <span class="mr-1 h-1.5 w-1.5 rounded-full bg-red-500"></span> LDAP Offline
                    </span>
                <?php else: ?>
                    <span class="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 border border-blue-200">
                        <span class="mr-1 h-1.5 w-1.5 rounded-full bg-blue-500"></span> LDAP Online
                    </span>
                <?php endif; ?>
            </div>

            <!-- Selección de Método de Autenticación -->
            <div class="flex justify-around border-b border-gray-200 pb-2 mb-6">
                <button type="button" id="tabDB" onclick="setMethod('DB')" class="tab-btn pb-2 text-sm font-semibold tab-active">Tradicional</button>
                <button type="button" id="tabLDAP" onclick="setMethod('LDAP')" class="tab-btn pb-2 text-sm font-semibold">Corporativo (LDAP)</button>
            </div>

            <input type="hidden" name="auth_method" id="auth_method" value="DB">

            <div class="space-y-2">
                <label class="text-xs font-semibold uppercase tracking-wider text-gray-600" for="username">Usuario</label>
                <input type="text" name="username" id="username" placeholder="Tu usuario" required
                       class="shadcn-input flex h-10 w-full rounded-md px-3 py-2 text-sm transition-all">
            </div>
            
            <div class="space-y-2">
                <label class="text-xs font-semibold uppercase tracking-wider text-gray-600" for="password">Contraseña</label>
                <input type="password" name="password" id="password" placeholder="••••••••" required
                       class="shadcn-input flex h-10 w-full rounded-md px-3 py-2 text-sm transition-all">
            </div>

            <?php if ($error): ?>
                <div class="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700 text-center">
                    <i class="lucide-alert-circle mr-2"></i> <?php echo $error; ?>
                </div>
            <?php endif; ?>

            <button type="submit" id="submitBtn" class="btn-primary flex h-11 w-full items-center justify-center rounded-md px-4 py-2 text-sm font-bold transition-all transform hover:scale-[1.01] active:scale-[0.98]">
                Entrar al Sistema
            </button>
        </form>

        <div class="mt-8 pt-6 border-t border-gray-200 flex flex-col gap-4">
            <button onclick="injectSQL()" class="text-xs font-medium text-gray-600 hover:text-gray-900 transition-colors flex items-center justify-center gap-2">
                <span class="p-1 rounded bg-gray-100">🚀</span> Bypass SQL Injection (Solo Tradicional)
            </button>
            <div class="text-[10px] text-gray-500 text-center">
                Infraestructura vinculada: MySQL Remoto (<?php echo $DB_HOST; ?>) | LDAP Corporativo (<?php echo $LDAP_HOST; ?>)
            </div>
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
