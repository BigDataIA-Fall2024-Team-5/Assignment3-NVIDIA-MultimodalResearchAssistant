# streamlit_pages/grid_view.py

import streamlit as st
from streamlit_pages.utils import fetch_publications, fetch_image_url
import os

def show_grid_view(API_BASE_URL):
    """Displays a grid view of the available publications."""
    # Fetch the list of publications from the server
    publications = fetch_publications(API_BASE_URL)

    if publications:
        st.subheader("Explore Publications")
        st.markdown("Select a publication to view more details.")
        st.markdown("---")

        # Define the number of columns in the grid
        num_cols = 4  # Set to 4 columns per row for better alignment

        # Placeholder image path for publications without images
        placeholder_image_path = os.path.join("no-image-placeholder.png")

        # Loop through publications and display them in a grid format
        for idx, pub in enumerate(publications):
            if idx % num_cols == 0:
                # Create a new row for every `num_cols` publications
                cols = st.columns(num_cols)

            # Get the column for the current publication
            col = cols[idx % num_cols]

            with col:
                # Extract the file key including the folder path
                file_key = "/".join(pub['cover_image_link'].split('/')[-3:]) if pub.get('cover_image_link') else None
                image_url = fetch_image_url(API_BASE_URL, file_key) if file_key else placeholder_image_path

                # Verify if the fetched image URL is None or not working
                if not image_url or image_url == placeholder_image_path:
                    image_url = placeholder_image_path

                # Display the image with a fixed size and make it clickable
                if image_url == placeholder_image_path:
                    # Display placeholder image if actual image not available
                    col.image(image_url, use_column_width=False, width=150, caption=pub['title'])
                else:
                    # Create a clickable image using an anchor tag in Markdown
                    image_html = f"""
                    <a href="/?selected_pub_id={pub['id']}">
                        <img src="{image_url}" alt="{pub['title']}" style="width:150px; height:200px; border-radius: 8px; margin-bottom: 5px;">
                    </a>
                    """
                    # Display the clickable image using Markdown
                    col.markdown(image_html, unsafe_allow_html=True)

                # Display the publication title as a clickable button
                if col.button(pub['title'], key=f"btn_{pub['id']}"):
                    # When the button is clicked, update the session state and navigate to the detail view
                    st.session_state["selected_pub"] = pub
                    st.session_state["page"] = "detail_view"
                    st.rerun()

        st.markdown("---")

    # Check URL parameters for selected publication using st.query_params
    query_params = st.query_params  # Access query parameters using st.query_params dictionary-like interface
    selected_pub_id = query_params.get('selected_pub_id', [None])[0]

    if selected_pub_id:
        # Validate the selected publication based on the ID in the query parameters
        selected_pub = next((pub for pub in publications if str(pub['id']) == selected_pub_id), None)
        if selected_pub:
            # Update session state for the selected publication
            st.session_state["selected_pub"] = selected_pub
            st.session_state["page"] = "detail_view"

            # Clear the query parameters to avoid repetition by setting an empty dictionary
            st.query_params.clear()
            
            # Rerun to go to the detailed view
            st.rerun()