const API_BASE = 'http://127.0.0.1:5000/api';

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupUpload();
    setupAccept();
    loadImages();
    loadStats();
    
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadImages();
        loadStats();
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
            
            if (response.ok) {
                showToast('Carga completada');
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
    
    const confidence = (imgData.prediction.confidence * 100).toFixed(0);
    
    div.innerHTML = `
        <img src="${imgData.url}" alt="${imgData.filename}" draggable="false">
        <div class="conf-tag">${confidence}%</div>
        <div class="image-info" title="${imgData.filename}">${imgData.filename}</div>
    `;
    
    return div;
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();
        
        document.getElementById('stat-total').textContent = stats.total_indexed;
        document.getElementById('stat-real').textContent = stats.real;
        document.getElementById('stat-ia').textContent = stats.ia;
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
