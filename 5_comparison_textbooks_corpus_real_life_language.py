import re
import stanza
import spacy
from pathlib import Path
import pandas as pd
import json


nlp_spacy = spacy.load("de_core_news_md")
nlp_stanza = stanza.Pipeline("de", tokenize_pretokenized=True)


# filter a corpus of native speakers

input_path = "/Masterarbeit/Pfeffer_Korpus/all_transcripts.txt"
output_path = Path("/Masterarbeit/Pfeffer_Korpus/all_transcripts_filtered.txt")

with open(input_path, "r", encoding="utf-8") as input_file:
    pfeffer_text = input_file.read()

# split in single transcripts
pfeffer_blocks = re.split(r"(Audiodatei:.*?WAV)", pfeffer_text)

pfeffer_cleaned_blocks = []

for block in pfeffer_blocks:
    # delete meta data
    block = re.sub(r"Audiodatei:.*?WAV", "", block)
    block = re.sub(r"DGD-Link:.*?(?=\s|$)", "", block)
    block = re.sub(r"Quelle:.*?(?=\s|$)", "", block)

    # delete transcript meta data
    block = re.sub(r"Datenbank für Gesprochenes Deutsch.*?Transkript\s+[A-Z0-9_-]+,?.*",'', block)

    # delete speaker numbers, more than 3 numbers long
    block = re.sub(r"\b\d{3,}\b", "", block)
    block = re.sub(r"\bS\d+\b", "", block)

    # delete comments in italics
    block = re.sub(r"\(\(.*?\)\)", "", block)
    block = re.sub(r"\[.*?\]", "", block)


    # delete multiple spaces
    block = re.sub(r"\s+", " ", block)
    block = block.strip()

    if block:
        pfeffer_cleaned_blocks.append(block)

pfeffer_cleaned_text = "\n\n".join(pfeffer_cleaned_blocks)
pfeffer_cleaned_text = pfeffer_cleaned_text.replace("- Audio an der betreffenden Stelle abspielen / Audio anhalten ", "")

# save filtered transcripts of NS corpus
with open(output_path, "w", encoding="utf-8") as output_file:
    output_file.write(pfeffer_cleaned_text)

print("Length of the text:", len(pfeffer_cleaned_text))


# excluded: 'ITJ','PTKVZ', 'TRUNC'
content_words_tags = ['NE', 'ADJA',  'VVIZU', 'VVIMP', 'PAV', 'ADJD', 'VVPP',
                      'NN', 'VVINF', 'ADV', 'VVFIN']

function_words_tags = ['APPRART','PRF', 'PTKZU', 'VAFIN', 'KON', 'VMFIN','VAPP', 'KOUS', 'CARD',
                       'PWAV', 'KOKOM', 'PWAT', 'PIS', 'PWS', 'PPER', 'PRELS', 'APPR', 'VMINF', 'PDAT',
                       'PPOSAT', 'PIAT', 'PPOSS', 'VAINF', 'PDS', 'PTKNEG', 'ART', 'PTKANT', 'APPO']

verbs_tags = ['VAFIN', 'VMFIN','VAPP', 'VMINF', 'VAINF', 'VVIZU', 'VVIMP', 'VVPP', 'VVINF', 'VVFIN', 'VAIMP', 'VMPP']


def make_df_from_a_dict_lemmas(lemmas_freqs_dict, name_of_the_analysis, all_or_content_words):

    """This function gets dictionary with lemma frequencies as input and saves a dataframe with these
    frequencies in an excel-file"""

    lemmas_freqs_analyse = list()
    for lemma in sorted(lemmas_freqs_dict, key=lemmas_freqs_dict.get, reverse=True):
        lemmas_freqs_analyse.append({"Lemma": lemma, "Frequency": lemmas_freqs_dict[lemma]})

    lemmas_freqs_df = pd.DataFrame(lemmas_freqs_analyse)

    # lemma_freqs_df = pd.DataFrame(lemmas_freqs_dict, columns = [f"Lemma, {name_of_the_analysis}", f"Frequency, {name_of_the_analysis}"])
    lemmas_freqs_df.to_excel(
        f"/Masterarbeit/evaluation_tables/Lemma_frequencies_{name_of_the_analysis}_{all_or_content_words}.xlsx")



