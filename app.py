import streamlit as st
import requests
import json

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from ddgs import DDGS


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

            pages = ddgs.text(
                query.replace("-", " ")
                + " ArchDaily OR Divisare OR Dezeen",
                max_results=10
            )


        for page in pages:


            url = page.get("href", "")


            if not url:
                continue


            # solo sitios de arquitectura

            if not any(
                site in url.lower()
                for site in [
                    "archdaily",
                    "divisare",
                    "dezeen",
                    "designboom",
                    "architizer"
                ]
            ):
                continue



            response = requests.get(
                url,
                headers={
                    "User-Agent":
                    "Mozilla/5.0"
                },
                timeout=10
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


                if src and src.startswith("http"):


                    results.append(
                        {
                            "image": src,
                            "title": page.get(
                                "title",
                                query
                            ),
                            "url": url
                        }
                    )


                if len(results) >= 20:
                    break



            if len(results) >= 20:
                break



        return results



    except Exception as e:

        st.error(e)

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
Casa Poli - Pezo von Ellrichshausen
Therme Vals - Peter Zumthor
Casa Gilardi - Luis Barragán
Casa Farnsworth - Mies van der Rohe
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
                    " architecture photography "
                    "built project "
                    "professional architectural photo"
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
# REFERENCIAS
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


        try:


            img = st.session_state.image_cache[url]


            cols[idx % 4].image(
                img,
                use_container_width=True
            )


        except Exception:

            pass




# =========================
# EXPORTAR JPG
# =========================


st.divider()


if st.button(
    "🖼️ Exportar Moodboard JPG",
    use_container_width=True
):


    if len(st.session_state.selected_images) > 0:


        thumb_width = 350

        gap = 10

        columns = 4


        processed = []


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


            processed.append(
                img
            )



        heights = [
            0
        ] * columns



        positions = []



        for img in processed:


            column = heights.index(
                min(heights)
            )


            x = column * (
                thumb_width + gap
            )


            y = heights[column]


            positions.append(
                (
                    img,
                    x,
                    y
                )
            )


            heights[column] += (
                img.height + gap
            )



        board = Image.new(
            "RGB",
            (
                columns * thumb_width +
                (columns - 1) * gap,
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
            file_name="moodboard.jpg",
            mime="image/jpeg",
            use_container_width=True
        )
