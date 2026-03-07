from typing import Final


# Constants and configuration

INPUT_DIR_STR: Final = "./input_photos"
OUTPUT_DIR_STR: Final = "./sorted_photos"
CACHE_DIR_STR: Final = ".photoarch"
IMAGE_FILE_EXTENSIONS: Final = {".jpg", ".png" }
VIDEO_FILE_EXTENSIONS: Final = {".mp4"}

# AI Model names and parameters
IMAGE_CAPTIONING_MODEL_NAME: Final = "Salesforce/blip2-flan-t5-xl"
SEMANTIC_SIMILARITY_MODEL_NAME: Final = "paraphrase-multilingual-MiniLM-L12-v2"
MODEL_CACHE_DIR: Final = "./models"

# English stopwords for keyword generation
STOPWORDS: Final = {
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
STOPWORDS_GERMAN: Final = {
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
    "ihres", "ihrem", "unser", "unsere", "unserer", "unseres", "euer", "eure", 
    "eurer", "eures"
}

KEYWORD_GENERIC_VIDEO: Final = "Video"  # Generic keyword for videos without meaningful AI-generated keywords

# OpenStreetMap Nominatim URL
NOMINATIM_URL: Final = "https://nominatim.openstreetmap.org/reverse"

# Foldering heuristics thresholds
FOLDER_MAX_DISTANCE_METERS: Final = 1500  # Maximum distance in meters to consider photos as belonging to the same folder
FOLDER_MAX_TIME_DIFFERENCE_HOURS: Final = 2  # Maximum time difference in hours to consider photos as belonging to the same folder
FOLDER_MAX_DIFFERENCE_SCORE_THRESHOLD: Final = 0.58  # Maximum difference score before starting a new folder (0.0-1.0)

# Weights for foldering criteria (must sum to 1.0)
FILE_DIFF_SCORE_TIME_WEIGHT: Final = 0.39 
FILE_DIFF_SCORE_LOCATION_WEIGHT: Final = 0.39
FILE_DIFF_SCORE_CAPTION_WEIGHT: Final = 0.22

# Adjusted weights when GPS data is missing (must sum to 1.0)
FILE_DIFF_SCORE_TIME_WEIGHT_NO_GPS: Final = 0.62
FILE_DIFF_SCORE_LOCATION_WEIGHT_NO_GPS: Final = 0.0
FILE_DIFF_SCORE_CAPTION_WEIGHT_NO_GPS: Final = 0.38

FOLDER_FORBIDDEN_CHARS: Final = r'[:/\\"\'<>&|.,;„“]' # Characters not used in folder names
FOLDER_NAME_KEYWORDS: Final = 10  # Number of keywords to include in folder names

# Month names for folder naming
MONTH_NAMES: Final = [
    "01 Jan", "02 Feb", "03 Mar", "04 Apr", "05 May", "06 Jun",
    "07 Jul", "08 Aug", "09 Sep", "10 Oct", "11 Nov", "12 Dec"
]
