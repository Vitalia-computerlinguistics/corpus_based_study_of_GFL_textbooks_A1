import stanza
from pathlib import Path
import pandas as pd


object_subject_dep_tags = ["obj", "iobj", "obl", "obl:arg", "obl:agent"]

verbs_tags = ['VAFIN','VMFIN','VAPP','VMINF','VAINF', 'VVIZU','VVIMP','VVPP','VVINF','VVFIN','VAIMP','VMPP']


nlp_stanza = stanza.Pipeline(lang='de', processors="tokenize,pos,lemma,depparse")

def is_verb(word):
    """This function gets a word as an input and outputs True, if it is a verb
    and False if not"""
    return word.xpos in verbs_tags


def has_direct_verb_head(tok, sent):

    """This function gets a tok and a sentence as an input and outputs
    True, if the word has a verb head and False if not"""

    head = sent.words[tok.head - 1]

    return is_verb(head)


def conj_of_verb_argument(tok, sent):

    """This function gets a tok and a sentence as an input and outputs True, if the tok is
     conjunct of a word with target-tag, that depends on a verb, otherwise the function
     outputs False"""

    if tok.deprel != "conj":
        return False, None

    if tok.head == 0:
        return False, None

    head = sent.words[tok.head - 1]

    if head.deprel not in object_subject_dep_tags:
        return False, None

    if head.head == 0:
        return False, None

    verb = sent.words[head.head - 1]

    if is_verb(verb):
        return True, head.deprel

    return False, None


def analyse_evaluation_set(text_path):

    """This function takes path of a file as an input and outputs dictionary with frequencies
    of target verb dependent tags, number of tokens, words and sentences in this file"""

    with open(text_path, mode="r", encoding="UTF-8") as infile:
        text = infile.read()

    # analyze text with stanza
    document_stanza = nlp_stanza(text)


    verb_dependent_freqs = {}

    count_toks = 0
    count_words = 0


    for i, sent in enumerate(document_stanza.sentences):

        for tok in sent.words:

            count_toks += 1

            # filter out punctuation marks
            if tok.upos == "PUNCT":
                continue


            count_words += 1


            # if token is verb dependent with target dependency tag, plus one to frequency
            # of the tag
            if tok.deprel in object_subject_dep_tags:

                if has_direct_verb_head(tok, sent):

                    verb_dependent_freqs[tok.deprel] = verb_dependent_freqs.get(tok.deprel, 0) + 1

                    #print(tok.deprel, tok.text, sent.text)

            else:
                # if token is conjunct of the word with target dependency tag and verb dependent,
                # plus one to the frequency of the corresponding target tag
                is_conj, parent_dep = conj_of_verb_argument(tok, sent)

                if is_conj:

                    verb_dependent_freqs[parent_dep] = verb_dependent_freqs.get(parent_dep, 0) + 1

                    #print("conj", parent_dep, tok.text, sent.text)



    verb_dependent_freqs["Number of Tokens"] = count_toks
    verb_dependent_freqs["Number of Words"] = count_words
    verb_dependent_freqs["Number of Sentences"] = len(document_stanza.sentences)


    return verb_dependent_freqs



source_dir = Path("/Masterarbeit/sents_for_inception")

files = source_dir.iterdir()


evaluation_set_features = []

# save dataframe with evaluation set information

for file in files:

    evaluation_set_dict = analyse_evaluation_set(file)


    row = {

        "Title of the corpus": file.stem,

        "Number of Sentences": evaluation_set_dict["Number of Sentences"],

        "Number of Tokens": evaluation_set_dict["Number of Tokens"],

        "Number of Words": evaluation_set_dict["Number of Words"]}


    for dep in object_subject_dep_tags:
        row[f"Number of {dep}"] = evaluation_set_dict.get(dep, 0)


    evaluation_set_features.append(row)



evaluation_set_features_df = pd.DataFrame(evaluation_set_features)


evaluation_set_features_df.to_excel("/Masterarbeit/Evaluation_set_features.xlsx")


