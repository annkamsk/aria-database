import json
from pathlib import Path
from typing import Any
from bs4 import BeautifulSoup
import requests

def parse_subtitle(title_tag) -> tuple[str, Any]:
    subtitle = []
    for sib in title_tag.next_siblings:
        if "Libretto" in sib.text:
            return " ".join([s for s in subtitle if s]), sib
        subtitle.append(sib.text.strip())


def parse_libretto(libretto_tag) -> tuple[str, Any]:
    libretto = []
    for sib in libretto_tag.next_siblings:
        if "ul" == sib.name:
            return " ".join([s for s in libretto if s]), sib
        libretto.append(sib.text.strip())


def parse_property(starting_tag, starting_value, next_tag_value) -> tuple[str, Any]:
    value = []
    start_parsing = False
    for child in starting_tag.descendants:
        if next_tag_value in child.text:
            return " ".join([s for s in value if s]), child
        if start_parsing:
            value.append(child.text.strip())
        if starting_value in child.text:
            start_parsing = True
        
    for sib in starting_tag.next_siblings:
        if next_tag_value in sib.text:
            return " ".join([s for s in value if s]), sib
        if start_parsing:
            value.append(child.text.strip())
        if starting_value in sib.text:
            start_parsing = True

    return " ".join([s for s in value if s]), starting_tag


def parse_properties(properties_top_tag) -> dict[str, str]:
    p = {}
    role = properties_top_tag.find("li").text
    role = role.split("Sound")[0]
    p["role"] = role.strip()
    p["other"] = str(properties_top_tag)
    return p


def parse_htmls() -> None:
    db = []
    for src in Path("html").glob("*.html"):
        print(src)
        with src.open("r", encoding="utf-8", errors="ignore") as src_file:
            soup = BeautifulSoup(src_file, 'html.parser')
            for title in soup.find_all("font", {"size": "+1"})[2:-2]:
                entry = {"title": title.b.text}
                entry["subtitle"], libretto_tag = parse_subtitle(title)
                entry["libretto"], properties_tag = parse_libretto(libretto_tag)
                properties = parse_properties(properties_tag)
                entry.update(properties)
                db.append(entry)

    with open("db.json", "w+") as json_file:
        json.dump(db, json_file, indent=2)


def parse_role():
    with open("db.json") as json_file:
        db = json.load(json_file)

    for entry in db:
        # Replace double no-break space with line break and split by it
        elements = entry["role"].replace("\u00a0\u00a0", "\n").split("\n")
        elements = [*elements[:-1], *elements[-1].split("\t")]

        for elem in elements:
            [key, *value] = elem.split(":")
            if not key:
                continue
            key = "_".join(key.strip().lower().split())
            entry[key] = " ".join(v.strip() for v in value)

    with open("db.json", "w+") as json_file:
        json.dump(db, json_file, indent=2)  


def parse_links():
    with open("db.json") as json_file:
        db = json.load(json_file)

    for entry in db:
        soup = BeautifulSoup(entry["other"], 'html.parser')
        li = soup.find("li")
        while li:
            if li.text.strip().startswith("Translation"):
                for a in li.find_all("a"):
                    if "Translation" in a.text:
                        entry["aria_translation"] = a["href"]
                    if "Libretto" in a.text:
                        entry["aria_libretto"] = a["href"]

            if li.text.strip().startswith("Recordings"):
                for a in li.find_all("a"):
                    if "Complete" in a.text:
                        entry["recordings_complete"] = a["href"]
                    if "Excerpts" in a.text:
                        entry["recordings_excerpts"] = a["href"]
            if li.text.strip().startswith("Where"):
                entry["where"] = {}
                for a in li.find_all("a"):
                    entry["where"][a.text] = a["href"]
            li = li.find("li")
        entry.pop("other")

    with open("db.json", "w+") as json_file:
        json.dump(db, json_file, indent=2)  


def get_lyrics():
    with open("db.json") as json_file:
        db = json.load(json_file)
    
    base_url = "https://aria-database.com"
    for entry in db:
        if (libretto := entry.get("aria_translation")):
            url = f"{base_url}/{libretto}"
            print(url)
            try:
                r = requests.get(url)
                file_name = libretto.split("/")[-1]
                with open(f'translation/{file_name}', "w+") as f:
                    f.write(r.text)
            except Exception as e:
                print(e)
                break

get_lyrics()