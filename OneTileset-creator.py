# 10/23/16
# The OneTileset Creator wizard for end users.

import json
import os
import os.path
import re
import sys
import time
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets; Qt = QtCore.Qt
from PyQt5.Qt import PYQT_VERSION_STR
import nsmbulib
import nsmbulib.Sarc
import nsmbulib.Tileset
import nsmbulib.Yaz0


VERSION = '1.0.0'
ONE_TILESET_DIR_NAME = 'OneTileset'
ONE_TILESET_SCRIPTS = {
    (True, True): 'oneTilesetScript_nsmbu_nslu.json',
    (True, False): 'oneTilesetScript_nsmbu.json',
    (False, True): 'oneTilesetScript_nslu.json',
}


########################################################################
########################### Translation Stuff ##########################
########################################################################
########################################################################


# Hardcoded translations are best because I want this script to have as
# few dependencies as possible, and because there's not much text here
# in the first place.
translations = {
    'None': { # Translation template

        # Please don't translate "OneTileset" or "OneTileset Creator".
        # Thanks!

        'Language': '',

        'Select a language:': '',


        'Welcome': '',

        'Welcome to OneTileset Creator [version] (running on Python '
        '[pyversion], PyQt [pyqtversion] and nsmbulib [nsmbulibversion])!'
        '<br><br>'
        'This program will create OneTileset from retail level files for you.'
        '<br><br>'
        'This program was written by a member of the Newer Team '
        '(http://newerteam.com), and is not sanctioned by Nintendo in '
        'any way.<br><br>'
        "It looks like you have all of the required files ready, so let's "
        'get started!': '',


        'Select input directories': '',

        'Select your <i>New Super Mario Bros. U</i> and/or '
            '<i>New Super Luigi U</i> <code>course_res_pack</code> '
            'folders below. Only a subset of OneTileset can be created '
            'unless you have both.<br><br>'
            "If you don't have either, you'll need to dump the files from "
            'your game disk (or eShop download). Google "wii u ddd" or '
            '"tcpgecko dump files" to learn about some homebrew apps that '
            "can do this. Once you've dumped the files, the "
            '<code>course_res_pack</code> folder will be in '
            '<code>/data/content/Common</code> (for '
            '<i>New Super Mario Bros. U</i>) or '
            '<code>/data/content/RDashRes</code> (for '
            '<i>New Super Luigi U</i>).': '',

        '<code>course_res_pack</code> folder '
        '(<i>New Super Mario Bros. U</i>):': '',

        '<code>course_res_pack</code> folder '
        '(<i>New Super Luigi U</i>):': '',

        'Select': '',

        'Select the course_res_pack folder from New Super Mario Bros. U': '',

        'Select the course_res_pack folder from New Super Luigi U': '',


        'Warning': '',

        "This doesn't seem to be a correct "
        '<code>course_res_pack</code> folder from '
        '<i>New Super Mario Bros. U</i>, so it may not be used '
        'during OneTileset creation.': '',

        "This doesn't seem to be a correct "
        '<code>course_res_pack</code> folder from '
        '<i>New Super Luigi U</i>, so it may not be used '
        'during OneTileset creation.': '',


        'Select output directory': '',

        'Select the directory you would like the new '
        '<code>OneTileset</code> folder to be placed in.': '',

        'Select a folder to save OneTileset to': '',


        'Please confirm': '',

        'Please review all of the information below before '
        'continuing. Once you click "Start", you won\'t be able '
        'to go back and change it.': '',

        'New Super Mario Bros. U': '',

        'New Super Luigi U': '',

        'Level files will be read from <code>[path]</code>': '',

        'Will not be processed. (The OneTileset output '
        "will be usable, but will lack this game's objects.)": '',

        'Output will be written to <code>[path]</code>': '',


        'Creating OneTileset': '',

        'Please wait; this will take a while.': '',

        'Setting up': '',

        'Loading <code>[path]</code>': '',

        'Processing <code>[tset]</code> from <code>[path]</code>': '',

        'Finished.': '',


        'Error': '',

        'The following error occurred:<br><br>'
        '<code>[traceback]</code><br><br>'
        'OneTileset Creator will now close. Sorry. To '
        'troubleshoot, first ensure that Python, PyQt5 and '
        'nsmbulib are all updated to the latest versions.<br><br>'
        'If the problem persists, screenshot this error message, '
        'run OneTileset Creator again and screenshot the Welcome '
        'page. Then post both screenshots to the OneTileset '
        'Creator Help thread on http://rhcafe.us.to/ . (You can '
        'use http://imgur.com to upload the screenshots.) Someone '
        'will help you out there.': '',


        'Finished': '',

        'All done! Your new OneTileset folder is<br><br>'
        '<code>[path]</code><br><br>'
        'Please remember that the data in your OneTileset folder is '
        'copyrighted by Nintendo. Do not redistribute it.<br><br>'
        'Have a great day!': '',

    },
    'Polski': { # Polish (contributed by DS)

        'Language': 'Język',

        'Select a language:': 'Wybierz język:',


        'Welcome': 'Hej!',

        'Welcome to OneTileset Creator [version] (running on Python '
        '[pyversion], PyQt [pyqtversion] and nsmbulib [nsmbulibversion])!'
        '<br><br>'
        'This program will create OneTileset from retail level files for you.'
        '<br><br>'
        'This program was written by a member of the Newer Team '
        '(http://newerteam.com), and is not sanctioned by Nintendo in '
        'any way.<br><br>'
        "It looks like you have all of the required files ready, so let's "
        'get started!':
        'Witaj w programie OneTileset Creator [version] (działającym na '
        'Pythonie [pyversion], PyQt [pyqtversion] i nsmbulib '
        '[nsmbulibversion])!<br><br>'
        'Stworzy on OneTileset z plików oficjalnej gry.<br><br>'
        'Program ten został napisany przez członka Newer Team '
        '(http://newerteam.com), i nie został w żaden sposób aprobowany przez '
        'Nintendo. <br><br>Wygląda na to że masz już wszystkie potrzebne '
        'pliki, więc zaczynajmy!',


        'Select input directories': 'Wybierz folder z plikami wejścia',

        'Select your <i>New Super Mario Bros. U</i> and/or '
        '<i>New Super Luigi U</i> <code>course_res_pack</code> '
        'folders below. Only a subset of OneTileset can be created '
        'unless you have both.<br><br>'
        "If you don't have either, you'll need to dump the files from "
        'your game disk (or eShop download). Google "wii u ddd" or '
        '"tcpgecko dump files" to learn about some homebrew apps that '
        "can do this. Once you've dumped the files, the "
        '<code>course_res_pack</code> folder will be in '
        '<code>/data/content/Common</code> (for '
        '<i>New Super Mario Bros. U</i>) or '
        '<code>/data/content/RDashRes</code> (for '
        '<i>New Super Luigi U</i>).':
        'Wybierz foldery zawierające pliki z folderu '
        '<code>course_res_pack</code> z <i>New Super Mario Bros. U</i> '
        'i/lub <i>New Super Luigi U</i> poniżej. Tylko część OneTileset może '
        'być utworzona jeśli nie posiadasz obu tych folderów.<br><br>'
        'Jeśli nie masz żadnych z nich, to musisz zgrać pliki ze swojej płyty '
        'z grą lub z wersji ściągniętej z serwisu eShop. Wygoogluj '
        '"wii u ddd" i "tcp gecko dump files" by dowiedzieć się jakie '
        'programy mogą to zrobić. Kiedy już zgrasz pliki, folder pod nazwą '
        '<code>course_res_pack</code> będzie w '
        '<code>/data/content/Common</code> (w przypadku '
        '<i>New Super Mario Bros. U</i>) lub '
        '<code>/data/content/RDashRes</code> (w przypadku '
        '<i>New Super Luigi U</i>).',

        '<code>course_res_pack</code> folder '
        '(<i>New Super Mario Bros. U</i>):':
        'Folder <code>course_res_pack</code> '
        '(<i>New Super Mario Bros. U</i>):',

        '<code>course_res_pack</code> folder '
        '(<i>New Super Luigi U</i>):':
        'Folder <code>course_res_pack</code> '
        '(<i>New Super Luigi U</i>):',

        'Select': 'Wybierz',

        'Select the course_res_pack folder from New Super Mario Bros. U':
        'Wybierz folder course_res_pack z New Super Mario Bros. U',

        'Select the course_res_pack folder from New Super Luigi U':
        'Wybierz folder course_res_pack z New Super Luigi U',


        'Warning': 'Ostrzeżenie',

        "This doesn't seem to be a correct "
        '<code>course_res_pack</code> folder from '
        '<i>New Super Mario Bros. U</i>, so it may not be used '
        'during OneTileset creation.':
        'To nie wygląda na prawidłowy folder '
        '<code>course_res_pack</code> z '
        '<i>New Super Mario Bros. U</i>, więc może nie zostać użyty '
        'podczas tworzenia OneTileset.',

        "This doesn't seem to be a correct "
        '<code>course_res_pack</code> folder from '
        '<i>New Super Luigi U</i>, so it may not be used '
        'during OneTileset creation.':
        "To nie wygląda na prawidłowy folder "
        '<code>course_res_pack</code> z '
        '<i>New Super Luigi. U</i>, więc może nie zostać użyty '
        'podczas tworzenia OneTileset.',


        'Select output directory': 'Wybierz folder wyjścia',

        'Select the directory you would like the new '
        '<code>OneTileset</code> folder to be placed in.':
        'Wybierz folder w którym ma być zapisany <code>OneTileset</code>.',

        'Select a folder to save OneTileset to':
        'Wybierz folder w którym ma być zapisany OneTileset',


        'Please confirm': 'Potwierdź',

        'Please review all of the information below before '
        'continuing. Once you click "Start", you won\'t be able '
        'to go back and change it.':
        'Przeanalizuj informacje poniżej zanim kontynuujesz. '
        'Po naciśnięciu "Start" nie będzie już można wrócić i ich '
        'zmienić.',

        'New Super Mario Bros. U': 'New Super Mario Bros. U',

        'New Super Luigi U': 'New Super Luigi U',

        'Level files will be read from <code>[path]</code>':
        'Pliki poziomów będą wzięte z <code>[path]</code>',

        'Will not be processed. (The OneTileset output '
        "will be usable, but will lack this game's objects.)":
        'Te pliki nie będą przetworzone. (Zapisany OneTileset '
        'będzie używalny, ale nie będzie zawierał obiektów z tej gry.)',

        'Output will be written to <code>[path]</code>':
        'OneTileset będzie zapisany w <code>[path]</code>',


        'Creating OneTileset': 'Tworzenie OneTileset',

        'Please wait; this will take a while.': 'Czekaj, to trochę potrwa...',

        'Setting up': 'Przygotowywanie',

        'Loading <code>[path]</code>': 'Ładowanie <code>[path]</code>',

        'Processing <code>[tset]</code> from <code>[path]</code>':
        'Przetwarzanie <code>[tset]</code> z <code>[path]</code>',

        'Finished.': 'Ukończono.',


        'Error': 'Błąd',

        'The following error occurred:<br><br>'
        '<code>[traceback]</code><br><br>'
        'OneTileset Creator will now close. Sorry. To '
        'troubleshoot, first ensure that Python, PyQt5 and '
        'nsmbulib are all updated to the latest versions.<br><br>'
        'If the problem persists, screenshot this error message, '
        'run OneTileset Creator again and screenshot the Welcome '
        'page. Then post both screenshots to the OneTileset '
        'Creator Help thread on http://rhcafe.us.to/ . (You can '
        'use http://imgur.com to upload the screenshots.) Someone '
        'will help you out there.':
        'Wystąpił następujący błąd:<br><br>'
        '<code>[traceback]</code><br><br>'
        'Program OneTileset Creator będzie zamknięty. Przepraszamy. '
        'Upewnij się że Python, PyQt5 i nsmbulib są zaktualizowane do '
        'najnowszych wersji.<br><br>'
        'Jeśli problem się powtórzy, zrób zrzut ekranu tej wiadomości, '
        'po czym uruchom program OneTileset Creator jeszcze raz i zrób zrzut '
        'ekranu powitalnego. Wstaw oba te zrzuty ekranów na wątek pomocy '
        'programu OneTileset Creator na http://rhcafe.us.to/ . (Możesz '
        'wrzucić je na http://imgur.com.). Ktoś ci tam pomoże.',


        'Finished': 'Ukończono',

        'All done! Your new OneTileset folder is<br><br>'
        '<code>[path]</code><br><br>'
        'Please remember that the data in your OneTileset folder is '
        'copyrighted by Nintendo. Do not redistribute it.<br><br>'
        'Have a great day!':
        'Wszystko gotowe! Twój folder OneTileset jest w<br><br>'
        '<code>[path]</code><br><br>'
        'Pamiętaj że wszelkie dane w folderze OneTileset są objęte '
        'prawem autorskim i należą do Nintendo. Nie rozprowadzaj '
        'ich.<br><br>Miłego dnia!',
    },
    'Nederlands': { # Dutch (contributed by Grop)

        'Language': 'Taal',

        'Select a language:': 'Selecteer een taal:',


        'Welcome': 'Welkom',

        'Welcome to OneTileset Creator [version] (running on Python '
        '[pyversion], PyQt [pyqtversion] and nsmbulib [nsmbulibversion])!' 
        '<br><br>'
        'This program will create OneTileset from retail level files for you.'
        '<br><br>'
        'This program was written by a member of the Newer Team '
        '(http://newerteam.com), and is not sanctioned by Nintendo in '
        'any way.<br><br>'
        "It looks like you have all of the required files ready, so let's "
        'get started!':
        'Welkom bij OneTileset Creator [version] (op Python [pyversion], '
        'PyQt [pyqtversion] en nsmbulib [nsmbulibversion])!<br><br>'
        'Dit programma genereert OneTileset uit de originele levelbestanden.'
        '<br><br>'
        'Dit programma is geschreven door een lid van het Newer Team '
        '(http://newerteam.com), en wordt op geen enkele wijze door Nintendo '
        'ondersteund.<br><br>'
        'Het lijkt erop dat je alle benodigde bestanden al klaar hebt staan, '
        'dus laten we beginnen!',


        'Select input directories': 'Selecteer mappen met levelbestanden',

        'Select your <i>New Super Mario Bros. U</i> and/or '
        '<i>New Super Luigi U</i> <code>course_res_pack</code> '
        'folders below. Only a subset of OneTileset can be created '
        'unless you have both.<br><br>'
        "If you don't have either, you'll need to dump the files from "
        'your game disk (or eShop download). Google "wii u ddd" or '
        '"tcpgecko dump files" to learn about some homebrew apps that '
        "can do this. Once you've dumped the files, the "
        '<code>course_res_pack</code> folder will be in '
        '<code>/data/content/Common</code> (for '
        '<i>New Super Mario Bros. U</i>) or '
        '<code>/data/content/RDashRes</code> (for '
        '<i>New Super Luigi U</i>).':
        'Selecteer de <i>New Super Mario Bros. U</i> en/of '
        '<i>New Super Luigi U</i> <code>course_res_pack</code> mappen '
        'hieronder. Slechts een gedeelte van OneTileset kan worden aangemaakt '
        'als je niet beide mappen hebt.<br><br>'
        'Als je geen van beide mappen hebt, moet je de bestanden van het spel '
        '"dumpen". Google "wii u ddd" of "tcpgecko dump files" om meer te '
        'weten te komen over enkele homebrew applicaties die dit kunnen doen. '
        'Als je de bestanden hebt bemachtigd, bevindt de '
        '<code>course_res_pack</code> map zich in '
        '<code>/data/content/Common</code> (voor '
        '<i>New Super Mario Bros. U</i>) of '
        '<code>/data/content/RDashRes</code> (voor <i>New Super Luigi U</i>).',

        '<code>course_res_pack</code> folder '
        '(<i>New Super Mario Bros. U</i>):':
        '<code>course_res_pack</code> map '
        '(<i>New Super Mario Bros. U</i>):',

        '<code>course_res_pack</code> folder '
        '(<i>New Super Luigi U</i>):':
        '<code>course_res_pack</code> map '
        '(<i>New Super Luigi U</i>):',

        'Select': 'Selecteer',

        'Select the course_res_pack folder from New Super Mario Bros. U':
        'Selecteer de map "course_res_pack" van New Super Mario Bros. U',

        'Select the course_res_pack folder from New Super Luigi U':
        'Selecteer de map "course_res_pack" van New Super Luigi U',


        'Warning': 'Waarschuwing',

        "This doesn't seem to be a correct "
        '<code>course_res_pack</code> folder from '
        '<i>New Super Mario Bros. U</i>, so it may not be used '
        'during OneTileset creation.':
        'Dit lijkt een foutieve '
        '<code>course_res_pack</code> map van '
        '<i>New Super Mario Bros. U</i> te zijn, dus het wordt '
        'niet gebruikt tijdens het genereren van OneTileset.',

        "This doesn't seem to be a correct "
        '<code>course_res_pack</code> folder from '
        '<i>New Super Luigi U</i>, so it may not be used '
        'during OneTileset creation.':
        'Dit lijkt een foutieve '
        '<code>course_res_pack</code> map van '
        '<i>New Super Luigi U</i> te zijn, dus het wordt '
        'niet gebruikt tijdens het genereren van OneTileset.',


        'Select output directory':
        'Selecteer de map waarin het resultaat geplaatst wordt',

        'Select the directory you would like the new '
        '<code>OneTileset</code> folder to be placed in.':
        'Selecteer de map waar <code>OneTileset</code> in aangemaakt '
        'moet worden.',

        'Select a folder to save OneTileset to':
        'Selecteer een map waar OneTileset in opgeslagen moet worden',


        'Please confirm': 'Controleer de gegevens',

        'Please review all of the information below before '
        'continuing. Once you click "Start", you won\'t be able '
        'to go back and change it.':
        'Controleer alsjeblieft alles wat je hebt ingevuld voordat je '
        'op "Start" drukt. Als je eenmaal begonnen bent, kun je niets '
        'meer veranderen.',

        'New Super Mario Bros. U': 'New Super Mario Bros. U',

        'New Super Luigi U': 'New Super Luigi U',

        'Level files will be read from <code>[path]</code>':
        'De levelbestanden zullen worden gelezen uit <code>[path]</code>',

        'Will not be processed. (The OneTileset output '
        "will be usable, but will lack this game's objects.)":
        'Wordt niet behandeld. (Het resultaat zal bruikbaar zijn, maar '
        'deze objecten uit het spel zullen ontbreken.)',

        'Output will be written to <code>[path]</code>':
        'Het resultaat wordt geplaatst in <code>[path]</code>',


        'Creating OneTileset': 'OneTileset aan het genereren...',

        'Please wait; this will take a while.':
        'Heb geduld; dit gaat wel eventjes duren...',

        'Setting up': 'Alles klaarmaken voor gebruik...',

        'Loading <code>[path]</code>': '<code>[path]</code> aan het laden...',

        'Processing <code>[tset]</code> from <code>[path]</code>':
        '<code>[tset]</code> uit <code>[path]</code> aan het behandelen...',

        'Finished.': 'Klaar!',


        'Error': 'Error',

        'The following error occurred:<br><br>'
        '<code>[traceback]</code><br><br>'
        'OneTileset Creator will now close. Sorry. To '
        'troubleshoot, first ensure that Python, PyQt5 and '
        'nsmbulib are all updated to the latest versions.<br><br>'
        'If the problem persists, screenshot this error message, '
        'run OneTileset Creator again and screenshot the Welcome '
        'page. Then post both screenshots to the OneTileset '
        'Creator Help thread on http://rhcafe.us.to/ . (You can '
        'use http://imgur.com to upload the screenshots.) Someone '
        'will help you out there.':
        'De volgende fout is opgetreden:<br><br>'
        '<code>[traceback]</code><br><br>'
        'OneTileset Creator zal nu stoppen. Sorry. Om het '
        'probleem op te lossen, controleer of Python, PyQt5 '
        'en nsmbulib allemaal up-to-date zijn.<br><br>'
        'Als het probleem aanhoudt, maak dan een screenshot '
        'van deze foutmelding en start OneTileset Creator opnieuw '
        'op en maak een screenshot van het welkomstscherm. Post '
        'beide screenshots in de (Engelstalige) OneTileset hulp-thread '
        'op http://rhcafe.us.to/ . (Je kunt http://imgur.com gebruiken '
        'voor het uploaden van beide screenshots.) Iemand daar zal je '
        'verder helpen.',


        'Finished': 'Klaar',

        'All done! Your new OneTileset folder is<br><br>'
        '<code>[path]</code><br><br>'
        'Please remember that the data in your OneTileset folder is '
        'copyrighted by Nintendo. Do not redistribute it.<br><br>'
        'Have a great day!':
        'Helemaal klaar! Jouw nieuwe OneTileset map is<br><br>'
        '<code>[path]</code><br><br>'
        'Onthoud dat de bestanden in die map onder het auteursrecht '
        'van Nintendo vallen. Geef deze bestanden dus niet weg.<br><br>'
        'Fijne dag nog!',
    },
}
del translations['None']

