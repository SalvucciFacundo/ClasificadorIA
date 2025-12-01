# Estructura del Clasificador IA - Versión Optimizada

## 📁 Estructura de Carpetas

```
ClasificadorIA/
│
├── ClasificadorIA.exe          # Ejecutable compilado (NO contiene UI ni lógica)
│
├── ui/                         # ⚡ Interfaz de usuario (EXTERNA)
│   ├── index.html             # Página principal
│   ├── styles.css             # Estilos
│   └── app.js                 # Lógica del frontend
│
├── logic/                      # ⚡ Módulos Python (EXTERNOS)
│   ├── data_manager.py        # Gestión de datos
│   └── model_manager.py       # Gestión del modelo ML
│
├── modelo/                     # Modelos entrenados
│   └── modelo_actual.pth      # Modelo PyTorch
│
├── entrada/                    # Imágenes a clasificar
├── clasificaciones/            # Imágenes clasificadas
│   ├── ia/                    # Clasificadas como IA
│   └── real/                  # Clasificadas como reales
│
├── dataset_base/               # Dataset de entrenamiento
│   ├── ia/
│   └── real/
│
├── index/                      # Índices y metadatos
│   └── index.json
│
└── logs/                       # Registros del sistema
```

## 🚀 Ventajas de esta Estructura

### 1. **Sin Recompilación para Cambios de UI**

- Modifica `ui/index.html`, `ui/styles.css` o `ui/app.js`
- Reinicia el programa
- ✅ Los cambios se reflejan inmediatamente

### 2. **Sin Recompilación para Cambios de Lógica**

- Modifica `logic/data_manager.py` o `logic/model_manager.py`
- Reinicia el programa
- ✅ Los cambios se reflejan inmediatamente

### 3. **Desarrollo Rápido**

- Iteración rápida durante el desarrollo

````

En este modo:

- Los cambios en `ui/` se reflejan al recargar el navegador
- Los cambios en `logic/` requieren reiniciar el script
- Más rápido para desarrollo iterativo

## 📝 Notas Importantes

1. **Carpetas Requeridas**: El .exe espera encontrar `ui/` y `logic/` en el mismo directorio
2. **Fallback**: Si no encuentra `ui/`, busca `interfaz/` (modo desarrollo)
3. **Logs**: Revisa la consola para mensajes de carga de módulos
4. **Debug Mode**: En modo desarrollo (script), se activan las dev tools del navegador

## ⚠️ Troubleshooting

### "Archivo de interfaz no encontrado"

- Verifica que existe la carpeta `ui/` junto al .exe
- Verifica que contiene `index.html`, `styles.css`, `app.js`

### "Error cargando módulo externo"

- Verifica que existe la carpeta `logic/` junto al .exe
- Verifica que contiene `data_manager.py` y `model_manager.py`
- Revisa los logs en consola para detalles del error

### El programa no inicia

- Ejecuta desde consola para ver mensajes de error:
  ```bash
  ClasificadorIA.exe
````
