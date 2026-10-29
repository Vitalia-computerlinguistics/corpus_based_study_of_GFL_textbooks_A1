import pandas as pd
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error
import fasttext
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from scipy.stats import ttest_ind, f_oneway


# load concreteness lexicon
concreteness_values_df = pd.read_csv("/Masterarbeit/Concreteness/MergedConcreteness.csv",
                                     sep=';', header=None)

concreteness_values_df.columns = ["Lemma", "Concreteness Value"]
concreteness_values_df["Lemma"] = concreteness_values_df["Lemma"].str.lower()

# create concreteness value dictionary
concreteness_dict = dict(zip(concreteness_values_df["Lemma"], concreteness_values_df["Concreteness Value"]))


# load pretrained fasttext 300 dimensions word embedding model for german
# trained on Common Crawl and Wikipedia
# link: https://fasttext.cc/docs/en/crawl-vectors
ft_model = fasttext.load_model("/Masterarbeit/Embeddings/cc.de.300.bin")

# train regression model

lemmas = concreteness_values_df["Lemma"].values

# create a word embedding vector for each lemma
lemma_embeddings = list()

for lemma in lemmas:
    lemma_embeddings.append(ft_model.get_word_vector(lemma))

X = np.array(lemma_embeddings)
y = concreteness_values_df["Concreteness Value"].values

# split data in train (80%) and test (20%) sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# train a regression model
# link: https://www.udacity.com/blog/2025/12/scikit-learn-tutorial-build-powerful-machine-learning-models-in-python.html
# create regression model and fit it with data
reg_model = Pipeline([("scaler", StandardScaler()),("ridge", Ridge(alpha=1.0))])
reg_model.fit(X_train, y_train)


def calculate_concreteness(lemma):

    """This function gets lemma as an input. If the lemma exists in the concreteness lexicon,
    the function outputs the lexicon value, if there is no value in the lexicon, the function
    outputs concreteness value predicted by the regression model"""

    lemma = lemma.lower()
    if lemma in concreteness_dict:
        return concreteness_dict[lemma]

    vec = ft_model.get_word_vector(lemma)
    return reg_model.predict(vec.reshape(1, -1))[0]


def calculate_mattr(tokens, window_size=100):
    """This function gets a list of tokens as an input. If this list is shorter than window_size,
    the function outputs None, when the list is longer, the function outputs mattr value of the list"""

    if len(tokens) < window_size:
        return None
    ttrs = []
    for i in range(len(tokens) - window_size + 1):
        window = tokens[i:i + window_size]
        ttrs.append(len(set(window)) / window_size)
    return np.mean(ttrs)



source_dir = Path("/Masterarbeit/Manual_analysis_transcripts")

chunk_size = 1000

content_words_tags = ['NE','ADJA','VVIZU','VVIMP','ADJD','VVPP','NN','VVINF','ADV','VVFIN']

tags_for_concreteness = ['ADJA','VVIZU','VVIMP','ADJD', 'VVPP','NN','VVINF','VVFIN']


chunk_features = []


def finalize_chunk(file_name, chunk_id, chunk_tokens, chunk_lemmas, chunk_sentences, chunk_letters,
                   chunk_content_words, chunk_concreteness, chunk_concreteness_known):

    """This function gets transcript name and chunk values as an input and outputs mean sentence and word
    length, readability, proportion of content words, mattr for tokens and lemmas, concreteness for all
    lemmas and only lemmas found in the lexicon features for the chunk as an output. If chunk is empty,
    the function outputs None"""


    if len(chunk_tokens) == 0:
        return None

    sent_len_list = list()

    for sent in chunk_sentences:
        sent_len_list.append(len(sent))

    mean_sent_len = np.mean(sent_len_list)
    mean_word_len = chunk_letters / len(chunk_tokens)

    readability = 164.935 - 18.792 * mean_word_len - 1.916 * mean_sent_len
    prop_content_words = chunk_content_words / len(chunk_tokens)

    if chunk_concreteness:
        chunk_concr = np.mean(chunk_concreteness)

    if chunk_concreteness_known:
        chunk_concr_known = np.mean(chunk_concreteness_known)

    return {"Corpus": file_name, "chunk_id": chunk_id, "n_words": len(chunk_tokens), "mean_sentence_length": mean_sent_len,
            "mean_word_length": mean_word_len, "readability": readability, "prop_content_words": prop_content_words,
            "mattr_tokens": calculate_mattr(chunk_tokens), "mattr_lemmas": calculate_mattr(chunk_lemmas),
            "concreteness": chunk_concr, "concreteness_known": chunk_concr_known}



