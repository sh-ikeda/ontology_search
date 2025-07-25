#!/usr/bin/env python3
"""
Ontology search program
Search ontology terms by label and synonym matching using owlready2
"""

import sys
import argparse
import re
import time
from owlready2 import get_ontology
from owlready2 import DataProperty


def generate_word_combinations(text):
    """
    Decompose input text into word combinations and generate possible combinations
    Separators: space, underscore, hyphen, period
    Sorted by word count (longest match first)
    """
    # Split by multiple separators
    words = re.split(r'[ _\-.]', text.strip())
    words = [w for w in words if w]  # Remove empty strings
    
    combinations = []
    
    # Generate combinations of consecutive words
    for length in range(len(words), 0, -1):  # From longest to shortest
        for i in range(len(words) - length + 1):
            combination = " ".join(words[i:i+length])
            combinations.append(combination)
    
    return combinations


def add_lowercase_synonyms(ontology):
    """
    Add lowercase versions of labels and synonyms as hasBroadSynonym
    Only add if the lowercase version doesn't already exist as a synonym
    """
    print("Adding lowercase synonyms for case-insensitive search...", file=sys.stderr)
    start_time = time.time()

    with ontology:
        class hasBroadSynonym(DataProperty):
            pass

    for cls in ontology.classes():
        existing_synonyms = set()

        # Collect existing synonyms (case-insensitive)
        if hasattr(cls, 'hasExactSynonym'):
            synonyms = cls.hasExactSynonym
            existing_synonyms.update(synonyms)
            # Add lowercase synonyms if not already existing
            for syn in synonyms:
                syn_lower = str(syn).lower()
                if syn_lower not in existing_synonyms:
                    cls.hasBroadSynonym.append(syn_lower)
        
        # Add lowercase label if not already a synonym
        label = cls.label[0]
        label_lower = label.lower()
        if label_lower not in existing_synonyms:
            cls.hasBroadSynonym.append(label_lower)
        
    
    add_time = time.time() - start_time
    print(f"Lowercase synonyms added in {add_time:.2f} seconds", file=sys.stderr)


def search_ontology_term(ontology, query, additional_conditions=None):
    """
    Search ontology terms that match the specified query
    Search labels, exact synonyms, and broad synonyms (for case-insensitive matching)
    """
    if additional_conditions is None:
        additional_conditions = {}
    
    all_results = []
    query_lower = query.lower()
    
    # First, search for exact match (case-sensitive)
    # Search by label
    search_kwargs = {"label": query}
    search_kwargs.update(additional_conditions)
    label_results = ontology.search(**search_kwargs)
    all_results.extend([(term, "label", query, None) for term in label_results])
    
    # Search by exact synonym
    search_kwargs = {"hasExactSynonym": query}
    search_kwargs.update(additional_conditions)
    synonym_results = ontology.search(**search_kwargs)
    
    # Find actual matching synonyms
    for term in synonym_results:
        if hasattr(term, 'hasExactSynonym'):
            synonyms = term.hasExactSynonym if isinstance(term.hasExactSynonym, list) else [term.hasExactSynonym]
            for syn in synonyms:
                if str(syn) == query:
                    all_results.append((term, "hasExactSynonym", query, str(syn)))
                    break
    
    # Search by broad synonym (case-insensitive)
    search_kwargs = {"hasBroadSynonym": query_lower}
    search_kwargs.update(additional_conditions)
    broad_synonym_results = ontology.search(**search_kwargs)
    
    # Find original matching terms for broad synonyms
    for term in broad_synonym_results:
        term_label = get_term_label(term)
        
        # Check if it matches the label (case-insensitive)
        if term_label.lower() == query_lower:
            # Skip if we already have exact label match
            if not any(result[0] == term and result[1] == "label" for result in all_results):
                all_results.append((term, "label", query, None))
        
        # Check if it matches an exact synonym (case-insensitive)
        elif hasattr(term, 'hasExactSynonym'):
            synonyms = term.hasExactSynonym if isinstance(term.hasExactSynonym, list) else [term.hasExactSynonym]
            for syn in synonyms:
                if str(syn).lower() == query_lower:
                    # Skip if synonym is just lowercase version of label
                    if str(syn).lower() != term_label.lower():
                        all_results.append((term, "hasExactSynonym", query, str(syn)))
                    break
    
    # Return if exact match found
    if all_results:
        return all_results
    
    # If no exact match, search with word decomposition (longest match first)
    word_combinations = generate_word_combinations(query)
    
    # Group by word count
    combinations_by_length = {}
    for combination in word_combinations:
        word_count = len(combination.split())
        if word_count not in combinations_by_length:
            combinations_by_length[word_count] = []
        combinations_by_length[word_count].append(combination)
    
    # Search from longest to shortest word count
    for word_count in sorted(combinations_by_length.keys(), reverse=True):
        current_results = []
        
        for combination in combinations_by_length[word_count]:
            combination_lower = combination.lower()
            
            # Search by label (case-sensitive)
            search_kwargs = {"label": combination}
            search_kwargs.update(additional_conditions)
            label_results = ontology.search(**search_kwargs)
            current_results.extend([(term, "label", combination, None) for term in label_results])
            
            # Search by exact synonym (case-sensitive)
            search_kwargs = {"hasExactSynonym": combination}
            search_kwargs.update(additional_conditions)
            synonym_results = ontology.search(**search_kwargs)
            
            for term in synonym_results:
                if hasattr(term, 'hasExactSynonym'):
                    synonyms = term.hasExactSynonym if isinstance(term.hasExactSynonym, list) else [term.hasExactSynonym]
                    for syn in synonyms:
                        if str(syn) == combination:
                            current_results.append((term, "hasExactSynonym", combination, str(syn)))
                            break
            
            # Search by broad synonym (case-insensitive)
            search_kwargs = {"hasBroadSynonym": combination_lower}
            search_kwargs.update(additional_conditions)
            broad_synonym_results = ontology.search(**search_kwargs)
            
            for term in broad_synonym_results:
                term_label = get_term_label(term)
                
                # Check if it matches the label (case-insensitive)
                if term_label.lower() == combination_lower:
                    # Skip if we already have exact label match
                    if not any(result[0] == term and result[1] == "label" and result[2] == combination for result in current_results):
                        current_results.append((term, "label", combination, None))
                
                # Check if it matches an exact synonym (case-insensitive)
                elif hasattr(term, 'hasExactSynonym'):
                    synonyms = term.hasExactSynonym if isinstance(term.hasExactSynonym, list) else [term.hasExactSynonym]
                    for syn in synonyms:
                        if str(syn).lower() == combination_lower:
                            # Skip if synonym is just lowercase version of label
                            if str(syn).lower() != term_label.lower():
                                current_results.append((term, "hasExactSynonym", combination, str(syn)))
                            break
        
        # If matches found for this word count, don't search shorter combinations
        if current_results:
            return current_results
    
    return []


