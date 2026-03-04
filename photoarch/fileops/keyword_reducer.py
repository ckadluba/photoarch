from collections import Counter


def select_top_words(keywords, top_n=7):
    """
    Cleans a list of keywords:
    - Remove duplicates (case-insensitive)
    - Selection of top-N most frequent words
    - Preserves original capitalization

    :param keywords: list of strings
    :param top_n: maximum number of keywords for the folder name
    :return: cleaned list of top-N keywords
    """

    # Count frequency (case-insensitive) but keep original words
    word_variants = {}  # lowercase -> list of original variants
    for word in keywords:
        lower = word.lower()
        if lower not in word_variants:
            word_variants[lower] = []
        word_variants[lower].append(word)

    # Count frequencies for each lowercase variant
    lowercase_counts = Counter([w.lower() for w in keywords])

    # For each lowercase word, pick the most common capitalization variant
    result = []
    for lower_word, count in lowercase_counts.most_common(top_n):
        # Pick most common variant (or first if tied)
        variants = word_variants[lower_word]
        most_common_variant = Counter(variants).most_common(1)[0][0]
        result.append(most_common_variant)

    return result
