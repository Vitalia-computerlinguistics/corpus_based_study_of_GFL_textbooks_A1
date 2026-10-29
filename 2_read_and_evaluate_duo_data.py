import json
import pandas as pd
from pathlib import Path
from difflib import SequenceMatcher

# set input and output directory
source_dir = Path("/Masterarbeit/JSON_files")
dialogues_output_file = "/Masterarbeit/Textbooks_materials_txt/duo_dialogues.txt"



duo_data = []

for file in sorted(source_dir.iterdir()):

    # read and save json-files with duo-data
    with open(file, "r", encoding="utf-8") as infile:
        data = json.load(infile)
        duo_data.extend(data)

# remove similar dialogues

# 80% similarity
similarity_percent = 0.8

# list of tokens-lists for cells
cells_list = []

# list of dialogue-transcripts
duo_texts_list = []

length_of_corpus = 0

with open(dialogues_output_file, "w", encoding="utf-8") as outfile:

    for line in duo_data:

        # search only for dialogue transcripts
        if line["metadata"].get("text_unit") != "dialogue":
            continue

        # filter duplicates out
        if line["tokens"] in cells_list:
            continue

        # save tokens of the dialogue-cell
        tokens_cell = []

        for token in line["tokens"]:
            tokens_cell.append(token["form"])

        # create a string of cell-tokens
        text = " ".join(tokens_cell).strip()

        # append text to dialogue-transcripts, if it is not too similar to
        # one of the dialogue-transcripts

        too_similar = False

        for other_text in duo_texts_list:

            # calculate similarity ratio
            # Link to code-example with SequenceMatcher()
            # https://docs.python.org/3/library/difflib.html
            similarity = SequenceMatcher(None, text, other_text).ratio()

            if similarity >= similarity_percent:
                too_similar = True
                break

        if too_similar:
            continue

        duo_texts_list.append(text)
        cells_list.append(line["tokens"])
        length_of_corpus += len(text)

        outfile.write(text + "\n")

print("Number of dialogues:", len(cells_list))
print("Corpus length:", length_of_corpus)


# define segments for verb distribution analysis
# possibility for splitting of data into productive and perception segments in the future

# student should solve an exercise
productive_segments = ["editing field", "model solution"]

# student perceives the content
perception_segments = ["task description", "this is new", "grammar", "additional information", "added media",
    "learning content", "positioning and instructions", "title of chapter scenario", "hint", "title"]

# current analysis include information of productive and perception segments
combined_segments = productive_segments + perception_segments


verbs_tags = ["VAFIN","VAINF", "VAPP", "VAIMP", "VMFIN","VMINF","VMPP", "VVFIN","VVINF","VVPP",
              "VVIMP","VVIZU"]



verb_data = {}

for line in duo_data:

    # search for relevant textbook segments
    meta = line.get("metadata")
    segment = meta.get("segment")

    if segment not in combined_segments:
        continue

    # save information about course, scenario and phase
    course = meta.get("course")
    scenario = meta.get("scenario")
    phase = meta.get("phase")


    for token in line.get("tokens"):

        xpos = token.get("pos_xpos")

        # search for verbs
        if xpos not in verbs_tags:
            continue

        #save verb lemma
        lemma = token.get("lemma")

        # get rid of empty lemmas
        if not lemma:
            continue

        lemma = lemma.strip().lower()

        if lemma in ["", "_"]:
            continue

        # save verb form
        form = token.get("form", "").lower()

        # save information about forms and location in structure units for verb lemmas
        if lemma not in verb_data:
            verb_data[lemma] = {
                "Frequency": 0,
                "Forms": {},
                "XPOS": {},
                "Course": {},
                "Scenario": {},
                "Phase": {},
                "Segment": {}}

        # count information to verb lemmas

        # frequency
        verb_data[lemma]["Frequency"] += 1

        # frequency of lemma forma
        verb_data[lemma]["Forms"][form] = verb_data[lemma]["Forms"].get(form, 0) + 1

        # frequency of lemma xpos
        verb_data[lemma]["XPOS"][xpos] = verb_data[lemma]["XPOS"].get(xpos, 0) + 1

        # frequency of the particular lemma occurences in the course
        verb_data[lemma]["Course"][course] = verb_data[lemma]["Course"].get(course, 0) + 1

        # frequency of the particular lemma occurences in the scenario
        scenario_key = f"{course}/{scenario}"
        verb_data[lemma]["Scenario"][scenario_key] = verb_data[lemma]["Scenario"].get(scenario_key, 0) + 1

        # frequency of the particular lemma occurences in the phase
        phase_key = f"{course}/{scenario}/{phase}"
        verb_data[lemma]["Phase"][phase_key] = verb_data[lemma]["Phase"].get(phase_key, 0) + 1

        # frequency of the particular lemma occurences in the segment
        verb_data[lemma]["Segment"][segment] = verb_data[lemma]["Segment"].get(segment, 0) + 1



verb_lemma_rows = []

# sort by lemma frequency
for lemma, data in sorted(verb_data.items(), key=lambda x: x[1]["Frequency"], reverse=True):
    verb_lemma_rows.append({
        "Lemma": lemma,
        "Frequency": data["Frequency"],
        "Forms": data["Forms"],
        "XPOS": data["XPOS"],
        "Course": data["Course"],
        "Scenario": data["Scenario"],
        "Phase": data["Phase"],
        "Segment": data["Segment"]})

# create df for verb lemma distributions
verb_lemma_df = pd.DataFrame(verb_lemma_rows)


output_verb_lemma_tables = Path("/Masterarbeit/Projekt_Masterarbeit/evaluation_tables/"
                         "duo_verbs_combined_complete.xlsx")

verb_lemma_df.to_excel(output_verb_lemma_tables, index=False)



