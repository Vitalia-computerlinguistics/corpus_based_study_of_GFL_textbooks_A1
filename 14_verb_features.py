from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, f_oneway


source_dir = Path("/Masterarbeit/Manual_analysis_transcripts")

chunk_size = 1000

# save paths for tables with results
output_features = "/Masterarbeit/Verb_chunk_features.xlsx"
output_chunk_summary = "/Masterarbeit/Verb_general_features_chunks.xlsx"
output_ttest = "/Masterarbeit/Verb_TTest_chunks.xlsx"
output_anova = "/Masterarbeit/Verb_ANOVA_textbooks.xlsx"
output_corpus_table = "/Masterarbeit/Verb_corpus_table.xlsx"


tb_pattern = "akademie|linie|netzwerk|starten|intensivtrainer|duo_dialogues"


verbs_tags = ['VAFIN','VMFIN','VAPP','VMINF','VAINF', 'VVIZU','VVIMP','VVPP','VVINF','VVFIN', 'VAIMP','VMPP']

aux_tags = ['VAFIN','VMFIN','VAPP','VMINF','VAINF','VAIMP']
aux_dep_tags_unattached = ["root","cop"]

adverb_tags = ["ADV","PAV","PWAV"]


chunk_features = []


def safe_div(a,b):

    """This function gets two variables as input. If divisor is higher than 0, it outputs
    division result, if not, NaN-value"""

    if b > 0:
        return a/b
    else:
        return np.nan

def cohens_d(x,y):

    """This function gets observations of two corpora for one feature and
        and returns rounded Cohen's d (effect size) between two groups"""

    # get sample sizes of two corpora
    nx, ny = len(x), len(y)

    # calculate pooled standard deviation and Cohen's d
    # link: https://www.formulas.today/formulas/cohens-d-and-t-tests/
    pooled = np.sqrt(((nx-1)*np.var(x,ddof=1)+(ny-1)*np.var(y,ddof=1))/(nx+ny-2))
    return (np.mean(x)-np.mean(y))/pooled

def format_p_value(p):

    """This function gets p-value as an input and outputs "< .001" for values, which are smaller than
    this number, and the value rounded to 3 decimal places, for values, that are equal or higher than
    this number"""

    if p < 0.001:
        return "< .001"
    else:
        return round(p,3)

def interpret_eta(p, eta):

    """This function gets p and eta squired values as input and evaluates significance
    and effect size as output"""

    if p < 0.05:
        interpretation = "significant"
    else:
        interpretation = "not significant"


    if eta < 0.01:
        effect_size_interpretation = "very small"
    elif eta < 0.06:
        effect_size_interpretation = "small"
    elif eta < 0.14:
        effect_size_interpretation = "medium"
    else:
        effect_size_interpretation = "large"

    return f"{interpretation}, {effect_size_interpretation} effect"