currentTranslation = ''

def _(englishString, **replacements):
    """
    Very simple translation function.
    """
    def doReplacements(original): 
        """
        Based on
        https://code.activestate.com/recipes/81330-single-pass-multiple-replace/
        . Replace in 'text' all occurences of any key in the given
        dictionary by its corresponding value.  Returns the new string.
        """
        if not replacements: return original

        # Create a regular expression  from the dictionary keys
        replacements2 = {'[%s]' % k: v for k, v in replacements.items()}
        regex = re.compile(
            "(%s)" % "|".join(map(re.escape, replacements2.keys())))

        # For each match, look-up corresponding value in dictionary
        return regex.sub(
            lambda mo: replacements2[mo.string[mo.start():mo.end()]],
            original)

    if currentTranslation in translations:
        if englishString in translations[currentTranslation]:
            return doReplacements(
                translations[currentTranslation][englishString])

    return doReplacements(englishString)


_dynTransRegistry = []
def dynTrans(updateTextFunction, englishString, **kwargs):
    """
    Register an update-text function with the dynamic-text-update system,
    and provide an English string for it. The update-text function will
    be called whenever the current app translation changes.
    """
    _dynTransRegistry.append([updateTextFunction, englishString, kwargs])
    updateTextFunction(_(englishString, **kwargs))


