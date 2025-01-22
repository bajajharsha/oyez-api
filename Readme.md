# **Analysing and Scraping Data from the Oyez API**

### Objective:

To scrape and analyze data from the Oyez API, organize it systematically, and test your understanding of Python concepts, data handling, and optimization techniques. The task covers a variety of skills including data structures, control flow, exception handling, typing, memory management, async programming, and task management.

# 1. Fetching the data from API

- Fetch data from API
- cases between 1990 and 2025
- group into decoded and not decided
- stuff to include
  - case facts
  - conclusion
  - images of all advocates (`name.extension`)
  - **Oral Argument Audio Transcripts**
  - Person details - information about individuals from `heard_by` and `decided_by`:
    - Biography
    - Roles
    - Schools attended
    - store their real images
  - Location Detail**s**
  - **Opinion Announcement Transcripts**
    - Store audio files of Opinion Announcements (only `.mp3` files)
  - **Written Opinions -** written opinions for detailed opinions
  ## Approach
  **Fetch Case URLs**: For each year, retrieve a list of cases using the endpoint `https://api.oyez.org/cases?per_page=0&filter=term:{year}`.
  **Process Each Case**: For every case, detailed data is fetched and passed to **`categorize_data`**, which processes the case further.
  - in the first API call, fetch the hrefs only
  - for each href, fetch the json
    - use that json to get further data
    - for person details - use the json data that is fetched from attorneys href
  ## Tools Used:
  - API Call:
    - `aiohttp` (Asynchronous): Fully asynchronous, allowing for high-concurrency operations.
    - `asyncio` : for asynchronous operation
    - `asyncio.Semaphore`: Used to restrict concurrent API calls.
    -

# 2. Categorization

```
Resolved/
└── case/
├── case.json
├── attorneys/
├── argument/
│ ├── transcript.txt
│ └── audio.mp3
├── members/
├── embeddings/
└── case.pdf

UnResolved/
└── case/
├── case.json
├── attorneys/
├── argument/
│ ├── transcript.txt
│ └── audio.mp3
├── members/
├── embeddings/
└── case.pdf
```