def calculate_chunk_features(file_name, chunk_id, df_chunk):

    """This function gets name of the transcript, segment id and dataframe with rows from manual
    analysis table associated with the current chunk as input and outputs dictionary with features for
    the segment"""

    # count verbs
    num_verbs = df_chunk["POS-Tag"].isin(verbs_tags).sum()
    if num_verbs == 0:
        return None

    # count adverbs
    num_adv = df_chunk["POS-Tag"].isin(adverb_tags).sum()
    # count auxiliary verbs
    num_aux = df_chunk["POS-Tag"].isin(aux_tags).sum()
    # count verb dependents
    num_dependents = (df_chunk["Verb Dependent"]==True).sum()

    # formulate verb dependent condition
    dependents_condition = df_chunk["Verb Dependent"] == True

    # count direct objs and conjuncts of these tags
    num_direct_obj = ((dependents_condition) & ((df_chunk["Dependency"] == "obj") | (df_chunk["Conj Head"] == "obj"))).sum()
    # count obl:agent tags and conjuncts of these tags
    num_passive_agent = ((dependents_condition) & ((df_chunk["Dependency"]=="obl:agent") | (df_chunk["Conj Head"]=="obl:agent"))).sum()
    # count obl:arg tags and conjuncts of these tags
    num_obl_arg = ((dependents_condition) & ((df_chunk["Dependency"]=="obl:arg") | (df_chunk["Conj Head"]=="obl:arg"))).sum()
    # count obl tags and conjuncts of these tags
    num_prep_obl = ((dependents_condition) & ((df_chunk["Dependency"]=="obl") | (df_chunk["Conj Head"]=="obl"))).sum()

    # count all target verb dependents
    dependents_total = num_direct_obj + num_passive_agent + num_obl_arg + num_prep_obl

    # count mean verb length
    mean_verb_length = df_chunk.loc[df_chunk["POS-Tag"].isin(verbs_tags), "Token"].str.len().mean()

    # count sentences with verbs on different positions
    sentence_pos = []
    num_initial = num_final=num_initial_final=num_other=0
    empty_sents = 0
    num_sent_without_verbs = 0
    num_sents = (df_chunk["POS-Tag"] == "#S").sum()

    for i, row in df_chunk.iterrows():

        token = row["Token"]
        pos = row["POS-Tag"]

        # initialize sentence
        if token == "#S":
            sentence_pos=[]

        # finish sentence
        elif token=="#/S":


            if sentence_pos and len(sentence_pos)>1:

                # if verb in sentence
                if any(pos_tag in verbs_tags for pos_tag in sentence_pos):

                    # define initial and final verb positions
                    initial = sentence_pos[0] in verbs_tags
                    final = sentence_pos[-1] in verbs_tags

                    # increase frequency of verb position
                    if initial and final:
                        num_initial_final+=1
                    elif initial:
                        num_initial+=1
                    elif final:
                        num_final+=1
                    else:
                        num_other+=1
                # count sentences without verbs
                else:
                    num_sent_without_verbs+=1
            else:
                empty_sents += 1
        else:
            # append pos-tag in sentence list
            sentence_pos.append(pos)

    num_sents = num_sents - empty_sents
    num_sent_with_verbs = num_sents - num_sent_without_verbs

    # return None, if the number of verbs in chunks is lower 3
    if num_sent_with_verbs < 3:
        return None


    #print(num_dependents, dependents_total, dependents_total - num_dependents)

    # calculate chunk features
    return {
        "Corpus": file_name,
        "chunk_id": chunk_id,

        "Mean verb length": mean_verb_length,
        "Adverbs to Verbs Ratio": safe_div(num_adv,num_verbs),
        "Verb Dependents to Verbs Ratio": safe_div(dependents_total,num_verbs),

        "Direct objects %": safe_div(num_direct_obj,num_dependents)*100,
        "Passive agent %": safe_div(num_passive_agent,num_dependents)*100,
        "Obl:arg tags %": safe_div(num_obl_arg,num_dependents)*100,
        "Obl tags %": safe_div(num_prep_obl,num_dependents)*100,

        "Verb initial p. %": safe_div(num_initial,num_sent_with_verbs)*100,
        "Verb final  p. %": safe_div(num_final,num_sent_with_verbs)*100,
        "Verb initial+final p. %": safe_div(num_initial_final,num_sent_with_verbs)*100,
        "Verb other p. %": safe_div(num_other,num_sent_with_verbs)*100,

        "Mean verbs per sentence": safe_div(num_verbs,num_sent_with_verbs),

        "Aux verbs %": safe_div(num_aux,num_verbs)*100,
        "Unattached aux %": safe_div(((df_chunk["Dependency"].isin(aux_dep_tags_unattached)) &
             (df_chunk["POS-Tag"].isin(aux_tags))).sum(), num_aux)*100}