def modifyDynTrans(updateTextFunction, englishString, **kwargs):
    """
    Replace the English string associated with this
    previously-registered update-text function.
    """
    for entry in _dynTransRegistry:
        if entry[0] == updateTextFunction:
            entry[1] = englishString
            entry[2] = kwargs
            entry[0](englishString, **kwargs)
            return


def updateDynTrans():
    """
    Update all dynamic translations.
    """
    for updateFxn, engStr, kwargs in _dynTransRegistry:
        updateFxn(_(engStr, **kwargs))


########################################################################
############################ File Processing ###########################
########################################################################
########################################################################


def export(object, name, path, info):
    """
    Export object `object` to path `path`, with name `name` and info `info`.
    """
    object.name = name
    object.role = object.Role(info.get('role', '?'))
    object.decorative = info.get('decorative', False)
    object.description = info.get('description', '')

    if not os.path.isdir(path):
        os.makedirs(path)

    objectFiles = object.asNewFormat()
    for fn, fd in objectFiles.items():
        fullFn = os.path.join(path, fn)
        with open(fullFn, 'wb') as f:
            f.write(fd)


def createOneTileset(updateProgress, nsmbuPath, nsluPath, outputPath):
    """
    This is the actual main function that creates OneTileset.
    `updateProgress` should be a callback that takes two parameters:
    a string describing the current operation and an amount-done value
    between 0 and 1. ONE_TILESET_DIR_NAME will be appended to
    `outputPath` for you.
    """
    updateProgress(_('Setting up'), 0)

    # Sanitize paths and append ONE_TILESET_DIR_NAME to the output path
    if not os.path.isdir(outputPath):
        raise RuntimeError('The output path %s does not exist.' % outputPath)
    outputPath = os.path.join(outputPath, ONE_TILESET_DIR_NAME)
    if judgeFolder(nsmbuPath, 'NSMBU') < 1: nsmbuPath = None
    if judgeFolder(nsluPath, 'NSLU') < 1: nsluPath = None

    # Load the appropriate oneTilesetScript_*.json file
    fn = ONE_TILESET_SCRIPTS[(nsmbuPath is not None, nsluPath is not None)]
    with open(fn, 'r', encoding='utf-8') as f:
        script = json.load(f)

    # Count the total number of levels and tilesets we'll have to open.
    # We count these together, and increment a counter whenever we
    # finish loading either one.
    totalThingsToLoad = 0
    for levels in script.values():
        for tilesets in levels.values():
            totalThingsToLoad += len(tilesets) + 1
    thingsLoaded = -1

    for game, courseResPack in [('NSMBU', nsmbuPath), ('NSLU', nsluPath)]:
        if courseResPack is None: continue
        if game not in script: continue

        for levelName, tilesets in script[game].items():
            for levelFN in [levelName + '.szs', levelName + '.sarc']:
                levelPath = os.path.join(courseResPack, levelFN)
                if os.path.isfile(levelPath): break
            else:
                raise RuntimeError(levelName + ' could not be found.')

            thingsLoaded += 1
            updateProgress(
                _('Loading <code>[path]</code>', path=levelPath),
                thingsLoaded / totalThingsToLoad)

            with open(levelPath, 'rb') as f:
                levelData = f.read()

            if nsmbulib.Yaz0.isCompressed(levelData):
                levelData = nsmbulib.Yaz0.decompress(levelData)

            level = nsmbulib.Sarc.load(levelData)

            for tilesetName, objectDefs in tilesets.items():

                thingsLoaded += 1
                updateProgress(_(
                    'Processing <code>[tset]</code> from <code>[path]</code>',
                    tset=tilesetName, path=levelPath),
                    thingsLoaded / totalThingsToLoad)

                if tilesetName not in level:
                    raise RuntimeError(tilesetName + ' could not be found.')

                tileset = nsmbulib.Tileset.load(level[tilesetName])

                for objectNum, objectDef in objectDefs.items():
                    objectName, newPath = objectDef['name'], objectDef['path']
                    del objectDef['name']; del objectDef['path']

                    export(
                        tileset[int(objectNum)],
                        objectName,
                        os.path.join(outputPath, newPath),
                        objectDef)

    updateProgress(_('Finished.'), 1)


