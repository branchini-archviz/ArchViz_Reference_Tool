import streamlit as st
from ddgs import DDGS
import requests
from PIL import Image
from io import BytesIO
from PIL import Image, ImageOps, ImageDraw
import math
from PIL import ImageFont

st.set_page_config(
    page_title="ArchViz Reference Finder",
    layout="wide"
)


if "results" not in st.session_state:
    st.session_state.results = {}

if "selected_images" not in st.session_state:
    st.session_state.selected_images = {}

elif isinstance(st.session_state.selected_images, list):
    st.session_state.selected_images = {}

if "image_cache" not in st.session_state:
    st.session_state.image_cache = {}

projects = st.text_area(
    "Proyectos",
    height=200,
    placeholder=
    """
Costa Rica 4444 - Adamo Faiden
Bulnes 2467 - Bares McCormack
Casa Levels - Luciano Kruk
"""
)


def search_images(query):

    try:
        with DDGS() as ddgs:
            images = ddgs.images(
                query,
                max_results=10
            )
            return images

    except Exception as e:
        return []



if st.button("Buscar referencias"):

    lista = projects.split("\n")

    st.session_state.results = {}

    for project in lista:

        if project.strip():

            images = search_images(project)

            st.session_state.results[project] = images



# Layout principal

tab_refs, tab_moodboard = st.tabs(
    ["Referencias", "Moodboard"]
)


# =========================
# GALERÍA DE REFERENCIAS
# =========================

with tab_refs:

    for project, images in st.session_state.results.items():

        st.divider()

        st.subheader(project)

        cols = st.columns(3)

        for i, result in enumerate(images):

            col = cols[i % 3]

            try:

                url = result["image"]

                if url not in st.session_state.image_cache:

                    response = requests.get(
                        url,
                        timeout=5
                    )

                    st.session_state.image_cache[url] = Image.open(
                        BytesIO(response.content)
                    )

                img = st.session_state.image_cache[url]

                col.image(img)

                selected = col.checkbox(
                    project,
                    key=f"{project}_{i}"
                )

                if selected:

                    if url not in st.session_state.selected_images:
                        st.session_state.selected_images[url] = project

                else:

                    if url in st.session_state.selected_images:
                        del st.session_state.selected_images[url]

            except Exception:
                pass


# =========================
# PANEL MOODBOARD
# =========================

with tab_moodboard:

    st.subheader("Moodboard")

    st.write(
        f"{len(st.session_state.selected_images)} imágenes"
    )

    mood_cols = st.columns(4)

    for idx, url in enumerate(st.session_state.selected_images.keys()):

        try:

            img = st.session_state.image_cache[url]

            cell = mood_cols[idx % 4]

            remove = cell.button(
                "✕",
                key=f"remove_{idx}"
            )

            if remove:

                st.session_state.selected_images.remove(url)

                st.rerun()

            cell.image(
                img,
                use_container_width=True
            )

        except Exception:
            pass

    st.divider()

 
if st.button(
    "🖼️ Exportar JPG",
    use_container_width=True
):

    if len(st.session_state.selected_images) > 0:

        cols = 4

        gap = 8

        thumb_width = 350

        column_heights = [0] * cols

        processed_images = []

        for url, project_name in st.session_state.selected_images.items():

            try:

                img = st.session_state.image_cache[url]

                img_copy = img.copy().convert("RGB")

                draw = ImageDraw.Draw(img_copy)

                text = project_name

                font_size = 32

                try:
                    font = ImageFont.truetype(
                        "DejaVuSans.ttf",
                        font_size
                    )
                except:
                    font = ImageFont.load_default()

                text_position = (
                    20,
                    img_copy.height - 55
                )

                draw.text(
                    text_position,
                    text,
                    fill="white",
                    font=font
                )

                ratio = img_copy.height / img_copy.width

                new_height = int(
                    thumb_width * ratio
                )

                img_copy = img_copy.resize(
                    (thumb_width, new_height)
                )

                processed_images.append(img_copy)

            except Exception:
                pass


        board_width = cols * thumb_width + (cols - 1) * gap

        placements = []

        for img in processed_images:

            column = column_heights.index(
                min(column_heights)
            )

            x = column * (thumb_width + gap)

            y = column_heights[column]

            placements.append(
                (img, x, y)
            )

            column_heights[column] += img.height + gap


        board_height = max(column_heights) - gap

        moodboard = Image.new(
            "RGB",
            (board_width, board_height),
            "white"
        )

        for img, x, y in placements:

            moodboard.paste(
                img,
                (x, y)
            )


        output = BytesIO()

        moodboard.save(
            output,
            format="JPEG",
            quality=95
        )


        st.download_button(
            "⬇️ Descargar Moodboard JPG",
            data=output.getvalue(),
            file_name="moodboard.jpg",
            mime="image/jpeg",
            use_container_width=True
        )
st.write(
    f"Imágenes seleccionadas: {len(st.session_state.selected_images)}"
)
