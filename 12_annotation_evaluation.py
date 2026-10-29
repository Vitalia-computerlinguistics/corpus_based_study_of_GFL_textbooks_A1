import pandas as pd
import ast
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt


def deep_list_to_a_normal_one(deep_list):

    """This function checks if an input is a list and converts a deep list to a flat list,
        if it is the case"""

    flat_list = []

    for sent in deep_list:
        if isinstance(sent, list):
            flat_list.extend(deep_list_to_a_normal_one(sent))
        else:
            flat_list.append(sent)

    return flat_list

# the function to recognize lists in strings:
# https://www.educative.io/answers/what-is-astliteralevalnodeorstring-in-python

def recognise_a_list(string_elem):
    """This function gets a string as an input and outputs a list recognised in this string"""

    try:
        return ast.literal_eval(string_elem)
    except (ValueError, SyntaxError):
        return string_elem


def resolve_conj(dep_list, head_list, index):

    """This function gets list of dependency tags and head positions of a
    sentence and index of the current token as an input and outputs dependency tag of this token or,
    if the current dependency tag is "conj", dependency tag of the head of the conjunct"""

    dep = dep_list[index]
    visited = set()

    # find gouverneur of a conjunct
    # also possible if it is conjunct chain

    while dep == "conj":

        # avoid infinite loop
        if index in visited:
            break

        visited.add(index)

        head = int(head_list[index]) - 1

        if head < 0 or head >= len(dep_list):
            break

        # find first head, that is not a conjunct
        dep = dep_list[head]
        index = head

    return dep


# load data, annotated with inception and stanza
annotation_df = pd.read_excel("/Masterarbeit/inception_export/annotated_data_and_Stanza_excel/all_annotations.xlsx")


verbs_tags = ['VAFIN','VMFIN','VAPP','VMINF','VAINF','VVIZU','VVIMP','VVPP','VVINF','VVFIN','VAIMP','VMPP']

target_deps = ["obj", "iobj", "obl", "obl:arg", "obl:agent"]

labels_for_clas_report = ["obj", "obl", "obl:arg", "obl:agent"]

gold_labels = []
pred_labels = []

gold_heads = []
pred_heads = []

combined_correct = []

error_analysis = []
false_positive_analysis = []

# count true positives, false positives, false negatives and true negatives
TP = 0
FP = 0
FN = 0
TN = 0


for i, row in annotation_df.iterrows():

    tokens = deep_list_to_a_normal_one(recognise_a_list(row["Tokens, Inception"]))

    pos_inception = deep_list_to_a_normal_one(recognise_a_list(row["XPOS Tags, Inception"]))
    dep_inception = deep_list_to_a_normal_one(recognise_a_list(row["Dependency Tags, Inception"]))
    head_inception = deep_list_to_a_normal_one(recognise_a_list(row["Head Position, Inception"]))

    pos_stanza = deep_list_to_a_normal_one(recognise_a_list(row["Stanza XPOS Tags"]))
    dep_stanza = deep_list_to_a_normal_one(recognise_a_list(row["Stanza Dependency Tags"]))
    head_stanza = deep_list_to_a_normal_one(recognise_a_list(row["Stanza Head Position"]))


    for j in range(len(tokens)):

        gold_dep = dep_inception[j]

        # NONE for not target tags, which are not annotated in inception
        if gold_dep == "_":
            gold_dep = "NONE"

        pred_dep = dep_stanza[j]

        if head_inception[j] is None or head_stanza[j] is None:
            continue

        gold_head = int(head_inception[j]) - 1
        pred_head = int(head_stanza[j]) - 1

        # assign dependency tags
        resolved_gold_dep = resolve_conj(dep_inception, head_inception, j)
        resolved_pred_dep = resolve_conj(dep_stanza, head_stanza, j)

        if resolved_gold_dep == "_":
            resolved_gold_dep = "NONE"

        # check if gold tag belongs to target group
        gold_is_target = False
        if resolved_gold_dep in target_deps:
            head = int(head_inception[j]) - 1
            if head >= 0 and pos_inception[head] in verbs_tags:
                gold_is_target = True


        # check if pred tag belongs to target group
        pred_is_target = False
        if resolved_pred_dep in target_deps:
            head = int(head_stanza[j]) - 1
            if head >= 0 and pos_stanza[head] in verbs_tags:
                pred_is_target = True


        # classify predictions
        if gold_is_target and pred_is_target:
            TP += 1
        elif pred_is_target and not gold_is_target:
            FP += 1
        elif gold_is_target and not pred_is_target:
            FN += 1
        else:
            TN += 1


        if pred_is_target and not gold_is_target:

            false_positive_analysis.append({
                "Sentence_id": i + 1,
                "Sentence_text": " ".join(map(str, tokens)),
                "Token": tokens[j],
                "Gold_Dep": resolved_gold_dep,
                "Pred_Dep": resolved_pred_dep})


        # only evaluate labels if gold or pred classified tok as target group
        if not (gold_is_target or pred_is_target):
            continue

        if gold_is_target:
            gold_label = resolved_gold_dep
        else:
            gold_label = "NONE"

        if pred_is_target:
            pred_label = resolved_pred_dep
        else:
            pred_label = "NONE"


        gold_labels.append(gold_label)
        pred_labels.append(pred_label)

        gold_heads.append(head_inception[j])
        pred_heads.append(head_stanza[j])

        # define relations between gold and pred head and label
        head_correct = head_inception[j] == head_stanza[j]
        label_correct = gold_label == pred_label

        # save dictionary with errors
        if head_correct and label_correct:
            combined_correct.append(1)
        else:
            combined_correct.append(0)

            error_analysis.append({
                "Sentence_ID": i + 1,
                "Sentence_text": " ".join(map(str, tokens)),
                "Token": tokens[j],
                "Gold_Dep": gold_label,
                "Pred_Dep": pred_label,
                "Gold_Head": head_inception[j],
                "Pred_Head": head_stanza[j]
            })


