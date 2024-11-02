import requests
import pandas as pd
import time
import logging
import typing
token="XYZ_Kwo4CBlTMI3l4vhBnjPpngz4lv71xA2wfXYZ"#i have used XYZ at the start and end of the token for my privacy
class myscrapper:
    def __init__(self, token: str):
        self.headers={
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url='https://api.github.com'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s -- %(message)s',
            datefmt='%I:%M %p'
        )
        self.logger=logging.getLogger(__name__)

    def makingrequest(self, url: str, params: typing.Optional[dict] = None) -> dict:
        while True:
            response=requests.get(url,headers=self.headers,params=params)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                resettime=int(response.headers.get('X-RateLimit-Reset', 0))
                sleeptime=max(resettime - time.time(), 0) + 1
                self.logger.warning(f"Rate limit hit. Sleeping for {sleeptime} seconds")
                time.sleep(sleeptime)
            else:
                self.logger.error(f"Error {response.status_code}: {response.text}")
                response.raise_for_status()

    def cleaning(self,company: str) -> str:
        if not company:
            return ""
        cleaned = company.strip().lstrip('@')
        return cleaned.upper()

    def searchingusers(self, location: str, min_followers: int) -> typing.List[dict]:
        users = []
        page = 1
        while True:
            self.logger.info(f"Fetching users page {page}")
            query=f"location:{location} followers:>={min_followers}"
            params={
                'q': query,
                'per_page': 100,
                'page': page
            }
            url=f"{self.base_url}/search/users"
            response=self.makingrequest(url, params)
            if not response['items']:
                break
            for user in response['items']:
                userdata=self.makingrequest(user['url'])
                cleaned_data={
                    'login': userdata['login'],
                    'name': userdata['name'] if userdata['name'] else "",
                    'company': self.cleaning(userdata.get('company')),
                    'location': userdata['location'] if userdata['location'] else "",
                    'email': userdata['email'] if userdata['email'] else "",
                    'hireable': userdata['hireable'] if userdata['hireable'] is not None else False,
                    'bio': userdata['bio'] if userdata['bio'] else "",
                    'public_repos': userdata['public_repos'],
                    'followers': userdata['followers'],
                    'following': userdata['following'],
                    'created_at': userdata['created_at']
                }
                users.append(cleaned_data)
            page+=1 
        return users
    def gettinguserrepos(self, username: str, max_repos: int = 500) -> typing.List[dict]:
        repos=[]
        page=1
        while len(repos)<max_repos:
            self.logger.info(f"Fetching repos for {username}")  # Updated log message
            params={
                'sort': 'pushed',
                'direction': 'desc',
                'per_page': 100,
                'page': page
            }
            url=f"{self.base_url}/users/{username}/repos"
            response=self.makingrequest(url, params)
            if not response:
                break   
            for repo in response:
                repodata={
                    'login': username,
                    'full_name': repo['full_name'],
                    'created_at': repo['created_at'],
                    'stargazers_count': repo['stargazers_count'],
                    'watchers_count': repo['watchers_count'],
                    'language': repo['language'] if repo['language'] else "",
                    'has_projects': repo['has_projects'],
                    'has_wiki': repo['has_wiki'],
                    'license_name': repo['license']['key'] if repo.get('license') else ""
                }
                repos.append(repodata)
                
            if len(response)<100:
                break    
            page+=1   
        return repos[:max_repos]
def main(): 
    if not token:
        print("Token Needed")
        return
    scraper = myscrapper(token)
    users = scraper.searchingusers(location='Austin', min_followers=100)
    usersdf = pd.DataFrame(users)
    usersdf.to_csv('users.csv', index=False)
    allrepos = []
    for user in users:
        repos = scraper.gettinguserrepos(user['login'])
        allrepos.extend(repos)
    repos = pd.DataFrame(allrepos)
    repos.to_csv('repositories.csv', index=False)
    print(f"Scraped Information from {len(users)} users and {len(allrepos)} repos")    
if __name__ == "__main__":
    main()