for file in sorted(source_dir.iterdir()):

    transcript_df = pd.read_excel(file)

    chunk_id = 0
    chunk_rows = []
    token_counter = 0

    for i, row in transcript_df.iterrows():

        chunk_rows.append(row)
        token_counter += 1

        # if chunk includes more than 1000 tokens and the current sentence is finished
        if token_counter >= chunk_size and row["Token"]=="#/S":

            # next chunk id
            chunk_id += 1
            # create dataframe from chunk rows
            df_chunk = pd.DataFrame(chunk_rows)

            # calculate chunk features
            feats = calculate_chunk_features(file.name, chunk_id, df_chunk)
            if feats:
                chunk_features.append(feats)

            chunk_rows = []
            token_counter = 0

    # save and analyse last chunk
    if chunk_rows:
        chunk_id += 1
        df_chunk = pd.DataFrame(chunk_rows)
        feats = calculate_chunk_features(file.name, chunk_id, df_chunk)
        if feats:
            chunk_features.append(feats)



# save chunks in a dataframe
chunk_df = pd.DataFrame(chunk_features)
chunk_df.to_excel(output_features, index=False)

feature_variables = list()

for chunk_variable in chunk_df.columns:
    if chunk_variable not in ["Corpus", "chunk_id"]:
        feature_variables.append(chunk_variable)

# corpus features based on chunks
chunk_summary_df = (chunk_df.groupby("Corpus")[feature_variables].mean().reset_index())

# remove data based on merged file with all textbook transcripts
chunk_summary_df = chunk_summary_df[~chunk_summary_df["Corpus"].str.contains("all_transcripts", case=False)]

# calculate data for all textbooks based on chunks for every individual textbook
tb_chunks = chunk_df[chunk_df["Corpus"].str.contains(tb_pattern, case=False)]


tb_mean_row = tb_chunks[feature_variables].mean()
tb_mean_row["Corpus"] = "TB_all"



chunk_summary_df = pd.concat([chunk_summary_df, pd.DataFrame([tb_mean_row])], ignore_index=True)

chunk_summary_df[feature_variables] = chunk_summary_df[feature_variables].round(2)

# save data for whole corpus based on chunks
chunk_summary_df.to_excel(output_chunk_summary,index=False)


# corpus-level analysis
corpus_features = []

for file in sorted(source_dir.iterdir()):

    if "all_transcripts" in file.name.lower():
        continue

    transcript_df = pd.read_excel(file)

    # calculate features for the whole transcript
    feats_transcript = calculate_chunk_features(file.name, 0, transcript_df)

    if feats_transcript:
        corpus_features.append(feats_transcript)

# df of corpus-level features
corpus_df = pd.DataFrame(corpus_features)

# find textbook data
tb_df = corpus_df[corpus_df["Corpus"].str.contains(tb_pattern, case=False)]

# calculate mean values for textbooks
tb_mean = tb_df[feature_variables].mean()
tb_mean["Corpus"] = "TB_all"

corpus_df = pd.concat([corpus_df, pd.DataFrame([tb_mean])], ignore_index=True)
corpus_df = corpus_df.drop(columns=["chunk_id"], errors="ignore")


cols_corp = ["Corpus"]

for corp_column in corpus_df.columns:
    if corp_column != "Corpus":
        cols_corp.append(corp_column)


corpus_df = corpus_df[cols_corp]


corpus_df[feature_variables] = corpus_df[feature_variables].round(2)

corpus_df.to_excel(output_corpus_table, index=False)


# define chunks for 3 studied corpora
textbooks = chunk_df[chunk_df["Corpus"].str.contains(tb_pattern, case=False)]
ns = chunk_df[chunk_df["Corpus"].str.contains("pfeffer", case=False)]
learners = chunk_df[chunk_df["Corpus"].str.contains("kandel", case=False)]


# Pearson correlation analysis

# remove mean data of textbooks, (individual textbook values are still existent)
chunk_corr = chunk_summary_df[~chunk_summary_df["Corpus"].str.contains("TB_all", case=False)]

