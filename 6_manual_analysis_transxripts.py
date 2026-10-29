import stanza
import spacy
from pathlib import Path
import pandas as pd


nlp_spacy = spacy.load("de_core_news_md")
nlp_stanza = stanza.Pipeline("de", tokenize_pretokenized=True)

# create lists for evaluation set candidates
sents_with_obj_obl = list()
sents_with_obj_obl_arg = list()
sents_with_obl_agent = list()
sents_with_more_than_one_objs = list()


object_dep_tags = ["obj", "iobj", "obl", "obl:arg", "obl:agent"]
verbs_tags = ['VAFIN', 'VMFIN','VAPP', 'VMINF', 'VAINF', 'VVIZU', 'VVIMP', 'VVPP', 'VVINF', 'VVFIN', 'VAIMP', 'VMPP']


all_dep_tags = list()

def nlp_analyser_pos_dep_lemma_morph(tbk_path, tbk_name):

    """This function gets a path and a name of a transcript as an input and saves a manual
     analysis excel table with token, pos-tag, lemma, verb dependent, sentence and conjunct
    head columns based on this transcript"""


    with open(tbk_path, mode = "r", encoding = "UTF-8") as infile:
        tbk_text = infile.read()

    # tokenize text with spacy
    document_spacy = nlp_spacy(tbk_text)

    sents_spacy = list(document_spacy.sents)

    sents_input = list()
    sents_pos_spacy = list()

    # create lists of spacy tokens and pos-tags
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

    tokens_manual_analyse = list()

    verb_dependents_freqs = dict()



    for i, sent in enumerate(document_stanza.sentences):

        # report, if spacy and stanza numbers of tokens do not match
        words = sent.words
        if len(words) != len(sents_pos_spacy[i]):
            print("Stanza, SpaCy mismatch!")

        # sign for begin of a sentence
        sent_objs_tags = list()
        tokens_manual_analyse.append({
            "Token": "#S",
            "POS-Tag": "#S",
            "Dependency": "#S",
            "Morphology information": "#S",
            "Lemma": "#S",
            "Verb Dependent": "#S",
            "Sentence": sent.text,
            "Conj Head": "-"
        })


        for j, tok in enumerate(sent.words):

            if tok.deprel not in all_dep_tags:
                all_dep_tags.append(tok.deprel)

            # replace Stanza tag by APPRART tag
            if sents_pos_spacy[i][j] == "APPRART":
                xpos_tag = "APPRART"
            else:
                xpos_tag = tok.xpos

            # filter out punctuation marks, symbols and non-words
            if tok.upos not in {"PUNCT", "SYM"} and xpos_tag != "XY":

                # Default: not verb dependent, not conjunct of verb dependent
                is_verb_dep = False
                conj_head_tag = "-"
                head_index = tok.head - 1
                head_tok = words[head_index]

                # verb dependent found
                if head_tok.xpos in verbs_tags and tok.deprel in object_dep_tags:
                    is_verb_dep = True

                # conjunct of verb dependent found
                elif tok.deprel == "conj" and head_tok.deprel in object_dep_tags:

                    # index of head of the parent
                    grand_head_index = head_tok.head - 1

                    if grand_head_index >= 0:

                        grand_head_tok = words[grand_head_index]

                        # verb dependent found
                        if grand_head_tok.xpos in verbs_tags:
                            is_verb_dep = True
                            conj_head_tag = head_tok.deprel

                tokens_manual_analyse.append({
                    "Token": tok.text,
                    "POS-Tag": xpos_tag,
                    "Dependency": tok.deprel,
                    "Morphology information": tok.feats,
                    "Lemma": tok.lemma,
                    "Verb Dependent": is_verb_dep,
                    "Sentence": sent.text,
                    "Conj Head": conj_head_tag
                })

            if tok.deprel in object_dep_tags:

                head_index = tok.head - 1
                if head_index >= 0:
                    head_token = sent.words[head_index]

                    if head_token.xpos in verbs_tags:

                        sent_objs_tags.append(tok.deprel)

                        # count freqs of verb dependent
                        verb_dependents_freqs[tok.deprel] = verb_dependents_freqs.get(tok.deprel, 0) + 1

                        #print(tok.text, tok.deprel, "-", head_token.text, head_token.xpos)

        if "obj" in sent_objs_tags and "obl" in sent_objs_tags and sent.text not in sents_with_obj_obl:

            sents_with_obj_obl.append(sent.text)

        if "obl:agent" in sent_objs_tags and sent.text not in sents_with_obl_agent:

            sents_with_obl_agent.append(sent.text)

        if "obj" in sent_objs_tags and "obl:arg" in sent_objs_tags and sent.text not in sents_with_obj_obl_arg:

            sents_with_obj_obl_arg.append(sent.text)

        if sent_objs_tags.count("obj")  >= 2 and sent.text not in sents_with_more_than_one_objs:

            sents_with_more_than_one_objs.append(sent.text)

        # append end of the sentence sign
        tokens_manual_analyse.append({
            "Token": "#/S",
            "POS-Tag": "#/S",
            "Dependency": "#/S",
            "Morphology information": "#/S",
            "Lemma": "#/S",
            "Verb Dependent": "#/S",
            "Sentence": sent.text,
            "Conj Head": "-"
        })



    tokens_manual_analyse_df = pd.DataFrame(tokens_manual_analyse)

    tokens_manual_analyse_df["is_real_token"] = ~tokens_manual_analyse_df["POS-Tag"].isin(["#S", "#/S"])

    valid_sentences = (tokens_manual_analyse_df.groupby("Sentence")["is_real_token"].any())

    # delete empty sentences
    tokens_manual_analyse_df = tokens_manual_analyse_df[tokens_manual_analyse_df["Sentence"].isin(valid_sentences[valid_sentences].index)]

    tokens_manual_analyse_df = tokens_manual_analyse_df.drop(columns="is_real_token")

    tokens_manual_analyse_df.to_excel(f"/Masterarbeit/Manual_analysis_transcripts/{tbk_name}_manual_analysis_trcpts.xlsx")

    print(all_dep_tags)

    return verb_dependents_freqs