def create_and_count_ngrams(tokens, n, tbk_name):

    """This function gets a list of entities, n-count for ngrams and name of a transcript
     as an input and saves a dataframe with frequencies of ngrams in an excel-file"""

    ngrams = list()

    for i in range(len(tokens) - n + 1):
        ngram = tokens[i:i + n]
        ngram_tuple = tuple(ngram)
        ngrams.append(ngram_tuple)


    freqs_ngrams = {}


    for ngram in ngrams:

        freqs_ngrams[ngram] = freqs_ngrams.get(ngram, 0) + 1

    ngrams_freqs_analyse = list()
    for ngram in sorted(freqs_ngrams, key=freqs_ngrams.get, reverse=True):

        ngrams_freqs_analyse.append({
            "Ngram": ngram,
            "Frequency": freqs_ngrams[ngram],
        })

    ngrams_freqs_df = pd.DataFrame(ngrams_freqs_analyse)

    ngrams_freqs_df.to_excel(
        f"/Masterarbeit/evaluation_tables/{tbk_name}_Ngrams_analyse.xlsx")


    return ngrams

def calculate_frequency_and_sort_df(entities_list, name_of_the_analysis, name_of_entities):

    """This function gets a list of entities, name of the analyses and name of entities as
    an input and saves a dataframe with downward sorted frequncies of these entities in a file"""

    freqs_entities = dict()

    for elem in entities_list:

        freqs_entities[elem] = freqs_entities.get(elem, 0) + 1

    entities_freqs_analyse = list()

    for elem in sorted(freqs_entities, key=freqs_entities.get, reverse=True):

        entities_freqs_analyse.append({
            name_of_entities: elem,
            "Frequency": freqs_entities[elem],
        })

    entities_freqs_df = pd.DataFrame(entities_freqs_analyse)

    entities_freqs_df.to_excel(
        f"/Masterarbeit/evaluation_tables/{name_of_the_analysis}_{name_of_entities}.xlsx")


