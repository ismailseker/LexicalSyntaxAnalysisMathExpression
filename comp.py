import re
import math
import streamlit as st
from graphviz import Digraph

TOKEN_TYPES = {
    'NUMBER': r'\d+(\.\d+)?',   # Sayılar (tam sayı ve ondalık)
    'PLUS': r'\+',              # Toplama
    'MINUS': r'-',              # Çıkarma
    'MULTIPLY': r'\*',          # Çarpma
    'DIVIDE': r'/',             # Bölme
    'CARET': r'\^',            # Üs alma
    'FACTORIAL': r'!',          # Faktöriyel
    'SIN': r'sin',              # Sinüs
    'COS': r'cos',              # Kosinüs
    'LPAREN': r'\(',            # Sol parantez
    'RPAREN': r'\)',            # Sağ parantez
}

GRAMMAR = {
    'E': ['T E_PRIME'], # E -> T E' (ifadeler)
    'E_PRIME': ['+ T E_PRIME', '- T E_PRIME', 'ε'], # E' -> + T E' | - T E' | ε
    'T': ['F T_PRIME'], # T -> F T' (terimler)
    'T_PRIME': ['* F T_PRIME', '/ F T_PRIME', 'ε'], # T' -> * F T' | / F T' | ε
    'F': ['( E )', 'NUMBER', 'sin F', 'cos F', 'F ^ F', 'F !'] # Faktörler
}

def lexer(expression):
    tokens = []
    index = 0
    while index < len(expression):
        match = None
        for token_type, pattern in TOKEN_TYPES.items():
            regex = re.compile(pattern)
            match = regex.match(expression, index)
            if match:
                tokens.append((token_type, match.group(0)))
                index = match.end()
                break
        if not match:
            raise ValueError(f"Unexpected character: {expression[index]}")
    tokens.append(('EOF', 'EOF'))  # Sonlandırıcı token
    return tokens

class ASTNode:
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []

    def __repr__(self, level=0):
        ret = "\t" * level + repr(self.value) + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.current_token = self.tokens[self.index]
        self.derivation_steps = []

    def advance(self):
        self.index += 1
        if self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]

    def match(self, token_type):
        if self.current_token[0] == token_type:
            value = self.current_token[1]
            self.advance()
            return value
        else:
            raise ValueError(f"Syntax Error: Expected {token_type}, found {self.current_token[0]}")

    def parse_E(self):
        self.derivation_steps.append("E -> T E'")
        left = self.parse_T()
        return self.parse_E_PRIME(left)

    def parse_E_PRIME(self, left):
        if self.current_token[0] == 'PLUS':
            self.derivation_steps.append("E' -> + T E'")
            self.match('PLUS')
            right = self.parse_T()
            node = ASTNode('+', [left, right])
            return self.parse_E_PRIME(node)
        elif self.current_token[0] == 'MINUS':
            self.derivation_steps.append("E' -> - T E'")
            self.match('MINUS')
            right = self.parse_T()
            node = ASTNode('-', [left, right])
            return self.parse_E_PRIME(node)
        else:
            self.derivation_steps.append("E' -> ε")
            return left

    def parse_T(self):
        self.derivation_steps.append("T -> F T'")
        left = self.parse_F()
        return self.parse_T_PRIME(left)

    def parse_T_PRIME(self, left):
        if self.current_token[0] == 'MULTIPLY':
            self.derivation_steps.append("T' -> * F T'")
            self.match('MULTIPLY')
            right = self.parse_F()
            node = ASTNode('*', [left, right])
            return self.parse_T_PRIME(node)
        elif self.current_token[0] == 'DIVIDE':
            self.derivation_steps.append("T' -> / F T'")
            self.match('DIVIDE')
            right = self.parse_F()
            node = ASTNode('/', [left, right])
            return self.parse_T_PRIME(node)
        else:
            self.derivation_steps.append("T' -> ε")
            return left

    def parse_F(self):
        if self.current_token[0] == 'LPAREN':
            self.derivation_steps.append("F -> ( E )")
            self.match('LPAREN')
            node = self.parse_E()
            self.match('RPAREN')
            return node
        elif self.current_token[0] == 'NUMBER':
            self.derivation_steps.append("F -> NUMBER")
            value = self.match('NUMBER')
            return ASTNode(value)
        elif self.current_token[0] == 'SIN':
            self.derivation_steps.append("F -> sin F")
            self.match('SIN')
            child = self.parse_F()
            return ASTNode('sin', [child])
        elif self.current_token[0] == 'COS':
            self.derivation_steps.append("F -> cos F")
            self.match('COS')
            child = self.parse_F()
            return ASTNode('cos', [child])
        elif self.current_token[0] == 'CARET':
            self.derivation_steps.append("F -> F ^ F")
            left = self.parse_F()
            self.match('CARET')
            right = self.parse_F()
            return ASTNode('^', [left, right])
        elif self.current_token[0] == 'FACTORIAL':
            self.derivation_steps.append("F -> F !")
            child = self.parse_F()
            self.match('FACTORIAL')
            return ASTNode('!', [child])
        else:
            raise ValueError(f"Syntax Error: Unexpected token {self.current_token[0]}")

    def parse(self):
        ast = self.parse_E()
        if self.current_token[0] != 'EOF':
            raise ValueError(f"Syntax Error: Unexpected token {self.current_token[0]}")
        return ast, self.derivation_steps

def visualize_ast(ast):
    def add_nodes_edges(graph, node, parent=None):
        node_id = str(id(node))
        graph.node(node_id, label=node.value)
        if parent:
            graph.edge(str(id(parent)), node_id)
        for child in node.children:
            add_nodes_edges(graph, child, node)

    graph = Digraph(format="png")
    add_nodes_edges(graph, ast)
    return graph    

def main():
    st.title("Analysis of Math Expression")

    expression = st.text_input("Enter Math Expression")

    if expression:
        try:
            st.subheader("Lexical Analysis (Tokens):")
            tokens = lexer(expression)
            st.write(tokens)

            st.subheader("Syntax Analysis (Grammar Derivation Steps):")
            parser = Parser(tokens)
            ast, derivation_steps = parser.parse()

            st.subheader("Türetim Adımları")
            for step in derivation_steps:
                st.write(step)

            st.subheader("Abstract Syntax Tree (AST)")
            ast_graph = visualize_ast(ast)
            st.graphviz_chart(ast_graph.source)

        except ValueError as e:
            st.error(f"Hata: {e}")

if __name__ == "__main__":
    main()
   
