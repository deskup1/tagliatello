
from ...graph import BaseNode, StringAttributeDefinition, IntegerAttributeDefinition, ComboAttributeDefinition

import dearpygui.dearpygui as dpg
import time
import requests
import json

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
            "tag": StringAttributeDefinition(),
            "wiki": StringAttributeDefinition()
        }
    
    def __danbooru_get_wiki(self, tag: str, retry: int = 3):
        tag = tag.strip().replace(" ", "_").replace("\\", "")
        
        body = None
        for _ in range(retry):
            url = f"https://danbooru.donmai.us/wiki_pages/{str(tag)}.json"
            wiki = requests.get(url)
            if wiki.status_code != 200:
                break
            try:
                content = wiki.content.decode("utf-8")
                body = json.loads(content)["body"]  
            except Exception as e:
                print(e)
                continue

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
            "tag": tag,
            "wiki": wiki
        }
