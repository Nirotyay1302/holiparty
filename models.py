from pymongo import MongoClient
from config import Config
import json
import os
import tempfile
from datetime import datetime

# Singleton MongoDB client - reuse connection across requests
_mongo_client = None
_mongo_disabled_until = 0  # epoch seconds; backoff when Mongo is failing

def _data_path(filename: str) -> str:
    base = getattr(Config, "DATA_DIR", "") or ""
    base = base.strip()
    if base:
        try:
            os.makedirs(base, exist_ok=True)
        except Exception:
            pass
        return os.path.join(base, filename)
    return filename

def _atomic_write_json(path: str, payload):
    """Write JSON atomically to avoid partial/corrupt files."""
    d = os.path.dirname(path) or "."
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    fd, tmp_path = tempfile.mkstemp(prefix="tmp_", suffix=".json", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass

def _deep_merge_keep_existing(base, updates):
    """
    Deep merge dictionaries without deleting existing data.
    - Empty strings / None / empty dicts are ignored (keep previous value)
    - Empty lists are ignored (keep previous value)
    - Non-empty lists replace previous lists
    """
    if not isinstance(base, dict) or not isinstance(updates, dict):
        return updates

    merged = dict(base)
    for k, v in updates.items():
        if k == "_id":
            continue
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        if isinstance(v, dict):
            if not v:
                continue
            merged[k] = _deep_merge_keep_existing(base.get(k, {}) if isinstance(base.get(k), dict) else {}, v)
            continue
        if isinstance(v, list):
            if not v:
                continue
            # if list is only empty strings, ignore
            if all((isinstance(i, str) and i.strip() == "") for i in v):
                continue
            merged[k] = v
            continue
        merged[k] = v
    return merged

def _strip_mongo_id(doc):
    if isinstance(doc, dict) and "_id" in doc:
        doc = dict(doc)
        doc.pop("_id", None)
    return doc

def _get_client():
    global _mongo_client
    global _mongo_disabled_until

    # When Mongo is down (TLS, network, auth), avoid blocking every request.
    try:
        import time
        if _mongo_disabled_until and time.time() < _mongo_disabled_until:
            return None
    except Exception:
        pass

    if _mongo_client is None:
        try:
            if not getattr(Config, "MONGO_URI", None):
                return None

            # TLS hardening for Atlas + Render. Using certifi avoids missing/old CA bundles.
            tls_kwargs = {}
            try:
                import certifi  # type: ignore
                tls_kwargs["tlsCAFile"] = certifi.where()
            except Exception:
                # If certifi isn't available, fall back to system CA.
                tls_kwargs = {}

            _mongo_client = MongoClient(
                Config.MONGO_URI,
                # Faster failover to JSON fallback keeps site responsive
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000,
                maxPoolSize=10,
                tls=True,
                **tls_kwargs,
            )
            # Re-enable Mongo on successful client init
            try:
                _mongo_disabled_until = 0
            except Exception:
                pass
        except Exception:
            pass
    return _mongo_client

class EventContent:
    # Use JSON file as fallback when MongoDB is not available
    JSON_FILE = _data_path('event_content.json')
    
    DEFAULT_CONTENT = {
        'event_date': 'March 4, 2026',
        'event_time': '10:00 AM – 5:00 PM',
        'venue': 'Dighi Garden Mankundu',
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
    CACHE_TTL = 300  # seconds (admin updates invalidate cache immediately)

    @classmethod
    def get_collection(cls):
        try:
            client = _get_client()
            if client:
                client.admin.command('ping')
                return client.holi_party.event_content
        except Exception as e:
            print(f"MongoDB not available, using JSON fallback: {e}")
            # Backoff to keep website responsive if Mongo is down
            try:
                import time
                global _mongo_disabled_until
                _mongo_disabled_until = time.time() + 60
            except Exception:
                pass
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
            # Cache JSON fallback too (avoids repeated DB attempts on each request)
            content = cls._load_from_json()
            cls._content_cache = content
            cls._cache_time = now
            return content

    @classmethod
    def invalidate_cache(cls):
        cls._content_cache = None
        cls._cache_time = 0

    @classmethod
    def save_content(cls, content):
        collection = cls.get_collection()
        if collection is not None:
            # Merge with existing record to avoid deleting previous data
            existing = _strip_mongo_id(collection.find_one() or {})
            merged = _deep_merge_keep_existing(existing, _strip_mongo_id(content or {}))
            collection.replace_one({}, merged, upsert=True)
            cls.invalidate_cache()
        else:
            # Merge with existing JSON to avoid deleting previous data
            existing = cls._load_from_json() if os.path.exists(cls.JSON_FILE) else {}
            existing = _strip_mongo_id(existing or {})
            merged = _deep_merge_keep_existing(existing, _strip_mongo_id(content or {}))
            _atomic_write_json(cls.JSON_FILE, merged)
            cls.invalidate_cache()

    @classmethod
    def _load_from_json(cls):
        if os.path.exists(cls.JSON_FILE):
            try:
                with open(cls.JSON_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return cls.DEFAULT_CONTENT
        else:
            cls.save_content(cls.DEFAULT_CONTENT)
            return cls.DEFAULT_CONTENT

class Booking:
    # Use JSON file as fallback when MongoDB is not available
    JSON_FILE = _data_path('bookings.json')

    @classmethod
    def get_collection(cls):
        try:
            client = _get_client()
            if client:
                client.admin.command('ping')
                return client.holi_party.bookings
        except Exception as e:
            print(f"MongoDB not available, using JSON fallback: {e}")
            # Backoff to keep website responsive if Mongo is down
            try:
                import time
                global _mongo_disabled_until
                _mongo_disabled_until = time.time() + 60
            except Exception:
                pass
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
        self.booking_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
        _atomic_write_json(self.JSON_FILE, bookings)

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
            # Load from JSON file; if empty/missing, fall back to Google Sheet (persistent)
            data = cls._load_from_json()
            if data:
                return data
            try:
                from utils.excel_utils import read_bookings_from_google_sheet
                sheet_data = read_bookings_from_google_sheet()
                return sheet_data or []
            except Exception:
                return data

    @classmethod
    def update_one(cls, filter_dict, update_dict):
        collection = cls.get_collection()
        if collection is not None:
            try:
                result = collection.update_one(filter_dict, update_dict)
                return result
            except Exception as e:
                print(f"Mongo update_one error: {e}")
                # Fall through to JSON fallback
                collection = None
        
        # Update in JSON file
        try:
            bookings = cls._load_from_json()
            found = False
            for i, booking in enumerate(bookings):
                if all(str(booking.get(k, '')).strip().upper() == str(v).strip().upper() for k, v in filter_dict.items()):
                    bookings[i].update(update_dict.get('$set', {}))
                    found = True
                    break
            
            if found:
                _atomic_write_json(cls.JSON_FILE, bookings)
                return type('Result', (), {'modified_count': 1})()
            return type('Result', (), {'modified_count': 0})()
        except Exception as e:
            print(f"JSON update_one error: {e}")
            import traceback
            traceback.print_exc()
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
                    _atomic_write_json(cls.JSON_FILE, bookings)
                    return type('Result', (), {'deleted_count': 1})()
            return type('Result', (), {'deleted_count': 0})()

    @classmethod
    def _load_from_json(cls):
        if os.path.exists(cls.JSON_FILE):
            try:
                with open(cls.JSON_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except Exception:
                return []
        return []
