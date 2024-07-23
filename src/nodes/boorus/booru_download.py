
import sys
if __name__ == "__main__":
    sys.path.append("")
    from src.graph import BaseNode, AttributeDefinition, IntegerAttributeDefinition, ListAttributeDefinition, AttributeKind, ComboAttributeDefinition, StringAttributeDefinition
    from src.helpers import pillow_from_any_string
    from src.nodes.progress_node import ProgressNode
else:
    from ...graph import BaseNode, AttributeDefinition, IntegerAttributeDefinition, ListAttributeDefinition, AttributeKind, ComboAttributeDefinition, StringAttributeDefinition
    from ..progress_node import ProgressNode
    from ...helpers import pillow_from_any_string
import booru as booru_api
import asyncio


class UrlGenerator:
    def __init__(self, booru, queries, limit_per_query):
        self.booru = booru
        self.queries = queries
        self.limit_per_query = limit_per_query
        self.current_page = 1
        self.current_query = 0
        self.current_images = []
        self.returned_images = 0

    def __iter__(self):
        return self
    
    def get_url(self, image):
        url = image.get("file_url")
        if url is None:
            url = image.get("url")
        if url is None:
            url = image.get("preview_url")
        return url

    def get_tags(self, image):
        tags = image.get("tags")
        if tags is None:
            tags = image.get("tag_string")
        return tags            
    
    def __next__(self):
        if self.returned_images >= self.limit_per_query:
            self.current_query += 1
            self.returned_images = 0

        if self.current_query >= len(self.queries):
            raise StopIteration
        
        while len(self.current_images) == 0:
            # self.current_images =  self.booru.search(self.queries[self.current_query], limit=self.limit_per_query, page=self.current_page)
            result = asyncio.run(self.booru.search(self.queries[self.current_query], limit=min(100, self.limit_per_query), page=self.current_page))
            parsed_result = booru_api.resolve(result)
            self.current_images = []
            for image in parsed_result:
                self.current_images.append({
                    "url": self.get_url(image),
                    "tags": " , ".join(self.get_tags(image))
                })

            self.current_page += 1
            if len(self.current_images) == 0:
                self.current_query += 1
                self.returned_images = 0
                if self.current_query >= len(self.queries):
                    raise StopIteration
                
        image = self.current_images.pop(0)
        self.returned_images += 1
        return image

class BooruDownloadNode(ProgressNode):

    @staticmethod
    def name():
        return "Booru Download Node"
    
    @staticmethod
    def category():
        return "Booru"

    def __init__(self):
        super().__init__()
        self.set_default_input("queries", [])
        self.set_default_input("limit", 10)
        self.set_default_input("retry", 3)
        self.set_default_input("timeout", 10)
        self.set_default_input("batch_size", 10)
        self.set_default_input("booru", "danbooru")
        self.iterator = None

        self.downloaded_images_count = 0
        self.available_boorus = {
            "danbooru": booru_api.Danbooru,
            "gelbooru": booru_api.Gelbooru,
            "konachan": booru_api.Konachan,
            "yandere": booru_api.Yandere,
            "rule34": booru_api.Rule34,
            "safebooru": booru_api.Safebooru,
            "tbib": booru_api.Tbib,
            "xbooru": booru_api.Xbooru,
            "realbooru": booru_api.Realbooru,
            "paheal": booru_api.Paheal,
            "e621": booru_api.E621,
            "e926": booru_api.E926,
            "hypnohub": booru_api.Hypnohub,
            "derpibooru": booru_api.Derpibooru,
        }


    @property
    def input_definitions(self):
        return {
            "booru": ComboAttributeDefinition(values_callback=lambda: list(self.available_boorus.keys())),
            "queries": ListAttributeDefinition(StringAttributeDefinition()),
            "limit": IntegerAttributeDefinition(),
            "batch_size": IntegerAttributeDefinition()
        }
    
    @property
    def output_definitions(self):
        return {
            "images": ListAttributeDefinition(AttributeDefinition(type_name="image"), kind=AttributeKind.GENERATOR),
            "tags_string": ListAttributeDefinition(StringAttributeDefinition(), kind=AttributeKind.GENERATOR)
        }
    
    def init(self):
        self.downloaded_images_count = 0
        self.set_progress(-1, -1)
        return super().init()

    
    def run(self, **kwargs) -> dict[str, object]:

        queries = kwargs.get("queries", [])
        booru = kwargs.get("booru", "")
        limit = kwargs.get("limit", 10)
        batch_size = kwargs.get("batch_size", 10)

        if self.iterator is None:
            self.iterator = UrlGenerator(self.available_boorus[booru](), queries, limit)

        images_batch = []
        tags_batch = []
        for _ in range(batch_size):
            try:
                result = next(self.iterator)
                images_batch.append(pillow_from_any_string(result["url"]))
                tags_batch.append(result["tags"])
                self.downloaded_images_count += 1
                self.set_progress(self.downloaded_images_count, (limit * len(queries)))

            except StopIteration:
                break

        if len(images_batch) == 0:
            self.iterator = None
            self.set_progress(self.downloaded_images_count, (limit * len(queries)), False)
            return {
                "images": BaseNode.GeneratorExit(),
                "tags_string": BaseNode.GeneratorExit()
            }
        
        return {
            "images": images_batch,
            "tags_string": tags_batch
        }


if __name__ == "__main__":
    node = BooruDownloadNode()

    while True:
        batch = node.run(booru="gelbooru", queries=["cat", "dog"], limit=10, batch_size=5)

        if batch["images"] == BaseNode.GeneratorExit():
            break

        print(batch["images"])