def create_most_frequent_words_dfs(text_path, name_of_the_analysis):

    """This function gets text of a transcript as an input and outputs the number of all and filtered
    tokens of this transcript as output. Additionally, this function saves excel tables with lemma frequencies,
    verb lemma frequencies, frequencies of all trigrams and of trigrams, that include verbs"""

    with open(text_path, mode = "r", encoding = "UTF-8") as infile:
        text = infile.read()

    # tokenize transcript with spacy
    document_spacy = nlp_spacy(text)

    sents_spacy = list(document_spacy.sents)

    sents_input = list()
    sents_pos_spacy = list()

    # create lists of tokens and of pos-tags
    for sent in sents_spacy:
        sentence = list()
        sent_spacy_pos = list()
        for tok in sent:
            sentence.append(tok.text)
            sent_spacy_pos.append(tok.tag_)
        sents_input.append(sentence)
        sents_pos_spacy.append(sent_spacy_pos)

    # use spacy tokens as an input for stanza
    document_stanza = nlp_stanza(sents_input)


    lemmas_freqs_dict = dict()
    content_lemmas_dict = dict()
    verbs_lemmas_dict = dict()
    count_toks = 0
    count_analysed_toks = 0
    stanza_sentences_pos = list()
    stanza_sentences_toks = list()
    stanza_sentences_toks_without_sent_tags = list()
    stanza_sentences_pos_without_sent_tags = list()


    for i, sent in enumerate(document_stanza.sentences):

        # report, if spacy and stanza numbers of tokens do not match
        if len(sent.words) != len(sents_pos_spacy[i]):
            print("Stanza, SpaCy mismatch!")

        # append begin of the sentence sign
        stanza_sentences_toks.append("<#S>")
        stanza_sentences_pos.append("<#S>")

        for j, tok in enumerate(sent.words):
            count_toks += 1

            # replace Stanza tag by APPRART tag
            if sents_pos_spacy[i][j] == "APPRART":
                xpos_tag = "APPRART"
            else:
                xpos_tag = tok.xpos

            # filter out punctuation marks, signs and non-words
            if tok.upos not in {"PUNCT", "SYM"} and xpos_tag != "XY":
                count_analysed_toks += 1
                stanza_sentences_toks.append(tok.text)
                stanza_sentences_pos.append(xpos_tag)
                stanza_sentences_toks_without_sent_tags.append(tok.text)
                stanza_sentences_pos_without_sent_tags.append(xpos_tag)
                lemmas_freqs_dict[tok.lemma.lower()] = lemmas_freqs_dict.get(tok.lemma.lower(), 0) + 1

                # create dictionary with frequencies of lemmas for content words
                if xpos_tag in content_words_tags:
                    content_lemmas_dict[tok.lemma.lower()] = content_lemmas_dict.get(tok.lemma.lower(), 0) + 1
                # create dictionary with frequencies of verb lemmas
                if xpos_tag in verbs_tags:
                    verbs_lemmas_dict[tok.lemma.lower()] = verbs_lemmas_dict.get(tok.lemma.lower(), 0) + 1

        # append end of the sentence sign
        stanza_sentences_toks.append("</#S>")
        stanza_sentences_pos.append("</#S>")


    # create excel-files with lemma frequencies
    make_df_from_a_dict_lemmas(lemmas_freqs_dict, name_of_the_analysis, "all_words")
    make_df_from_a_dict_lemmas(content_lemmas_dict, name_of_the_analysis, "content_words")
    make_df_from_a_dict_lemmas(verbs_lemmas_dict, name_of_the_analysis, "verbs")

    # create excel-files with trigram frequencies
    toks_trigrams = create_and_count_ngrams(stanza_sentences_toks, 3, f"{name_of_the_analysis}_toks")
    xpos_trigrams = create_and_count_ngrams(stanza_sentences_pos, 3, f"{name_of_the_analysis}_pos")
    toks_trigrams_without_sent_tags = create_and_count_ngrams(stanza_sentences_toks_without_sent_tags, 3, f"{name_of_the_analysis}_without_sent_tags_toks")
    xpos_trigrams_without_sent_tags = create_and_count_ngrams(stanza_sentences_pos_without_sent_tags, 3, f"{name_of_the_analysis}_without_sent_tags_pos")


    verbs_toks_trigrams = list()
    verbs_xpos_trigrams = list()
    verbs_toks_trigrams_without_sent_tags = list()
    verbs_xpos_trigrams_without_sent_tags = list()

    # create excel-files with frequencies of trigrams, that include verbs: tokens and pos tags
    for i, trigram in enumerate(xpos_trigrams):
        if any(tag in verbs_tags for tag in trigram):
            verbs_xpos_trigrams.append(trigram)
            verbs_toks_trigrams.append(toks_trigrams[i])

    calculate_frequency_and_sort_df(verbs_toks_trigrams, name_of_the_analysis, "verbs_trigrams_tokens")
    calculate_frequency_and_sort_df(verbs_xpos_trigrams, name_of_the_analysis, "verbs_trigrams_xpos_tags")


    for i, trigram in enumerate(xpos_trigrams_without_sent_tags):
        if any(tag in verbs_tags for tag in trigram):
            verbs_xpos_trigrams_without_sent_tags.append(trigram)
            verbs_toks_trigrams_without_sent_tags.append(toks_trigrams_without_sent_tags[i])

    calculate_frequency_and_sort_df(verbs_toks_trigrams_without_sent_tags, name_of_the_analysis, "verbs_trigrams_tokens_without_sent_tags")
    calculate_frequency_and_sort_df(verbs_xpos_trigrams_without_sent_tags, name_of_the_analysis, "verbs_trigrams_xpos_tags_without_sent_tags")


    # present all tokens and filtered tokens
    print(f"The number of tokens in {name_of_the_analysis} is {count_toks}")
    print(f"The number of analysed tokens in {name_of_the_analysis} is {count_analysed_toks}")

    return [count_toks, count_analysed_toks]

# analyze textbook transcripts and NS corpus

source_dir = Path("/Masterarbeit/Textbooks_materials_filtered")
files = source_dir.iterdir()
number_of_toks_dict = dict()


for file in sorted(files):

    number_of_toks_dict[file.stem] = create_most_frequent_words_dfs(file, file.stem)

