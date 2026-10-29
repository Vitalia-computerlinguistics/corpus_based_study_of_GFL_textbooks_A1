from pathlib import Path
import pandas as pd

# set input and output paths
source_dir = Path("/Masterarbeit/Manual_analysis_transcripts")
output_dir = Path("/Masterarbeit/modal_verbs_distributions")


modal_verbs_tags = ['VMFIN','VMINF','VMPP']
modal_verbs_lemmas = ["müssen","können","dürfen", "sollen","wollen","mögen","möchten"]


# create dictionary with frequencies per corpus
corpus_modal_counts = {"NS":{}, "TB":{},"LR":{}}

textbook_modal_counts = {}

lemmas_wrong_pos_tags_dict = {}

# token counters
corpus_token_counts = {"NS":0,"TB":0,"LR":0}
textbook_token_counts = {}


for file in sorted(source_dir.iterdir()):


    corpus_df = pd.read_excel(file)


    corpus_df["Lemma"] = corpus_df["Lemma"].astype(str).str.lower()

    # filer out begin and end of the sentence tokens
    token_count = corpus_df[~corpus_df["Token"].isin(["#S","#/S"])].shape[0]

   # modal verb has modal lemma or pos-tag of modal verb
    modal_df = corpus_df.loc[(corpus_df["Lemma"].isin(modal_verbs_lemmas)) | (corpus_df["POS-Tag"].isin(modal_verbs_tags))]

    # frequencies of modal verb lemmas
    modal_freqs = modal_df["Lemma"].value_counts().to_dict()

    modal_freqs_df = pd.DataFrame.from_dict(modal_freqs, orient="index", columns=["Frequency"]).reset_index()

    modal_freqs_df.columns = ["Modal Verb","Frequency"]

    # normalized frequencies per file
    modal_freqs_df["Norm per 10000 tokens"] = (modal_freqs_df["Frequency"] / token_count) * 10000

    modal_freqs_df.to_excel(output_dir / f"{file.stem}.xlsx", index=False)


    # determine corpus
    name = file.stem.lower()

    corpus_type = None

    if "pfeffer" in name:
        corpus_type = "NS"

    elif "kandel" in name:
        corpus_type = "LR"

    elif "all_transcripts" in name:
        corpus_type = "TB"


    if corpus_type is not None:
        corpus_token_counts[corpus_type] += token_count

    # count modal verb frequencies per corpus
    if corpus_type is not None:

        for verb, freq in modal_freqs.items():

            corpus_modal_counts[corpus_type][verb] = corpus_modal_counts[corpus_type].get(verb,0) + freq

    # count modal verb frequencies and number of tokens for each textbook
    if any(tb in name for tb in ["akademie","linie","netzwerk","starten","intensivtrainer","duo_dialogues"]):

        textbook_modal_counts[file.stem] = modal_freqs
        textbook_token_counts[file.stem] = token_count

    # mistakes df, modal verb lemmas without modal verb pos tags
    mistakes_df = corpus_df.loc[(corpus_df["Lemma"].isin(modal_verbs_lemmas))
                                & (~corpus_df["POS-Tag"].isin(modal_verbs_tags))]

    for lemma in mistakes_df["Lemma"]:

        lemmas_wrong_pos_tags_dict[lemma] = lemmas_wrong_pos_tags_dict.get(lemma,0) + 1

# save frequencies of modal verbs per corpus in an excel table
corpus_freq_df = pd.DataFrame(corpus_modal_counts).fillna(0)

for corpus in corpus_freq_df.columns:

    tokens = corpus_token_counts[corpus]

    corpus_freq_df[f"{corpus}_norm_per_10000"] = round(((corpus_freq_df[corpus] / tokens) * 10000), 2)

corpus_freq_df.index.name = "Modal Verb"

corpus_freq_df = corpus_freq_df.reset_index()

corpus_freq_df.to_excel(output_dir / "modal_verbs_corpus_frequencies.xlsx", index=False)


# save frequencies of modal verbs per textbook in an excel table
textbook_freq_df = pd.DataFrame(textbook_modal_counts).fillna(0)

for book in textbook_modal_counts:

    tokens = textbook_token_counts[book]

    textbook_freq_df[f"{book}_norm_per_10000"] = round(((textbook_freq_df[book] / tokens) * 10000), 2)

textbook_freq_df.index.name = "Modal Verb"

textbook_freq_df = textbook_freq_df.reset_index()

textbook_freq_df.to_excel(output_dir / "modal_verbs_textbooks_frequencies.xlsx", index=False)

# save dataframe with mistakes: modal verb lemma, but no modal verb pos tag
mistakes_df = pd.DataFrame.from_dict(lemmas_wrong_pos_tags_dict, orient="index", columns=["Frequency"])

mistakes_df = mistakes_df.reset_index()
mistakes_df.columns = ["Modal Verb","Frequency"]

mistakes_df.to_excel(output_dir / "modal_verbs_lemmas_POS_tags_mistakes.xlsx", index=False)

