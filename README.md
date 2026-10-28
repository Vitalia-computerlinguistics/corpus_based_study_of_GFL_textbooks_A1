# corpus_based_study_of_GFL_textbooks_A1
# Textbook vs. Real-Life German: A Corpus-Based Study of Linguistic Features in A1 Learning Materials with a Focus on Verb Use

Textbooks and learning materials serve as one of the main references when learning
a new language, especially at lower levels. 
The goal of this project is to ascertain whether the language presented in
German textbooks differs from native speaker (NS) expressions and, if so, to
characterize these differences using feature values. In addition, I plan to compare
textbook language and learner language in order to analyse the influence that learning
materials have on students’ language. Furthermore, part of the current study focuses
on verb use in NS, textbook and learner corpora, as well as on the introduction of new
verbs in textbooks.
There are four main tasks to be completed for the purposes of the present study, along
with corresponding methods:

1. To compare textbook dialogue transcripts with real-life language data and
learner corpus in order to identify differences between NS language, learner
language, and textbook language. Methods: analysis of lemma frequency lists,
most frequent POS-tag trigrams and comparison of feature values such as
mean word and sentence length, type-token ratio, readability, proportion of
content words, and concreteness

3. To evaluate the Stanza Dependency Parser: create an evaluation set consisting
of 50 sentences with verb dependents based on NS, textbook, and learner data;
manually annotate verb dependents with obj, obl:agent, obl:arg, and obl tags;
and compare manually annotated gold-standard tags with automatically
assigned Stanza dependency tags

5. To analyse the teaching of verbs in textbooks with regard to complexity,
reliability, and salience. Methods: comparison of feature values such as mean
verb length, adverbs-to-verbs ratio, verb-dependents-to-verbs ratio,
percentages of syntactic tags (obj, obl:agent, obl:arg, obl), verb positions in
sentences, mean number of verbs per sentence, percentage of auxiliary verbs,
and percentage of unattached auxiliary verbs

6. To analyse the distribution of verbs across structural entities in the Deutsch-Uni
Online corpus (A1 level): calculate frequencies of verb lemmas across structural
entities, measure entropy for each verb based on these frequencies and
analyse the distribution
The following section discusses each feature in more detail and substantiates it with
reference to existing research.


# Corpora
The Kansas Developmental Learner corpus: https://www.linguistik.huberlin.de/en/institut-en/professuren-en/korpuslinguistik/research/kandel

Pfeffer-Korpus German colloquial languages: https://agd.ids-mannheim.de/PF--
_extern.shtml

# Textbooks transcripts:
Akademie Deutsch A1+: Intensivlehrwerk Band 1. Transkriptionen. (2020). Hueber
Verlag

Deutsch-Uni Online A1.1-A1.2: https://www.deutsch-uni.com/de/

Linie 1 A1.1: Transkriptionen. Ernst Klett Verlag, Stuttgart

Linie 1 A1.2: Transkriptionen. (2017). Ernst Klett Verlag, Stuttgart
59

Menschen A1: Intensivtrainer. Transkriptionen der Hörtexte. Hueber Verlag

Netzwerk neu A1: Transkriptionen zum Kurs- und Übungsbuch. (2019). Ernst Klett
Verlag, Stuttgart

Starten wir! A1: Kursbuch. Transkriptionen. (2022). Hueber Verlag

# This project consists of five main parts:

Preprocessing of data: files 1 to 5

Analysis of linguistic features of three corpora: textbook transcripts (TB), native speaker corpus (NS), and learner corpus (LR): files 5–8
Evaluation of the Stanza Dependency Parser in terms of verb dependents with obj, obl:agent, obl:arg, and obl tags. Automatically annotated data are compared with a manually annotated gold standard created in the INCEpTION tool: files 9–12
Analysis of linguistic features of the three corpora with a focus on verb use: files 13 to 14
Analysis of verb distribution in Deutsch-Uni online learning materials: files 2, 15

Project files:
1_convert_pdf_materials_miner.py
2_read_and_evaluate_duo_data.py
3_read_transcripts_Pfeffer_corpus.py
4_filter_textbook_transcripts.py
5_comparison_textbooks_corpus_real_life_language.py
6_manual_analysis_transxripts.py
7_general_features.py
8_pos_tags_plots.py
9_import_in_inception.py
10_evaluation_set_analysis.py
11_save_annotation_results.py
12_annotation_evaluation.py
13_modal_verbs.py
14_verb_features.py
15_verbs_dispersion.py

