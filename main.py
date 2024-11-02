from __future__ import annotations
from copy import deepcopy
from io import TextIOWrapper as File

# --------------------------------------

def equalsAtPos(s: str, pos: int, target: str) -> bool:
    return s[pos : pos + len(target)] == target

def findNearestLabel(s: str, pos: int) -> tuple[str, int]:
    openingBracketPosition: int = -1
    closingBracketPosition: int = -1
    for i in range(pos, -1, -1):
        if equalsAtPos(s, i, "[[") or equalsAtPos(s, i, "|"):
            openingBracketPosition = i
            break
    for i in range(pos, len(s)):
        if equalsAtPos(s, i, "]]") or equalsAtPos(s, i, "|"):
            closingBracketPosition = i
            break
    startIndexOffset: int = 1 if s[openingBracketPosition] == "|" else 2
    return (s[openingBracketPosition + startIndexOffset : closingBracketPosition],
            openingBracketPosition)

def posNotX(s: str, pos: int) -> bool:
    return not (equalsAtPos(s, pos - 2, "x=") or equalsAtPos(s, pos - 3, "x=?"))

def posNotComment(s: str, pos: int) -> bool:
    for i in range(pos, -1, -1):
        if equalsAtPos(s, i, "<!--"):
            return False
        if equalsAtPos(s, i, "-->") or equalsAtPos(s, i, "\n"):
            return True
    return True

# --------------------------------------

class Node:

    def __init__(self: Node, name: str = "", descendants: list[Node] = []) -> None:
        self.name: str = name
        self.descendants: list[Node] = descendants

# --------------------------------------

class AnimalTree:

    @staticmethod
    def parseFromTokens(tokens: list[str]) -> AnimalTree:
        
        currentLevel: int = 0
        root: Node = Node()
        levelToNode: dict[int, Node] = {0: root}

        for token in tokens:
            if token == "{":
                currentLevel += 1
                levelToNode[currentLevel] = Node()
                levelToNode[currentLevel - 1].descendants.append(levelToNode[currentLevel])
            elif token == "}":
                currentLevel -= 1
            else:
                levelToNode[currentLevel - 1].descendants.append(Node(token))

        return AnimalTree(root)

    @staticmethod
    def parseFromFile(filename: str) -> AnimalTree:
        
        file: File = open(filename, "r")
        content: str = file.read()
        file.close()

        tokens: list[str] = []
        for i in range(len(content)):
            if equalsAtPos(content, i, "{{"):
                tokens.append("{")
            elif equalsAtPos(content, i, "}}"):
                tokens.append("}")
            elif equalsAtPos(content, i, "idae]]"):
                family, pos = findNearestLabel(content, i)
                if posNotX(content, pos) and posNotComment(content, pos):
                    tokens.append(family)
            elif equalsAtPos(content, i, "/includeonly"):
                break

        return AnimalTree.parseFromTokens(tokens[1 : -1])

    def __init__(self: AnimalTree, root: Node) -> None:
        self.root: Node = root

    def select(self: AnimalTree, animals: list[str]) -> AnimalTree:
        return self.selectWithAlias([(animal, animal) for animal in animals])
    
    def selectWithAlias(self: AnimalTree, animalsWithAlias: list[tuple[str, str]]) -> AnimalTree:
        raise RuntimeError # TODO
    
    def display(self: AnimalTree) -> None:
        raise RuntimeError # TODO

# --------------------------------------

print(AnimalTree.parseFromTokens([]))
exit()

animalTree: AnimalTree = AnimalTree.parseFromFile("passerines.txt")
subsetTree: AnimalTree = animalTree.selectWithAlias([
    ("Icteridae", "Blackbird"),
    ("Turdidae", "Bluebird"),
    ("Fringillidae", "Canary"),
    ("Alaudidae", "Lark"),
    ("Oriolidae", "Oriole"),
    ("Muscicapidae", "Robin"),
    ("Hirundinidae", "Swallow"),
    ("Troglodytidae", "Wren"),
    ("Corvidae", "Jay & Raven")
])

subsetTree.display()