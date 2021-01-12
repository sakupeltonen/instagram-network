import pyautogui as gui
from time import sleep
# also requires opencv-python for setting confidence level in locateOnScreen
# needs to be modified for retina support

# pause between every autogui action
gui.PAUSE = 0.1
# mouse to top-left corner stops program
gui.FAILSAFE = True


def _do_shortcut(modifiers, key):
    if isinstance(modifiers, str):
        modifiers = [modifiers]
    for k in modifiers:
        gui.keyDown(k)
    gui.press(key)
    for k in modifiers:
        gui.keyUp(k)


def open_program(term='nord'):
    _do_shortcut('option', 'space')
    gui.write(term)
    gui.press('enter')
    sleep(3)


def full_screen():
    _do_shortcut(["option", "ctrl"], "enter")


def establish_vpn(country):
    open_program()
    full_screen()
    location = gui.locateOnScreen("ui_elements/" + country + ".png", confidence=.7)
    assert location, "Could not find " + country
    gui.moveTo(location)
    gui.click()
    sleep(3)
    if _vpn_status():
        print("VPN: connected to " + country)
    open_program("pycharm")


def _vpn_status():
    # not_connected = gui.locateOnScreen("connect2.png")
    connected = gui.locateOnScreen("ui_elements/disconnect2.png")
    cancel = gui.locateOnScreen("ui_elements/cancel.png")

    if cancel:
        sleep(5)
        # not_connected = gui.locateOnScreen("connect2.png")
        connected = gui.locateOnScreen("ui_elements/disconnect2.png")

    assert connected, "Could not connect to VPN"

    return True


