import streamlit as st
from ddgs import DDGS
import requests

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


st.set_page_config(
    page_title="ArchViz Reference Finder",
    layout="wide"
)


# =========================
# ESTADOS
# =========================

if "results" not in st.session_state:
    st.session_state.results = {}

if "selected_images" not in st.session_state:
    st.session_state.selected_images = {}

if "image_cache" not in st.session_state:
    st.session_state.image_cache = {}



# =========================
# BUSCADOR
# =========================


def search_images(query):

    results = []


    try:

        with DDGS() as ddgs:


            # Buscar páginas de proyectos reales
            search_results = ddgs.text(
                query + " architecture project ArchDaily Dezeen Divisare",
                max_results=5
            )


        urls = []


        for item in search_results:

            url = item.get(
                "href",
                ""
            )

            if url:

                urls.append(url)



        # Extraer imágenes de esas páginas

        for page_url in urls:


            try:

                response = requests.get(
                    page_url,
                    timeout=8,
                    headers={
                        "User-Agent":
                        "Mozilla/5.0"
                    }
                )


                soup = BeautifulSoup(
                    response.text,
                    "html.parser"
                )


                images = soup.find_all(
                    "img"
                )


                for img in images:


                    src = (
                        img.get("src")
                        or
                        img.get("data-src")
                    )


                    if src:


                        image_url = urljoin(
                            page_url,
                            src
                        )


                        # filtros básicos

                        if any(
                            x in image_url.lower()
                            for x in [
                                ".jpg",
                                ".jpeg",
                                ".png",
                                ".webp"
                            ]
                        ):


                            results.append(
                                {
                                    "image": image_url,
                                    "title": query,
                                    "url": page_url
                                }
                            )


                    if len(results) >= 30:

                        break



            except Exception:

                pass



            if len(results) >= 30:

                break



        return results[:30]



    except Exception:


        return []


# =========================
# INTERFAZ
# =========================


st.title(
    "🏛️ ArchViz Reference Finder"
)


projects_input = st.text_area(
    "Obras de arquitectura (una por línea)",
    height=160,
    placeholder="""
Ej:

Casa Poli - Pezo von Ellrichshausen
Casa Gilardi - Luis Barragán
Therme Vals - Peter Zumthor
Casa Corten - Estudio PKa
"""
)



extra_info = st.text_area(
    "Información adicional de búsqueda (opcional)",
    height=100,
    placeholder="""
Ej:
Busco fotografía exterior.
Atmósfera minimalista, luz cálida, editorial.
"""
)



if st.button(
    "🔍 Buscar referencias",
    use_container_width=True
):


    if projects_input:


        projects = projects_input.split("\n")


        st.session_state.results = {}


        for project in projects:


            project = project.strip()


            if project:


                query = (
                    project
                    +
                    ", architectural photography, "
                    "real built project, "
                    "professional architecture photographer, "
                    "high quality architecture image"
                )


                if extra_info:

                    query += (
                        ", "
                        +
                        extra_info
                    )


                images = search_images(
                    query
                )


                st.session_state.results[
                    project
                ] = images



# =========================
# TABS
# =========================


tab_refs, tab_moodboard = st.tabs(
    [
        "Referencias",
        "Moodboard"
    ]
)



# =========================
# GALERÍA
# =========================


with tab_refs:


    for project, images in st.session_state.results.items():


        st.divider()


        st.subheader(
            project
        )


        cols = st.columns(3)



        for i, result in enumerate(images):


            col = cols[i % 3]


            try:


                url = result.get(
                    "image",
                    ""
                )


                title = result.get(
                    "title",
                    project
                )


                link = result.get(
                    "url",
                    ""
                )



                if url not in st.session_state.image_cache:


                    response = requests.get(
                        url,
                        timeout=5
                    )


                    img = Image.open(
                        BytesIO(response.content)
                    )


                    st.session_state.image_cache[url] = img



                img = st.session_state.image_cache[url]



                col.image(
                    img,
                    use_container_width=True
                )


                col.caption(
                    title
                )


                if link:

                    col.write(
                        link
                    )



                selected = col.checkbox(
                    "Seleccionar",
                    key=f"{project}_{i}"
                )



                if selected:


                    st.session_state.selected_images[url] = project


                else:


                    if url in st.session_state.selected_images:

                        del st.session_state.selected_images[url]



            except Exception:

                pass



# =========================
# MOODBOARD
# =========================


with tab_moodboard:


    st.subheader(
        "Moodboard"
    )


    if st.button(
        "🗑️ Limpiar Moodboard"
    ):


        st.session_state.selected_images = {}

        st.rerun()



    st.write(
        f"Imágenes seleccionadas: {len(st.session_state.selected_images)}"
    )



    cols = st.columns(4)



    for idx, url in enumerate(
        st.session_state.selected_images.keys()
    ):


        img = st.session_state.image_cache[url]


        col = cols[idx % 4]


        col.image(
            img,
            use_container_width=True
        )



# =========================
# EXPORTAR JPG
# =========================


st.divider()


if st.button(
    "🖼️ Exportar Moodboard JPG",
    use_container_width=True
):


    if st.session_state.selected_images:


        thumb_width = 350

        gap = 10

        cols = 4


        images = []


        for url, project in st.session_state.selected_images.items():


            img = (
                st.session_state.image_cache[url]
                .copy()
                .convert("RGB")
            )


            ratio = img.height / img.width


            img = img.resize(
                (
                    thumb_width,
                    int(thumb_width * ratio)
                )
            )


            draw = ImageDraw.Draw(
                img
            )


            try:

                font = ImageFont.truetype(
                    "DejaVuSans.ttf",
                    18
                )

            except:

                font = ImageFont.load_default()



            draw.text(
                (
                    15,
                    img.height - 30
                ),
                project,
                fill="white",
                font=font
            )


            images.append(
                img
            )



        heights = [
            0
        ] * cols


        positions = []


        for img in images:


            col = heights.index(
                min(heights)
            )


            x = col * (
                thumb_width + gap
            )


            y = heights[col]


            positions.append(
                (
                    img,
                    x,
                    y
                )
            )


            heights[col] += (
                img.height + gap
            )



        board = Image.new(
            "RGB",
            (
                cols * thumb_width +
                (cols - 1) * gap,
                max(heights)
            ),
            "white"
        )



        for img, x, y in positions:


            board.paste(
                img,
                (
                    x,
                    y
                )
            )



        output = BytesIO()


        board.save(
            output,
            format="JPEG",
            quality=95
        )


        st.download_button(
            "⬇️ Descargar JPG",
            data=output.getvalue(),
            file_name="archviz_moodboard.jpg",
            mime="image/jpeg"
        )
