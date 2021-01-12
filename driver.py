from scraper import InstaBot
from database import UserDatabase
from other import secrets
from insight import *
from other.autogui import establish_vpn
import time
import datetime

HIBERNATION_INTERVAL = 15
USER_CHANGE_INTERVAL = 50
FOLL_CAP = 1000

db = UserDatabase("instagram2.db")

senpai = common_tools.Senpai()  # sleep and data tracker


bot = None
own_users = list(secrets.users.keys())
current_user_index = -1


def switch_user(bot, current_user_index):
    if bot:
        bot.driver.close()
    # change vpn
    current_user_index += 1
    current_user = own_users[current_user_index]
    pw = secrets.users[current_user]
    return InstaBot(current_user, pw, senpai), current_user_index

# bot, current_user_index = switch_user(bot, current_user_index)


def scrape(users):
    requests_sent = 0

    for user in users:
        if not should_scrape(db, user, FOLL_CAP):
            continue

        start_time = time.time()
        print("")
        print(user)

        # Find account page
        try:
            bot.find_account(user)
        except NameError as e:
            print(e)
            db.mark_username_changed(user)
            continue

        requests_sent += 1

        # Check if we have image
        get_image = not common_tools.got_image(user)

        # Scrape data
        try:
            data = bot.get_user_data(user, cap=FOLL_CAP, get_image=get_image)
        except Exception as e:
            print(e)
            continue

        private, n_post, n_followers, n_following, \
            followers, following, name, bio, post_descriptions = data

        private = int(private)
        if not name:
            name = ""

        name_encoded = name.encode("utf-8")
        bio_encoded = bio.encode("utf-8")

        data_dict = {"private": private, "post_count": n_post,
                     "followers_count": n_followers, "following_count": n_following,
                     "name": name_encoded, "bio": bio_encoded}

        db.set(user, data_dict)

        if name != "":
            print("{}\n{}".format(name, repr(bio)))
        else:
            print("{}".format(repr(bio)))

        print("private {}, n_post {}, n_followers {}, n_following {}"
              .format(bool(private), n_post, n_followers, n_following))

        if followers and following:
            print("Followers: {}".format(followers))
            print("Following: {}".format(following))

            n_followers_int = common_tools.string_to_int(n_followers)  # temp
            n_following_int = common_tools.string_to_int(n_following)
            if len(followers) != n_followers_int:
                print("Error: len(followers) {} doesn't match n_followers {}".
                      format(len(followers), n_followers_int))
            if len(following) != n_following_int:
                print("Error: len(followers) {} doesn't match n_followers {}".
                      format(len(following), n_following_int))

        if post_descriptions:
            print("{} post descriptions".format(len(post_descriptions)))

        end_time = time.time()
        time_message = datetime.datetime.now().strftime("%A, %d. %H:%M:%S")
        time_elapsed = int(end_time - start_time)
        print("{} (took {}s)".format(time_message, time_elapsed))

        if followers and following:
            db.insert_followers(user, followers)
            db.insert_following(user, following)
            requests_sent += len(followers) // 150  # 12
            requests_sent += len(following) // 150  # 12
            # eg. 500+500 foll corresponds to loading pages of about 7 accounts

        if post_descriptions:
            post_descriptions = [(desc[0], desc[1].encode("utf-8"))
                                 for desc in post_descriptions]
            db.insert_post_descriptions(user, post_descriptions)


        db.conn.commit()

        senpai.random_delay(5)
        if requests_sent % USER_CHANGE_INTERVAL == USER_CHANGE_INTERVAL - 1:
            return

        if requests_sent % HIBERNATION_INTERVAL == HIBERNATION_INTERVAL - 1:
            senpai.hibernate(time=300)


bio_todo = get_bio_priority(db)

while True:
    establish_vpn("austria")
    bot, current_user_index = switch_user(bot, current_user_index)
    scrape([x[0] for x in bio_todo])