def judgeFolder(folder, game='NSMBU'):
    """
    Check the validity of the folder given. Return codes are as follows:
    -1: The folder is nonexistent.
    0: The folder exists, but is missing some or all of the level files.
    1: Everything checks out.
    """
    if not os.path.isdir(folder):
        return -1

    # Try to ensure that the user actually selected the real folder.
    # Here are some levels I picked somewhat arbitrarily that we can
    # check for.
    samples = ['1-1', '1-2', '2-1', '1-58', '7-20', '8-43', '9-9']
    if game == 'NSMBU': samples += ['11-1', '13-2', '18-8']
    for sample in samples:
        for ext in ['.szs', '.sarc']:
            if os.path.isfile(os.path.join(folder, sample + ext)):
                break
        else:
            return 0

    return 1


########################################################################
############################## Wizard GUI ##############################
########################################################################
########################################################################


def createLanguagePage(wizard):
    """
    Create the select-your-language wizard page.
    """
    page = QtWidgets.QWizardPage(wizard)
    dynTrans(page.setTitle, 'Language')

    # Introduction text label
    label = QtWidgets.QLabel(page)
    label.setWordWrap(True)
    dynTrans(label.setText, 'Select a language:')

    # Language-select dropdown
    def dropdownChanged(newValue):
        global currentTranslation
        currentTranslation = newValue
        updateDynTrans()
    dropdown = QtWidgets.QComboBox(page)
    dropdown.addItems(['English'] + sorted(translations))
    dropdown.currentTextChanged.connect(dropdownChanged)

    # Layout
    L = QtWidgets.QVBoxLayout(page)
    L.addWidget(label)
    L.addWidget(dropdown)

    return page


