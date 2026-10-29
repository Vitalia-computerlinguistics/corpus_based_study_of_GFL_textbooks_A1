from pathlib import Path
from bs4 import BeautifulSoup
import re


def read_transcripts_pfeffer(path, script_name):

    """This function gets path and name of Pfeffer corpus transcript pdf-file as an input
    and outputs txt file with the content of this file"""

    with open(path, mode = "r", encoding= "UTF-8") as infile:
        html_code = infile.read()


    soup = BeautifulSoup(html_code, "html.parser")

    #print(soup.prettify())
    #print(soup.get_text())

    # space as separator, otherwise there will be no space between sentences due to html-code structure
    # of these files
    text = soup.get_text(separator=" ")

    # delete more than one spaces
    text = re.sub(r"\s+", " ", text)

    # separate sentence marks from following words
    # link, regex groups: https://www.geeksforgeeks.org/python/python-regex-replace-captured-groups/?utm_source=chatgpt.com
    text = re.sub(r"([.!?])([A-Za-zÄÖÜäöü])", r"\1 \2", text)

    # delete spaces before sentence marks
    text = re.sub(r"\s+([.!?,;:])", r"\1", text)



    output_path = f"/Masterarbeit/Pfeffer_Korpus/Transcripts_as_txt/{script_name}.txt"

    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write(text.strip())



source_dir = Path("/Masterarbeit/Pfeffer_Korpus/Transcripte")
files = source_dir.iterdir()

# save pfeffer-corpus pdfs as txt-files
for file in sorted(files):
    read_transcripts_pfeffer(file, file.name)


# save all pfeffer-corpus transcripts in one file

source_dir = Path(f"/Masterarbeit/Pfeffer_Korpus/Transcripts_as_txt")
files = source_dir.iterdir()

output_path = "/Masterarbeit/Pfeffer_Korpus/all_transcripts.txt"
outfile = open(output_path, "w", encoding="utf-8")

for file in sorted(files):
    with open(file, mode = "r", encoding= "UTF-8") as infile:
        text = infile.read()

    # link, a-mode: https://www.geeksforgeeks.org/python/difference-between-modes-a-a-w-w-and-r-in-built-in-open-function/
    with open(output_path, "a", encoding="utf-8") as outfile:
        outfile.write(text.strip() + "\n\n")