# all dialogues of native speakers in one file
number_of_toks_dict["Pfeffer"] = create_most_frequent_words_dfs("/Masterarbeit/Pfeffer_Korpus/all_transcripts_filtered.txt", "Pfeffer_native_speakers")


# analyze learner corpus

with open("/Masterarbeit/Falko_KanDel/annis_long_cohort_2_2014-export14116464370242787.txt",
          mode="r", encoding="UTF-8") as infile:
    falko_tokens = list()
    token_dict = dict()
    for line in infile:
        if line.strip():
            # if new token starts
            if line.strip()[0].isdigit():
                if token_dict:
                    # save information of the previous token
                    falko_tokens.append(token_dict)


                token_dict = dict()
                line_elems = line.strip().split()
                token_dict["id"] = line_elems[0]
                token_dict["tok"] = line_elems[-1]

            # end of the file
            elif line.strip() == "finished":
                falko_tokens.append(token_dict)
            else:
                line_elems = line.strip().split()
                # left - name of the category, right - category
                token_dict[line_elems[0]] = line_elems[1]



punct_marks = ['$("', '"$,"', '$.', '$,', '$(']

falko_tags = list()

# save names of falko layers
for tok_feats in falko_tokens:
    for falko_tag in tok_feats.keys():
        if falko_tag not in falko_tags:
            falko_tags.append(falko_tag)

print(falko_tags)

# save falko words as a string
falko_text = ""

for tok_feats in falko_tokens:
    if "word" in tok_feats.keys():
        # falko_text = falko_text + " " + tok_feats["id"] + " " + tok_feats["txt"]
        falko_text = falko_text + " " + tok_feats["word"]
    else:
        print(tok_feats["id"])

with open("/Masterarbeit/Falko_as_full_text.txt", "w", encoding="utf-8") as outfile:
    outfile.write(falko_text)

# print(falko_text)

# analyse ZH1 (target hypothesis 1) tokens
zh1_tok_falko = list()
zh1_lemma_falko = list()
zh1_pos_falko = list()

lemma_freqs_falko = dict()
pos_freqs_falko = dict()
content_lemmas_freqs_falko = dict()
verbs_freqs_falko = dict()

sents_nr = "s0"

for tok_feats in falko_tokens:

    # save ZH1 information sentence by sentence
    if "ZH1S" in tok_feats.keys() and tok_feats["ZH1S"] != sents_nr:

        if sents_nr != "s0":
            zh1_tok_falko.append(tok_sent)
            zh1_lemma_falko.append(lemma_sent)
            zh1_pos_falko.append(pos_sent)

        sents_nr = tok_feats["ZH1S"]

        tok_sent = list()
        lemma_sent = list()
        pos_sent = list()

        if "ZH1" in tok_feats.keys():
            tok_sent.append(tok_feats["ZH1"])
        # else: print(f"No ZH1 word: {tok_feats["id"]}")

        if "ZH1lemma" in tok_feats.keys():
            lemma_sent.append(tok_feats["ZH1lemma"])
        # else: print(f"No ZH1 lemma: {tok_feats["id"]}")

        if "ZH1pos" in tok_feats.keys():
            pos_sent.append(tok_feats["ZH1pos"])
        # else:
        # print(f"No ZH1 POS-tag: {tok_feats["id"]}")

    elif tok_feats["ZH1S"] == sents_nr:

        if "ZH1" in tok_feats.keys():
            tok_sent.append(tok_feats["ZH1"])
        # else: print(f"No ZH1 word: {tok_feats["id"]}")

        if "ZH1lemma" in tok_feats.keys():
            lemma_sent.append(tok_feats["ZH1lemma"])
        # else: print(f"No ZH1 lemma: {tok_feats["id"]}")

        if "ZH1pos" in tok_feats.keys():
            pos_sent.append(tok_feats["ZH1pos"])
        # else:
        # print(f"No ZH1 POS-tag: {tok_feats["id"]}")

# append information for last sentence
zh1_tok_falko.append(tok_sent)
zh1_lemma_falko.append(lemma_sent)
zh1_pos_falko.append(pos_sent)