for file in sorted(source_dir.iterdir()):

    manual_transcript_df = pd.read_excel(file)

    # create values
    chunk_id = 0
    chunk_tokens = []
    chunk_lemmas = []
    chunk_sentences = []
    chunk_letters = 0
    chunk_content_words = 0
    chunk_concreteness = []
    chunk_concreteness_known = []
    current_sentence = []

    for i, row in manual_transcript_df.iterrows():

        token = str(row["Token"])
        lemma = str(row["Lemma"]).lower()

        # initialize sentence
        if token == "#S":
            current_sentence = []
            continue

        # finish sentence
        elif token == "#/S":

            chunk_sentences.append(current_sentence)

            # if maximum length achived
            if len(chunk_tokens) >= chunk_size:

                # new chunk id
                chunk_id += 1

                # calculate chunk features
                chunk_data = finalize_chunk(file.name, chunk_id, chunk_tokens, chunk_lemmas, chunk_sentences,
                                            chunk_letters, chunk_content_words, chunk_concreteness, chunk_concreteness_known)

                if chunk_data:
                    chunk_features.append(chunk_data)

                # reset chunk values
                chunk_tokens, chunk_lemmas, chunk_sentences = [], [], []
                chunk_letters = 0
                chunk_content_words = 0
                chunk_concreteness, chunk_concreteness_known = [], []

            continue

        # save data in current chunk and in current sentence
        current_sentence.append(token)
        chunk_tokens.append(token)
        chunk_lemmas.append(lemma)
        chunk_letters += len(token)

        if row["POS-Tag"] in content_words_tags:
            chunk_content_words += 1

        if row["POS-Tag"] in tags_for_concreteness:
            concr_val = calculate_concreteness(lemma)
            chunk_concreteness.append(concr_val)
            if lemma in concreteness_dict:
                chunk_concreteness_known.append(concreteness_dict[lemma])

    # analyze last chunk
    if len(chunk_tokens) > 0:
        chunk_id += 1
        chunk_data = finalize_chunk(file.name, chunk_id, chunk_tokens, chunk_lemmas, chunk_sentences,
                                    chunk_letters, chunk_content_words, chunk_concreteness, chunk_concreteness_known)
        if chunk_data:
            chunk_features.append(chunk_data)


# save chunk df with features of chunks for all corpora
chunk_df = pd.DataFrame(chunk_features)
chunk_df.to_excel("/Masterarbeit/Chunk_features.xlsx", index=False)


# features names
feature_names = ["mean_sentence_length", "mean_word_length", "readability", "prop_content_words", "mattr_tokens", "mattr_lemmas",
    "concreteness","concreteness_known"]

# formulate pattern to filter textbooks
tb_pattern = "akademie|linie|netzwerk|starten|intensivtrainer|duo_dialogues"


# corpus features based on chunks
chunk_summary_df = (chunk_df.groupby("Corpus")[feature_names].mean().reset_index())

# remove data based on merged file with all textbook transcripts
chunk_summary_df = chunk_summary_df[~chunk_summary_df["Corpus"].str.contains("all_transcripts", case=False)]

# calculate data for all textbooks based on chunks for every individual textbook
tb_chunks = chunk_df[chunk_df["Corpus"].str.contains(tb_pattern, case=False)]

tb_mean_row_ch = tb_chunks[feature_names].mean()
tb_mean_row_ch["Corpus"] = "TB_all"

chunk_summary_df = pd.concat([chunk_summary_df, pd.DataFrame([tb_mean_row_ch])], ignore_index=True)

chunk_summary_df[feature_names] = chunk_summary_df[feature_names].round(2)

# save data for whole corpus based on chunks
chunk_summary_df.to_excel("/Masterarbeit/General_features_chunks.xlsx", index=False)


# corpus-level analysis

corpus_features = []

