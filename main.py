from __future__ import annotations
from copy import deepcopy
from io import TextIOWrapper as File
from sys import maxsize as INT_MAX

# --------------------------------------------------------------------------------------------------

def isDigit(char: str) -> bool:
    return ord("0") <= ord(char) and ord(char) <= ord("9")

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

def findNearestPointer(s: str, openBracketPos: int) -> str:
    closeBracketPos: int = openBracketPos + 1
    while s[closeBracketPos] != "}":
        closeBracketPos += 1
    return s[openBracketPos + 1 : closeBracketPos]

def posNotX(s: str, pos: int) -> bool:
    return not (equalsAtPos(s, pos - 2, "x=") or equalsAtPos(s, pos - 3, "x=?"))

def posNotComment(s: str, pos: int) -> bool:
    for i in range(pos, -1, -1):
        if equalsAtPos(s, i, "<!--"):
            return False
        if equalsAtPos(s, i, "-->") or equalsAtPos(s, i, "\n"):
            return True
    return True

def returnToPreviousWorkingTree(currDepthForEachTree: dict[str, int]) -> str:
    minimumTreeName: str = ""
    minimumTreeDepth: int = INT_MAX
    for treeName, treeDepth in currDepthForEachTree.items():
        if treeDepth != 0 and treeDepth < minimumTreeDepth:
            minimumTreeName = treeName
            minimumTreeDepth = treeDepth
    return minimumTreeName

def splitTokensByTree(tokens: list[str]) -> dict[str, list[str]]:

    tokensForEachTree: dict[str, list[str]] = {}
    currDepthForEachTree: dict[str, int] = {}
    currWorkingTree: str = ""

    for i in range(len(tokens)):
        token: str = tokens[i]

        if token[0] == "!":
            tokensForEachTree[token[1:]] = []
            currDepthForEachTree[token[1:]] = 1
            currWorkingTree = token[1:]

        elif token == "{":
            if tokens[i - 1][0] != "!":
                currDepthForEachTree[currWorkingTree] += 1 # TODO: increment for all open trees
            tokensForEachTree[currWorkingTree].append(token)

        elif token == "}":
            currDepthForEachTree[currWorkingTree] -= 1
            tokensForEachTree[currWorkingTree].append(token)
            if currDepthForEachTree[currWorkingTree] == 0:
                currWorkingTree = returnToPreviousWorkingTree(currDepthForEachTree)
        
        else:
            tokensForEachTree[currWorkingTree].append(token)

    for treeName in tokensForEachTree:
        tokensForEachTree[treeName] = tokensForEachTree[treeName][1 : -1]

    return tokensForEachTree

# --------------------------------------------------------------------------------------------------

class Node:

    def __init__(self: Node, name: str = "", descendants: list[Node] = []) -> None:
        self.name: str = name
        self.descendants: list[Node] = deepcopy(descendants)

    def __eq__(self: Node, other: object) -> bool:
        return id(self) == id(other)

    def isLeaf(self: Node) -> bool:
        return len(self.descendants) == 0
    
    def numLeaves(self: Node) -> int:
        if self.isLeaf():
            return 1
        else:
            return sum([node.numLeaves() for node in self.descendants])

    def display(self: Node, level: int) -> None:
        displayName: str = self.name if self.name != "" else f"Clade @ {id(self)}"
        suffix: str = f" ({self.numLeaves()} leaf nodes):" if not self.isLeaf() else ""
        print(2 * level * " " + displayName + suffix)
        for descendant in self.descendants:
            descendant.display(level + 1)

    def checkForReplacements(self: Node, trees: list[AnimalTree]) -> None:
        for i in range(len(self.descendants)):
            descendant: Node = self.descendants[i]
            if not descendant.isLeaf():
                descendant.checkForReplacements(trees)
            elif descendant.name[0] == "@":
                pointer: str = descendant.name[1:]
                indexForPointer: int = AnimalTree.findIndexForPointer(trees, pointer)
                self.descendants[i] = AnimalTree.recombineIntoSingleTree(trees, indexForPointer).root

    def simplify(self: Node) -> None:
        for i in range(len(self.descendants)):
            descendant: Node = self.descendants[i]
            descendant.simplify()
            if len(descendant.descendants) == 1:
                broadName: str = descendant.name
                narrowName: str = descendant.descendants[0].name
                self.descendants[i] = descendant.descendants[0]
                self.descendants[i].name = broadName if narrowName == "" else narrowName

    def applyAliases(self: Node, aliases: dict[str, str]) -> None:
        if self.name in aliases:
            self.name = aliases[self.name]
        for descendant in self.descendants:
            descendant.applyAliases(aliases)
    
    def prune(self: Node, animals: list[str]) -> None:
        indexesToDelete: list[int] = []
        for i in range(len(self.descendants)):
            descendant: Node = self.descendants[i]
            if not descendant.isLeaf():
                descendant.prune(animals)
            if descendant.isLeaf() and descendant.name not in animals:
                indexesToDelete.append(i)
        indexesToDelete.reverse()
        for indexToDelete in indexesToDelete:
            del self.descendants[indexToDelete]

