# Constants and configuration

INPUT_DIR_STR = "./input_photos"
OUTPUT_DIR_STR = "./sorted_photos"
CACHE_DIR_STR = ".cache"
IMAGE_FILE_EXTENSIONS = {".jpg" }
VIDEO_FILE_EXTENSIONS = {".mp4"}

# Model paths
MODEL_NAME = "Salesforce/blip2-flan-t5-xl"
MODEL_CACHE_DIR = "./models"

# English stopwords for keyword generation
STOPWORDS = {
    "a", "an", "and", "the", "of", "in", "on", "with", "for", "at", "by", "from",
    "to", "up", "down", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "can", "will", "just", "don", "should",
    "now", "it", "is", "are", "was", "were", "be", "been", "being", "have", "has", 
    "having", "do", "does", "did", "doing", "his", "her", "its", "they", "them", "this", 
    "that", "hers", "ours", "yours", "their", "what", "which", "who", "whom", "whose", "my"
}

# German stopwords for keyword generation
STOPWORDS_GERMAN = {
    "ein", "eine", "einer", "eines", "einem", "einen", "und", "der", "die", "das", 
    "von", "in", "an", "auf", "mit", "für", "bei", "durch", "aus", "zu", "nach", 
    "vor", "hinter", "über", "unter", "wieder", "weiter", "dann", "einmal", "hier",
    "dort", "da", "wann", "wo", "warum", "wie", "alle", "jeder", "jede", "jedes", 
    "beide", "einige", "wenige", "mehr", "meist", "meiste", "andere", "manche", 
    "solche", "kein", "keine", "nicht", "nur", "eigen", "selbst", "gleich", "so", 
    "als", "auch", "sehr", "kann", "wird", "werden", "soll", "sollte", "jetzt", 
    "es", "ist", "sind", "war", "waren", "sein", "gewesen", "haben", "hat", "hatte",
    "tun", "tut", "tat", "sein", "ihr", "ihre", "sein", "seine", "sie", "ihnen", 
    "dies", "diese", "dieser", "dieses", "dem", "den", "des", "im", "am", "zum", 
    "zur", "ins", "vom", "beim", "bei", "über", "unter", "um", "darauf", "darin",
    "ihres", "unser", "unsere", "unserer", "unseres", "euer", "eure", "eurer", "eures"
}

# OpenStreetMap Nominatim URL
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

FOLDER_MAX_DISTANCE_METERS = 1000  # Maximum distance in meters to consider photos as belonging to the same folder
FOLDER_MAX_TIME_DIFFERENCE_HOURS = 3  # Maximum time difference in hours to consider photos as belonging to the same folder
FOLDER_FORBIDDEN_CHARS = r'[:/\\"\'<>&|,;]„“' # Characters not used in folder names

# Month names for folder naming
MONTH_NAMES = [
    "01 Jan", "02 Feb", "03 Mar", "04 Apr", "05 May", "06 Jun",
    "07 Jul", "08 Aug", "09 Sep", "10 Oct", "11 Nov", "12 Dec"
]
