from pymongo import MongoClient
from config import Config
import json
import os

# Singleton MongoDB client - reuse connection across requests
_mongo_client = None

def _get_client():
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000, maxPoolSize=10)
        except Exception:
            pass
    return _mongo_client

class EventContent:
    # Use JSON file as fallback when MongoDB is not available
    JSON_FILE = 'event_content.json'
    
    DEFAULT_CONTENT = {
        'event_date': 'March 4, 2026',
        'event_time': '10:00 AM – 5:00 PM',
        'venue': 'Amrakunja Park',
        'organizer': 'Spectra Group',
        'contact_persons': [
            {'name': 'Nirotyay Mukherjee', 'phone': '7278737263'},
            {'name': 'Anirban Sarkar', 'phone': '7439153943'}
        ],
        'pricing': {
            'entry_pass': 200,
            'entry_plus_starter': 350,
            'entry_plus_starter_lunch': 499,
            'food_available': 'Veg and Non-Veg options available at counters'
        },
        'complimentary': 'Abir & Special Lassi',
        'offers': '',
        'hero_image': 'static/images/holi-hero.jpg',
        'gallery_images': [
            'images/image 1.jpeg',
            'https://images.unsplash.com/photo-1576018617798-17d3969b8781?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1583163093287-1a0d5459bdce?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1615723795498-a89ca47339c7?w=800&h=600&fit=crop'
        ]
    }

    _content_cache = None
    _cache_time = 0
    CACHE_TTL = 60  # seconds

    @classmethod
    def get_collection(cls):
        try:
            client = _get_client()
            if client:
                client.admin.command('ping')
                return client.holi_party.event_content
        except Exception as e:
            print(f"MongoDB not available, using JSON fallback: {e}")
        return None

    @classmethod
    def get_content(cls):
        import time
        now = time.time()
        if cls._content_cache and (now - cls._cache_time) < cls.CACHE_TTL:
            return cls._content_cache
        collection = cls.get_collection()
        if collection is not None:
            content = collection.find_one()
            if content:
                cls._content_cache = content
                cls._cache_time = now
                return content
            else:
                cls.save_content(cls.DEFAULT_CONTENT)
                cls._content_cache = cls.DEFAULT_CONTENT
                cls._cache_time = now
                return cls.DEFAULT_CONTENT
        else:
            return cls._load_from_json()

    @classmethod
    def invalidate_cache(cls):
        cls._content_cache = None
        cls._cache_time = 0

    @classmethod
    def save_content(cls, content):
        collection = cls.get_collection()
        if collection is not None:
            collection.replace_one({}, content, upsert=True)
            cls.invalidate_cache()
        else:
            with open(cls.JSON_FILE, 'w') as f:
                json.dump(content, f, indent=2)
            cls.invalidate_cache()

    @classmethod
    def _load_from_json(cls):
        if os.path.exists(cls.JSON_FILE):
            with open(cls.JSON_FILE, 'r') as f:
                return json.load(f)
        else:
            cls.save_content(cls.DEFAULT_CONTENT)
            return cls.DEFAULT_CONTENT

class Booking:
    # Use JSON file as fallback when MongoDB is not available
    JSON_FILE = 'bookings.json'

    @classmethod
    def get_collection(cls):
        try:
            client = _get_client()
            if client:
                client.admin.command('ping')
                return client.holi_party.bookings
        except Exception as e:
            print(f"MongoDB not available, using JSON fallback: {e}")
        return None

    def __init__(self, name, email, phone, address, passes, ticket_id, order_id, payment_status='Pending', entry_status='Not Used', pass_type='entry', amount=None, is_group_booking=False):
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self.passes = passes
        self.ticket_id = ticket_id
        self.order_id = order_id
        self.payment_status = payment_status
        self.entry_status = entry_status
        self.pass_type = pass_type
        self.amount = amount if amount is not None else passes * 200
        self.is_group_booking = is_group_booking

    def save(self):
        collection = self.get_collection()
        if collection is not None:
            collection.insert_one(self.__dict__)
        else:
            # Save to JSON file
            self._save_to_json()

    def _save_to_json(self):
        bookings = self._load_from_json()
        bookings.append(self.__dict__)
        with open(self.JSON_FILE, 'w') as f:
            json.dump(bookings, f, indent=2, default=str)

    @classmethod
    def find_one(cls, **kwargs):
        collection = cls.get_collection()
        if collection is not None:
            return collection.find_one(kwargs)
        else:
            # Load from JSON file
            bookings = cls._load_from_json()
            for booking in bookings:
                if all(booking.get(k) == v for k, v in kwargs.items()):
                    return booking
            return None

    @classmethod
    def find_all(cls):
        collection = cls.get_collection()
        if collection is not None:
            return list(collection.find())
        else:
            # Load from JSON file
            return cls._load_from_json()

    @classmethod
    def update_one(cls, filter_dict, update_dict):
        collection = cls.get_collection()
        if collection is not None:
            return collection.update_one(filter_dict, update_dict)
        else:
            # Update in JSON file
            bookings = cls._load_from_json()
            for i, booking in enumerate(bookings):
                if all(booking.get(k) == v for k, v in filter_dict.items()):
                    bookings[i].update(update_dict['$set'])
                    with open(cls.JSON_FILE, 'w') as f:
                        json.dump(bookings, f, indent=2, default=str)
                    return type('Result', (), {'modified_count': 1})()
            return type('Result', (), {'modified_count': 0})()

    @classmethod
    def delete_one(cls, filter_dict):
        collection = cls.get_collection()
        if collection is not None:
            return collection.delete_one(filter_dict)
        else:
            bookings = cls._load_from_json()
            for i, booking in enumerate(bookings):
                if all(booking.get(k) == v for k, v in filter_dict.items()):
                    bookings.pop(i)
                    with open(cls.JSON_FILE, 'w') as f:
                        json.dump(bookings, f, indent=2, default=str)
                    return type('Result', (), {'deleted_count': 1})()
            return type('Result', (), {'deleted_count': 0})()

    @classmethod
    def _load_from_json(cls):
        if os.path.exists(cls.JSON_FILE):
            with open(cls.JSON_FILE, 'r') as f:
                return json.load(f)
        return []