for file in sorted(source_dir.iterdir()):

    if "all_transcripts" in file.name.lower():
        continue

    transcript_df = pd.read_excel(file)

    tokens = []
    lemmas = []
    sentences = []
    current_sentence = []
    letters = 0
    content_words = 0
    concreteness_vals = []
    concreteness_known_vals = []

    # calculate the number of known and unknow lemmas for concreteness
    lemmas_in_lex = 0
    lemmas_not_in_lex = 0

    for i, row in transcript_df.iterrows():

        token = str(row["Token"])
        lemma = str(row["Lemma"]).lower()

        # initialize sentence
        if token == "#S":
            current_sentence = []
            continue

        # finish sentence
        elif token == "#/S":
            sentences.append(current_sentence)
            continue

        # save values for corpus-level feature calculation
        current_sentence.append(token)
        tokens.append(token)
        lemmas.append(lemma)
        letters += len(token)

        if row["POS-Tag"] in content_words_tags:
            content_words += 1

        if row["POS-Tag"] in tags_for_concreteness:

            if lemma in concreteness_dict:
                lemmas_in_lex += 1
            else:
                lemmas_not_in_lex += 1

            concr_val = calculate_concreteness(lemma)
            concreteness_vals.append(concr_val)

            if lemma in concreteness_dict:
                concreteness_known_vals.append(concreteness_dict[lemma])

    # show the number of known and unknown lemmas
    print("Lemmas for concreteness calculation")
    print(f"{file.name}: in_lex={lemmas_in_lex}, not_in_lex={lemmas_not_in_lex}")

    if len(tokens) == 0:
        continue

    # calculate corpus level features

    corpus_sents_list = []
    for sent in sentences:
        corpus_sents_list.append(len(sent))

    mean_sent_len = np.mean(corpus_sents_list)
    mean_word_len = letters / len(tokens)
    readability = 164.935 - 18.792 * mean_word_len - 1.916 * mean_sent_len
    prop_content_words = content_words / len(tokens)

    if concreteness_vals:
        concr = np.mean(concreteness_vals)

    if concreteness_known_vals:
        concr_known = np.mean(concreteness_known_vals)


    corpus_features.append({"Corpus": file.name, "mean_sentence_length": mean_sent_len,
        "mean_word_length": mean_word_len, "readability": readability,
        "prop_content_words": prop_content_words, "mattr_tokens": calculate_mattr(tokens),
        "mattr_lemmas": calculate_mattr(lemmas), "concreteness": concr,
        "concreteness_known": concr_known})


corpus_df = pd.DataFrame(corpus_features)

# calculate corpus based value for all textbooks
tb_df = corpus_df[corpus_df["Corpus"].str.contains(tb_pattern, case=False)]

tb_row = tb_df[feature_names].mean()
tb_row["Corpus"] = "TB_all"

corpus_df = pd.concat([corpus_df,pd.DataFrame([tb_row])],ignore_index=True)

corpus_df[feature_names] = corpus_df[feature_names].round(2)


# save corpus level features in excel table
corpus_df.to_excel("/Masterarbeit/Corpus_level_table.xlsx", index=False)

# calculate correlation between corpus-level and chunk based values

# remove summarized values for all textbooks
chunk_corr = chunk_summary_df[~chunk_summary_df["Corpus"].str.contains("TB_all", case=False)]

corpus_corr = corpus_df[~corpus_df["Corpus"].str.contains("TB_all", case=False)]

# create merged df of chunk based and corpus-level features
# use suffixes, because column names are same
merged_df = pd.merge(chunk_corr, corpus_corr, on="Corpus", suffixes=("_chunk", "_corpus"))


correlations = []

# calculate correlation for every feature
for feature in feature_names:

    # calculate Pearson correlation coefficient
    r = np.corrcoef(chunk_corr[feature], corpus_corr[feature])[0,1]

    correlations.append(r)

    print(f"{feature}: r = {round(r, 3)} (n={len(chunk_corr)})")



# calculate overall correlation
all_chunk = []
all_corpus = []

for feature in feature_names:
    all_chunk.extend(chunk_corr[feature])
    all_corpus.extend(corpus_corr[feature])

# Correlation across all features and observations
overall_r = np.corrcoef(all_chunk, all_corpus)[0,1]
print(f"Correlation across all feats: r = {round(overall_r,3)} (n={len(all_chunk)})")


# correlation for merged tb values

# extract TB_all rows from both tables
tb_chunk_row = chunk_summary_df[chunk_summary_df["Corpus"] == "TB_all"].iloc[0]
tb_corpus_row = corpus_df[corpus_df["Corpus"] == "TB_all"].iloc[0]

chunk_vals = []
corpus_vals = []
diff_results = []

for feature in feature_names:

    chunk_val = tb_chunk_row[feature]
    corpus_val = tb_corpus_row[feature]

    # differences between values
    diff = chunk_val - corpus_val


    chunk_vals.append(chunk_val)
    corpus_vals.append(corpus_val)

    print(f"{feature}: chunk={round(chunk_val, 3)}, corpus={round(corpus_val, 3)}, diff={round(diff, 3)}")

    diff_results.append({"Feature": feature, "Chunk_value": round(chunk_val,3),
                         "Corpus_value": round(corpus_val,3), "Difference": round(diff,3)})

