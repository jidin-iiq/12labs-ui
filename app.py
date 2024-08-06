import streamlit as st
import random
import time

# Hardcoded Instagram reel URLs for mocking
INSTAGRAM_REELS = [
    "https://www.instagram.com/reel/CsLJc_FohZP",
    "https://www.instagram.com/reel/CsJlNfGNLKA",
    "https://www.instagram.com/reel/CsIt71GJFwL",
    "https://www.instagram.com/reel/CsBifwoo9cH",
    "https://www.instagram.com/reel/Cr7spd1ok8y",
    "https://www.instagram.com/reel/CrySYwnIXmS",
    "https://www.instagram.com/reel/CrprD5OoSdV",
    "https://www.instagram.com/reel/CriIvv1Ii-B",
    "https://www.instagram.com/reel/Cra3g_5I1h8",
    "https://www.instagram.com/reel/CrXpk68I5wi",
    "https://www.instagram.com/reel/CrVEtiEI6z7",
    "https://www.instagram.com/reel/CrSf7WBofqh",
    "https://www.instagram.com/reel/CrQ5bhMI3I3",
    "https://www.instagram.com/reel/CrQkplSItMO",
    "https://www.instagram.com/reel/CrQCJ6kIwqb",
    "https://www.instagram.com/reel/CrObDqrK8PW",
    "https://www.instagram.com/reel/CrI_cr0sRHU",
    "https://www.instagram.com/reel/CrAtdj6okFU",
    "https://www.instagram.com/reel/Cq-3JaYow0Z",
    "https://www.instagram.com/reel/Cq-i0m_ofxf",
    "https://www.instagram.com/reel/Cq-ER15qGO_",
    "https://www.instagram.com/reel/Cq5u7DdIpkV",
    "https://www.instagram.com/reel/Cq5aNhEoRcu",
    "https://www.instagram.com/reel/Cq4wxX9IRas",
    "https://www.instagram.com/reel/CqsdzY4I1MG",
    "https://www.instagram.com/reel/CqnQzYNovV9",
    "https://www.instagram.com/reel/Cqk4QVeIw8Y",
    "https://www.instagram.com/reel/Cqkg5O-oJtN",
    "https://www.instagram.com/reel/Cqh5IAgIaaa",
    "https://www.instagram.com/reel/CqPlCsKIWf3",
    "https://www.instagram.com/reel/CqNARalpPkk",
    "https://www.instagram.com/reel/CqKh6ZBIg8z",
    "https://www.instagram.com/reel/Cp7tESUIcuw",
    "https://www.instagram.com/reel/Cp5IwwZoL05",
    "https://www.instagram.com/reel/Cp2OzEHo9Dp",
    "https://www.instagram.com/reel/Cpr3BoaLajB"
]

# Function to fetch Instagram Reels data (mocked)
def fetch_data_mock(handle, video_type):
    random_count = random.randint(5, 35)
    return INSTAGRAM_REELS[:random_count]

# Function to mock the query and return random results
def query_mock(query_text):
    random_count = random.randint(5, 35)
    results = [{"url": INSTAGRAM_REELS[i]} for i in range(random_count)]
    return results

# Streamlit app
def main():
    st.title("Phyllo <> Twelve Labs")

    video_type = st.selectbox("Select Video Type", ["GRWM", "Unboxing", "Fitness", "Gaming", "Travel"])

    if "videos" not in st.session_state:
        st.session_state.videos = None

    if "results" not in st.session_state:
        st.session_state.results = None

    if st.session_state.videos is None:
        # Step 1: Take Instagram handle input
        handle = st.text_input("Enter Instagram hashtag/keyword/mention:")
        if st.button("Fetch Videos"):
            if handle:
                with st.spinner("Fetching data using Phyllo API..."):
                    time.sleep(15)
                    st.session_state.videos = fetch_data_mock(handle, video_type)
                st.success("Data fetched successfully!")

    if st.session_state.videos is not None and st.session_state.results is None:
        # Step 2: Take search query input
        query_text = st.text_input("Enter search query:")
        if st.button("Search"):
            if query_text:
                with st.spinner("Searching the indexed videos..."):
                    st.session_state.results = query_mock(query_text)
                st.success("Search completed successfully!")
            else:
                st.warning("Please enter a search query.")

    if st.session_state.results is not None:
        # Step 3: Display search results
        if st.session_state.results:
            st.write(f"Found {len(st.session_state.results)} videos")
            for result in st.session_state.results:
                # Display the Instagram reel using an iframe
                st.markdown(
                    f'<iframe src="https://www.instagram.com/p/{result["url"].split("/")[-1]}/embed" width="400" height="480" frameborder="0" scrolling="no" allowtransparency="true"></iframe>',
                    unsafe_allow_html=True
                )
        else:
            st.warning("No results found.")

if __name__ == "__main__":
    main()
