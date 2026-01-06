<?php
/**
 * BUSCADOR PROTEGIDO CON INTERBLOQUEO LDAP-DB
 */
require_once 'config.php'; // Esto ya maneja la sesión y las credenciales protegidas

// CORTE DE SEGURIDAD: Solo usuarios con ticket LDAP o rol básico
if (!isset($_SESSION['user'])) {
    die("<div style='color:red; font-family:sans-serif; padding:20px; border:1px solid red;'>
            <h2>🚫 Acceso Denegado</h2>
            <p>Debes iniciar sesión para acceder al buscador.</p>
            <a href='index.php'>Ir al Login</a>
         </div>");
}

$search = isset($_GET['q']) ? $_GET['q'] : '';

// Intentar conexión con las credenciales que config.php nos entregó
$conn = new mysqli($DB_HOST, $DB_USER, $DB_PASS, $DB_NAME, $DB_PORT);

if ($conn->connect_error) {
    if (!isset($is_authorized) || !$is_authorized) {
        die("<div style='background:#fef2f2; border:1px solid #fee2e2; padding:2rem; border-radius:1rem; margin-top:2rem; font-family:sans-serif;'>
                <h2 style='color:#991b1b; margin-top:0;'>🔒 SISTEMA BLOQUEADO</h2>
                <p style='color:#b91c1c;'>No tienes una sesión de LDAP activa que te permita acceder a la Base de Datos.</p>
                <p style='color:#7f1d1d; font-size:0.875rem;'>Por favor, vuelve al login y selecciona 'Corporativo (LDAP)'.</p>
                <a href='index.php' style='display:inline-block; margin-top:1rem; padding:0.5rem 1rem; background:#991b1b; color:white; border-radius:0.5rem; text-decoration:none;'>Volver al Login</a>
             </div>");
    }
}

// Lógica de búsqueda VULNERABLE (SQL Injection intencional para el lab)
$sql = "SELECT * FROM products WHERE name LIKE '%$search%' OR description LIKE '%$search%'";
$result = $conn->query($sql);

// No cerramos PHP aquí para que las variables existan abajo
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buscador de Productos | Light Store</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #fafafa;
            color: #171717;
        }
        .search-container {
            background: white;
            border-bottom: 1px solid #e5e5e5;
        }
        .product-card {
            background: white;
            border: 1px solid #e5e5e5;
            transition: all 0.2s ease;
        }
        .product-card:hover {
            border-color: #a3a3a3;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }
    </style>
</head>
<body class="min-h-screen">
    
    <!-- Header / Search Bar -->
    <header class="search-container sticky top-0 z-50 py-6">
        <div class="container mx-auto px-4 max-w-4xl">
            <div class="flex items-center justify-between mb-8">
                <div class="flex items-center gap-2">
                    <i data-lucide="shopping-bag" class="text-blue-600 h-6 w-6"></i>
                    <h1 class="text-xl font-bold tracking-tight">Light Store</h1>
                </div>
                <div class="flex items-center gap-4">
                    <span class="text-xs text-slate-400">Usuario: <span class="font-bold text-slate-700"><?php echo htmlspecialchars($_SESSION['user']); ?></span></span>
                    <a href="logout.php" class="text-sm font-medium text-slate-500 hover:text-slate-900 flex items-center gap-1">
                        <i data-lucide="log-out" class="h-4 w-4"></i> Salir
                    </a>
                </div>
            </div>

            <form action="search.php" method="GET" class="relative group">
                <input 
                    type="text" 
                    name="q" 
                    placeholder="Buscar productos (ej: Laptop, Teclado...)" 
                    value="<?php echo htmlspecialchars($search); ?>"
                    class="w-full h-14 pl-12 pr-4 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                >
                <i data-lucide="search" class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5"></i>
                <button type="submit" class="absolute right-3 top-1/2 -translate-y-1/2 px-4 py-2 bg-slate-900 text-white text-xs font-semibold rounded-lg hover:bg-slate-800 transition-colors">
                    Buscar
                </button>
            </form>
            
            <?php if ($search): ?>
                <p class="text-xs text-slate-400 mt-4">
                    Resultados para: <span class="text-slate-900 font-medium font-mono text-xs">"<?php echo htmlspecialchars($search); ?>"</span>
                </p>
            <?php endif; ?>
        </div>
    </header>

    <!-- Content -->
    <main class="container mx-auto py-12 px-4 max-w-4xl">
        <div class="grid gap-6 md:grid-cols-2">
            <?php 
            if ($result && $result->num_rows > 0) {
                while($row = $result->fetch_assoc()) {
                    ?>
                    <div class="product-card p-6 rounded-2xl flex flex-col gap-4">
                        <div class="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center">
                            <i data-lucide="box" class="text-slate-400 h-6 w-6"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-slate-900 mb-1"><?php echo htmlspecialchars($row['name']); ?></h3>
                            <p class="text-sm text-slate-500 leading-relaxed"><?php echo htmlspecialchars($row['description']); ?></p>
                        </div>
                        <div class="mt-auto pt-4 flex items-center justify-between">
                            <span class="text-xs font-bold text-blue-600 uppercase tracking-widest">En Stock</span>
                            <span class="text-sm font-bold text-slate-900">$<?php echo isset($row['price']) ? $row['price'] : '0.00'; ?></span>
                        </div>
                    </div>
                    <?php
                }
            } else {
                ?>
                <div class="col-span-full py-20 text-center">
                    <div class="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i data-lucide="search-x" class="text-slate-400 h-10 w-10"></i>
                    </div>
                    <h3 class="text-lg font-bold text-slate-900">No se encontraron productos</h3>
                    <p class="text-sm text-slate-500">Intenta con otros términos como "Laptop" o "Monitor".</p>
                </div>
                <?php
            }
            ?>
        </div>

        <!-- Debug Info (Opcional para el lab) -->
        <div class="mt-20 pt-10 border-t border-dashed border-slate-200">
            <p class="text-[10px] text-slate-300 font-mono italic">Lab Debug: Vulnerable Query</p>
            <p class="text-[10px] text-slate-400 font-mono bg-slate-50 p-2 mt-1 rounded border border-slate-100">
                <?php echo isset($sql) ? $sql : 'No query generated'; ?>
            </p>
        </div>
    </main>

    <script>
        lucide.createIcons();
    </script>
</body>
</html>
<?php 
if (isset($conn) && $conn) {
    $conn->close();
}
?>
