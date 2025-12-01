const API_BASE = 'http://127.0.0.1:5000/api';

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupUpload();
    setupAccept();
    loadImages();
    loadStats();
    setupConsole();
    
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadImages();
        loadStats();
    });

    document.getElementById('refresh-stats-btn').addEventListener('click', () => {
        loadStats();
        showToast('Estadísticas actualizadas');
    });
});

function setupTabs() {
    const tabs = document.querySelectorAll('.nav-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`${tab.dataset.tab}-tab`).classList.add('active');
        });
    });
}

function setupConsole() {
    const toggleBtn = document.getElementById('console-toggle-btn');
    const panel = document.getElementById('console-panel');
    const closeBtn = document.getElementById('close-console-btn');
    const copyLogsBtn = document.getElementById('copy-logs-btn');
    const logsContainer = document.getElementById('console-logs');
    const autoScrollCheckbox = document.getElementById('auto-scroll');
    
    toggleBtn.addEventListener('click', () => {
        panel.classList.toggle('hidden');
        if (!panel.classList.contains('hidden')) {
            fetchLogs();
        }
    });
    
    closeBtn.addEventListener('click', () => {
        panel.classList.add('hidden');
    });
    
    // Copy logs to clipboard
    copyLogsBtn.addEventListener('click', async () => {
        try {
            const response = await fetch(`${API_BASE}/logs`);
            const logs = await response.json();
            const logsText = logs.join('\n');
            
            await navigator.clipboard.writeText(logsText);
            showToast('✅ Logs copiados al portapapeles');
        } catch (error) {
            console.error('Error copying logs:', error);
            showToast('❌ Error al copiar logs');
        }
    });
    
    // Poll logs every 2 seconds
    setInterval(fetchLogs, 2000);
    
    async function fetchLogs() {
        if (panel.classList.contains('hidden')) return;
        
        try {
            const response = await fetch(`${API_BASE}/logs`);
            const logs = await response.json();
            
            // Clear and rebuild (simple approach, could be optimized)
            logsContainer.innerHTML = '';
            logs.forEach(log => {
                const div = document.createElement('div');
                div.className = 'log-entry';
                
                if (log.includes('[ERROR]')) div.classList.add('error');
                else if (log.includes('[WARNING]')) div.classList.add('warning');
                else div.classList.add('info');
                
                div.textContent = log;
                logsContainer.appendChild(div);
            });
            
            if (autoScrollCheckbox.checked) {
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
        } catch (error) {
            console.error('Error fetching logs:', error);
        }
    }
}

function setupUpload() {
    const btn = document.getElementById('upload-btn');
    const input = document.getElementById('file-upload');
    
    btn.addEventListener('click', () => input.click());
    
    input.addEventListener('change', async () => {
        if (input.files.length === 0) return;
        
        const formData = new FormData();
        for (let i = 0; i < input.files.length; i++) {
            formData.append('files[]', input.files[i]);
        }
        
        showToast('Subiendo imágenes...');
        
        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showToast(`Carga completada: ${data.files.length} archivos`);
                if (data.errors && data.errors.length > 0) {
                    console.error("Upload errors:", data.errors);
                    showToast(`Hubo ${data.errors.length} errores (ver consola)`);
                }
                loadImages();
            } else {
                showToast('Error en la carga');
            }
        } catch (error) {
            console.error(error);
            showToast('Error de conexión');
        }
        
        input.value = ''; // Reset
    });
}

function setupAccept() {
    document.getElementById('accept-btn').addEventListener('click', async () => {
        const items = [];
        
        // Gather items from IA column
        document.querySelectorAll('#list-ia .image-item').forEach(el => {
            items.push({ filename: el.dataset.filename, label: 'ia' });
        });
        
        // Gather items from Real column
        document.querySelectorAll('#list-real .image-item').forEach(el => {
            items.push({ filename: el.dataset.filename, label: 'real' });
        });
        
        if (items.length === 0) {
            showToast('No hay imágenes para aceptar');
            return;
        }
        
        if (!confirm(`¿Aceptar ${items.length} clasificaciones?`)) return;
        
        showToast('Procesando...');
        
        try {
            const response = await fetch(`${API_BASE}/accept`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items })
            });
            
            if (response.ok) {
                const data = await response.json();
                showToast(`Procesado: ${data.stats.real} Real, ${data.stats.ia} IA`);
                loadImages();
                loadStats();
            } else {
                showToast('Error al procesar');
            }
        } catch (error) {
            console.error(error);
            showToast('Error de conexión');
        }
    });
}

