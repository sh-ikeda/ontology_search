# Ontology search

## About
Just to search for ontology terms by exact matching.

## Install
```
$ git clone https://github.com/sh-ikeda/ontology_search.git
$ cd ontology_search
$ pip install -r requirements.txt
$ python -c "import nltk; nltk.download('punkt_tab')"
```

## Usage
```
$ python ontology_search.py input.txt ontology.owl
```
The input text is assumed to have one query per line.


### Options
`-c`: Add a filter. e.g. `-c hasDbXref:NCBI_TaxID:9606` restricts search to only terms with the annotaion.

### Input ontology preparation
The matching is *case sensitive*. It is recommended to expand the target ontology to include lowercase-converted strings as synonyms before using the ontology as an input of this program.

The awk script `owl_expand_lowercase_synonym.awk` can be used for this purpose.
```
$ awk -f owl_expand_lowercase_synonym.awk cl-base.owl > cl-base.expand.owl
```

Adding such synonyms when loading the ontology in this program was considered, but this resulted in a significant slowdown in loading.

## How this works
1. Search for terms exactly matching to an input line.
2. When exact matched terms are not found, the input line is split into n-grams. After splitting the line with `nltk.word_tokenize()`, the symbols `[-_+/]` is also used to split the text. e.g. `MCF-7 cell` is split into ["MCF-7", "cell", "MCF", "7"].