# --------------------------------------------------------------------------------------------------

class AnimalTree:

    @staticmethod
    def parseFromTokensSingleTree(tokens: list[str]) -> AnimalTree:
        
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
                levelToNode[currentLevel].descendants.append(Node(token))

        return AnimalTree(root)
    
    @staticmethod
    def parseFromTokensMultipleTrees(tokens: dict[str, list[str]]) -> list[AnimalTree]:
        trees: list[AnimalTree] = []
        for treeName, treeTokens in tokens.items():
            trees.append(AnimalTree.parseFromTokensSingleTree(treeTokens))
            trees[-1].root.name = treeName
        return trees
    
    @staticmethod
    def recombineIntoSingleTree(trees: list[AnimalTree], rootIndex: int) -> AnimalTree:
        rootTree: AnimalTree = trees[rootIndex]
        rootTree.root.checkForReplacements(trees)
        return rootTree
    
    @staticmethod
    def findIndexForPointer(trees: list[AnimalTree], pointer: str) -> int:
        for i in range(len(trees)):
            if trees[i].root.name == pointer:
                return i
        raise RuntimeError("no matching tree for pointer has been found")
    
    @staticmethod
    def parseFromTokens(tokens: list[str]) -> AnimalTree:
        trees: list[AnimalTree] = AnimalTree.parseFromTokensMultipleTrees(splitTokensByTree(tokens))
        return AnimalTree.recombineIntoSingleTree(trees, 0)

    @staticmethod
    def parseFromFile(filename: str, rootNodeName: str) -> AnimalTree:
        
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
            elif content[i] == "{" and content[i + 1] != "{" and content[i - 1] != "{":
                pointer: str = findNearestPointer(content, i)
                symbol: str = "@" if isDigit(content[i - 2]) else "!"
                tokens.append(symbol + pointer)
            elif equalsAtPos(content, i, "/includeonly"):
                break

        tokens = ["!" + rootNodeName] + tokens[1 : -1]
        return AnimalTree.parseFromTokens(tokens)

    def __init__(self: AnimalTree, root: Node) -> None:
        self.root: Node = root

    def select(self: AnimalTree, animals: list[str]) -> AnimalTree:
        return self.selectWithAlias({animal: animal for animal in animals})
    
    def prune(self: AnimalTree, animals: list[str]) -> AnimalTree:
        newTree: AnimalTree = deepcopy(self)
        newTree.root.prune(animals)
        return newTree
    
    def applyAliases(self: AnimalTree, aliases: dict[str, str]) -> None:
        self.root.applyAliases(aliases)

    def selectWithAlias(self: AnimalTree, animalsWithAlias: dict[str, str]) -> AnimalTree:
        prunedTree: AnimalTree = self.prune([animal for animal, alias in animalsWithAlias.items()])
        prunedTree.simplify()
        prunedTree.applyAliases(animalsWithAlias)
        return prunedTree
    
    def simplify(self: AnimalTree) -> None:
        self.root.simplify()
        if len(self.root.descendants) == 1:
            rootName: str = self.root.name
            onlyDescendantName: str = self.root.descendants[0].name
            self.root = self.root.descendants[0]
            self.root.name = rootName if rootName != "" else onlyDescendantName
    
    def display(self: AnimalTree) -> None:
        print()
        self.root.display(level = 0)

# --------------------------------------------------------------------------------------------------

def parsePasserines() -> None:
    passerines: AnimalTree = AnimalTree.parseFromFile("passerines.txt", "PASSERIFORMES")
    passerines.simplify()
    passerines.display()
    passerines.selectWithAlias({
        "Icteridae": "Blackbird",
        "Turdidae": "Bluebird",
        "Fringillidae": "Canary",
        "Alaudidae": "Lark",
        "Oriolidae": "Oriole",
        "Muscicapidae": "Robin",
        "Hirundinidae": "Swallow",
        "Troglodytidae": "Wren",
        "Corvidae": "Jay & Raven"
    }).display()

def parseTestudines() -> None:
    testudines: AnimalTree = AnimalTree.parseFromFile("testudines.txt", "TESTUDINES")
    testudines.simplify()
    testudines.display()

# --------------------------------------------------------------------------------------------------

parsePasserines()
parseTestudines()