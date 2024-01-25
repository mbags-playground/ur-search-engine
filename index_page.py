import os
from datetime import datetime
from bs4 import BeautifulSoup
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, DATETIME
from selenium import webdriver
from urllib.parse import urljoin, urlparse
import multiprocessing

# Define the schema for your search index
schema = Schema(
    title=TEXT(stored=True),
    content=TEXT,
    url=ID(stored=True, unique=True),
    date=DATETIME(stored=True)
)

# Create or open an index in a directory (change 'indexdir' to your preferred directory)
indexdir = "index_dir"
if not os.path.exists(indexdir):
    os.mkdir(indexdir)

ix = create_in(indexdir, schema)

# External file to track visited URLs
visited_urls_file = "visited_urls.txt"
links_to_visit_file = "links_to_visit.txt"
def load_links_to_visit():
    if os.path.exists(links_to_visit_file):
        with open(links_to_visit_file, 'r') as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_links_to_visit(links_to_visit):
    with open(links_to_visit_file, 'w') as f:
        f.write("\n".join(links_to_visit))


def load_visited_urls():
    if os.path.exists(visited_urls_file):
        with open(visited_urls_file, 'r') as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_visited_urls(visited_urls):
    with open(visited_urls_file, 'w') as f:
        f.write("\n".join(visited_urls))
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
# Define a function to fetch and index a webpage using Selenium
def index_webpage(url, depth=3, open_in_new_tab=False):
    visited_urls=load_visited_urls()
    links_to_visit = load_links_to_visit()
    
    if(url not in visited_urls or depth==3):
        try:
            print(f"Indexing {url}")
          
         

            if open_in_new_tab:
                driver.execute_script("window.open();")
                driver.switch_to.window(driver.window_handles[-1])
            driver.get(url)
            driver.implicitly_wait(30)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            title = soup.title.text.strip() if soup.title else ""
            content = soup.get_text().strip()

            current_date = datetime.now()

            with ix.writer() as writer:
                    print(f"Indexing new document for URL: {url}")
                    writer.add_document(title=title, content=content, url=url, date=current_date)

            visited_urls.add(url)
            save_visited_urls(visited_urls)
            if depth > 0:
                print(f"Indexing links in {url}, depth={depth}")

                for link in soup.find_all('a', href=True):
                    print(f"Found link: {link['href']}")

                    next_url = urljoin(url, link['href'])
                    parsed_url = urlparse(next_url)
                    base_domain = parsed_url.netloc
                    print(f"Base domain: {base_domain}")
                    links_to_visit.add(next_url)

                    # Check for links that have the domain "ur.ac.rw"
                    if "ur.ac.rw" in base_domain:
                        index_webpage(next_url, depth - 1, open_in_new_tab=True)
                    

        except Exception as e:
            visited_urls.add(url)
            print(f"Error indexing {url}: {e}")
        

if __name__ == '__main__':
    start_url = "https://ur.ac.rw/"

    # Split the crawling process among multiple processes
    num_processes = multiprocessing.cpu_count()
    url_chunks = [start_url]  # Modify this if you want to start from different URLs
    print("Number of processor processing data", num_processes)
    processes = []
    for url_chunk in url_chunks:
        process = multiprocessing.Process(target=index_webpage, args=(url_chunk,))
        processes.append(process)
        process.start()

    # Wait for all processes to finish
    for process in processes:
        process.join()
    driver.quit()

