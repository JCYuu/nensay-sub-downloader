import asyncio
import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import webbrowser

class Chapter:
    def __init__(self, title, link):
        self.title = title
        self.link = link


async def login(session):
    print('Login in...')
    async with session.get("http://nensaysubs.net/") as response:
        soup = BeautifulSoup(await response.text(), 'html.parser')
        captcha = eval(soup.find(name='h1', attrs={'class': 'text4'}).text)
        await asyncio.sleep(1)
    async with session.post("http://nensaysubs.net/ingreso/index.php/", data={'valor': captcha}) as response:
        print(response)


async def reload_filter(soup):
    query_list = []
    children = soup.find_all(name='td', attrs={'valign': 'top'})
    filtering = [x.findChildren('a', recursive=True) for x in children]
    for i, element in enumerate(filtering):
        title = element[0].text
        query_list.append(title)
    print(query_list)
    return query_list


async def reload_chapters(soup):
    ch_list = []
    title = ''
    dl = ''
    for tag in soup.find_all(['span', 'input']):
        if tag.get('id') == 'bloqueados':
            child = tag.find('a', attrs={'id': 'caramelo'})
            start_pos = child.get('href').find('senos')
            dl = child.get('href')[start_pos:]
        if tag.get('value') == 'Bajar': dl = tag.get('onclick')[13:-3]
        if tag.get('id') == 'animetitu': title = tag.text
        if title != '' and dl != '':
            ch_list.append(Chapter(title, dl))
            title = dl = ''
    return ch_list


async def search(session, query):
    if not query:
        print('Please insert a valid search criteria')
        return
    async with session.post(f"http://nensaysubs.net/buscador/?query={query.replace(' ', '+')}") as response:
        soup = BeautifulSoup(await response.text(), 'html.parser')
        query_list = await reload_filter(soup)
        if not query_list:
            print('No results were found for your query, try another one')
            return
        while True:
            print(f"Here is the result for {query}:")
            for i, element in enumerate(query_list):
                print(f'{i}: {element}')
            previous = soup.find(name='a', text='Anterior')
            nxt = soup.find(name='a', text='Siguiente')
            if previous is not None: print('-1: Previous page')
            if nxt is not None: print('-2: Next page')
            try:
                select = int(input())
            except:
                print('Wrong selection, try again. Select an option using the numbers')
                continue
            if select == -2:
                async with session.get(nxt.get('href')) as next_page:
                    soup = BeautifulSoup(await next_page.text(), 'html.parser')
                    query_list = await reload_filter(soup)
            elif select == -1:
                async with session.get(previous.get('href')) as next_page:
                    soup = BeautifulSoup(await next_page.text(), 'html.parser')
                    query_list = await reload_filter(soup)
            elif select > -1: break
            else: print('Wrong selection, try again')
        chosen = query_list[select]
        await download(session, chosen)


async def download(session, chosen):
    async with session.post(f"http://nensaysubs.net/sub/{chosen.replace(' ', '_')}") as response:
        soup = BeautifulSoup(await response.text(), 'html.parser')
        ch_list = await reload_chapters(soup)
        while True:
            print(f'Here are {chosen} subtitles: ')
            for i, j in enumerate(ch_list): print(f'{i}: {j.title}')
            previous = soup.find(name='a', text='Anterior')
            nxt = soup.find(name='a', text='Siguiente')
            if previous is not None: print('-1: Previous page')
            if nxt is not None: print('-2: Next page')
            cap = int(input())
            if cap == -2:
                async with session.get(nxt.get('href')) as next_page:
                    soup = BeautifulSoup(await next_page.text(), 'html.parser')
                    ch_list = await reload_chapters(soup)
            elif cap == -1:
                async with session.get(previous.get('href')) as next_page:
                    soup = BeautifulSoup(await next_page.text(), 'html.parser')
                    ch_list = await reload_chapters(soup)
            elif cap > -1: break
            else: print('Wrong selection, try again')
        zip_name = ch_list[cap].title
        link = ch_list[cap].link
        dl_link = f'https://nensaysubs.net/{link}'
        print(zip_name)
        print(dl_link)
        async with session.get(dl_link):
            async with session.get('http://nensaysubs.net/senos/seguro.php') as pic:
                chunk = await pic.content.read()
                with open('photo.png', 'wb') as file:
                    file.write(chunk)
                webbrowser.open('photo.png')
                print('***Please send the onscreen code***')
                code = input()
                print(code)
                print('Sending the zipped file. If file is corrupted then you entered the wrong code')
                async with session.post('http://nensaysubs.net/solicitud/', data={'code': code.lower()}) as dl:
                    chunk = await dl.content.read()
                    print('Enter a desired path for the download, leave empty for default')
                    path = input()
                    if path.endswith('/') or path.endswith("\""):
                        path = path[:-2]
                    if "\"" in path: path += "\""
                    if '/' in path: path += '/'
                    full_path = f'{path}{zip_name}.zip'
                    with open(full_path, 'wb') as file:
                        file.write(chunk)
                    print(f"Done!\nFile has been saved in {full_path}")


async def main():
    connector = aiohttp.TCPConnector(force_close=True)
    client = ClientSession(cookie_jar=aiohttp.CookieJar(), connector=connector)
    async with client as session:
        await login(session)
        while True:
            print('''##################
Select one option:
1: Search
2: Exit
##################''')
            try:
                opt = int(input())
            except:
                print('Wrong selection, try again')
                continue
            if opt == 1:
                print('Insert search criteria: ')
                query = input()
                await search(session, query)
            elif opt == 2:
                break
            else:
                print('Wrong selection, try again')


asyncio.get_event_loop().run_until_complete(main())