def parse_additional_conditions(condition_str):
    """
    Parse additional search conditions
    Format: "hasDbXref:NCBI_TaxID:9606"
    """
    if not condition_str:
        return {}
    
    try:
        parts = condition_str.split(':', 2)
        if len(parts) >= 3:
            attr_name = parts[0]
            value = ':'.join(parts[1:])
            return {attr_name: value}
        elif len(parts) == 2:
            attr_name, value = parts
            return {attr_name: value}
        else:
            raise ValueError("Invalid format")
    except Exception:
        raise ValueError(f"Invalid additional condition format: {condition_str}")


def get_term_label(term):
    """
    Get the label of an ontology term
    """
    if hasattr(term, 'label') and term.label:
        return term.label[0] if isinstance(term.label, list) else str(term.label)
    return getattr(term, 'name', str(term).split('#')[-1].split('/')[-1])


def main():
    parser = argparse.ArgumentParser(description='Ontology search program')
    parser.add_argument('owl_file', help='Path to ontology OWL file')
    parser.add_argument('query_file', help='Path to text file containing queries')
    parser.add_argument('--condition', '-c', 
                       help='Additional search condition (e.g., hasDbXref:NCBI_TaxID:9606)')
    
    args = parser.parse_args()
    
    try:
        # Parse additional conditions
        additional_conditions = {}
        if args.condition:
            additional_conditions = parse_additional_conditions(args.condition)
        
        # Load ontology with timing
        print("Loading ontology...", file=sys.stderr)
        start_time = time.time()
        ontology = get_ontology(f"file://{args.owl_file}").load()
        load_time = time.time() - start_time
        print(f"Ontology loaded in {load_time:.2f} seconds", file=sys.stderr)
        
        # Add lowercase synonyms for case-insensitive search
        add_lowercase_synonyms(ontology)
        
        # Output header (TSV format)
        print("Query\tMatchedPart\tTermID\tMatchType\tTermLabel\tMatchedSynonym")
        
        # Read query file and process each line
        print("Starting term search...", file=sys.stderr)
        search_start_time = time.time()
        
        with open(args.query_file, 'r', encoding='utf-8') as f:
            for line in f:
                query = line.strip()
                if not query:  # Skip empty lines
                    continue
                
                # Search ontology terms
                term_results = search_ontology_term(ontology, query, additional_conditions)
                
                # Output results in TSV format
                if term_results:
                    for term, match_type, matched_part, matched_synonym in term_results:
                        # Get term ID
                        term_id = getattr(term, 'name', str(term).split('#')[-1].split('/')[-1])
                        # Get term label
                        term_label = get_term_label(term)
                        # Prepare synonym column
                        synonym_col = matched_synonym if matched_synonym else ""
                        print(f"{query}\t{matched_part}\t{term_id}\t{match_type}\t{term_label}\t{synonym_col}")
                else:
                    print(f"{query}\t\t\t\t\t")
        
        search_time = time.time() - search_start_time
        print(f"Search completed in {search_time:.2f} seconds", file=sys.stderr)
    
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
