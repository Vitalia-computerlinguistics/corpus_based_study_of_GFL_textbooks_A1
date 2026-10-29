import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ast
import os
from adjustText import adjust_text


input_table_verbs = "/Masterarbeit/Projekt_Masterarbeit/evaluation_tables/duo_verbs_combined_complete.xlsx"
duo_verbs_df = pd.read_excel(input_table_verbs)



def parse_dict(cell):
    """This function recognizes dictionary patterns in a cell of string-type and outputs dictionary"""

    if isinstance(cell, dict):
        return cell
    try:
        return ast.literal_eval(cell)
    except:
        return {}

# calculate entropy
# https://www.geeksforgeeks.org/data-science/how-to-calculate-entropy-in-decision-tree/

def entropy(counts):

    """This function gets a list of frequencies as an input and outputs Shannon-Entropie value for
    a verb based on these frequencies"""

    total = sum(counts)
    if total == 0:
        return 0

    # calculate probabilities
    probs = []
    for count in counts:
        if count > 0:
            probs.append(count / total)

    # calculate entropy
    entropy_value = 0
    for prob in probs:
        entropy_value += -prob * np.log(prob)

    return entropy_value

# calculate dispersion

results = []

for i, row in duo_verbs_df.iterrows():
    lemma = str(row.get("Lemma", "")).strip()
    freq = row.get("Frequency", 0)

    phase_dict = parse_dict(row.get("Phase", {}))
    counts = list(phase_dict.values())

    results.append({
        "Lemma": lemma,
        "Frequency": freq,
        "n_phases": len(phase_dict),
        "entropy": entropy(counts)})

disp_result_df = pd.DataFrame(results)

# remove wrong annotated toks, that are not verb lemmas
disp_result_df = disp_result_df[disp_result_df["Lemma"].str.strip() != ""]
disp_result_df = disp_result_df[disp_result_df["Lemma"].str.strip() != "hallo"]
disp_result_df = disp_result_df[disp_result_df["Lemma"].str.strip() != "oh"]
disp_result_df = disp_result_df[disp_result_df["Lemma"].str.strip() != "besuch"]
disp_result_df = disp_result_df[disp_result_df["Lemma"].str.strip() != "mein"]


# calculate log of frequency
disp_result_df["log_freq"] = np.log1p(disp_result_df["Frequency"])

# create scatter plot
# link: https://matplotlib.org/stable/gallery/shapes_and_collections/scatter.html

fig, ax = plt.subplots(figsize=(12, 8))

ax.scatter(disp_result_df["log_freq"], disp_result_df["entropy"], s=disp_result_df["n_phases"] * 5,alpha=0.6)

ax.set_xlabel("log(Frequency)")
ax.set_ylabel("Entropy (Dispersion over Phases)")
ax.set_title("Verb Dispersion across Phases")
ax.grid(True)

# only verbs, that occur in more than 10 phases get labels on the plot

texts = []

label_df = disp_result_df[disp_result_df["n_phases"] >= 10]

for i, row in label_df.iterrows():
    if row["Lemma"]: texts.append(ax.text(row["log_freq"], row["entropy"], row["Lemma"], fontsize=6, alpha=0.85))

# adjust text, so that there is no overlap between verb lemmas on the plot
# link: https://adjusttext.readthedocs.io/en/latest/Examples.html

adjust_text(texts, expand_points=(1.2, 1.4), expand_text=(1.2, 1.4), force_text=0.6, force_points=0.4,
            lim=200, ensure_inside_axes=True, arrowprops=dict(arrowstyle="-", lw=0.3, alpha=0.5))


ax.set_xlim(left=0)
ax.set_ylim(bottom=0)

plt.tight_layout()

# save plot

output_plot = "/Masterarbeit/Projekt_Masterarbeit/evaluation_tables/duo_verbs_scatter_labels_filtered.png"

plt.savefig(output_plot, dpi=300)
plt.close()

# safe dataframe with entropy values
output_file = input_table_verbs.replace(".xlsx", "_dispersion_results.xlsx")
disp_result_df.to_excel(output_file, index=False)
