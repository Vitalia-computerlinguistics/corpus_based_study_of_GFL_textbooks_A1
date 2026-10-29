import conllu
import stanza
from pathlib import Path


nlp = stanza.Pipeline(lang='de', processors="tokenize,pos,lemma")


def nlp_analyser_for_inception(text_path, output_path):
    """This function gets path of input and output files with evaluation set data
    as an input and saves tokenized and annotated with lemmas and pos-tags file in conllu format"""

    with open(text_path, mode = "r", encoding = "UTF-8") as infile:
        text = infile.read()


    doc = nlp(text)

    with open(output_path, mode="w", encoding="utf-8") as outfile:

        for sent_id, sent in enumerate(doc.sentences, start=1):

            outfile.write(f"# sent_id = {sent_id}\n")
            outfile.write(f"# text = {sent.text}\n")

            for i, word in enumerate(sent.words, start=1):
                outfile.write(
                    f"{i}\t"                       
                    f"{word.text}\t"               
                    f"{word.lemma or word.text}\t" 
                    f"{word.upos or '_'}\t"        
                    f"{word.xpos or '_'}\t"        
                    f"_\t"                         
                    f"_\t"                         
                    f"_\t"                         
                    f"_\t"                         
                    f"_\n"
                )

            outfile.write("\n")


source_dir = Path("/Masterarbeit/sents_for_inception")
files = source_dir.iterdir()



for file in sorted(files):

    nlp_analyser_for_inception(file,f"/Masterarbeit/sents_for_inception_final/{file.stem}.conllu")