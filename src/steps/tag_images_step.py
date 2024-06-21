import PIL.Image
import tools.tagger as rt

class TagImagesStep:
    def __init__(self, tagger):
        self.tagger: rt.Wd14Tagger = tagger

    def run(self, **kwargs):
        images = kwargs["images"]
        results = []
        for image in images:
            tagger_result = self.tagger.tags(image)
            tags = {}


            for key, value in tagger_result[3].items():
                tags[key.replace("_", " ")] = value
            for key, value in tagger_result[4].items():
                tags[key.replace("_", " ")] = value
            # get largest item and its value from tagger_result[2]
            key, value = max(tagger_result[2].items(), key=lambda x: x[1])
            tags[key.replace("_", " ")] = value

            # append tags keys to results sorted by value
            results.append(sorted(tags, key=tags.get, reverse=True))

        return results
    
if __name__ == "__main__":
    image = PIL.Image.open("0142.png")
    tagger = rt.Wd14Tagger()
    step = TagImagesStep(tagger)
    results = step.run(images=[image])