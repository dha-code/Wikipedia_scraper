import requests
import json
from bs4 import BeautifulSoup
import re
from requests import Session

class PageNotFound(Exception):
    pass

# Function to get text from wiki link
def get_wiki_text(wikipedia_url: str, session: Session):
    req = session.get(wikipedia_url)
    soup = BeautifulSoup(req.text, 'html.parser')
    return soup

# Function to retrieve personal details of US leaders
def get_personal_details(wikipedia_url: str, session: Session):
    soup = get_wiki_text(wikipedia_url, session)
    table = soup.find('table', attrs={'class':'infobox'})
    flag = 0;
    metadata = {}

    for row in table.find_all('tr'):    
        headers = row.find_all('th')
        elements = row.find_all('td')

        # Reset the flag after the Personal details block is over using the th tag infobox-header
        for all_th in headers:
            if (all_th.text.strip() == "Personal details"):
                flag = 1;
                break
            if (all_th.has_attr('class')):
                if (all_th['class'][0] == 'infobox-header'):
                    flag = 0

        if(flag == 1):
            for all_th in headers:
                info_key = all_th.text.strip()
                metadata[info_key] = []
            for all_td in elements:
                text1 = re.sub(r'\(.*?\)','',all_td.text.strip())
                text2 = re.sub(r'[^\w\s]','',text1.strip())
                metadata[info_key] = re.sub(r'\s{2,}',' ',text2).split('\n')
    metadata.pop('Personal details', None)
    return metadata

# Function to get the first paragraph of a wiki page
def get_first_paragraph(wikipedia_url: str, session: Session):
    print(wikipedia_url) # keep this for the rest of the notebook
    soup = get_wiki_text(wikipedia_url, session)
    
    # Store all the p tags in a list. Strip and check that its not empty 
    # First paragraph - Has digits (year of birth) and is more than 20 words
    paragraphs = [para.text.strip() for para in soup.find_all("p") if len(para.text.strip())>0]
    for para in paragraphs:
        if((re.match('.*[1-9].*',para)) and (len(para.split()) >= 15)):
            #first_paragraph = re.sub(r'\[.{,2}\]','',para)
            first_paragraph = re.sub(r'\[.*?\]','',para)
            break
    return first_paragraph

# Function to return leaders info 
def get_leaders():
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

# Function to write the JSON into a new file
def save(leaders_per_country: dict, filename: str):
    with open(filename,"w") as file:
        json.dump(leaders_per_country, file, indent=4, separators=(". ", " = "))
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