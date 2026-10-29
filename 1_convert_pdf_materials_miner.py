from pathlib import Path
from pdfminer.high_level import extract_text


# Link to a code with extract_text() function of pdfminer:
# https://pdfminersix.readthedocs.io/en/latest/tutorial/highlevel.html

def convert_pdf_transcripts_to_txt(transcript_path, transcript_name):

    """This function gets path and name of a pdf-file with a transcript as an input
     and writes the content of that transcript to a txt file"""

    transcript = extract_text(transcript_path)

    with open(f"/Masterarbeit/Textbooks_materials_txt/{transcript_name[:-4]}.txt", "w", encoding="utf-8") as output_file:
        output_file.write(transcript)



# apply on transcripts in single files
source_dir_textbook_materials = Path("/Masterarbeit/Textbooks_materials/Transcripts")

files = source_dir_textbook_materials.iterdir()
for file in sorted(files):
    convert_pdf_transcripts_to_txt(file, file.name)

#print(text[:1000])

# apply on netzwerk textbook consisted of multiple files
source_dir_netzwerk = Path("/Masterarbeit/Textbooks_materials/Netzwerk")
files = source_dir_netzwerk.iterdir()


# sum content of all netzwerk transcripts in one file
netzwerk_transcript = ""

for file in sorted(files):
    text_netzwerk = extract_text(file)
    netzwerk_transcript += text_netzwerk

with open("/Masterarbeit/Textbooks_materials_txt/Netzwerk.txt", "w", encoding="utf-8") as output_file:
    output_file.write(netzwerk_transcript)

# apply on linie textbook consisted of multiple files
source_dir_linie = Path("/Masterarbeit/Textbooks_materials/Linie_1")
files = source_dir_linie.iterdir()
linie_transcript = ""

# sum content of all linie transcripts in one file
for file in sorted(files):
    text_linie = extract_text(file)
    linie_transcript += text_linie

with open("/Masterarbeit/Textbooks_materials_txt/Linie.txt", "w", encoding="utf-8") as output_file:
    output_file.write(linie_transcript)
