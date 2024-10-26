import json
from logger import Logger


class DataManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
            cls._instance.filename = 'database.json'
            cls._instance.data = cls._instance.init()
        return cls._instance

    def init(self):
        Logger.info("Initializing DataManager")
        try:
            with open(self.filename, 'r') as file:
                data = json.load(file)
                data = {
                    'products': set(data.get('products', [])),
                    'channels': set(data.get('channels', []))
                }
                Logger.info("DataManager initialized with data", data)
                return data
        except FileNotFoundError:
            Logger.warn(f"Database file {self.filename} not found. Initializing with empty data.")
            return {'products': set(), 'channels': set()}
        except json.JSONDecodeError as error:
            Logger.error('Error initializing DataManager:', error)
            raise

    def save(self):
        Logger.info("Saving data to file")
        try:
            with open(self.filename, 'w') as file:
                json.dump({
                    'products': list(self.data['products']),
                    'channels': list(self.data['channels'])
                }, file, indent=2)
        except IOError as error:
            Logger.error('Error saving data:', error)
            raise

    def get_all_product_urls(self):
        """Return all product URLs."""
        return self.data['products']

    def add_product_url(self, product_url):
        """Add a product URL to the set."""
        Logger.info(f"Adding product URL: {product_url}")
        self.data['products'].add(product_url)
        self.save()

    def product_exists(self, product_url):
        """Check if a product URL exists in the set."""
        return product_url in self.data['products']

    def remove_product_url(self, product_url):
        """Remove a product URL from the set if it exists."""
        Logger.info(f"Removing product URL: {product_url}")
        if product_url in self.data['products']:
            self.data['products'].remove(product_url)
            self.save()
            Logger.info(f"Product URL '{product_url}' removed.")
        else:
            Logger.error(f"Product URL '{product_url}' not found.")

    def clear_all_products(self):
        """Clear all product URLs."""
        Logger.info("Clearing all product URLs")
        self.data['products'].clear()
        self.save()

    def add_notification_channel(self, channel_id):
        """Add a channel ID to the notification channels set."""
        Logger.info(f"Adding notification channel: {channel_id}")
        self.data['channels'].add(channel_id)
        self.save()
        return len(self.data['channels'])

    def remove_notification_channel(self, channel_id):
        """Remove a channel ID from the notification channels set."""
        Logger.info(f"Removing notification channel: {channel_id}")
        if channel_id in self.data['channels']:
            self.data['channels'].remove(channel_id)
            self.save()
            Logger.info(f"Channel '{channel_id}' removed.")
            return True
        else:
            Logger.warn(f"Channel '{channel_id}' not found in notification channels.")
            return False

    def get_notification_channels(self):
        """Get all notification channel IDs."""
        return self.data['channels']

    def channel_exists(self, channel_id):
        """Check if a channel ID exists in the notification channels set."""
        return channel_id in self.data['channels']