def createWelcomePage(wizard):
    """
    Create the welcome wizard page.
    """
    page = QtWidgets.QWizardPage(wizard)
    dynTrans(page.setTitle, 'Welcome')

    pyversion = sys.version.replace('\n', ' ')

    # Welcome text label
    label = QtWidgets.QLabel(page)
    label.setWordWrap(True)
    dynTrans(label.setText,
        'Welcome to OneTileset Creator [version] (running on Python '
        '[pyversion], PyQt [pyqtversion] and nsmbulib [nsmbulibversion])!'
        '<br><br>'
        'This program will create OneTileset from retail level files for you.'
        '<br><br>'
        'This program was written by a member of the Newer Team '
        '(http://newerteam.com), and is not sanctioned by Nintendo in '
        'any way.<br><br>'
        "It looks like you have all of the required files ready, so let's "
        'get started!',
        version=VERSION, pyversion=pyversion, pyqtversion=PYQT_VERSION_STR,
        nsmbulibversion="1.0")

    # Layout
    L = QtWidgets.QVBoxLayout(page)
    L.addWidget(label)

    return page


class ChooseInputPage(QtWidgets.QWizardPage):
    """
    A wizard page that lets you choose input directories.
    """
    def __init__(self, wizard):
        super().__init__(wizard)
        # 320 allows all the intro text to fit... in KDE5, at least
        self.setMinimumHeight(320)
        dynTrans(self.setTitle, 'Select input directories')

        # Intro text label
        introLabel = QtWidgets.QLabel(self)
        introLabel.setWordWrap(True)
        dynTrans(introLabel.setText,
            'Select your <i>New Super Mario Bros. U</i> and/or '
            '<i>New Super Luigi U</i> <code>course_res_pack</code> '
            'folders below. Only a subset of OneTileset can be created '
            'unless you have both.<br><br>'
            "If you don't have either, you'll need to dump the files from "
            'your game disk (or eShop download). Google "wii u ddd" or '
            '"tcpgecko dump files" to learn about some homebrew apps that '
            "can do this. Once you've dumped the files, the "
            '<code>course_res_pack</code> folder will be in '
            '<code>/data/content/Common</code> (for '
            '<i>New Super Mario Bros. U</i>) or '
            '<code>/data/content/RDashRes</code> (for '
            '<i>New Super Luigi U</i>).')

        # course_res_pack (NSMBU) label
        nsmbuLabel = QtWidgets.QLabel(self)
        nsmbuLabel.setWordWrap(True)
        dynTrans(nsmbuLabel.setText,
            '<code>course_res_pack</code> folder '
            '(<i>New Super Mario Bros. U</i>):')

        # course_res_pack (NSLU) label
        nsluLabel = QtWidgets.QLabel(self)
        nsluLabel.setWordWrap(True)
        dynTrans(nsluLabel.setText,
            '<code>course_res_pack</code> folder '
            '(<i>New Super Luigi U</i>):')

        # Folder-select line edits
        nsmbuLE = QtWidgets.QLineEdit(self)
        nsmbuLE.textChanged.connect(self.completeChanged)
        wizard.chooseInputNSMBUEdit = nsmbuLE
        nsluLE = QtWidgets.QLineEdit(self)
        nsluLE.textChanged.connect(self.completeChanged)
        wizard.chooseInputNSLUEdit = nsluLE

        # Folder-select buttons
        nsmbuSelBtn = QtWidgets.QPushButton(self)
        dynTrans(nsmbuSelBtn.setText, 'Select')
        nsmbuSelBtn.clicked.connect(self.nsmbuSelBtnClicked)
        nsluSelBtn = QtWidgets.QPushButton(self)
        dynTrans(nsluSelBtn.setText, 'Select')
        nsluSelBtn.clicked.connect(self.nsluSelBtnClicked)

        # Layout
        nsmbuEntryLyt = QtWidgets.QHBoxLayout()
        nsmbuEntryLyt.addWidget(nsmbuLE)
        nsmbuEntryLyt.addWidget(nsmbuSelBtn)
        nsluEntryLyt = QtWidgets.QHBoxLayout()
        nsluEntryLyt.addWidget(nsluLE)
        nsluEntryLyt.addWidget(nsluSelBtn)
        L = QtWidgets.QVBoxLayout(self)
        L.addWidget(introLabel)
        L.addWidget(nsmbuLabel)
        L.addLayout(nsmbuEntryLyt)
        L.addWidget(nsluLabel)
        L.addLayout(nsluEntryLyt)


    def nsmbuSelBtnClicked(self):
        """
        The "Select" button was clicked for the NSMBU line edit.
        """
        fn = QtWidgets.QFileDialog.getExistingDirectory(self,
            _('Select the course_res_pack folder from '
                'New Super Mario Bros. U'),
            self.wizard().chooseInputNSMBUEdit.text(),
            )
        if not fn: return

        self.wizard().chooseInputNSMBUEdit.setText(fn)
        judge = judgeFolder(fn, 'NSMBU')
        if judge == 0:
            QtWidgets.QMessageBox.warning(self, _('Warning'),
                _("This doesn't seem to be a correct "
                    '<code>course_res_pack</code> folder from '
                    '<i>New Super Mario Bros. U</i>, so it may not be used '
                    'during OneTileset creation.'))


    def nsluSelBtnClicked(self):
        """
        The "Select" button was clicked for the NSLU line edit.
        """
        fn = QtWidgets.QFileDialog.getExistingDirectory(self,
            _('Select the course_res_pack folder from '
                'New Super Luigi U'),
            self.wizard().chooseInputNSLUEdit.text(),
            )
        if not fn: return

        self.wizard().chooseInputNSLUEdit.setText(fn)
        judge = judgeFolder(fn, 'NSLU')
        if judge == 0:
            QtWidgets.QMessageBox.warning(self, _('Warning'),
                _("This doesn't seem to be a correct "
                    '<code>course_res_pack</code> folder from '
                    '<i>New Super Luigi U</i>, so it may not be used '
                    'during OneTileset creation.'))


    def isComplete(self):
        """
        Return True if a valid NSMBU and/or NSLU course_res_pack
        directory has been entered, or False otherwise
        """
        nsmbuCRP = self.wizard().chooseInputNSMBUEdit.text()
        nsluCRP = self.wizard().chooseInputNSLUEdit.text()
        return (judgeFolder(nsmbuCRP, 'NSMBU') == 1
            or judgeFolder(nsluCRP, 'NSLU') == 1)