# create dataframe with verb dependent frequencies

source_dir = Path("/Masterarbeit/Textbooks_materials_filtered")
files = source_dir.iterdir()

verb_dependents_freqs_all_transcripts = dict()


for file in sorted(files):

    verb_dependents_dict_file = nlp_analyser_pos_dep_lemma_morph(file, file.name)
    for key in verb_dependents_dict_file.keys():
        verb_dependents_freqs_all_transcripts[key] = verb_dependents_freqs_all_transcripts.get(key, 0) + verb_dependents_dict_file[key]


verb_dependents_freqs_df_transcripts = pd.DataFrame([verb_dependents_freqs_all_transcripts])

verb_dependents_freqs_pfeffer = nlp_analyser_pos_dep_lemma_morph("/Masterarbeit/Pfeffer_Korpus/all_transcripts_filtered.txt", "Pfeffer_native_speakers")
verb_dependents_freqs_df_pfeffer = pd.DataFrame([verb_dependents_freqs_pfeffer])

verb_dependents_df_falko = pd.read_excel("/Masterarbeit/Verb_dependents_freqs.xlsx", index_col=0)

verb_dependents_all_df = pd.concat([verb_dependents_freqs_df_transcripts.assign(corpus="Textbook transcripts"),
                                    verb_dependents_freqs_df_pfeffer.assign(corpus="Pfeffer"),
                                     verb_dependents_df_falko.assign(corpus="KanDel")], ignore_index=True)

cols = ["corpus", "obj", "obl", "obl:arg", "obl:agent"]
verb_dependents_all_df = verb_dependents_all_df[cols]


verb_dependents_all_df.to_excel(f"/Masterarbeit/Verb_dependents_all_freqs.xlsx", index=False)


# save evaluation set candidates
with open("/Masterarbeit/sents_with_obj_obl.txt", "w", encoding="utf-8") as outfile:
    print(f"Number of sentences for annotation, obj and obl: {len(sents_with_obj_obl)}")
    for sentence in sents_with_obj_obl:
        outfile.write(sentence + "\n")

with open("/Masterarbeit/sents_with_obj_obl_arg.txt", "w", encoding="utf-8") as outfile:
    print(f"Number of sentences for annotation, obj and obl:arg: {len(sents_with_obj_obl_arg)}")
    for sentence in sents_with_obj_obl_arg:
        outfile.write(sentence + "\n")

with open("/Masterarbeit/sents_with_obl_agent.txt", "w", encoding="utf-8") as outfile:
    print(f"Number of sentences for annotation, obl:agent: {len(sents_with_obl_agent)}")
    for sentence in sents_with_obl_agent:
        outfile.write(sentence + "\n")

with open("/Masterarbeit/sents_with_more_than_one_objs.txt", "w", encoding="utf-8") as outfile:
    print(f"Number of sentences for annotation, more than one objs: {len(sents_with_more_than_one_objs)}")
    for sentence in sents_with_more_than_one_objs:
        outfile.write(sentence + "\n")

