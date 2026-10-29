from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np



source_dir = Path("/Masterarbeit/Manual_analysis_transcripts")

# paths for outputs of pos distribution analysis
output_file = "/Masterarbeit/Plots_POS_distribution/POS_distribution_stacked_corpora.png"
table_file = "/Masterarbeit/Plots_POS_distribution/POS_distribution_table.xlsx"


no_words_pos_tags = {"#/S", "#S", "$(", "XY"}

# minimum percentage for individual category, smaller values are presented as other
minimum_percentage = 1


labels_for_legend = {"KanDel": "Learner Corpus (KanDeL)", "all_transcripts": "Textbook transcripts",
    "Pfeffer": "Native Speakers (Pfeffer)"}

# save files for evaluation in a dict
files = {}

for file in source_dir.iterdir():

    if "KanDel" in file.stem:
        files["KanDel"] = file

    elif "all_transcripts" in file.stem:
        files["all_transcripts"] = file

    elif "Pfeffer" in file.stem:
        files["Pfeffer"] = file


# count absolute numbers of pos-tags
freq_dict = {}

for corpus, file in files.items():

    transcript_df = pd.read_excel(file)

    # filter pos-tags
    transcript_df = transcript_df[~transcript_df["POS-Tag"].isin(no_words_pos_tags)]

    freqs = transcript_df["POS-Tag"].value_counts()

    freq_dict[corpus] = freqs


# save absolute frequencies in a dataframe
freq_df = pd.DataFrame(freq_dict).fillna(0).astype(int)

# calculate percentages

# divide row by the sum of column values and multiply by 100
percent_df = freq_df.div(freq_df.sum(axis=0), axis=1) * 100

# minimum value in at least one corpus
minimum_value_condition = percent_df.max(axis=1) >= minimum_percentage

# dataframe with higher percentage pos-tags
high_percentage_df = percent_df[minimum_value_condition].copy()

# dataframe with low percentage pos-tags
low_percentage_df = percent_df[~minimum_value_condition].copy()

high_perc_freq = freq_df.loc[high_percentage_df.index].copy()
low_perc_freq = freq_df.loc[low_percentage_df.index].copy()

if not low_percentage_df.empty:

    other_label = f"Other (<{minimum_percentage}%)"

    high_percentage_df.loc[other_label] = low_percentage_df.sum()
    high_perc_freq.loc[other_label] = low_perc_freq.sum()


# sum of pos-tags in all corpora
high_percentage_df["total"] = high_percentage_df.sum(axis=1)
# sort df by frequencies
high_percentage_df = high_percentage_df.sort_values("total", ascending=False)
high_percentage_df = high_percentage_df.drop(columns="total")

high_perc_freq = high_perc_freq.loc[high_percentage_df.index]

# add percentages of "other" pos-tags
other_label = f"Other (<{minimum_percentage}%)"

if other_label in high_percentage_df.index:

    percent_row = high_percentage_df.loc[[other_label]]
    freq_row = high_perc_freq.loc[[other_label]]

    high_percentage_df = high_percentage_df.drop(other_label)
    high_perc_freq = high_perc_freq.drop(other_label)

    high_percentage_df = pd.concat([high_percentage_df, percent_row])
    high_perc_freq = pd.concat([high_perc_freq, freq_row])


high_percentage_df = high_percentage_df.round(2)


combined_table = pd.DataFrame(index=high_percentage_df.index)

for corpus in high_percentage_df.columns:
    # save absolute numbers and percentages for every corpus
    combined_table[corpus] = (high_percentage_df[corpus].astype(str) + " % (" + high_perc_freq[corpus].astype(str)+ ")")

# write dataframe objects into excel sheets
# link: https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html

with pd.ExcelWriter(table_file) as writer:

    high_percentage_df.to_excel(writer, sheet_name="Percent")

    high_perc_freq.to_excel(writer, sheet_name="Absolute")

    combined_table.to_excel(writer, sheet_name="Combined")


# matplotlib, create stacked plot
# link: https://matplotlib.org/stable/gallery/lines_bars_and_markers/bar_stacked.html

fig, ax = plt.subplots(figsize=(12, 6))

tags = high_percentage_df.index
corpora = high_percentage_df.columns

# 10 colours colormap
colors = plt.cm.tab10.colors


corpus_colors = {}
for i, corpus in enumerate(corpora):
    corpus_colors[corpus] = colors[i]

x = np.arange(len(tags))
bar_width = 0.6

legend_added = set()

for i, tag in enumerate(tags):

    # start value for stacked bars
    bottom = 0

    for corpus in corpora:

        value = high_percentage_df.loc[tag, corpus]

        if corpus not in legend_added:

            label = labels_for_legend.get(corpus, corpus)

            legend_added.add(corpus)

        else:

            label = None

        ax.bar(x[i], value, width=bar_width, bottom=bottom, color=corpus_colors[corpus], label=label)

        bottom += value


# labels on the plot

ax.set_ylabel("Percentage (%)")

ax.set_title("POS-Tag Distribution across Corpora")

ax.set_xticks(x)

ax.set_xticklabels(tags, rotation=45, ha="right")

ax.set_ylim(0, 60)

ax.legend(title="Corpora", bbox_to_anchor=(1.02, 1), loc="upper left")

plt.tight_layout()

plt.savefig(output_file, dpi=300, bbox_inches="tight")

plt.close()
