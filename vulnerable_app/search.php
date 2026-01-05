<?php
include 'db_setup.php';
$search = $_GET['q'] ?? '';
$results = [];

if ($search) {
    // VULNERABILIDAD: Inyección SQL en la búsqueda
    $query = "SELECT * FROM products WHERE name LIKE '%$search%' OR description LIKE '%$search%'";
    try {
        $stmt = $db->query($query);
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (Exception $e) {
        $error = "Error: " . $e->getMessage();
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search | SecureApp</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #020817; color: #f8fafc; }
        .shadcn-card { background-color: #020817; border: 1px solid #1e293b; }
        .shadcn-input { background-color: #020817; border: 1px solid #1e293b; color: #f8fafc; }
        .shadcn-input:focus { border-color: #3b82f6; outline: none; }
        .shadcn-primary { background-color: #f8fafc; color: #020817; }
        .shadcn-secondary { background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; }
    </style>
</head>
<body class="p-8">
    <div class="max-w-4xl mx-auto">
        <div class="flex items-center justify-between mb-8">
            <div>
                <h1 class="text-3xl font-bold tracking-tight text-white">Inventario de Productos</h1>
                <p class="text-slate-400 mt-2">Buscador interno de stock disponible.</p>
            </div>
            <a href="index.php" class="text-sm font-medium text-slate-400 hover:text-white transition-colors">Volver al Login →</a>
        </div>

        <div class="shadcn-card rounded-xl p-6 mb-8">
            <form method="GET" class="flex gap-4">
                <input type="text" name="q" value="<?php echo $search; ?>" 
                       class="shadcn-input flex-1 h-11 rounded-md px-4 py-2 text-sm"
                       placeholder="Buscar por nombre o descripción...">
                <button type="submit" class="shadcn-primary px-6 h-11 rounded-md text-sm font-semibold transition-colors">
                    Buscar
                </button>
            </form>
        </div>

        <?php if ($search): ?>
            <div class="mb-6">
                <p class="text-sm text-slate-400">Resultados para: <span class="text-blue-400 font-mono">"<?php echo $search; ?>"</span></p>
            </div>
            
            <div class="grid gap-4">
                <?php if (!empty($results)): ?>
                    <?php foreach ($results as $row): ?>
                        <div class="shadcn-card rounded-lg p-5 border-l-4 border-l-blue-500">
                            <h3 class="text-lg font-semibold text-white mb-2"><?php echo $row['name']; ?></h3>
                            <p class="text-sm text-slate-400"><?php echo $row['description']; ?></p>
                        </div>
                    <?php endforeach; ?>
                <?php else: ?>
                    <div class="text-center py-12 shadcn-card rounded-xl border-dashed border-2">
                        <p class="text-slate-500 italic">No se encontraron productos para tu búsqueda.</p>
                    </div>
                <?php endif; ?>
            </div>
        <?php endif; ?>

        <div class="mt-12 rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-6">
            <h3 class="flex items-center gap-2 text-sm font-semibold text-yellow-500 uppercase tracking-wider mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
                Laboratorio de Pruebas
            </h3>
            <div class="grid sm:grid-cols-2 gap-4 text-xs font-mono">
                <div class="space-y-2">
                    <p class="text-slate-500">Payload XSS Reflejado:</p>
                    <code class="block bg-slate-900 p-2 rounded border border-slate-800 text-blue-400 break-all cursor-pointer hover:bg-slate-800" onclick="navigator.clipboard.writeText(this.innerText)">
                        &lt;script&gt;alert('Reflected XSS')&lt;/script&gt;
                    </code>
                </div>
                <div class="space-y-2">
                    <p class="text-slate-500">SQLi Error-Based:</p>
                    <code class="block bg-slate-900 p-2 rounded border border-slate-800 text-green-400 break-all cursor-pointer hover:bg-slate-800" onclick="navigator.clipboard.writeText(this.innerText)">
                        ' UNION SELECT 1,username,password FROM users--
                    </code>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
