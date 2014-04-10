import threading
import sys
import mariobot
import curvebot
import pokerbot
import citabot
import lutomlinbot

default_run_bots = ['curve','poker','cds','lutomlin']#'mario'
bots = {}
bot_threads = {}

def refresh_bots():
    reload(mariobot)
    reload(curvebot)
    reload(pokerbot)
    reload(citabot)
    reload(lutomlinbot)
    
    global bot_ref
    bot_ref =  {'mario':mariobot.MarioBot,
                'curve':curvebot.CurveBot,
                'poker':pokerbot.PokerBot,
                'cds':citabot.CitaBot,
                'lutomlin':lutomlinbot.LutomlinBot,}
    
refresh_bots()

def start_bot(nick):
    bot = bot_ref[nick]('#mario',nick)
    thread = threading.Thread(target=bot.start)
    bots.update({nick:bot})
    bot_threads.update({nick:thread})
    thread.daemon = True
    thread.start()
    
def kill_bot(nick):
    bots[nick].connection.part('#mario')
    bots[nick].disconnect()
    bots[nick].connection.close()
    bot_threads[nick]._Thread__stop()
    bots.pop(nick)

def reload_bot(nick):
    try:
        kill_bot(nick)
    except Exception as err:
        print err
    refresh_bots()
    start_bot(nick)
    
for nick in default_run_bots:
    start_bot(nick)