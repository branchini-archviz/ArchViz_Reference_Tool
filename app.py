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

elif isinstance(st.session_state.selected_images, list):
    st.session_state.selected_images = {}


if "image_cache" not in st.session_state:
    st.session_state.image_cache = {}



# =========================
# MODELO IA
# =========================

@st.cache_resource
def load_ai_model():

    from transformers import (
        BlipProcessor,
        BlipForConditionalGeneration
    )

    processor = BlipProcessor.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )

    model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )

    return processor, model



def analyze_image(image):

    processor, model = load_ai_model()

    inputs = processor(
        image,
        return_tensors="pt"
    )

    output = model.generate(
        **inputs,
        max_new_tokens=30
    )

    description = processor.decode(
        output[0],
        skip_special_tokens=True
    )

    description = (
        "architectural project, "
        "house design, "
        "real building photography, "
        "architecture magazine, "
        + description
    )


    return description

    architecture_prompt = (
        "architectural photography, "
        "real built project, "
        "contemporary architecture, "
        "ArchDaily, Dezeen, "
        "professional architecture photographer, "
        "high quality architecture reference, "
    )


    final_query = (
        description
        +
        ", "
        +
        architecture_prompt
    )


    return final_query


# =========================
# BUSCADOR
# =========================

def search_images(query):

    results = []

    sites = [
        "archdaily.com",
        "dezeen.com",
        "divisare.com",
        "designboom.com",
        "world-architects.com"
    ]


    try:

        with DDGS() as ddgs:


            for site in sites:


                search_query = (
                    query
                    +
                    " architecture photography built project real photo site:"
                    +
                    site
                )


                images = ddgs.images(
                    query + " -cartoon -illustration -meme -quote",
                    max_results=30
                )


                results.extend(
                    images
                )


                if len(results) >= 30:
                    break



        return results[:30]


    except Exception:

        return []


    except Exception:

        return []



# =========================
# INTERFAZ BUSQUEDA
# =========================


st.title(
    "ArchViz Reference Finder"
)


uploaded_image = st.file_uploader(
    "📤 Subir imagen de referencia (opcional)",
    type=[
        "jpg",
        "jpeg",
        "png"
    ]
)


extra_info = st.text_area(
    "📝 Información adicional (opcional)",
    height=120,
    placeholder="""
Ej:
Casa minimalista costera.
Busco atmósfera editorial, cálida y materiales naturales.
Hormigón visto, vidrio y vegetación.
"""
)



if st.button(
    "🔍 Buscar referencias",
    use_container_width=True
):

    query = ""


    if uploaded_image:

        image = Image.open(
            uploaded_image
        )


        st.image(
            image,
            width=350
        )


        with st.spinner(
            "Analizando imagen..."
        ):

            query = analyze_image(
                image
            )


    if extra_info:

        query += " " + extra_info

    else:

        query += (
            ", architecture project, "
            "architectural photography"
        )



    if query:


        st.session_state.results = {}


        st.write(
            "Búsqueda generada:"
        )


        st.info(
            query
        )


        images = search_images(
            "architecture building project photography " + query
        )


        st.session_state.results[
            query
        ] = images

# =========================
# TABS PRINCIPALES
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


                url = result["image"]

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


                    st.session_state.image_cache[url] = Image.open(
                        BytesIO(response.content)
                    )


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


                    if url not in st.session_state.selected_images:

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
        "🗑️ Limpiar Moodboard",
        use_container_width=True
    ):


        st.session_state.selected_images = {}

        st.rerun()



    st.write(
        f"{len(st.session_state.selected_images)} imágenes"
    )



    mood_cols = st.columns(4)



    for idx, url in enumerate(
        st.session_state.selected_images.keys()
    ):


        try:


            img = st.session_state.image_cache[url]


            cell = mood_cols[idx % 4]



            remove = cell.button(
                "✕",
                key=f"remove_{idx}"
            )



            if remove:


                del st.session_state.selected_images[url]

                st.rerun()



            cell.image(
                img,
                use_container_width=True
            )



        except Exception:


            pass



    st.divider()


# =========================
# EXPORTAR MOODBOARD JPG
# =========================


if st.button(
    "🖼️ Exportar JPG",
    use_container_width=True
):


    if len(st.session_state.selected_images) > 0:



        cols = 4

        gap = 8

        thumb_width = 350


        column_heights = [
            0
        ] * cols


        processed_images = []



        for url, project_name in st.session_state.selected_images.items():


            try:


                img = st.session_state.image_cache[url]


                img_copy = img.copy().convert(
                    "RGB"
                )



                ratio = (
                    img_copy.height /
                    img_copy.width
                )



                new_height = int(
                    thumb_width * ratio
                )



                img_copy = img_copy.resize(
                    (
                        thumb_width,
                        new_height
                    )
                )



                draw = ImageDraw.Draw(
                    img_copy
                )



                try:


                    font = ImageFont.truetype(
                        "DejaVuSans.ttf",
                        18
                    )


                except:


                    font = ImageFont.load_default()



                text_position = (
                    15,
                    img_copy.height - 25
                )



                # sombra

                draw.text(
                    (
                        text_position[0] + 1,
                        text_position[1] + 1
                    ),
                    project_name,
                    fill="black",
                    font=font
                )



                # texto blanco

                draw.text(
                    text_position,
                    project_name,
                    fill="white",
                    font=font
                )



                processed_images.append(
                    img_copy
                )



            except Exception:


                pass




        board_width = (
            cols * thumb_width
            +
            (cols - 1) * gap
        )



        placements = []



        for img in processed_images:



            column = column_heights.index(
                min(column_heights)
            )



            x = column * (
                thumb_width + gap
            )



            y = column_heights[column]



            placements.append(
                (
                    img,
                    x,
                    y
                )
            )



            column_heights[column] += (
                img.height + gap
            )




        board_height = (
            max(column_heights)
            -
            gap
        )



        moodboard = Image.new(
            "RGB",
            (
                board_width,
                board_height
            ),
            "white"
        )



        for img, x, y in placements:


            moodboard.paste(
                img,
                (
                    x,
                    y
                )
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
