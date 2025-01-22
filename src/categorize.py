import asyncio
import aiohttp
from pathlib import Path
import json
import re
from bs4 import BeautifulSoup
import os


# Function to download image asynchronously
async def download_image(image_url, save_path):
    try:
        async with aiohttp.ClientSession() as session:                                      # Create session
            async with session.get(image_url) as response:                                  # GET Request 
                response.raise_for_status() 
                with open(save_path, 'wb') as img_file:
                    img_file.write(await response.read())
        return True
    except aiohttp.ClientError as e:
        print(f"Error downloading image from {image_url}: {e}")
        return False

# Asynchronously fetch advocate data from the href API
async def fetch_image_url(href, json_data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(href) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Get the list of images
                images = data.get("images", [])
                if images:
                    # Take the first image from the list
                    first_image = images[0].get("file", {})
                    image_url = first_image.get("href", "")
                    if image_url.endswith(".jpg"):
                        return image_url, data
                return None, data
    except aiohttp.ClientError as e:
        print(f"Error fetching data from {href}: {e}")
        return None, None

# Function to clean up case names to avoid invalid characters in file paths
def clean_case_name(case_name):
    # Replace spaces with underscores, remove commas and special characters
    case_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', case_name)
    return case_name

# Function to create JSON file
def create_json_file(file_path, new_data):
    if Path(file_path).exists():
        with open(file_path, 'r') as file:
            existing_data = json.load(file)
        
        existing_data.append(new_data)
        
        with open(file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)
    else:
        with open(file_path, 'w') as file:
            json.dump([new_data], file, indent=4)  # Wrap new data in a list to form a valid JSON structure

def extract_plain_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

async def handle_advocates(case_data, attorneys_dir, json_data):
    advocate_tasks = []
    advocates = case_data.get("advocates", [])
    if advocates and isinstance(advocates, list):
        for advocate_data in advocates:
            try:
                advocate = advocate_data.get("advocate", None)
                if advocate:
                    advocate_name = clean_case_name(advocate.get("name", "unknown_advocate"))
                    advocate_href = advocate.get("href", "")
                    if advocate_href:
                        advocate_tasks.append(fetch_and_download_image(advocate_href, advocate_name, attorneys_dir, json_data, type = "advocate"))
            except Exception as e:
                print(f"Error processing advocate data: {e}")
    else:
        print("No valid advocates data found.")

    # Wait for all tasks to complete
    if advocate_tasks:
        await asyncio.gather(*advocate_tasks)

async def handle_members(case_data, members_dir, json_data):
    members_tasks = []
    try:
        heard_by_list = case_data.get("heard_by", [])
        for members_list in heard_by_list:
            members = members_list.get("members", [])
            for member in members:
                if member:
                    member_name = clean_case_name(member.get("name", "unknown_member"))
                    member_href = member.get("href", "")
                    if member_href:
                        members_tasks.append(fetch_and_download_image(member_href, member_name, members_dir, json_data, type = "member"))
                        
        if members_tasks:
            await asyncio.gather(*members_tasks)
    except Exception as e:
        print(f"Error processing member data: {e}")           
    
async def handle_arguments(case_data, argument_dir, json_data):
    argument_tasks = []
    oral_argument_audio = case_data.get("oral_argument_audio", [])
    try:
        for argument_data in oral_argument_audio:
            argument_id = argument_data.get("id", "unknown_argument_id")
            argument_title = argument_data.get("title", "unknown_argument_title")
            argument_href = argument_data.get("href", "")
            if argument_href:
                argument_tasks.append(fetch_and_download_audio(argument_href, argument_title, argument_dir, json_data))
                
                
        if argument_tasks:
            await asyncio.gather(*argument_tasks)
    except Exception as e:
        print(f"Error processing argument data: {e}")

    

# Asynchronously categorize case data and handle advocate images
async def categorize_data(case_data):
    if not case_data:
        print("No case data found.")
        return

    # CASE NAME
    case_name = clean_case_name(case_data.get("name", "unknown_case"))
    
    # RESOLVED OR UNRESOLVED
    case_status_dir = "Resolved" if any("decided" in (event.get("event", "") if event else "").lower() for event in case_data.get("timeline", [])) else "UnResolved"
    
    # Create the main CASE folder
    case_dir = Path("Cases") / case_status_dir / case_name
    case_dir.mkdir(parents=True, exist_ok=True)

    # Create ATTORNEY directory
    attorneys_dir = case_dir / "attorneys"
    attorneys_dir.mkdir(parents=True, exist_ok=True)

    # Create MEMBERS directory
    members_dir = case_dir / "members"
    members_dir.mkdir(parents=True, exist_ok=True)
    
    # Create ARGUMENT directory
    argument_dir = case_dir / "argument"
    argument_dir.mkdir(parents=True, exist_ok=True)
    
    # Create CASE.JSON File
    case_json_path = case_dir / f"{case_name}.json"
    
    # Build JSON data 
    json_data = {
        "name": case_name,
        "term": case_data.get("term", None),
        "timeline": case_data.get("timeline", []),
        "facts_of_the_case": extract_plain_text(case_data.get("facts_of_the_case")) if case_data.get("facts_of_the_case") else None,
        "conclusion": extract_plain_text(case_data.get("conclusion")) if case_data.get("conclusion") else None,
        "advocates": [],
        "members": [],
    }

    # await handle_advocates(case_data, attorneys_dir, json_data)
    # await handle_members(case_data, members_dir, json_data)
    
    await asyncio.gather(
        handle_advocates(case_data, attorneys_dir, json_data),
        handle_members(case_data, members_dir, json_data), 
        handle_arguments(case_data, argument_dir, json_data),
        return_exceptions=True
    )

    # Extract advocate data and add it to json_data
    # if advocates:
    #     for advocate_data in advocates:
    #         try:
    #             advocate = advocate_data.get("advocate", {})
    #             if advocate:
    #                 advocate_name = clean_case_name(advocate.get("name", "unknown_advocate"))
    #                 advocate_image_path = attorneys_dir / f"{advocate_name}.jpg"  # Image path where it was saved
    #                 advocate_info = {
    #                     "name": advocate_name,
    #                     "image": str(advocate_image_path) or None,  # Image path instead of URL
    #                 }
    #                 json_data["advocates"].append(advocate_info)
    #         except Exception as e:
    #             print(f"Error adding data into json: {e}")

    # Call the function to create the JSON file
    create_json_file(case_json_path, json_data)

# Helper function to fetch the advocate's image URL and download it
async def fetch_and_download_image(href, name, dir, json_data, type):
    image_url, data = await fetch_image_url(href, json_data)
    if image_url:
        # Define the image save path
        image_path = dir / f"{name}.jpg"
        res = await download_image(image_url, image_path)
        
        info = {
            "name": clean_case_name(name),
            "image": str(image_path) if res else "No Image Available",  
            "roles": data.get("roles") or None,
            "biography": extract_plain_text(data.get("biography")) or None,
            "law_school": data.get("law_school") or None,
        }
        if (type == "advocate"):
            create_json_file(dir / f"advocates.json", info)
            json_data["advocates"].append(info)
        elif (type == "member"):
            create_json_file(dir / f"members.json", info)
            json_data["members"].append(info)
            
async def download_audio(url, url_path, dir, json_data):
    try:
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(url_path, 'wb') as file:
                        file.write(await response.read())
                    return True
    except Exception as e:
        print(f"Error downloading audio from {url}: {e}")
        return False            

async def fetch_and_download_audio(href, title, dir, json_data):
    async with aiohttp.ClientSession() as session:
        async with session.get(href) as response:
                data = await response.json()
                audio_urls = data.get("media_file", {})
                for audio_url in audio_urls:
                    if audio_url.get("mime") == "audio/mpeg":
                        url = audio_url.get("href")
                title_clean = clean_case_name(title)
                url_path = dir / f"{title_clean}.mp3"
                res = await download_audio(url, url_path, dir, json_data)
                
                transcript_details = data.get("transcript", {})
                transcript = await download_transcript(transcript_details, title, dir, json_data)
                info = {
                    "title": clean_case_name(title),
                    "audio": str(url_path) if res else "No Audio Available",  
                    "transscipt": str(transcript)
                }
                    
                create_json_file(dir / f"arguments.json", info)
 
async def download_transcript(transcript_details, title, dir, json_data):
    try:
        transcript_title = clean_case_name(transcript_details.get("title", "unknown_transcript_title"))
        sections = transcript_details.get("sections", [])
        
        file_path = os.path.join(dir, f"{transcript_title}.txt")
        os.makedirs(dir, exist_ok=True)
        
        with open(file_path, "a") as transcript_file:
            for section in sections:
                turns = section.get("turns", [])
                for turn in turns:
                    start_time = turn.get("start", "N/A")
                    speaker_name = turn.get("speaker", {}).get("name", "Unknown Speaker")
                    text_blocks = turn.get("text_blocks", [])
                    
                    for block in text_blocks:
                        text = block.get("text", "")
                        line = f"[{start_time}] {speaker_name}: {text}\n"
                        transcript_file.write(line)
                        
        return file_path
    except Exception as e:
        print(f"An error occurred on downloading transcript {e}")
        return "No transcript available"
    
   
# Main function to handle case processing
# async def process_case(case_data):
#     # Generate a unique case index (UUID or other unique identifier)
#     case_index = str(uuid.uuid4())
#     await categorize_data(case_data, case_index)
