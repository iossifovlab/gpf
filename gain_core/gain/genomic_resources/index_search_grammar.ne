expression ->  token | or | and  {% id %}

and -> token and_identifier token {% function(d) { return {"and": [d[0], d[2]]} } %}
    | and and_identifier token {% function(d) { return {"and": [d[0], d[2]]} } %}
    | token and_identifier and {% function(d) { return {"and": [d[0], d[2]]} } %}
    | or and_identifier or {% function(d) { return {"and": [d[0], d[2]]} } %}
    | or and_identifier token {% function(d) { return {"and": [d[0], d[2]]} } %}
    | token and_identifier or {% function(d) { return {"and": [d[0], d[2]]} } %}

and_identifier -> _ "&" _ {% id %}
    | _ {% id %}

or -> token or_identifier token {% function(d) { return {"or": [d[0], d[2]]} } %}
    | or or_identifier token {% function(d) { return {"or": [d[0], d[2]]} } %}
    | token or_identifier or {% function(d) { return {"or": [d[0], d[2]]} } %}
    | and or_identifier and {% function(d) { return {"or": [d[0], d[2]]} } %}
    | and or_identifier token {% function(d) { return {"or": [d[0], d[2]]} } %}
    | token or_identifier and {% function(d) { return {"or": [d[0], d[2]]} } %}

or_identifier -> _ "|" _ {% id %}

token -> word {% 
            function(d, l, reject) {
                const word = d[0]
                if(word[0] === "-") {
                    return reject
                }
                return word
            } 
        %}
    | "-" word {% function(d) {return {"not": d[1]}} %}

word -> [a-zA-Z0-9!@#$%^*()\[\]\./\\';:<>?\-_=+]:+ {% function(d) { return d[0].join("") } %}
    | "\"" [a-zA-Z0-9!@#$%^*()\[\]\./\\';:<>?\-_=+ ]:+ "\"" {% function(d) { return { "precise": d[1].join("") } } %}

_ -> [\s]:+ {% function(d) {return d[0]} %}