#print(zh1_tok_falko[:6], zh1_lemma_falko[:6], zh1_pos_falko[:6])

zh1_tok_falko_flat = list()
zh1_lemma_falko_flat = list()
zh1_pos_falko_flat = list()

zh1_tok_falko_flat_without_sent_tags = list()
zh1_lemma_falko_flat_without_sent_tags = list()
zh1_pos_falko_flat_without_sent_tags = list()


# save falko information in manual analysis table with tokens, lemmas, pos-tags, dependency tags, verb
# dependent/no verb dependent, conjunct of verb dependent columns
tokens_manual_analyse_falko = list()
falko_stanza_dep = list()
falko_stanza_is_verb_dependent = []
falko_conj_heads_list = list()

all_dep_tags_falko = list()

# analyze falko tokens with stanza
nlp_stanza_pretokenized = stanza.Pipeline("de", tokenize_pretokenized=True)

document_stanza_pt = nlp_stanza_pretokenized(zh1_tok_falko)

# selecting sentences for the evaluation
sents_with_obj_obl = list()
sents_with_obj_obl_arg = list()
sents_with_obl_agent = list()
sents_with_more_than_one_objs = list()
object_dep_tags = ["obj", "iobj", "obl", "obl:arg", "obl:agent"]

verb_dependents_freqs_falko = dict()

for sentence in document_stanza_pt.sentences:
    sent_stanza_falko = list()
    sent_is_verb_dependent = []
    sent_objs_tags = list()
    sent_conj_heads_list = list()

    words = sentence.words

    for tok in words:

        head_index = tok.head - 1

        # default value: not verb dependent and not a conjunct of verb dependent
        is_verb_dep = False
        conj_head = "-"

        if tok.deprel not in all_dep_tags_falko:
            all_dep_tags_falko.append(tok.deprel)


        if tok.deprel in object_dep_tags and head_index >= 0:

            head_tok = words[head_index]

            # verb dependent found
            if head_tok.xpos in verbs_tags:
                is_verb_dep = True

        # if dependency tag is conjunct
        elif tok.deprel == "conj":

            head_tok = words[head_index]
            # index of the parent's parent
            grand_head_index = head_tok.head - 1

            if grand_head_index >= 0:

                grand_head_tok = words[grand_head_index]

                # conjunct of verb dependent found
                if grand_head_tok.xpos in verbs_tags and head_tok.deprel in object_dep_tags:
                    is_verb_dep = True
                    conj_head = head_tok.deprel

        sent_stanza_falko.append(tok.deprel)
        sent_is_verb_dependent.append(is_verb_dep)
        sent_conj_heads_list.append(conj_head)

        if tok.deprel in object_dep_tags:
            sent_objs_tags.append(tok.deprel)

            if is_verb_dep:
                verb_dependents_freqs_falko[tok.deprel] = verb_dependents_freqs_falko.get(tok.deprel, 0) + 1

    falko_stanza_dep.append(sent_stanza_falko)
    falko_stanza_is_verb_dependent.append(sent_is_verb_dependent)
    falko_conj_heads_list.append(sent_conj_heads_list)

    # data set for evaluation set candidates
    if "obj" in sent_objs_tags and "obl" in sent_objs_tags and sentence.text not in sents_with_obj_obl:
        sents_with_obj_obl.append(sentence.text)

    if "obl:agent" in sent_objs_tags and sentence.text not in sents_with_obl_agent:
        sents_with_obl_agent.append(sentence.text)

    if "obj" in sent_objs_tags and "obl:arg" in sent_objs_tags and sentence.text not in sents_with_obj_obl_arg:
        sents_with_obj_obl_arg.append(sentence.text)

    if sent_objs_tags.count("obj") >= 2 and sentence.text not in sents_with_more_than_one_objs:
        sents_with_more_than_one_objs.append(sentence.text)

# save sentences with evaluation set candidates
with open("/Masterarbeit/falko_sents_with_obj_obl.txt", "w", encoding="utf-8") as outfile:
    print(f"Number of sentences for annotation, obj and obl: {len(sents_with_obj_obl)}")
    for sentence in sents_with_obj_obl:
        outfile.write(sentence + "\n")