class ChooseOutputPage(QtWidgets.QWizardPage):
    """
    A wizard page that lets you choose the OneTileset directory
    """
    def __init__(self, wizard):
        super().__init__(wizard)
        dynTrans(self.setTitle, 'Select output directory')

        # Intro text label
        introLabel = QtWidgets.QLabel(self)
        introLabel.setWordWrap(True)
        dynTrans(introLabel.setText,
            'Select the directory you would like the new '
            '<code>OneTileset</code> folder to be placed in.')

        # Folder-select line edit
        le = QtWidgets.QLineEdit(self)
        le.textChanged.connect(self.completeChanged)
        wizard.chooseOutputEdit = le

        # Folder-select button
        selBtn = QtWidgets.QPushButton(self)
        dynTrans(selBtn.setText, 'Select')
        selBtn.clicked.connect(self.selBtnClicked)

        # Layout
        L = QtWidgets.QGridLayout(self)
        L.addWidget(introLabel, 0, 0, 1, 2)
        L.addWidget(le, 1, 0)
        L.addWidget(selBtn, 1, 1)


    def selBtnClicked(self):
        """
        The "Select" button was clicked for the line edit.
        """
        fn = QtWidgets.QFileDialog.getExistingDirectory(self,
            _('Select a folder to save OneTileset to'),
            self.wizard().chooseOutputEdit.text(),
            )
        if fn:
            self.wizard().chooseOutputEdit.setText(fn)


    def isComplete(self):
        """
        Return True if a valid NSMBU and/or NSLU course_res_pack
        directory has been entered, or False otherwise
        """
        return os.path.isdir(self.wizard().chooseOutputEdit.text())



