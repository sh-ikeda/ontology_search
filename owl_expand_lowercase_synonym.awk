### 

BEGIN {
    prefix = "http://example.com/"
    ns = "ex"
    prop = "hasLowercaseSynonym"
}

/<\/owl:AnnotationProperty>/ && !property_defined {
    print
    print ""
    print ""
    print ""
    print "    <!-- " prefix prop " -->"
    print ""
    print "    <owl:AnnotationProperty rdf:about=\"" prefix prop "\">"
    print "        <rdfs:label>has_lowercase_synonym</rdfs:label>"
    print "    </owl:AnnotationProperty>"

    property_defined = 1
    next
}

/^ +xmlns:/ && !ns_defined {
    print
    print "      xmlns:" ns "=\"" prefix "\""

    ns_defined = 1
    next
}

/^        <oboInOwl:hasExactSynonym>/ {
    syn = gensub(/ *<\/?oboInOwl:hasExactSynonym>/, "", "g", $0)
    labels[syn] = 1
    lower_labels[tolower(syn)] = 1
}

/^        <rdfs:label>/ {
    label = gensub(/ *<\/?rdfs:label>/, "", "g", $0)
    labels[label] = 1
    lower_labels[tolower(label)] = 1
}

/^    <\/owl:Class>/ {
    for (l in lower_labels) {
        if (!labels[l])
            print "        <" ns ":" prop ">" l "</" ns ":" prop ">"
    }
    print
    delete labels
    delete lower_labels
    next
}

{
    print
}