corpus_corr = corpus_df[~corpus_df["Corpus"].str.contains("TB_all", case=False)]

# merge chunks and corpus-level features
merged_df = pd.merge(chunk_corr, corpus_corr, on="Corpus", suffixes=("_chunk", "_corpus"))


# correlation featurewise

correlations = []

# calculate correlation for every feature
for feature in feature_variables:

    # calculate Pearson correlation coefficient
    r = np.corrcoef(chunk_corr[feature], corpus_corr[feature])[0,1]

    correlations.append(r)

    print(f"{feature}: r = {round(r, 3)} (n={len(chunk_corr)})")


# calculate overall correlation
all_chunk = []
all_corpus = []

for feature in feature_variables:
    all_chunk.extend(chunk_corr[feature])
    all_corpus.extend(corpus_corr[feature])

# Correlation across all features and observations
overall_r = np.corrcoef(all_chunk, all_corpus)[0,1]
print(f"Correlation across all feats: r = {round(overall_r,3)} (n={len(all_chunk)})")


# extract TB_all rows from both tables
tb_chunk_row = chunk_summary_df[chunk_summary_df["Corpus"] == "TB_all"].iloc[0]
tb_corpus_row = corpus_df[corpus_df["Corpus"] == "TB_all"].iloc[0]

chunk_vals = []
corpus_vals = []
diff_results = []

for feature in feature_variables:

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


# perform t-test

results=[]

for var in feature_variables:

    ns_vals = ns[var].dropna()
    tb_vals = textbooks[var].dropna()
    lr_vals = learners[var].dropna()

    row = {"Variable": var, "NS mean": round(ns_vals.mean(),2), "TB mean": round(tb_vals.mean(),2), "LR mean": round(lr_vals.mean(),2)}

    # calculate t, p values and Cohen's d for each pair
    # equal_var=False - parameter for Welch’s t-test
    # link: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html

    t, p=ttest_ind(ns_vals, tb_vals,equal_var=False)
    row["NS vs TB p"]=p
    row["NS vs TB d"] = round(cohens_d(ns_vals,tb_vals),2)


    t, p=ttest_ind(tb_vals, lr_vals,equal_var=False)
    row["TB vs LR p"] = p
    row["TB vs LR d"] = round(cohens_d(tb_vals,lr_vals),2)


    t, p=ttest_ind(ns_vals, lr_vals,equal_var=False)
    row["NS vs LR p"] = p
    row["NS vs LR d"] = round(cohens_d(ns_vals,lr_vals),2)

    results.append(row)

# save t-test results
pd.DataFrame(results).to_excel(output_ttest,index=False)


# perform ANOVA

anova_results=[]

# find name of each textbook
textbook_names=textbooks["Corpus"].unique()


for var in feature_variables:

    groups=[]
    sizes=[]

    for name in textbook_names:
        # extract feature values for the textbook
        vals = textbooks[textbooks["Corpus"]==name][var].dropna()

        if len(vals)>1 and np.var(vals)>0:
            groups.append(vals)
            sizes.append(len(vals))

    if len(groups)>1:

        # perform one-sided ANOVA
        # link: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html
        # using of * to present elements individually as arguments

        F,p = f_oneway(*groups)

        # calculate degrees of freedom between and within
        df_between=len(groups)-1
        N=sum(sizes)
        df_within=N-len(groups)

        # calculate eta squared, effect size
        # link: https://search.r-project.org/CRAN/refmans/MOTE/html/eta.F.html
        eta_sq=(F*df_between)/((F*df_between)+df_within)

        # save anova results
        anova_results.append({
            "Variable":var,
            "F":round(F,2),
            "P value":format_p_value(p),
            "eta_squared":round(eta_sq,3),
            "interpretation":interpret_eta(p,eta_sq)
        })

pd.DataFrame(anova_results).to_excel(output_anova,index=False)