class ConfirmationPage(QtWidgets.QWizardPage):
    """
    A wizard page that shows you all relevant info before the actual
    OneTileset creation begins
    """
    def __init__(self, wizard):
        super().__init__(wizard)
        self.setMinimumHeight(350) # Paths can be loooooooooong.
        dynTrans(self.setTitle, 'Please confirm')
        self.setCommitPage(True) # Disables the next page's Back button
                                 # and some other nice stuff

        # "Commit" sounds weird.
        dynTrans(lambda s: self.setButtonText(wizard.CommitButton, s), 'Start')

        # Welcome text label
        label = QtWidgets.QLabel(self)
        label.setWordWrap(True)
        dynTrans(label.setText, '') # placeholder
        wizard.confirmationLabel = label

        # Layout
        L = QtWidgets.QVBoxLayout(self)
        L.addWidget(label)


    def initializePage(self):
        """
        This runs every time the user clicks the "next" button on the
        previous page, so it's a good place to update the text label
        with the current info.
        """
        nsmbu = self.wizard().chooseInputNSMBUEdit.text()
        nslu = self.wizard().chooseInputNSLUEdit.text()
        onetileset = os.path.join(self.wizard().chooseOutputEdit.text(),
                                  ONE_TILESET_DIR_NAME)

        newText = _('Please review all of the information below before '
            'continuing. Once you click "Start", you won\'t be able '
            'to go back and change it.')

        newText += '<h3>%s</h3>' % _('New Super Mario Bros. U')
        if judgeFolder(nsmbu, 'NSMBU') == 1:
            newText += _('Level files will be read from <code>[path]</code>',
                path=nsmbu)
        else:
            newText += _('Will not be processed. (The OneTileset output '
                "will be usable, but will lack this game's objects.)")

        newText += '<h3>%s</h3>' % _('New Super Luigi U')
        if judgeFolder(nslu, 'NSLU') == 1:
            newText += _('Level files will be read from <code>[path]</code>',
                path=nslu)
        else:
            newText += _('Will not be processed. (The OneTileset output '
                "will be usable, but will lack this game's objects.)")

        newText += '<h3>OneTileset</h3>' # Exempt from translation.
        newText += _('Output will be written to <code>[path]</code>',
                     path=onetileset)

        modifyDynTrans(self.wizard().confirmationLabel.setText, newText)
    


