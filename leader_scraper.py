import requests
import json
from bs4 import BeautifulSoup
import re
from requests import Session

class PageNotFound(Exception):
    """
    Custom class for raising exception
    """
    pass

def get_wiki_text(wikipedia_url: str, session: Session) -> str:
    """
    Function to get text from wiki link
    :params wikipedia_url :str Link to the wiki site
    :params session :str Session ID
    :returns str Text from Wiki site
    """
    req = session.get(wikipedia_url)
    soup = BeautifulSoup(req.text, 'html.parser')
    if req.status_code != 200:
        raise PageNotFound(req.reason)
    return soup

def cleanup_bio(para: str) -> str:
    """
    Function to clean up the first line from Wiki link 
    :params para :str First line from Wiki site
    :returns str Text cleanup of unwanted text elements
    """
    phonotics = re.sub(r'\[.*?\]|\/.*\/.*?\;|\/.*\/|ⓘ|uitspraak|.couter','',para)
    empty_paranthesis = re.sub(r'\(\s?\)',' ',phonotics)
    clean_text = re.sub(r'\s{2,}',' ',empty_paranthesis)
    return clean_text

def get_personal_details(wikipedia_url: str, session: Session) -> dict:
    """
    Function to retrieve personal details of US leaders
    :params wikipedia_url :str Link to the wiki site
    :params session :str Session ID
    :returns :dict With personal details from Wiki page
    """
    soup = get_wiki_text(wikipedia_url, session)
    table = soup.find('table', attrs={'class':'infobox'})
    flag = 0;
    metadata = {}

    for row in table.find_all('tr'):    
        headers = row.find_all('th')
        elements = row.find_all('td')

        # Reset the flag after the Personal details block is over using the th tag infobox-header
        # Ensures that only the personal details are scraped
        for all_th in headers:
            if (all_th.text.strip() == "Personal details"):
                flag = 1;
                break
            if (all_th.has_attr('class')):
                if (all_th['class'][0] == 'infobox-header'):
                    flag = 0

        # Runs only for the rows within Personal details block since the flag is set 
        if(flag == 1):
            for all_th in headers:
                info_key = all_th.text.strip()
                metadata[info_key] = []
            for all_td in elements:
                text1 = re.sub(r'\(.*?\)','',all_td.text.strip())
                text2 = re.sub(r'[^\w\s]','',text1.strip())
                metadata[info_key] = re.sub(r'\s{2,}',' ',text2).split('\n')

    # Remove the empty key 'Personal details' and return the data
    metadata.pop('Personal details', None)
    return metadata

def get_first_paragraph(wikipedia_url: str, session: Session) -> str:
    """
    Function to get the first paragraph of a wiki page
    :params wikipedia_url :str Link to the wiki site
    :params session :str Session ID
    :returns :str The cleanup first paragraph
    """
    print(wikipedia_url) # To know the progress 
    soup = get_wiki_text(wikipedia_url, session)
    
    # Store all the p tags in a list. Strip and check that its not empty 
    # First paragraph - Has digits (year of birth) and is more than 20 words
    paragraphs = [para.text.strip() for para in soup.find_all("p") if len(para.text.strip())>0]
    for para in paragraphs:
        if((re.match('.*[1-9].*',para)) and (len(para.split()) >= 15)):
            first_paragraph = cleanup_bio(para)
            break
    return first_paragraph

# 
def get_leaders() -> dict:
    """
    Function to return a li leaders info 
    :returns :dict The mapping of leaders and their information
    """
    countries = requests.get(f"{root_url}/{countries_url}", cookies=cookies).json()

    # Go through all the countries and extract the name of the leaders in a dict
    leaders_per_country = {country:requests.get(f"{root_url}/{leaders_url}", cookies=cookies, params={'country':country}).json() 
                           for country in countries}
    
    # Starting session to go over all the wiki links of the leaders
    with Session() as session:
        for country,leaders in leaders_per_country.items():
            for each in leaders: 
                each["first_wiki_para"] = get_first_paragraph(each["wikipedia_url"], session)
                # For US leaders scrap the personal details from Wiki page
                if(country == 'us'):
                    each["personal_details"] = get_personal_details(each["wikipedia_url"], session)

    return leaders_per_country

def save(leaders_per_country: dict, filename: str):
    """
    Function to write the JSON into a new file
    :param leaders_per_country :dict The mapping of leaders and their information
    :param filename :str Output filename
    """
    with open(filename,"w", encoding="utf-8") as file:
        json.dump(leaders_per_country, file, indent=4, separators=(". ", " = "), ensure_ascii=False)
    print("Saved the data in",filename)

# Initialise URL paths
root_url = "https://country-leaders.onrender.com"
status_url = "/status"
cookie_url = "/cookie"
countries_url = "/countries"
leaders_url = "/leaders"

# Query the root URL and check the status
req = requests.get(f"{root_url}/{status_url}")
if req.status_code != 200:
    raise PageNotFound(req.reason)

# Get cookies 
cookies = requests.get(root_url+"/"+cookie_url).cookies

# Get the information of the leaders and save it in a file
leaders_per_country = get_leaders()
save(leaders_per_country, "leaders.json")