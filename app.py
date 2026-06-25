import streamlit as st
from ddgs import DDGS
import requests

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json


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

            search_results = ddgs.text(
                query + " site:archdaily.com OR site:dezeen.com OR site:divisare.com",
                max_results=5
            )


        urls = []


        for item in search_results:

            url = item.get("href")

            if url:
                urls.append(url)



        for page_url in urls:


            try:


                response = requests.get(
                    page_url,
                    timeout=10,
                    headers={
                        "User-Agent":
                        "Mozilla/5.0"
                    }
                )


                soup = BeautifulSoup(
                    response.text,
                    "html.parser"
                )



                image_urls = []



                # 1 - OpenGraph

                og_images = soup.find_all(
                    "meta",
                    property="og:image"
                )


                for img in og_images:

                    content = img.get(
                        "content"
                    )

                    if content:

                        image_urls.append(
                            content
                        )



                # 2 - JSON-LD

                scripts = soup.find_all(
                    "script",
                    type="application/ld+json"
                )


                for script in scripts:

                    try:

                        data = json.loads(
                            script.string
                        )


                        if isinstance(
                            data,
                            dict
                        ):


                            img = data.get(
                                "image"
                            )


                            if isinstance(
                                img,
                                list
                            ):

                                image_urls.extend(
                                    img
                                )


                            elif img:

                                image_urls.append(
                                    img
                                )


                    except:

                        pass



                # 3 - srcset

                imgs = soup.find_all(
                    "img"
                )


                for img in imgs:


                    srcset = img.get(
                        "srcset"
                    )


                    if srcset:


                        first = srcset.split(",")[0]

                        image_urls.append(
                            first.split()[0]
                        )



                # Guardar resultados

                for img_url in image_urls:


                    img_url = urljoin(
                        page_url,
                        img_url
                    )


                    if img_url not in [
                        x["image"]
                        for x in results
                    ]:


                        results.append(
                            {
                                "image": img_url,
                                "title": query,
                                "url": page_url
                            }
                        )



                    if len(results) >= 30:

                        return results[:30]



            except Exception:

                pass



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