class ProgressPage(QtWidgets.QWizardPage):
    """
    A wizard page that displays progress while OneTileset is being
    created
    """
    def __init__(self, wizard):
        super().__init__(wizard)
        dynTrans(self.setTitle, 'Creating OneTileset')
        self.creationDone = False

        # Intro text label
        introLabel = QtWidgets.QLabel(self)
        introLabel.setWordWrap(True)
        dynTrans(introLabel.setText,
            'Please wait; this will take a while.')

        # Progress label
        self.progressLabel = QtWidgets.QLabel(self)
        self.progressLabel.setWordWrap(True)

        # Progress bar
        self.progressBar = QtWidgets.QProgressBar(self)

        # Layout
        L = QtWidgets.QVBoxLayout(self)
        L.addWidget(introLabel)
        L.addWidget(self.progressLabel)
        L.addWidget(self.progressBar)


    def initializePage(self):
        """
        Start the OneTileset creation thread
        """

        # We have to use QThreads here because otherwise Qt freaks out
        # if you try to make an error messagebox from it. "AAAAAAAHHHHHH
        # WHY THE HECK ARE YOU NOT USING A QTHREAD??? ERROR ERROR ERROR"
        # For the right way to use a QThread, read this:
        # https://blog.qt.io/blog/2010/06/17/youre-doing-it-wrong/

        def runThread():
            """
            A wrapper around createOneTileset() that catches exceptions
            and exits gracefully if one occurs.
            """
            try:
                createOneTileset(
                    self.progressCallback,
                    self.wizard().chooseInputNSMBUEdit.text(),
                    self.wizard().chooseInputNSLUEdit.text(),
                    self.wizard().chooseOutputEdit.text())
            except Exception as e:
                tb = traceback.format_exc().replace('\n', '<br>')
                tb = tb.replace(' ', '&nbsp;')
                QtWidgets.QMessageBox.critical(None, _('Error'),
                    _('The following error occurred:<br><br>'
                    '<code>[traceback]</code><br><br>'
                    'OneTileset Creator will now close. Sorry. To '
                    'troubleshoot, first ensure that Python, PyQt5 and '
                    'nsmbulib are all updated to the latest versions.<br><br>'
                    'If the problem persists, screenshot this error message, '
                    'run OneTileset Creator again and screenshot the Welcome '
                    'page. Then post both screenshots to the OneTileset '
                    'Creator Help thread on http://rhcafe.us.to/ . (You can '
                    'use http://imgur.com to upload the screenshots.) Someone '
                    'will help you out there.',
                    traceback=tb))
                app.exit()

        # Needs to be assigned to self to avoid being garbage-collected
        self.thread = QtCore.QThread()
        self.thread.started.connect(runThread)
        self.thread.start(self.thread.NormalPriority)


    def progressCallback(self, task, amtDone):
        """
        This is called by the creation thread with the current task
        in progress (a string) and the current amount done (float, 0-1).
        """
        self.progressLabel.setText(task)
        self.progressBar.setValue(amtDone * 100)
        self.thread.msleep(100) # Allow the window to update
        self.creationDone = amtDone == 1
        if self.creationDone:
            self.completeChanged.emit()


    def isComplete(self):
        """
        Return True if a OneTileset is completed.
        """
        return self.creationDone



class FinishedPage(QtWidgets.QWizardPage):
    """
    A wizard page that tells you that we're all done.
    """
    def __init__(self, wizard):
        super().__init__(wizard)
        dynTrans(self.setTitle, 'Finished')

        label = QtWidgets.QLabel(self)
        label.setWordWrap(True)
        dynTrans(label.setText, '') # placeholder
        wizard.finishedLabel = label

        # Layout
        L = QtWidgets.QVBoxLayout(self)
        L.addWidget(label)


    def initializePage(self):
        """
        This runs after the user clicks the "next" button on the
        previous page, so it's a good place to update the text label
        with the current info.
        """
        onetileset = os.path.join(self.wizard().chooseOutputEdit.text(),
                                  ONE_TILESET_DIR_NAME)

        newText = _('All done! Your new OneTileset folder is<br><br>'
            '<code>[path]</code><br><br>'
            'Please remember that the data in your OneTileset folder is '
            'copyrighted by Nintendo. Do not redistribute it.<br><br>'
            'Have a great day!',
            path=onetileset)
        modifyDynTrans(self.wizard().finishedLabel.setText, newText)


def main(argv):
    """
    The main wizard startup function.
    """

    global app
    app = QtWidgets.QApplication(argv)

    # Ensure that the required files are all present, and die
    # immediately with a descriptive error if not
    otsj = 'oneTilesetScript_%s.json'
    required = [otsj % 'nsmbu', otsj % 'nslu', otsj % 'nsmbu_nslu']
    has = [os.path.isfile(f) for f in required]
    if not all(has):
        missing = [f for f, h in zip(required, has) if not h]

        # This would appear before the language-selection page, so
        # translating it would be pointless.
        QtWidgets.QMessageBox.critical(None, 'Missing files',
            'The following files should be in the same directory as this '
            'wizard (<i>%s</i>), but appear to be missing:<br><br>%s<br><br>'
            'Please redownload your copy of this wizard to get them.'
            % (os.getcwd(), '<br>'.join(missing)))
        return

    wizard = QtWidgets.QWizard()

    wizard.addPage(createLanguagePage(wizard))
    wizard.addPage(createWelcomePage(wizard))
    wizard.addPage(ChooseInputPage(wizard))
    wizard.addPage(ChooseOutputPage(wizard))
    wizard.addPage(ConfirmationPage(wizard))
    wizard.addPage(ProgressPage(wizard))
    wizard.addPage(FinishedPage(wizard))

    wizard.setWindowTitle('OneTileset Creator')
    wizard.show()

    return app.exec_()

main(sys.argv)