async function loadImages() {
    const listIA = document.getElementById('list-ia');
    const listReal = document.getElementById('list-real');
    
    listIA.innerHTML = '<div class="loading">Cargando...</div>';
    listReal.innerHTML = '<div class="loading">Cargando...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/images`);
        const images = await response.json();
        
        listIA.innerHTML = '';
        listReal.innerHTML = '';
        
        let countIA = 0;
        let countReal = 0;
        
        images.forEach(img => {
            const el = createImageElement(img);
            if (img.prediction.label === 'ia') {
                listIA.appendChild(el);
                countIA++;
            } else {
                listReal.appendChild(el);
                countReal++;
            }
        });
        
        document.getElementById('count-ia').textContent = countIA;
        document.getElementById('count-real').textContent = countReal;
        
    } catch (error) {
        console.error('Error loading images:', error);
        listIA.innerHTML = 'Error';
        listReal.innerHTML = 'Error';
    }
}

function createImageElement(imgData) {
    const div = document.createElement('div');
    div.className = 'image-item';
    div.draggable = true;
    div.dataset.filename = imgData.filename;
    div.ondragstart = drag;
    
    const confidence = imgData.prediction === "Error" ? "Err" : (imgData.prediction.confidence * 100).toFixed(0) + "%";
    
    div.innerHTML = `
        <img src="${imgData.url}" alt="${imgData.filename}" draggable="false">
        <div class="conf-tag">${confidence}</div>
        <div class="image-info" title="${imgData.filename}">${imgData.filename}</div>
        <button class="remove-btn" title="Eliminar de la cola" onclick="removeImage('${imgData.filename}')">×</button>
    `;
    
    return div;
}

// Remove image from classification queue
async function removeImage(filename) {
    if (!confirm(`¿Eliminar "${filename}" de la cola de clasificación?`)) return;
    
    try {
        const response = await fetch(`${API_BASE}/remove`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        
        if (response.ok) {
            showToast(`✅ "${filename}" eliminada`);
            loadImages();
        } else {
            const data = await response.json();
            showToast(`❌ Error: ${data.error || 'No se pudo eliminar'}`);
        }
    } catch (error) {
        console.error('Error removing image:', error);
        showToast('❌ Error de conexión');
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();
        
        document.getElementById('stat-base-real').textContent = stats.dataset_base_real;
        document.getElementById('stat-base-ia').textContent = stats.dataset_base_ia;
        document.getElementById('stat-class-real').textContent = stats.clasificaciones_real;
        document.getElementById('stat-class-ia').textContent = stats.clasificaciones_ia;
        document.getElementById('stat-total-learned').textContent = stats.total_learned;
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Drag and Drop Logic
function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.dataset.filename);
    ev.target.classList.add('dragging');
}

function allowDrop(ev) {
    ev.preventDefault();
}

function drop(ev, targetCol) {
    ev.preventDefault();
    const filename = ev.dataTransfer.getData("text");
    const draggedEl = document.querySelector(`.image-item[data-filename="${filename}"]`);
    
    if (draggedEl) {
        draggedEl.classList.remove('dragging');
        
        // Determine target container
        const targetListId = targetCol === 'ia' ? 'list-ia' : 'list-real';
        const targetList = document.getElementById(targetListId);
        
        targetList.appendChild(draggedEl);
        
        updateCounts();
    }
}

function updateCounts() {
    document.getElementById('count-ia').textContent = document.getElementById('list-ia').children.length;
    document.getElementById('count-real').textContent = document.getElementById('list-real').children.length;
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.remove('hidden');
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}
