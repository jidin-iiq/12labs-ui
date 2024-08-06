import streamlit as st
import requests
import os
import asyncio
import nest_asyncio
from glob import glob
from twelvelabs import TwelveLabs
from twelvelabs.models.task import Task
from moviepy.editor import VideoFileClip
from datetime import datetime

# Ensure asyncio event loop compatibility with Streamlit
nest_asyncio.apply()

# Function to fetch Instagram Reels data
def fetch_data(handle, offset=0):
    url = "https://api.insightiq.ai/v1/social/creators/contents/fetch"
    payload = {
        "profile_url": f"https://www.instagram.com/{handle}/",
        "work_platform_id": "9bb8913b-ddd9-430b-a66a-d74d846e6c66",
        "content_type": "REELS",
        "offset": offset
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": st.secrets["INSIGHTIQ_API_KEY"]
    }
    
    response = requests.post(url, json=payload, headers=headers).json()
    videos = []
    while len(videos) < 2:
        if 'data' in response:
            content_list = response['data']
            for content in content_list:
                videos.append([content['url'], content['media_url']])
            payload["offset"] += len(videos) - payload["offset"]
            response = requests.post(url, json=payload, headers=headers).json()
        else:
            return videos
    return videos

# Function to download video files
def download_video(url, file_name, folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    file_path = os.path.join(folder_name, file_name)
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"Download complete: {file_path}")
    else:
        print(f"Failed to download video from {url}")

# Function to save video segments
def save_video_segment(file_path, start_time, end_time):
    clip = VideoFileClip(file_path).subclip(start_time, end_time)
    temp_file_path = "temp_video_segment.mp4"
    clip.write_videofile(temp_file_path, codec="libx264")
    return temp_file_path

# Function to create an index in Twelve Labs
def create_index():
    client = TwelveLabs(api_key=st.secrets["TWELVE_LABS_API_KEY"])
    index_name = f"instagram_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    index = client.index.create(
        name=index_name,
        engines=[
            {
                "name": "marengo2.6",
                "options": ["visual", "conversation", "text_in_video"],
            }
        ],
        addons=["thumbnail"], 
    )
    print(f"Created index: id={index.id} name={index.name} engines={index.engines}")
    return index

# Asynchronous function to upload video files to Twelve Labs
async def upload_video(video, index):
    client = TwelveLabs(api_key=st.secrets["TWELVE_LABS_API_KEY"])
    dicts = {}
    fname = video
    print(f"Uploading {fname}")
    try:
        task = await asyncio.to_thread(client.task.create, index_id=index.id, file=fname, language="en")
        print(f"Created task: id={task.id}")

        def on_task_update(task: Task):
            print(f"  Status={task.status}")

        await asyncio.to_thread(task.wait_for_done, sleep_interval=30, callback=on_task_update)

        if task.status != "ready":
            raise RuntimeError(f"Indexing failed with status {task.status}")
        print(f"Uploaded {fname}. The unique identifier of your video is {task.video_id}.")
        dicts[task.video_id] = fname
    except Exception as e:
        print(f"Failed to upload {fname}: {e}")
    return dicts

# Asynchronous function to handle multiple video uploads
async def video_push(index):
    VIDEO_PATH = "vids/*.mp4"  # Update the path accordingly
    tasks = [upload_video(video, index) for video in glob(VIDEO_PATH)]
    results = await asyncio.gather(*tasks)
    combined_dict = {}
    for result in results:
        combined_dict.update(result)
    return combined_dict

# Function to query the indexed videos
def query(query_text, index):
    client = TwelveLabs(api_key=st.secrets["TWELVE_LABS_API_KEY"])
    search_results = client.search.query(index_id=index.id, query_text=query_text, options=["visual", "conversation"])
    results = []

    def print_page(page):
        for clip in page:
            if clip.confidence == "high":  # Only include results with high confidence
                result = {
                    "video_id": clip.video_id,
                    "score": clip.score,
                    "confidence": clip.confidence,
                    "start": clip.start,
                    "end": clip.end
                }
                results.append(result)

    while True:
        try:
            print_page(next(search_results))
        except StopIteration:
            break
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

# Streamlit app
def main():
    st.title("Phyllo <> Twelve Labs")

    if "videos" not in st.session_state:
        st.session_state.videos = None

    if "index" not in st.session_state:
        st.session_state.index = None

    if "hmap" not in st.session_state:
        st.session_state.hmap = None

    if "results" not in st.session_state:
        st.session_state.results = None

    if st.session_state.videos is None:
        # Step 1: Take Instagram handle input
        handle = st.text_input("Enter Instagram hashtag/keyword/mention:")
        if st.button("Fetch Videos"):
            if handle:
                with st.spinner("Fetching data using Phyllo API..."):
                    st.session_state.videos = fetch_data(handle)
                st.success("Data fetched successfully!")

    if st.session_state.videos is not None and st.session_state.index is None:
        # Step 2: Download videos
        folder = "vids"
        progress_bar = st.progress(0)
        total_videos = len(st.session_state.videos)

        for i, video in enumerate(st.session_state.videos):
            fname = video[0].split('/')[-1] + '.mp4'
            download_video(video[1], fname, folder)
            progress_bar.progress((i + 1) / total_videos)

        st.success("Videos downloaded successfully!")

        # Step 3: Create index in Twelve Labs
        with st.spinner("Creating index in Twelve Labs..."):
            st.session_state.index = create_index()
        st.success("Index created successfully!")

    if st.session_state.index is not None and st.session_state.hmap is None:
        # Step 4: Upload videos to Twelve Labs
        progress_bar = st.progress(0)
        with st.spinner("Uploading videos to Twelve Labs..."):
            st.session_state.hmap = asyncio.run(video_push(st.session_state.index))
            progress_bar.progress(1.0)
        st.success("Videos uploaded successfully!")

    if st.session_state.hmap is not None and st.session_state.results is None:
        # Step 5: Take search query input
        query_text = st.text_input("Enter search query:")
        if st.button("Search"):
            if query_text:
                with st.spinner("Searching the indexed videos..."):
                    st.session_state.results = query(query_text, st.session_state.index)
                st.success("Search completed successfully!")
            else:
                st.warning("Please enter a search query.")

    if st.session_state.results is not None:
        # Step 6: Display search results
        if st.session_state.results:
            result_selection = st.selectbox(
                "Select a video segment to play:",
                [f"Video segment {i+1}" for i, result in enumerate(st.session_state.results)]
            )
            if st.button("Play Video Segment"):
                selected_index = int(result_selection.split(" ")[-1]) - 1
                selected_result = st.session_state.results[selected_index]
                file_path = st.session_state.hmap[selected_result['video_id']]
                start_time = selected_result['start']
                end_time = selected_result['end']
                segment_path = save_video_segment(file_path, start_time, end_time)
                st.video(segment_path)
        else:
            st.warning("No results found.")

if __name__ == "__main__":
    main()