# Correlation across features of merged tb corpus
r = np.corrcoef(chunk_vals, corpus_vals)[0, 1]
print(f"TB corpus correlation across features: r = {round(r, 3)} (n={len(chunk_vals)})")


# perform t-test between 3 studied corpora

def cohens_d(x, y):
    """This function gets observations of two corpora for one feature and
    and returns rounded Cohen's d (effect size) between two groups"""

    x, y = np.array(x.dropna()), np.array(y.dropna())

    # get sample sizes of two corpora
    nx, ny = len(x), len(y)

    # calculate pooled standard deviation and Cohen's d
    # link: https://www.formulas.today/formulas/cohens-d-and-t-tests/
    pooled = np.sqrt(((nx-1)*np.var(x,ddof=1)+(ny-1)*np.var(y,ddof=1))/(nx+ny-2))

    return round((np.mean(x)-np.mean(y))/pooled,2)

# define corpora
textbooks = chunk_df[chunk_df["Corpus"].str.contains(tb_pattern, case=False)]
ns = chunk_df[chunk_df["Corpus"].str.contains("pfeffer", case=False)]
learners = chunk_df[chunk_df["Corpus"].str.contains("kandel", case=False)]

results = []

for feature in feature_names:
    ns_vals = ns[feature].dropna()
    tb_vals = textbooks[feature].dropna()
    lr_vals = learners[feature].dropna()

    row = {"Feature": feature, "NS mean": round(ns_vals.mean(),2), "TB mean": round(tb_vals.mean(),2), "LR mean": round(lr_vals.mean(),2)}

    # calculate t, p values and Cohen's d for each pair
    # equal_var=False - parameter for Welch’s t-test
    # link: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html

    t, p = ttest_ind(ns_vals, tb_vals, equal_var=False)
    row["NS vs TB p"] = p
    row["NS vs TB d"] = cohens_d(ns_vals,tb_vals)


    t,p = ttest_ind(tb_vals, lr_vals, equal_var=False)
    row["TB vs LR p"] = p
    row["TB vs LR d"] = cohens_d(tb_vals,lr_vals)


    t,p = ttest_ind(ns_vals, lr_vals, equal_var=False)
    row["NS vs LR p"] = p
    row["NS vs LR d"] = cohens_d(ns_vals,lr_vals)

    results.append(row)

# save t-test results
pd.DataFrame(results).to_excel("/Masterarbeit/TTest_results.xlsx", index=False)


# perform ANOVA

anova_results = []

# search for textbook chunks
textbook_chunks = chunk_df[chunk_df["Corpus"].str.contains("akademie|linie|netzwerk|starten|intensivtrainer|duo_dialogues", case=False)]

# find name of each textbook
textbook_names = textbook_chunks["Corpus"].unique()

# define number of groups for ANOVA
k = len(textbook_names)


for feature in feature_names:

    groups = []
    group_sizes = []


    for name in textbook_names:

        # extract feature values for the textbook
        tbk_feats_values = textbook_chunks[textbook_chunks["Corpus"] == name][feature].dropna()

        if len(tbk_feats_values) > 1:
            groups.append(tbk_feats_values)
            group_sizes.append(len(tbk_feats_values))

    if len(groups) > 1:

        # perform one-sided ANOVA
        # link: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html
        # using of * to present elements individually as arguments
        F, p = f_oneway(*groups)

        # calculate degrees of freedom between and within
        df_between = len(groups) - 1
        N = sum(group_sizes)
        df_within = N - len(groups)

        # calculate eta squared, effect size
        # link: https://search.r-project.org/CRAN/refmans/MOTE/html/eta.F.html
        eta_sq = (F * df_between) / ((F * df_between) + df_within)

        # interpret anova results for the table
        if p < 0.001:
            p_for_table = "< .001"
        else:
            p_for_table = f"= {round(p, 3)}"

        if p < 0.05:
            interpretation = "significant"
        else:
            interpretation = "not significant"

        if eta_sq < 0.01:
            effect_size_interpretation = "very small"
        elif eta_sq < 0.06:
            effect_size_interpretation = "small"
        elif eta_sq < 0.14:
            effect_size_interpretation = "medium"
        else:
            effect_size_interpretation = "large"

        # save anova results
        anova_results.append({
            "Variable": feature,
            "F": round(F, 2),
            "df_between": df_between,
            "df_within": df_within,
            "p_value": p,
            "p_report": p_for_table,
            "eta_squared": round(eta_sq, 3),
            "interpretation": interpretation,
            "eta_interpretation": effect_size_interpretation})

anova_df = pd.DataFrame(anova_results)

anova_df.to_excel("/Masterarbeit/ANOVA_textbooks_full.xlsx", index=False)
