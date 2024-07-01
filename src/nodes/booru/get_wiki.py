
from ...graph import BaseNode, StringAttributeDefinition, IntegerAttributeDefinition, ComboAttributeDefinition

import dearpygui.dearpygui as dpg
import time
import requests


class DanbooruWikiNode(BaseNode):

    def __init__(self):
        super().__init__()
        self.set_default_input("retry", 3)


    @property
    def input_definitions(self):
        return {
            "tag": StringAttributeDefinition(),
            "retry": IntegerAttributeDefinition()
        }
    
    @property
    def output_definitions(self):
        return {
            "wiki": StringAttributeDefinition()
        }
    
    def __danbooru_get_wiki(self, tag: str, retry: int = 3):
        tag = tag.strip().replace(" ", "_")
        
        for _ in range(retry):
            tags = requests.get(f"https://danbooru.donmai.us/tags.json?search%5Bname_matches%5D={tag}")
            if tags.status_code == 200:
                break
        else:
            return ""
        
        tags = tags.json()
        if len(tags) == 0:
            return ""
        
        tag: dict = tags[0]

        for _ in range(retry):
            wiki = requests.get(f"https://danbooru.donmai.us/wiki_pages/{str(tag['name'])}.json")
            if wiki.status_code == 200:
                break
        else:
            return ""
        
        body = wiki.json().get("body")
        if body is None:
            return ""
        
        return body
    

    
    @staticmethod
    def name():
        return "Danbooru Wiki Node"
    
    @staticmethod
    def category():
        return "Booru"
        
    def run(self, **kwargs):
        tag = kwargs["tag"]
        retry = kwargs["retry"]
        wiki = self.__danbooru_get_wiki(tag, retry)
        return {
            "wiki": wiki
        }
