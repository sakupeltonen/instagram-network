from selenium import webdriver

import urllib.request  # temp for images
import os

from other import common_tools

MIN_FOLL = 12  # avoid annoying suggestions section in short lists

"""
private methods generally assume that bot is already on user's page
"""

class InstaBot:
    def __init__(self, username, pw, sleeper):
        self.username = username
        self.s = sleeper
        self.driver = webdriver.Chrome()
        self.driver.get("https://instagram.com")
        sleeper.random_delay(2)

        # accept cookies
        try:
            self.driver.find_element_by_xpath("/html/body/div[2]/div/div/div/div[2]/button[1]").click()
            sleeper.random_delay(1)
        except Exception as e:
            pass

        # Log in
        self.driver.find_element_by_xpath("//input[@name=\"username\"]").send_keys(username)
        self.driver.find_element_by_xpath("//input[@name=\"password\"]").send_keys(pw)
        self.driver.find_element_by_xpath('//button[@type="submit"]').click()
        sleeper.random_delay(3)

        # Click not now on enable notifications
        try:
            self.driver.find_element_by_xpath("//button[contains(text(), 'Not Now')]").click()
            sleeper.random_delay(2)
            self.driver.find_element_by_xpath("//button[contains(text(), 'Not Now')]").click()
            sleeper.random_delay(2)
        except Exception as e:
            pass

        self.scroll_retries = 15
        self.scroll_delay = 0.4
        self.scroll_retry_delay = 1.5

    def find_account(self, username):
        self.driver.get("https://instagram.com/{}".format(username))
        self.s.random_delay(1.5)
        not_found = "Sorry, this page isn't available." in self.driver.page_source
        if not_found:
            raise NameError("{} not found".format(username))

    def _get_followers(self):
        return self._get_list("followers")

    def _get_following(self):
        return self._get_list("following")

    def _get_list(self, foll):
        """Starts from user page, assumes that not private to self.username.
        Lists where suggestions may appear fail."""
        assert foll in ["followers", "following"], "Invalid foll: {}" % foll

        try:
            # Click followers / following button
            foll_btn = self.driver.find_element_by_xpath("//a[contains(@href,'/{}')]".format(foll))
            foll_btn.click()
            self.s.random_delay(3)

            # scroll_box = self.driver.find_element_by_xpath("/html/body/div[4]/div/div/div[2]")
            scroll_box = self.driver.find_element_by_class_name("isgrP")

            last_ht, ht = 0, 1
            retries_left = self.scroll_retries
            retries_used = 0
            current_retries = 0
            while last_ht != ht or retries_left > 0:
                last_ht = ht
                self.s.random_delay(self.scroll_delay)
                ht = self.driver.execute_script("""
                                    arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                                    return arguments[0].scrollHeight;
                                    """, scroll_box)
                if last_ht == ht:
                    retries_left -= 1
                    current_retries += 1
                    self.s.random_delay(self.scroll_retry_delay)
                else:
                    # if managed to move, adds the amount of retries to the retries used counter
                    # this won't be called when the list actually ends
                    retries_used += current_retries
                    current_retries = 0

            links = scroll_box.find_elements_by_tag_name('a')

            names = [name.text for name in links if name.text != '']
            if "See All Suggestions" in names:
                print("Error: 'See All Suggestions' in names")
            print("-- scraped: {} with {}/{} retries used, retry delay {}s, scroll delay {:.2}s--"
                  .format(len(names), retries_used, self.scroll_retries,
                          self.scroll_retry_delay, self.scroll_delay))
            if retries_used > self.scroll_retries / 2:
                self.scroll_delay += 0.03
            else:
                self.scroll_delay -= 0.02
                self.scroll_delay = max(self.scroll_delay, 0.32)

            # Close the list
            # self.driver.find_element_by_xpath("/html/body/div[4]/div/div/div[1]/div/div[2]/button").click()
            # self.driver.find_element_by_class_name("wpO6b ")
            self.driver.refresh()
            self.s.random_delay(2)
        except Exception as e:
            print(e)
            return None

        return names

    def _get_info(self):
        """
        Private method returning is_private and counts
        Can be used on any accounts that are private or public
        """
        private = "This Account is Private" in self.driver.page_source
        # n. of posts, followers, following
        counts = self.driver.find_elements_by_class_name("g47SY ")
        counts = tuple([count.text for count in counts])
        return (private, *counts)

    def _get_profile_pic(self, user, private):
        """
        Private method for getting profile pic, and converting jpg to png with alpha channel
        """
        if private:
            img = self.driver.find_element_by_class_name("be6sR")
        else:
            img = self.driver.find_element_by_class_name("_6q-tv")

        src = img.get_attribute('src')
        path = os.getcwd() + "/img/"
        urllib.request.urlretrieve(src, "{}{}.jpg".format(path, user))
        self.s.random_delay(2)

        # Convert to PNG
        if os.path.isfile(path + user + ".jpg"):
            common_tools.add_alpha(path + user)
        else:
            print("{}: could not find image".format(user))

    def _get_post_descriptions(self):
        # TODO scroll to the bottom to load all images (if under some max amount)

        # image url provides a unique identifier
        tile_elements = self.driver.find_elements_by_css_selector(
            "div[class='v1Nh3 kIKUG  _bz0w']")
        self.s.random_delay(1)
        ids = [image.find_element_by_tag_name("a").get_attribute("href")
               for image in tile_elements]
        self.s.random_delay(1)
        # https://www.instagram.com/p/CBoaLX4p8Kk/ --> CBoaLX4p8Kk
        ids = [_id.split("/")[-2] for _id in ids]

        # get instagram generated descriptions
        image_elements = self.driver.find_elements_by_class_name("KL4Bh")
        self.s.random_delay(1)
        descriptions = [image.find_element_by_tag_name("img").get_attribute("alt")
                        for image in image_elements]
        self.s.random_delay(1)

        return list(zip(ids, descriptions))

    def _get_bio(self):
        name, bio = None, None
        try:
            name_element = self.driver.find_element_by_class_name("rhpdm")
            name = name_element.text
            bio = self.driver.find_element_by_class_name("-vDIg").text.split('\n')[1:]
            bio = '\n'.join(bio)
        except Exception as _:
            bio = self.driver.find_element_by_class_name("-vDIg").text

        return name, bio

    def get_user_data(self, username, cap=1000,
                      get_followers=True, get_following=True, get_image=True):
        """
        Public method for scraping username
        """
        # self.find_account(username)
        private, n_post, n_followers, n_following = self._get_info()

        followers, following, post_descriptions = None, None, None

        if get_image:
            self._get_profile_pic(username, private)

        name, bio = self._get_bio()

        if not private:
            post_descriptions = self._get_post_descriptions()

            n_followers_int = common_tools.string_to_int(n_followers)
            n_following_int = common_tools.string_to_int(n_following)

            if MIN_FOLL < n_followers_int < cap and MIN_FOLL < n_following_int < cap:
                if get_followers:
                    followers = self._get_followers()

                if get_following:
                    following = self._get_following()

        return private, n_post, n_followers, n_following, followers, following, name, bio, post_descriptions


