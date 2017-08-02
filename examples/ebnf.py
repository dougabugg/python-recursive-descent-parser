from rdparser import grammar

c, b = grammar()

# an incomplete grammar for parsing Extended Backus–Naur form

c.identifier = {r"[a-zA-Z][a-zA-Z0-9_]*"}
symbols = r"\sa-zA-Z0-9[\]{}()<>=|.,;_"
symbols1 = {r"[{}']+".format(symbols)}
symbols2 = {r'[{}"]+'.format(symbols)}
c.terminal = (b('"') + symbols1 + '"') | (b("'") + symbols2 + "'")
c.lhs = c.identifier
# ideally, we would define c.rhs and be done with it.
# c.rhs = c.identifier | c.terminal | "[" + c.rhs + "]" | "{" + c.rhs + "}"\
#     | "(" + c.rhs + ")" | c.rhs + "|" + c.rhs | c.rhs + "," + c.rhs
# however, to avoid infinite recursion, we must get creative and remove recursion
c.seq = "[" + c.rhs + "]" | "{" + c.rhs + "}" | "(" + c.rhs + ")"
c.rhs_term = c.identifier | c.terminal
c.rhs_front = c.seq | c.rhs_term
c.rhs = c.rhs_front + [(b("|") | ",") + c.rhs]
c.rule = c.lhs + "=" + c.rhs + ";"
c.grammar = c.rule[:]["rules[]"] + b.EOS

source = """
letter = "A" | "B" | "C" | "D" | "E" | "F" | "G"
       | "H" | "I" | "J" | "K" | "L" | "M" | "N"
       | "O" | "P" | "Q" | "R" | "S" | "T" | "U"
       | "V" | "W" | "X" | "Y" | "Z" | "a" | "b"
       | "c" | "d" | "e" | "f" | "g" | "h" | "i"
       | "j" | "k" | "l" | "m" | "n" | "o" | "p"
       | "q" | "r" | "s" | "t" | "u" | "v" | "w"
       | "x" | "y" | "z" ;
digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
symbol = "[" | "]" | "{" | "}" | "(" | ")" | "<" | ">"
       | "'" | '"' | "=" | "|" | "." | "," | ";" ;
character = letter | digit | symbol | "_" ;
 
identifier = letter , { letter | digit | "_" } ;
terminal = "'" , character , { character } , "'" 
         | '"' , character , { character } , '"' ;

lhs = identifier ;
rhs = identifier
     | terminal
     | "[" , rhs , "]"
     | "{" , rhs , "}"
     | "(" , rhs , ")"
     | rhs , "|" , rhs
     | rhs , "," , rhs ;

rule = lhs , "=" , rhs , ";" ;
grammar = { rule } ;
"""

end, node, error = c.grammar.parse_or_print(source)
assert(error is None)