# Matriz general IPP

Aplicación para consultar la matriz de materias IPP con la lógica de limpieza pedida:

- Filas originales conservadas.
- Materias ordenadas alfabéticamente.
- Si una materia tiene varias filas, se muestran juntas sin mezclar su información.
- Filtros aplicados sobre las filas originales.
- Descarga de la matriz limpia y de la vista filtrada.
- ABM de filas de materias en el navegador, con exportación CSV.

## ABM

La página `ABM` permite agregar, editar y eliminar filas de materias. En esta versión estática para Netlify, los cambios se guardan en el navegador de quien usa la app mediante almacenamiento local. Para compartir una base editada entre varias personas, exportá la matriz editada en CSV o conectá una base de datos.

## Versión para Netlify

Netlify publica la carpeta `public/`. El sitio estático ya incluye los datos generados:

- `public/data/matriz.json`
- `public/Matriz limpia.xlsx`

## Deploy gratis en Netlify

1. Subir este repo a GitHub.
2. En Netlify, elegir `Add new site` y conectar el repositorio.
3. Configurar:
   - Build command: dejar vacío
   - Publish directory: `public`
4. Deploy.

También podés dejar que Netlify lea directamente `netlify.toml`, que ya tiene esa configuración.

## Uso local Streamlit

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Generar datos estáticos localmente

```bash
python scripts/build_static_data.py
```

Ejecutá ese comando cuando cambie el Excel fuente y quieras actualizar los datos publicados.
