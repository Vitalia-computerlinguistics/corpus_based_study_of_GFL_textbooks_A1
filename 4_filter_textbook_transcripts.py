import re
from pathlib import Path


# set input and output paths
source_dir = Path("/Masterarbeit/Textbooks_materials_txt")
output_dir = Path("/Masterarbeit/Textbooks_materials_filtered")

files = sorted(source_dir.iterdir())

# formulate metadata for removal

# publisher information
publisher_info = r"""
©\s*(?:Ernst\s+Klett\s+Sprachen|Klett\-Langenscheidt|Hueber)\s+.*?
Alle\s+Rechte\s+vorbehalten\..*?
Kopiergebühren\s+sind\s+abgegolten\."""

# textbook information
textbook_titles = r"""\b(Netzwerk\s+neu\s+A1|Menschen\s+A1|Akademie\s+Deutsch|Intensivlehrwerk|
Linie\s+1|Starten\s+wir!)\b"""

# lines with meta information
meta_lines = r"""^(?:.*\b(Transkript(?:ionen)?|Transkript\s+Audios|Transkript\s+Video
|Transkript\s+Redemittelclips|Transkripte|Kursbuch|Übungsbuch)\b.*)$"""

# information about structural entities
structure_lines = r"""^(Kapitel|Lektion|Aufgabe|Dialog|Seite|Gespräch)\s*\d+.*$"""

# specific meta pattern of akademie textbook
akademie_pattern = r"""
\b(\d+_AkaDeu_[A-Za-z0-9_]+|\d+[a-z]?_(?:[A-Za-zÄÖÜäöüß0-9\-]+_?)+|-?\d+[a-z]?
(?:_[A-Za-zÄÖÜäöüß0-9\-]+)+)\b"""

# time information in transcripts
time_markers = r"\(\s*\d{1,2}:\d{2}\s*Minuten\s*\)"

# dialogue with numbers
dialog_markers = r"\bDialog\s*\d+\s*:\s*"

# tracks with numbers
track_markers = r"\bTrack\s+\d+(?:\.\d+)?\b"

# lessons with numbers
lesson_range_pattern = r"\bLektionen\s+\d+\s+bis\s+\d+\s*:?\s*"

# chapters with numbers
chapter_range_pattern = r"\bKapitel\s+\d+\s+bis\s+\d+\s*:?\s*"

# tasks with numbers
task_range_pattern = r"\bAufgabe\s+\d+\s+und\s+\d+\b"

# speaker names with ":"
speaker_names_pattern = r"\b[A-ZÄÖÜ][a-zäöüß]+:"

# speaker names with numbers
speaker_with_number_pattern = r"\bSprecher(?:in)?\s*\d+\s*:\s*"

def filter_tbks_comments(tbk_path: Path):

    """This function gets a path of a textbook as an input, filters out meta information,
    writes filtered content in a file named like the unfiltered file but in another directory
    and outputs filtered content of the file"""

    with open(tbk_path, "r", encoding="utf-8") as infile:
        text = infile.read()

    # remove further patterns
    text = text.replace(
        "Im  Folgenden finden  Sie  die  Transkriptionen  zu  den  Audios  aus  dem  Intensivlehrwerk,",
        "")

    text = text.replace(
        "die nicht im Buch abgedruckt sind.","")

    text = text.replace("Intensivlehrwerk Band 1", "")

    # filter out publisher information
    text = re.sub(publisher_info, "", text, flags=re.DOTALL | re.VERBOSE)

    # filter out meta information

    for pattern in [textbook_titles, meta_lines, structure_lines, akademie_pattern, time_markers, dialog_markers,
                    track_markers, lesson_range_pattern, chapter_range_pattern, task_range_pattern, speaker_names_pattern,
                    speaker_with_number_pattern]:
        text = re.sub(pattern, "", text, flags=re.MULTILINE | re.VERBOSE)


    # replace new lines and multiple spaces through a space
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()


    # remove further patterns
    text = text.replace("Intensivtrainer, ISBN 978-3-19-041901-2, © Hueber Verlag", " ")
    text = text.replace("Deutsch in Alltag und Beruf Stufe A1.2", " ")


    output_path = output_dir / f"{tbk_path.stem}.txt"

    # save filtered textbook transcript in a file
    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write(text)

    return text


# write all textbook transcripts in one file
with open("/Masterarbeit/Textbooks_materials_filtered/all_transcripts", "w", encoding="utf-8") as outfile:

    for file in files:
        outfile.write(filter_tbks_comments(file))
        #print(file.stem)


