# -*- coding: utf-8 -*-
"""Kotwice: temat quizu -> zakresy stron KSIĄŻKI, wyprowadzone ze spisu treści podręcznika.

Klucz to dokładna nazwa arkusza xlsx (Excel obcina do 31 znaków), opcjonalnie z sufiksem
"|PREFIKS" dla arkuszy zawierających kilka bloków podtematów.
Wartość to lista zakresów [od, do] stron wydrukowanych w książce.
"""

ANCHORS = {
    # --- 1. WSTĘP (11-27) ---
    '1.Podział anatomiczny układu ne': [[11, 13], [28, 29], [46, 47]],
    '1.Neurohistologia':               [[11, 15]],
    '1.Ośrodki i drogi układu nerwow': [[13, 16], [62, 67]],
    '1.Rozwój układu nerwowego':       [[15, 27]],

    # --- 2. MÓZGOWIE, OPONY, PŁYN, UNACZYNIENIE (28-45) ---
    '2.Opony mózgowo-rdzeniowe':       [[28, 36], [39, 40]],
    '2.Płyn mózgowo-rdzeniowy':        [[36, 40]],
    '2.Unaczynienie':                  [[40, 46]],
    '2.Koło tętnicze mózgu':           [[41, 43]],
    '2.Zatoki żylne':                  [[43, 46]],
    '2.Rozwój mózgowia':               [[15, 27], [39, 40], [70, 72], [86, 86], [108, 109], [128, 129]],

    # --- 3. RDZEŃ KRĘGOWY (46-54) ---
    '3.Budowa zewnętrzna':             [[46, 48]],
    '3.Budowa wewnętrzna':             [[48, 52]],
    '3.Istota szara':                  [[48, 52]],
    '3.Istota biała':                  [[48, 52], [140, 143]],
    '3.Segmenty rdzenia':              [[46, 48], [52, 54]],
    '3.Korzenie nerwowe':              [[46, 48], [52, 54]],

    # --- 4. KRESOMÓZGOWIE (55-77) ---
    '4.Półkule mózgu':                 [[55, 65]],
    '4.Kora mózgu - płat czołowy':     [[55, 70]],
    '4.Kora mózgu - płat ciemieniowy': [[55, 70]],
    '4.Kora mózgu - płat skroniowy':   [[55, 70]],
    '4.Kora mózgu - płat potyliczny':  [[55, 70]],
    '4.Kora mózgu - Wyspa':            [[55, 62]],
    '4.Płaty mózgu':                   [[55, 70]],
    '4.Komory boczne':                 [[73, 77]],

    # --- 5. MIĘDZYMÓZGOWIE (78-88) ---
    '5.Wzgórze':                       [[78, 82], [85, 86]],
    '5.Podwzgórze':                    [[82, 86]],
    '5.Niskowzgórze':                  [[84, 86], [131, 133]],
    '5.Nadwzgórze':                    [[82, 83]],
    '5.Komora III':                    [[87, 88]],

    # --- 6. PIEŃ MÓZGU (89-109) ---
    '6.Rdzeń przedłużony':             [[89, 95]],
    '6.Most':                          [[95, 101]],
    '6.Śródmózgowie|POKR':             [[101, 106]],                          # pokrywa / blaszka czworacza
    '6.Śródmózgowie|KOMO':             [[101, 106]],                          # konary (odnogi) mózgu
    '6.Śródmózgowie|ISCZ':             [[101, 106], [131, 134]],              # istota czarna
    '6.Śródmózgowie|JACZ':             [[101, 106], [131, 134], [142, 144]],  # jądro czerwienne
    '6.Śródmózgowie|WOMO':             [[106, 108], [87, 88], [130, 131]],    # wodociąg mózgu

    # --- 7. MÓŻDŻEK (123-129) ---
    '7.Budowa':                        [[123, 129]],
    '7.Kora móżdżku':                  [[125, 129]],
    '7.Jądra móżdżku':                 [[125, 129]],
    '7.Drogi móżdżkowe':               [[127, 129], [140, 143]],

    # --- 8. UKŁAD LIMBICZNY (135-138, 155-158) ---
    '8.Hipokamp|HIBU':                 [[135, 138], [155, 158]],
    '8.Hipokamp|HIPO':                 [[135, 138], [155, 158]],
    '8.Hipokamp|HIFU':                 [[135, 138], [155, 158]],
    '8.Hipokamp|HIKL':                 [[135, 138], [155, 158]],
    '8.Ciało migdałowate':             [[135, 138], [155, 158]],
    '8.Zakręt obręczy':                [[135, 138], [155, 158], [62, 65]],
    '8.Sklepienie':                    [[135, 138], [155, 158], [62, 65]],
    '8.Przegroda':                     [[135, 138], [155, 158]],

    # --- 9. JĄDRA PODSTAWY (131-134) ---
    '9.Prążkowie':                     [[131, 134]],
    '9.Gałka blada':                   [[131, 134]],
    '9.Istota czarna':                 [[131, 134], [101, 106]],
    '9.Jądro niskowzgórzowe':          [[131, 134], [84, 86]],
    '9.Połączenia jąder podstawy':     [[131, 134]],
    '9.Znaczenie kliniczne':           [[131, 134]],

    # --- 10. UKŁAD POZAPIRAMIDOWY (132-134, 142-144) ---
    '10.Elementy układu pozapiramido': [[131, 134]],
    '10.Drogi pozapiramidowe':         [[132, 134], [142, 144], [152, 154]],
    '10.Regulacja napięcia mięśniowe': [[132, 134], [142, 144], [152, 154]],
    '10.Kontrola ruchów automatyczny': [[132, 134], [142, 144]],
    '10.Znaczenie kliniczne':          [[132, 134], [142, 144]],

    # --- 11. ISTOTA BIAŁA PÓŁKUL (133-135, 62-65) ---
    '11.Torebka wewnętrzna':           [[133, 135], [62, 65]],
    '11.Torebka zewnętrzna':           [[133, 135], [62, 65]],
    '11.Spoidła':                      [[133, 135], [62, 65]],
    '11.Drogi kojarzeniowe':           [[133, 135], [62, 65]],
    '11.Promienistość wieńcowa':       [[133, 135], [62, 65]],
    '11.Znaczenie kliniczne':          [[133, 135], [62, 65]],

    # --- 12. KOMORY MÓZGU ---
    '12.Komory boczne':                [[73, 77]],
    '12.Komora III':                   [[87, 88]],
    '12.Wodociąg mózgu':               [[106, 108], [87, 88]],
    '12.Komora IV':                    [[130, 131], [97, 99]],
    '12.Splot naczyniówkowy':          [[75, 77], [88, 88], [130, 131], [36, 38]],
    '12.Płyn mózgowo-rdzeniowy':       [[36, 40]],

    # --- 13. NERWY CZASZKOWE (110-123, 138-140) ---
    '13.I':    [[110, 112], [122, 123], [154, 156], [135, 136]],
    '13.II':   [[110, 113], [122, 123], [165, 170]],
    '13.III':  [[111, 114], [122, 123], [138, 140]],
    '13.IV':   [[112, 115], [122, 123], [138, 140]],
    '13.V':    [[113, 116], [122, 123], [138, 140], [170, 173]],
    '13.VI':   [[114, 117], [122, 123], [138, 140]],
    '13.VII':  [[115, 118], [122, 123], [138, 140]],
    '13.VIII': [[116, 119], [122, 123], [138, 140], [158, 165]],
    '13.IX':   [[117, 120], [122, 123], [138, 140]],
    '13.X':    [[118, 121], [122, 123], [138, 140]],
    '13.XI':   [[119, 122], [122, 123], [138, 140]],
    '13.XII':  [[120, 123], [138, 140]],

    # --- 14. DROGI NERWOWE ---
    '14.Drogi wstępujące':             [[140, 142], [149, 152]],
    '14.Drogi zstępujące':             [[142, 144], [152, 154]],
    '14.Drogi kojarzeniowe':           [[133, 135], [62, 65]],
    '14.Drogi spoidłowe':              [[133, 135], [62, 65]],
    '14.Drogi projekcyjne':            [[133, 135], [62, 65]],
    '14.Znaczenie kliniczne':          [[142, 144], [152, 154], [52, 54]],

    # --- 15. UKŁAD AUTONOMICZNY (144-147, 51-52) ---
    '15.Układ współczulny':            [[144, 147], [51, 52]],
    '15.Układ przywspółczulny':        [[144, 147], [51, 52]],
    '15.Układ jelitowy':               [[144, 147]],
    '15.Sploty autonomiczne':          [[144, 147]],
    '15.Neuroprzekaźniki':             [[144, 147], [131, 134]],
    '15.Znaczenie kliniczne':          [[144, 147], [52, 54], [164, 165]],

    # --- 16. UKŁAD CZUCIOWY (149-153, 140-142) ---
    '16.Czucie powierzchniowe':        [[149, 151], [140, 142]],
    '16.Czucie głębokie':              [[150, 152], [140, 142]],
    '16.Czucie trzewne':               [[145, 147]],
    '16.Droga sznurów tylnych':        [[140, 141], [150, 152]],
    '16.Droga rdzeniowo-wzgórzowa':    [[140, 142], [149, 151]],
    '16.Integracja czucia':            [[147, 153]],

    # --- 17. UKŁAD RUCHOWY ---
    '17.Droga piramidowa':             [[142, 144], [152, 154], [133, 134]],
    '17.Drogi pozapiramidowe':         [[132, 134], [142, 144], [152, 154]],
    '17.Kora ruchowa':                 [[65, 70], [147, 149]],
    '17.Motoneuron górny':             [[142, 144], [152, 154]],
    '17.Motoneuron dolny':             [[142, 144], [152, 154], [48, 52]],
    '17.Kontrola ruchu':               [[132, 134], [142, 144], [127, 129]],

    # --- 18. ZMYSŁY (153-173) ---
    '18.Układ wzrokowy':               [[165, 170], [110, 113]],
    '18.Układ słuchowy':               [[158, 161], [116, 119]],
    '18.Układ przedsionkowy':          [[161, 165], [116, 119]],
    '18.Układ węchowy':                [[154, 156], [135, 136]],
    '18.Układ smakowy':                [[153, 155]],
    '18.Integracja sensoryczna':       [[147, 149], [151, 153]],
}
