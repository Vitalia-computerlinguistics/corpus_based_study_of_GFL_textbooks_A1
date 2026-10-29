import conllu
import pandas as pd
from pathlib import Path
import stanza


def tokens_pos_dep_head_tagging_on_inception(sent_lists):

    """This function gets list of sentences as an input and outputs lists of tokens,
    pos-, dependency and head tags"""

    document_stanza = nlp_stanza([sent_lists])

    tokens_stanza_text = []
    tokens_stanza_pos = []
    tokens_stanza_dep = []
    tokens_stanza_head = []

    for sentence in document_stanza.sentences:
        for tok in sentence.words:
            tokens_stanza_text.append(tok.text)
            tokens_stanza_pos.append(tok.xpos)
            tokens_stanza_dep.append(tok.deprel)
            tokens_stanza_head.append(tok.head)

    return tokens_stanza_text, tokens_stanza_pos, tokens_stanza_dep, tokens_stanza_head

nlp_stanza = stanza.Pipeline("de", processors="tokenize,pos, lemma,depparse", tokenize_pretokenized=True)

source_dir = Path("/Masterarbeit/inception_export/annotated_data")

files = source_dir.iterdir()

all_annotation_dfs = list()

# iterate through files extracted from the inception annotation tool
for file in sorted(files):

    file_sent_tokens = list()
    file_sent_xpos_tags = list()
    file_sent_head_tags = list()
    file_sent_dep_tags = list()

    with open(file, "r", encoding="utf-8") as f:
        conll = f.read()

        sentences = conllu.parse(conll)


        for sentence in sentences:

            sent_tokens = list()
            sent_xpos_tags = list()
            sent_dep_tags = list()
            sent_head_tags = list()

            for token in sentence:

                print("id", token["id"])
                print("form:", token["form"])
                sent_tokens.append(token["form"])
                print("lemma:", token["lemma"])
                print("upos:", token["upos"])
                print("xpos:", token["xpos"])
                sent_xpos_tags.append(token["xpos"])
                print("feats:", token["feats"])
                print("deprel:", token["deprel"])
                sent_dep_tags.append(token["deprel"])
                print("head:", token["head"])
                sent_head_tags.append(token["head"])
                print()
                print()

            if sent_tokens:
                file_sent_tokens.append(sent_tokens)
                file_sent_xpos_tags.append(sent_xpos_tags)
                file_sent_dep_tags.append(sent_dep_tags)
                file_sent_head_tags.append(sent_head_tags)


    # create a serie for tokens, lemmas, xpos, dependency and head tags and join them to a data frame
    index_all = list(range(1,len(file_sent_tokens)+1))
    file_tokens_s = pd.Series(file_sent_tokens, index = index_all)
    file_x_pos_tags_s = pd.Series(file_sent_xpos_tags, index = index_all)
    file_dep_tags_s = pd.Series(file_sent_dep_tags, index=index_all)
    file_head_tags_s = pd.Series(file_sent_head_tags, index=index_all)


    # save inception and stanza analysis in annotation dataframe
    annotation_df = pd.concat([file_tokens_s, file_x_pos_tags_s, file_dep_tags_s, file_head_tags_s], axis = 1)
    annotation_df.columns = ["Tokens, Inception", "XPOS Tags, Inception", "Dependency Tags, Inception", "Head Position, Inception"]
    #print(annotation_df.head(20))


    annotation_df[["Stanza Tokens", "Stanza XPOS Tags", "Stanza Dependency Tags", "Stanza Head Position"]] = pd.DataFrame(
        annotation_df["Tokens, Inception"].apply(tokens_pos_dep_head_tagging_on_inception).tolist(),
        index=annotation_df.index)


    annotation_df.to_excel(f"/Masterarbeit/inception_export/annotated_data_and_Stanza_excel/{file.stem}_annotation.xlsx")

    annotation_df["File"] = file.stem

    all_annotation_dfs.append(annotation_df)


all_files_df = pd.concat(all_annotation_dfs, ignore_index=True)

all_files_df.to_excel("/Masterarbeit/inception_export/annotated_data_and_Stanza_excel/all_annotations.xlsx", index=False)




