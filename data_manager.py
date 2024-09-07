import json
from logger import Logger


class DataManager:
    def __init__(self):
        self.filename = 'database.json'
        self.data = self.init()

    def init(self):
        try:
            with open(self.filename, 'r') as file:
                data = json.load(file)
                return set(data)
        except FileNotFoundError:
            return set()
        except json.JSONDecodeError as error:
            Logger.error('Error initializing DataManager:', error)
            raise

    def save(self):
        try:
            with open(self.filename, 'w') as file:
                json.dump(list(self.data), file, indent=2)
        except IOError as error:
            Logger.error('Error saving data:', error)
            raise

    def get_all_product_urls(self):
        """Return all product URLs."""
        return self.data

    def add_product_url(self, product_url):
        """Add a product URL to the set."""
        self.data.add(product_url)
        self.save()

    def product_exists(self, product_url):
        """Check if a product URL exists in the set."""
        return product_url in self.data

    def remove_product_url(self, product_url):
        """Remove a product URL from the set if it exists."""
        if product_url in self.data:
            self.data.remove(product_url)
            self.save()
        else:
            Logger.error(f"Product URL '{product_url}' not found.")