with open("/Masterarbeit/falko_sents_with_obj_obl_arg.txt", "w", encoding="utf-8") as outfile:
    print(f"Number of sentences for annotation, obj and obl:arg: {len(sents_with_obj_obl_arg)}")
    for sentence in sents_with_obj_obl_arg:
        outfile.write(sentence + "\n")

with open("/Masterarbeit/falko_sents_with_obl_agent.txt", "w", encoding="utf-8") as outfile:
    print(f"Number of sentences for annotation, obl:agent: {len(sents_with_obl_agent)}")
    for sentence in sents_with_obl_agent:
        outfile.write(sentence + "\n")

with open("/Masterarbeit/falko_sents_with_more_than_one_objs.txt", "w",
          encoding="utf-8") as outfile:
    print(f"Number of sentences for annotation, more than one objs: {len(sents_with_more_than_one_objs)}")
    for sentence in sents_with_more_than_one_objs:
        outfile.write(sentence + "\n")


verb_dependents_freqs_df = pd.DataFrame([verb_dependents_freqs_falko])

verb_dependents_freqs_df.to_excel(
    f"/Masterarbeit/Verb_dependents_freqs.xlsx")

count_toks_falko = 0
count_analysed_toks_falko = 0


# prepare falko data for manual analysis table with token, pos-tag, lemma, verb dependent,
# sentence and conjunct head columns


for i in range(len(zh1_tok_falko)):

    sentence_string = " ".join(zh1_tok_falko[i])

    tokens_manual_analyse_falko.append({
        "Token": "#S",
        "POS-Tag": "#S",
        "Lemma": "#S",
        "Dependency": "#S",
        "Verb Dependent": "#S",
        "Sentence": sentence_string,
        "Conj Head": "-"
    })

    zh1_tok_falko_flat.append("#S")
    zh1_lemma_falko_flat.append("#S")
    zh1_pos_falko_flat.append("#S")

    for j in range(len(zh1_tok_falko[i])):

        count_toks_falko += 1

        # filter out punctuation marks and non-words
        if (zh1_pos_falko[i][j].startswith("$") == False) and zh1_pos_falko[i][j] != "XY":
            count_analysed_toks_falko += 1
            conj_head_tag = "-"

            zh1_tok_falko_flat.append(zh1_tok_falko[i][j])
            zh1_lemma_falko_flat.append(zh1_lemma_falko[i][j])
            zh1_pos_falko_flat.append(zh1_pos_falko[i][j])

            zh1_tok_falko_flat_without_sent_tags.append(zh1_tok_falko[i][j])
            zh1_lemma_falko_flat_without_sent_tags.append(zh1_lemma_falko[i][j])
            zh1_pos_falko_flat_without_sent_tags.append(zh1_pos_falko[i][j])

            tokens_manual_analyse_falko.append({
                "Token": zh1_tok_falko[i][j],
                "POS-Tag": zh1_pos_falko[i][j],
                "Lemma": zh1_lemma_falko[i][j],
                "Dependency": falko_stanza_dep[i][j],
                "Verb Dependent": falko_stanza_is_verb_dependent[i][j],
                "Sentence": sentence_string,
                "Conj Head": falko_conj_heads_list[i][j]
            })


    tokens_manual_analyse_falko.append({
        "Token": "#/S",
        "POS-Tag": "#/S",
        "Lemma": "#/S",
        "Dependency": "#/S",
        "Verb Dependent": "#/S",
        "Sentence": sentence_string,
        "Conj Head": "-"
    })

    zh1_tok_falko_flat.append("#/S")
    zh1_lemma_falko_flat.append("#/S")
    zh1_pos_falko_flat.append("#/S")

falko_lemmas_dict_all = dict()
falko_lemmas_dict_content_words = dict()
falko_lemmas_dict_verbs = dict()

print("Flat list:", zh1_tok_falko_flat)



