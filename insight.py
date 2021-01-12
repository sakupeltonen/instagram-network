from operator import itemgetter  # sorted(list, key=itemgetter(1), reverse=True)

import re
import emojis

from other import common_tools


def get_mutual_relationships(db):
    """Get list of tuples where users follow each other."""
    sql = """
        SELECT a.source, a.target
        FROM (SELECT * FROM followers) a 
        INNER JOIN (SELECT * FROM followers) b 
        ON a.source=b.target AND a.target=b.source"""

    return db.simple_query(sql)


def get_tagged_users(db):
    """Extract all lists of tagged users from photo descriptions."""
    sql = """SELECT username, description FROM pictures"""
    data = db.simple_query(sql)

    res = []
    for username, desc in data:
        desc = desc.decode("utf-8")
        if not desc:
            continue
        tags = extract_tags(desc, excluding=username)
        if tags:
            tags[-1] = tags[-1][:-1]  # remove dot
            res.append((username, tags))

    # convert to dict
    followers = db.simple_query("SELECT username FROM accounts")
    res_dict = {x[0]: [] for x in followers}

    for pair in res:
        tagger, tagged = pair  # (tagger, [users])
        res_dict[tagger] += tagged

    return res_dict


def extract_tags(text, excluding=None):
    """
    Extract tags from a text eg. an automatically generated description of a photo.

    Input
        text:
        excluding: username. usually the username of the tagger, because it is always included in the
            automatically generated descriptions

    TODO remove duplicate get_tagged_users
    """

    lines = text.splitlines()
    words = [word for line in lines for word in line.split(" ")]
    tags = [word for word in words if '@' in word]

    # remove the @ sign. have to be careful because foo@username is a valid tag
    tags = [tag.split('@')[-1] for tag in tags]

    if excluding:
        tags = [tag for tag in tags if tag != excluding]
    return tags


def get_bio_priority(db, min_count=10, also_private=True):
    """
    Helper function used to find users that should be scraped next

    TODO when names are scraped through lists, should look at whether bio is not Null.
    """

    # empty string marks an empty bio that has been scraped
    _sql = ""
    if not also_private:
        _sql = "AND (b.private IS NULL OR b.private==0)"

    sql = """
        SELECT b.username, a.count
        FROM (SELECT target, COUNT(*) AS count
              FROM followers GROUP BY target) a
              INNER JOIN
              (SELECT username, private, name, bio, username_changed
              FROM accounts) b
              ON a.target=b.username
        WHERE a.count > {} AND name IS NULL AND username_changed IS NOT 1 {}"""\
        .format(min_count, _sql)

    records = db.simple_query(sql)
    records = sorted(records, key=itemgetter(1), reverse=True)
    return records


def get_priority(db, also_private=False):
    """
    Helper function used to find users that should be scraped next.

    Returns:
        [(username, count of scraped followers)] in descending order of count
        where the users are not private, and whose followers haven't been scraped

    note: doesn't filter out users who have too many eg. >1000 followers
    """

    _sql = ""
    if not also_private:
        _sql = "AND (b.private IS NULL OR b.private==0)"

    sql = """
        SELECT b.username, a.count
        FROM (SELECT target, COUNT(*) AS count
              FROM followers GROUP BY target) a
              INNER JOIN
              (SELECT username, private, followers_updated_date
              FROM accounts) b
              ON a.target=b.username
        WHERE b.followers_updated_date IS NULL {}""".format(_sql)

    records = db.simple_query(sql)
    records = sorted(records, key=itemgetter(1), reverse=True)
    return records


def should_scrape(db, username, cap):
    info = db.get("all_info", username)

    _, private, _, followers_count, following_count, \
        followers_updated_date, following_updated_date,\
        name, bio, username_changed = info

    if bio is None:
        return True  # bio hasn't been scraped

    if username_changed:
        return False

    if private is None:
        return True  # profile hasn't been looked at

    if private:
        return False

    if followers_updated_date is None:
        n_followers = common_tools.string_to_int(followers_count)
        n_following = common_tools.string_to_int(following_count)

        if n_followers < 13 or n_following < 13:
            return False
        if n_followers < cap and n_following < cap:
            return True
    return False


def texts_to_dict(db):
    """
    TEMP: process bios
    """
    sql = """SELECT username, bio FROM accounts WHERE bio IS NOT NULL AND bio IS NOT "" """
    data = db.simple_query(sql)
    data = [(x[0], x[1].decode("utf-8")) for x in data]
    data = [x for x in data if x[1] != ""]

    category_dict = {category: [x.emoji for x in emojis.db.get_emojis_by_category(category)]
                     for category in emojis.db.get_categories()}
    # not interesting categories: food & drink, travel & places, animals & nature, symbols
    #   - objects: mainly used for eg. 📍, 📩 . could be useful for structuring but not interesting as a feature
    # interesting categories: activity, smileys & emotion, flags
    all_emojis = emojis.db.get_emoji_aliases().values()
    feature_emojis = category_dict["Activities"] + \
                     category_dict["Smileys & Emotion"] + \
                     category_dict["Flags"]

    other_emojis = [e for e in all_emojis if e not in feature_emojis]

    # other_emojis contains many interesting: staff of hermes, justice thing, wave,

    delimiters = ["\n", " ", ",", "&", "-", "\|"] # + other_emojis
    regex = "|".join(delimiters)
    # regex = regex[:3338] + regex[3350:]  # didn't recognize these for some reason

    def custom_split(text):
        emoji_features = []
        # interesting_emoji_features = []
        # not_interesting_emoji_features = []
        for e in set(emojis.iter(text)):
            emoji_features.append(e)
            text = text.replace(e, " ")
            # if e in feature_emojis:
            #     interesting_emoji_features.append(e)
            # else:
            #     not_interesting_emoji_features.append(e)

        splitted = re.split(regex, text)
        splitted = [w for w in splitted if w != ""]
        return splitted, emoji_features  # interesting_emoji_features, not_interesting_emoji_features

    data_splitted = [(x[0], *custom_split(x[1])) for x in data]

    # words
    word_sets = [set(x[1]) for x in data_splitted]
    all_words = set([word for x in word_sets for word in x])
    word_counts = {word.lower(): 0 for word in all_words}

    for word_set in word_sets:
        for word in word_set:
            word_counts[word.lower()] += 1

    res = list(word_counts.items())
    res = sorted(res, key=itemgetter(1), reverse=True)

    # emojis
    emoji_sets = [set(x[2]) for x in data_splitted]
    emoji_counts = {e:0 for e in all_emojis}

    for emoji_set in emoji_sets:
        for e in emoji_set:
            emoji_counts[e] += 1

    emoji_res = list(emoji_counts.items())
    emoji_res = sorted(emoji_res, key=itemgetter(1), reverse=True)

    return word_counts
    # extract tags
    # words ending in dot could be fixed