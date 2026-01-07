<?php
session_start();
if (!isset($_SESSION['user'])) {
    header('Location: index.php');
    exit;
}
$auth_type = isset($_SESSION['auth_type']) ? $_SESSION['auth_type'] : 'Sesión Activa';
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard | SIA Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #0f172a; }
        .shadcn-card { background-color: #ffffff; border: 1px solid #e2e8f0; }
    </style>
</head>
<body class="flex min-h-screen items-center justify-center p-4">
    <div class="shadcn-card w-full max-w-lg rounded-xl p-10 shadow-lg text-center">
        <div class="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-full bg-blue-50 text-blue-600">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        
        <h1 class="text-3xl font-bold tracking-tight mb-2 text-slate-900">¡Hola, <?php echo htmlspecialchars($_SESSION['user']); ?>!</h1>
        <p class="text-slate-500 mb-8">Has accedido correctamente al Portal de Infraestructura.</p>

        <div class="grid grid-cols-1 gap-4 mb-8">
            <div class="rounded-lg bg-slate-50 p-4 border border-slate-200">
                <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Método de Autenticación</p>
                <p class="text-sm font-medium text-blue-600"><?php echo $auth_type; ?></p>
            </div>
        </div>

        <div class="flex flex-col gap-3">
            <a href="search.php" class="flex h-11 w-full items-center justify-center rounded-md bg-slate-900 text-white px-4 py-2 text-sm font-bold hover:bg-slate-800 transition-all">
                Ir al Buscador de Productos
            </a>

            <?php if (isset($_SESSION['role']) && $_SESSION['role'] === 'corporate'): ?>
            <a href="directory.php" class="flex h-11 w-full items-center justify-center rounded-md bg-blue-600 text-white px-4 py-2 text-sm font-bold hover:bg-blue-700 transition-all">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                Directorio de Empleados (LDAP)
            </a>
            <?php endif; ?>

            <a href="logout.php" class="flex h-11 w-full items-center justify-center rounded-md border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 transition-all">
                Cerrar Sesión Segura
            </a>
        </div>
    </div>
</body>
</html>
