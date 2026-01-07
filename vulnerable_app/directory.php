<?php
/**
 * DIRECTORIO CORPORATIVO DE EMPLEADOS
 * Solo accesible para usuarios con rol 'corporate' (Autenticados vía LDAP)
 */
session_start();
require_once 'auth_ldap.php';

// Control de Acceso Estricto
if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'corporate') {
    header("Location: welcome.php");
    exit;
}

$query = isset($_GET['q']) ? $_GET['q'] : '';
$results = [];
$count = 0;

if ($query) {
    // La función es vulnerable a inyección LDAP intencionalmente
    $entries = buscar_usuarios_ldap($query);
    if ($entries && isset($entries['count'])) {
        $count = $entries['count'];
        $results = $entries;
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Directorio Corporativo | SIA Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #0f172a; }
        .shadcn-card { background-color: #ffffff; border: 1px solid #e2e8f0; }
        .btn-primary { background-color: #0f172a; color: white; }
        .btn-primary:hover { background-color: #1e293b; }
    </style>
</head>
<body class="min-h-screen p-8">
    <div class="max-w-4xl mx-auto space-y-6">
        
        <!-- Header -->
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-2xl font-bold tracking-tight text-slate-900">Directorio de Empleados</h1>
                <p class="text-slate-500">Búsqueda interna en servidor LDAP (<?php echo $LDAP_HOST; ?>)</p>
            </div>
            <a href="welcome.php" class="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors">
                <i data-lucide="arrow-left" class="h-4 w-4"></i> Volver al Dashboard
            </a>
        </div>

        <!-- Search Bar -->
        <div class="shadcn-card rounded-xl p-6 shadow-sm">
            <form method="GET" class="flex gap-4">
                <div class="relative flex-1">
                    <i data-lucide="search" class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400"></i>
                    <input type="text" name="q" value="<?php echo htmlspecialchars($query); ?>" 
                           placeholder="Buscar por nombre, usuario o email..." 
                           class="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 pl-10 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:border-transparent transition-all">
                </div>
                <button type="submit" class="btn-primary inline-flex h-10 items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 disabled:pointer-events-none disabled:opacity-50">
                    Buscar LDAP
                </button>
            </form>
        </div>

        <!-- Results -->
        <?php if ($query): ?>
            <div class="space-y-4">
                <h3 class="text-sm font-medium text-slate-500 uppercase tracking-wider">
                    Resultados encontrados: <span class="text-slate-900"><?php echo $count; ?></span>
                </h3>

                <?php if ($count > 0): ?>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <?php for ($i = 0; $i < $count; $i++): ?>
                            <?php 
                                $entry = $results[$i];
                                $cn = isset($entry['cn'][0]) ? $entry['cn'][0] : 'Desconocido';
                                $uid = isset($entry['uid'][0]) ? $entry['uid'][0] : 'N/A';
                                $mail = isset($entry['mail'][0]) ? $entry['mail'][0] : 'Sin email';
                                $dn = isset($entry['dn']) ? $entry['dn'] : '';
                            ?>
                            <div class="shadcn-card rounded-lg p-4 hover:shadow-md transition-shadow">
                                <div class="flex items-start justify-between">
                                    <div class="flex items-center gap-3">
                                        <div class="h-10 w-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-sm border border-blue-100">
                                            <?php echo strtoupper(substr($cn, 0, 2)); ?>
                                        </div>
                                        <div>
                                            <h4 class="font-bold text-slate-900 text-sm"><?php echo htmlspecialchars($cn); ?></h4>
                                            <p class="text-xs text-slate-500 font-mono"><?php echo htmlspecialchars($uid); ?></p>
                                        </div>
                                    </div>
                                    <span class="inline-flex items-center rounded-full border border-slate-200 px-2.5 py-0.5 text-xs font-semibold text-slate-500">
                                        LDAP
                                    </span>
                                </div>
                                
                                <div class="mt-4 space-y-2">
                                    <div class="flex items-center gap-2 text-xs text-slate-600">
                                        <i data-lucide="mail" class="h-3 w-3 text-slate-400"></i>
                                        <?php echo htmlspecialchars($mail); ?>
                                    </div>
                                    <div class="flex items-center gap-2 text-xs text-slate-600 truncate" title="<?php echo htmlspecialchars($dn); ?>">
                                        <i data-lucide="database" class="h-3 w-3 text-slate-400"></i>
                                        <span class="truncate max-w-[200px]"><?php echo htmlspecialchars($dn); ?></span>
                                    </div>
                                </div>
                            </div>
                        <?php endfor; ?>
                    </div>
                <?php else: ?>
                    <div class="rounded-lg border border-dashed border-slate-300 p-8 text-center text-slate-500">
                        No se encontraron empleados con ese criterio.
                    </div>
                <?php endif; ?>
            </div>
        <?php endif; ?>
    </div>
    <script>
        lucide.createIcons();
    </script>
</body>
</html>
