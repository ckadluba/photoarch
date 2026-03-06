def get_keywords_from_caption(caption, stopwords) -> list[str]:
    keywords_full = caption.split()
    keywords_no_stopwords = [k for k in keywords_full if k.lower() not in stopwords]
    keywords_unique = list(dict.fromkeys(keywords_no_stopwords)) 
    return keywords_unique