# -*- coding: utf-8 -*-

# Add-on for Anki that modifies the function _burySiblings
#
# Copyright: 2019 ijgnd
#            2019 Thomas Kahn
#            2018-2019 Lovac42
#            Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html


from pprint import pprint as pp

from anki import version
from anki.hooks import addHook
from anki.lang import getLang
from anki.sched import Scheduler as schedv1
from anki.utils import ids2str, intTime

from aqt import mw
from aqt.utils import showInfo, tooltip
from aqt.qt import *


anki20 = version.startswith("2.0.")
if not anki20:
    from anki.schedv2 import Scheduler as schedv2
German = getLang() == "de"


def my_burySiblings(self, card):
    toBury = []
    nconf = self._newConf(card)
    buryNew = nconf.get("bury", True)
    rconf = self._revConf(card)
    buryRev = rconf.get("bury", True)
    # loop through and remove from queues
    for cid, queue in self.col.db.execute("""
select id, queue from cards where nid=? and id!=?
and (queue=0 or (queue=2 and due<=?))""",
            card.nid, card.id, self.today):
        if queue == 2:
            if not nospacing:
                if buryRev:
                    tooltip('conflicting settings in add-on and deck settings')
                    toBury.append(cid)
                # if bury disabled, we still discard to give same-day spacing
                try:
                    self._revQueue.remove(cid)
                except ValueError:
                    pass
        else:
            if not nospacing:
                if buryNew:
                    # tooltip('conflicting settings in add-on and deck settings')
                    toBury.append(cid)
                # if bury disabled, we still discard to give same-day spacing
                try:
                    self._newQueue.remove(cid)
                except ValueError:
                    pass
    # then bury
    if toBury:
        if not anki20 and self.col.schedVer() != 1:
            self.buryCards(toBury, manual=False)
        else:
            self.col.db.execute(
            "update cards set queue=-2,mod=?,usn=? where id in "+ids2str(toBury),
            intTime(), self.col.usn())
            self.col.log(toBury)
schedv1._burySiblings = my_burySiblings
if not anki20:
    schedv2._burySiblings = my_burySiblings


msg_ger = (u"Option aktiviert! Karten, die zu derselben Notiz gehören, werden "
           u"jetzt unmittelbar nacheinander abgefragt.<br><br>"
           u"Um bestimmte einzelne Karten erst morgen abfragen zu lassen, kannst du, "
           u"wenn du danach gefragt wirst, einfach die \"-\"-Taste (Bindestrich-Taste) "
           u"auf deiner Tastatur drücken. Das ist z.B. sinnvoll, wenn du gerade gefragt "
           u"wurdest: \"Was heißt 'Kuchen' auf Englisch?\" Und dann direkt danach: \"Was "
           u"bedeutet 'cake' auf Deutsch?\"<br><br>Weitere Infos zu dieser Funktion findest "
           u"du auf der Seite <a href=\"https://ankiweb.net/shared/info/268644742\">des "
           u"dazugehörigen Anki-Addons</a>.")
msg_en = (u"Option has been activated! Sibling Cards (= cards belonging to the same note) "
          u"will now be asked right after each other.<br><br>To put the review of specific "
          u"cards off until tomorrow press the \"-\"-key when you are asked about them. "
          u"This makes sense in situations where you've just been asked: \"What does 'Kuchen' "
          u"mean in Englisch?\" And the next question is: \"What does 'cake' mean in "
          u"German?\"<br><br>"
          u"More information about this option can be found on the page "
          u"<a href=\"https://ankiweb.net/shared/info/268644742\">"
          u"of the corresponding Anki-Add-On</a>.")


def toggleSameDaySpacing():
    global nospacing
    nospacing ^= True
    mw.col.conf['268644742_intraday_spacing'] ^= True
    mw.col.setMod()
    showInfo(msg_ger if German else msg_en)
    mw.reset()


menu_added = 0
def add_same_day_spacing_to_menu():
    global menu_added
    menu_added += 1
    if not menu_added > 1:
        try:
            m = mw.menuView
        except:
            mlabel_ger = u"&Kartenreihenfolge"
            mlabel_en = u"&Study"
            mw.menuView = QMenu(mlabel_ger if German else mlabel_en)
            action = mw.menuBar().insertMenu(mw.form.menuTools.menuAction(), mw.menuView)
            m = mw.menuView

        label_ger = u'Zusammengehörende Karten direkt nacheinander abfragen'
        label_en = u'change scheduler - no same-day spacing for siblings/show due siblings in order'
        a = m.addAction(label_ger if German else label_en)
        a.setCheckable(True)
        a.setChecked(nospacing)
        a.toggled.connect(toggleSameDaySpacing)


def onProfileLoaded():
    global nospacing
    if '268644742_intraday_spacing' in mw.col.conf:
        nospacing = mw.col.conf['268644742_intraday_spacing']
    else:
        nospacing = False
        mw.col.conf['268644742_intraday_spacing'] = False
        mw.col.setMod()
    add_same_day_spacing_to_menu()
addHook('profileLoaded', onProfileLoaded)
