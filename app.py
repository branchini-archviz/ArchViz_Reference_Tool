import streamlit as st
from duckduckgo_search import DDGS
import requests
from PIL import Image
from io import BytesIO


st.set_page_config(
    page_title="ArchViz Reference Finder",
    layout="wide"
)

st.title("ArchViz Reference Finder")

st.write(
    "Pegá proyectos con nombre y arquitecto"
)


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

    results=[]
try:
    with DDGS() as ddgs:
        images = ddgs.images(
            query,
            max_results=5
        )
        return images

    except Exception as e:
        return []



if st.button("Buscar referencias"):

    lista = projects.split("\n")

    for project in lista:

        if project.strip():

            st.divider()

            st.subheader(project)

            images = search_images(project)

            cols = st.columns(5)

            for i, url in enumerate(images):

                try:

                    response = requests.get(
                        url,
                        timeout=5
                    )

                    img = Image.open(
                        BytesIO(response.content)
                    )

                    cols[i].image(
                        img,
                        use_container_width=True
                    )

                    cols[i].checkbox(
                        "Guardar",
                        key=f"{project}_{i}"
                    )

                except:
                    pass
