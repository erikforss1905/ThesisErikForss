# ThesisErikForss
This repository contains code that was developed as part of the master thesis at Technical University Darmstadt, Department Corporate Finance.

In dieser Repository befinden sich Programmcode und Dateien, die im Rahmen der Masterthesis am Fachgebiet Unternehmensfinanzierung erarbeitet wurden.

## Scraper für das Unternehmensregister
In der Datei `crawler.py` befindet sich der Scraper, mit dem Informationen aus dem Unternehmensregisters zunächst katalogisiert werden. 
Nach der Katalogisierung der Suchergebnisse können die Suchergebnisse automatisiert ausgelesen und lokal gespeichert werden. 
Im Rahmen der Masterthesis wurden lediglich Stimmrechtsmitteilungen durchsucht. 
Zur Ausführung wird der Webbrowser [Google Chrome](https://www.google.com/intl/de_de/chrome/) sowie ein zur Browser-Version passender [chromedriver](https://chromedriver.chromium.org/downloads) benötigt, der im gleichen Verzeichnis abgelegt werden sollte wie `crawler.py`.
Die Suchergebnisse sind in der Datei `FullSearchResult.csv` katalogisiert.
Für den Zugriff auf die Stimmrechtsmitteilungen kontaktieren Sie bitte den Autor. 

## Automatische Textsuche und Klassifikation
Die Vorsortierung und Klassifikation der Stimmrechtsmitteilungen erfolgt mit dem Skript `classification.py`. 

## Multilineare Regression
Die Multinlineare Regression wurde mit dem Python-Paket `statsmodels` durchgeführt.
Das Skript dazu ist die Datei `Regression.py`.
Alle Ergebnisse und Daten befinden sich im Ordner `Regression`, insbesondere die Ergebnisse der Regression als csv-Datei in `Regression/Results/summary.csv`.

## _Buy and Hold Abnormal Returns_ Analyse
Die Ergebnisse der BHAR Analyse befinden sich als csv-Datei im Ordner `BHAR`.