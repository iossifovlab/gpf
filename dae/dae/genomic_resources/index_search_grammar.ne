expression ->  token | or | and  {% id %}

and -> token _ "and" _ token {% function(d) { return {"and": [d[0], d[4]]} } %}
    | and _ "and" _ token {% function(d) { return {"and": [d[0], d[4]]} } %}
    | token _ "and" _ and {% function(d) { return {"and": [d[0], d[4]]} } %}
    | or _ "and" _ or {% function(d) { return {"and": [d[0], d[4]]} } %}
    | or _ "and" _ token {% function(d) { return {"and": [d[0], d[4]]} } %}
    | token _ "and" _ or {% function(d) { return {"and": [d[0], d[4]]} } %}

or -> token _ "or" _ token {% function(d) { return {"or": [d[0], d[4]]} } %}
    | or _ "or" _ token {% function(d) { return {"or": [d[0], d[4]]} } %}
    | token _ "or" _ or {% function(d) { return {"or": [d[0], d[4]]} } %}
    | and _ "or" _ and {% function(d) { return {"or": [d[0], d[4]]} } %}
    | and _ "or" _ token {% function(d) { return {"or": [d[0], d[4]]} } %}
    | token _ "or" _ and {% function(d) { return {"or": [d[0], d[4]]} } %}

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

word -> [a-zA-Z0-9!@#$%^&*()\[\]\./\\'";:<>?\-_=+]:+ {% function(d) { return d[0].join("") } %}
    | "\"" _:* word _:* "\"" {% function(d) { return d[2] } %}

_ -> [\s]:+ {% function(d) {return d[0]} %}