for token in tokens_manual_analyse_falko:
    if token["Lemma"] not in {"#S", "#/S"}:
        falko_lemmas_dict_all[token["Lemma"].lower()] = falko_lemmas_dict_all.get(token["Lemma"].lower(), 0) + 1

    if token["POS-Tag"] in content_words_tags:
        falko_lemmas_dict_content_words[token["Lemma"].lower()] = falko_lemmas_dict_content_words.get(
            token["Lemma"].lower(), 0) + 1

    if token["POS-Tag"] in verbs_tags:
        falko_lemmas_dict_verbs[token["Lemma"].lower()] = falko_lemmas_dict_verbs.get(token["Lemma"].lower(), 0) + 1

# excel tables with lemmas, trigrams, verb lemmas and verb trigrams,
# content word lemmas and content word trigrams frequencies for falko data

# with tags for beginning and end of the sentence

zh1_tok_falko_trigrams = create_and_count_ngrams(zh1_tok_falko_flat, 3, "KanDel_toks")
zh1_lemma_falko_trigrams = create_and_count_ngrams(zh1_lemma_falko_flat, 3, "KanDel_lemmas")
zh1_pos_falko_trigrams = create_and_count_ngrams(zh1_pos_falko_flat, 3, "KanDel_pos")

make_df_from_a_dict_lemmas(falko_lemmas_dict_all, "KanDel", "all_words")
make_df_from_a_dict_lemmas(falko_lemmas_dict_content_words, "KanDel", "content_words")
make_df_from_a_dict_lemmas(falko_lemmas_dict_verbs, "KanDel", "verbs")

falko_verbs_toks_trigrams = list()
falko_verbs_xpos_trigrams = list()

for i, trigram in enumerate(zh1_pos_falko_trigrams):
    if any(tag in verbs_tags for tag in trigram):
        falko_verbs_xpos_trigrams.append(trigram)
        falko_verbs_toks_trigrams.append(zh1_tok_falko_trigrams[i])

calculate_frequency_and_sort_df(falko_verbs_toks_trigrams, "KanDel_toks", "verbs_trigrams")
calculate_frequency_and_sort_df(falko_verbs_xpos_trigrams, "KanDel_pos_tags", "verbs_trigrams")

# without tags for beginning and end of the sentence

zh1_tok_falko_trigrams_without_sent_tags = create_and_count_ngrams(zh1_tok_falko_flat_without_sent_tags, 3,
                                                                   "KanDel_toks_without_sent_tags")
zh1_lemma_falko_trigrams_without_sent_tags = create_and_count_ngrams(zh1_lemma_falko_flat_without_sent_tags, 3,
                                                                     "KanDel_lemmas_without_sent_tags")
zh1_pos_falko_trigrams_without_sent_tags = create_and_count_ngrams(zh1_pos_falko_flat_without_sent_tags, 3,
                                                                   "KanDel_pos_without_sent_tags")

falko_verbs_toks_trigrams_without_sent_tags = list()
falko_verbs_xpos_trigrams_without_sent_tags = list()

for i, trigram in enumerate(zh1_pos_falko_trigrams_without_sent_tags):
    if any(tag in verbs_tags for tag in trigram):
        falko_verbs_xpos_trigrams_without_sent_tags.append(trigram)
        falko_verbs_toks_trigrams_without_sent_tags.append(zh1_tok_falko_trigrams_without_sent_tags[i])

calculate_frequency_and_sort_df(falko_verbs_toks_trigrams_without_sent_tags, "KanDel_toks",
                                "verbs_trigrams_without_sent_tags")
calculate_frequency_and_sort_df(falko_verbs_xpos_trigrams_without_sent_tags, "KanDel_pos_tags",
                                "verbs_trigrams_without_sent_tags")

tokens_manual_analyse_falko_df = pd.DataFrame(tokens_manual_analyse_falko)

tokens_manual_analyse_falko_df.to_excel(
    "/Masterarbeit/Manual_analysis_transcripts/KanDel_manual_analysis.xlsx")

number_of_toks_dict["KanDel"] = [count_toks_falko, count_analysed_toks_falko]

# save number of all and filtered tokens for all the corpora in a dictionary
with open("/Masterarbeit/number_of_toks_dict.json", "w", encoding="utf-8") as outfile:
    json.dump(number_of_toks_dict, outfile, ensure_ascii=False, indent=2)

for key, value in number_of_toks_dict.items():

    print(f"{key}: {value}")