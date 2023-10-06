import sqlite3, json
from src.scrapers import LeerCapitulo, Nartag
from time import sleep
import re

servers = {"Nartag": Nartag, "LeerCapitulo": LeerCapitulo}
def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None

async def regenerate_all():
    nartag = True
    leercapitulo = True
    i = 1
    
    while nartag or leercapitulo:
        if nartag and leercapitulo:
            leercapitulo_mangas = await LeerCapitulo.get_manga_list(i)
            nartag_mangas = await Nartag.get_manga_list(i)
            
            leercapitulo = bool(leercapitulo_mangas)
            nartag = bool(nartag_mangas)
            
            mangas = leercapitulo_mangas + nartag_mangas
            mangas = *map(json.dumps, mangas),
            
            with open("data.json", "a+") as f:
                for manga in mangas:
                    f.write(f"\n{manga},")
            sleep(1)
        
        elif nartag:
            nartag_mangas = await Nartag.get_manga_list(i)
            nartag = bool(nartag_mangas)
            mangas = *map(json.dumps, nartag_mangas),
            with open("data.json", "a+") as f:
                for manga in mangas:
                    f.write(f"\n{manga},")
            sleep(3.5)
        
        elif leercapitulo:
            leercapitulo_mangas = await LeerCapitulo.get_manga_list(i)
            leercapitulo = bool(leercapitulo_mangas)
            mangas = *map(json.dumps, leercapitulo_mangas),
            
            with open("data.json", "a+") as f:
                for manga in mangas:
                    f.write(f"\n{manga},")
            sleep(5)
        i += 1
        
    conn = sqlite3.connect("MangaReader.db")
    conn.create_function("REGEXP", 2, regexp)
    cursor = conn.cursor()
    with open("data.json", "r") as f:
        data = json.load(f)
        unique_data = []
        for el in data:
            if el not in unique_data:
                unique_data.append(el)
    
    for el in range(len(unique_data)):
        try:
            print("\033[H\033[J", end="")
            print(f"{unique_data[el]['title']} - {el}/{len(unique_data)}")
            scraper = servers[unique_data[el]["server"]]
            manga = await scraper.get_manga_info(unique_data[el])
            manga["cover_url"] = "https://www.leercapitulo.com" + manga["cover_url"] if scraper.__name__ == "LeerCapitulo" else manga["cover_url"]
            manga["genre"] = json.dumps(manga["genre"])
            cursor.execute(
                "INSERT INTO WebComics VALUES(" + 
                "\"{title}\", \"{typeof}\", {rating}, \'{genre}\', \'{overview}\', \"{server}\", \"{name_url}\", \"{cover_url}\")".format(**manga))
            conn.commit()
        except:
            with open("error.txt", "a+", encoding="utf-8") as f:
                f.write(f"\n{unique_data[el]['title']}-{unique_data[el]['server']}")
            continue

    cursor.close()
    conn.close()



if __name__ == "__main__":
    option = input("""MangaReader-DB CLI
[1] Regenerate all DB
[2] Regenerate only a specific Manga
[3] View all Mangas\nSelect an option: """)