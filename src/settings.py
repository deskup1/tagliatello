import yaml
import os

class Settings:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.settings = {}
        self.load()
        self.default_settings()

    def default_settings(self):
        if self.settings == {}:
            self.settings = {
                "hf_cache_dir": "hf_cache"
            }
            self.save()

    def load(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as file:
                file.write("")

        with open(self.file_path, "r") as file:
            self.settings = yaml.safe_load(file)
  
        if self.settings is None:
            self.settings = {}

    def save(self):
        with open(self.file_path, "w") as file:
            yaml.dump(self.settings, file)

        hf_cache_dir = self.settings.get("hf_cache_dir", None)
        if hf_cache_dir is not None:
            os.environ["HF_HOME"] = hf_cache_dir

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def __getitem__(self, key):
        return self.settings.get(key, None)
    
    def set(self, key, value):
        self.settings[key] = value

    def __setitem__(self, key, value):
        self.settings[key] = value

    def delete(self, key):
        del self.settings[key]

    def __delitem__(self, key):
        del self.settings[key]

    def __contains__(self, key):
        return key in self.settings

    def __iter__(self):
        return iter(self.settings)

    def __len__(self):
        return len(self.settings)
    
SETTINGS = Settings("app-data.yaml")