print("Evaluated tokens:", len(gold_labels))
print("False positives:", FP)


# calculate evaluation metrics
if (TP + FP) > 0:
    precision = TP / (TP + FP)
else:
    precision = 0

if (TP + FN) > 0:
    recall = TP / (TP + FN)
else:
    recall = 0

if (precision + recall) > 0:
    f1 = (2 * precision * recall) / (precision + recall)
else:
    f1 = 0

accuracy_verb_dep = (TP + TN) / (TP + TN + FP + FN)


print("Evaluation of verb dependent detection")
print("Precision:", round(precision,2))
print("Recall:", round(recall,2))
print("F1:", round(f1,2))
print("Accuracy:", round(accuracy_verb_dep,2))


# unlabelled attachment score: correct detection of heads
uas = accuracy_score(gold_heads, pred_heads)
print("UAS:", round(uas,2))

# labelled attachment score: correct detection of heads and lemmas
las = sum(combined_correct) / len(combined_correct)
print("LAS:", round(las,2))


labels_for_eval = ["NONE"] + labels_for_clas_report


# classification report
# safe classification report in an excel table
report_dict = classification_report(gold_labels, pred_labels, labels=labels_for_eval, output_dict=True, zero_division=0)

report_df = pd.DataFrame(report_dict).transpose()

report_df = report_df.round(2)

report_df.to_excel("/Masterarbeit/inception_export/evaluation_results/dependency_label_classification_report.xlsx")


# create confusion matrix and safe in an excel table

cm = confusion_matrix(gold_labels, pred_labels, labels=labels_for_eval)

# create lists for indices and columns
index_labels = []
for g_label in labels_for_eval:
    index_labels.append(f"Gold_{g_label}")

column_labels = []
for p_label in labels_for_eval:
    column_labels.append(f"Pred_{p_label}")

# create confusion matrix df
cm_df = pd.DataFrame(cm, index=index_labels, columns=column_labels)


cm_df = cm_df.round(2)

cm_df.to_excel("/Masterarbeit/inception_export/evaluation_results/dependency_confusion_matrix.xlsx")


# safe confusion matrix as a figure

disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels_for_eval)

disp.plot(cmap="Blues", xticks_rotation=45)

plt.title("Dependency Label Confusion Matrix")

plt.tight_layout()

plt.savefig("/Masterarbeit/inception_export/evaluation_results/dependency_confusion_matrix.pdf")

plt.close()

# safe dataframe with analysis of errors
pd.DataFrame(error_analysis).to_excel(
"/Masterarbeit/inception_export/evaluation_results/dependency_errors.xlsx", index=False)


pd.DataFrame(false_positive_analysis).to_excel(
"/Masterarbeit/inception_export/evaluation_results/false_positive_verb_dependents.xlsx", index=False)