#!/usr/bin/env python3
'''
get inference

input: polarized trees from getMono.py

Hai Hu, Feb 2018
'''

import getMono
import sys, re, os, copy

def main():
    sentToTest = None
    if len(sys.argv) >= 2:
        sentToTest = int(sys.argv[1]) # sentence to test
        print('sentToTest:',sentToTest)
    trees = getMono.CCGtrees()
    trees.readCandCxml('tmp.candc.xml')

    # build knowledge
    # k = buildKnowledgeTest() # April 26
    k = Knowledge()     # JUNE 12
    k.buildAll()
    print('\nknowledge built!\n--------------\n')

    # return

    # TODO read in sent, do replacement

    print()
    print('-' * 20)
    t = trees.trees[0]
    if any(x in sys.argv for x in ['-v1', '-vall']):
        t.printTree()
    t.getPM()
    if any(x in sys.argv for x in ['-v2', '-vall']):
        t.printTree()
    t.polarize()
    if any(x in sys.argv for x in ['-v3', '-vall']):
        t.printTree()
    t.printSent()

    # ---------------------------
    # now replacement
    print('\nNOW REPLACEMENT\n')
    t.replacement(k=k)
    for i in t.inferences:
        i.replacement(k=k)
        # for j in i.inferences:
        #     j.replacement(k=k)

    print('\nwe can infer:')

    t.printAllInferences()

    # getInferOld(t, conc='No historian catwalks .')


class Knowledge:
    def __init__(self):
        self.frags = {}  # TODO should we call them preorders?
        # key is string, value is Fragment class
        self.numPairs = 0
        self.allnouns = []   # a list of LeafNode
        self.subsecAdj = []  # a list of LeafNode

    def addPair(self, pair):  # pair is a tuple = (small, big)
        small = pair[0]  # a CCGtree
        big = pair[1]    # a CCGtree

        # add big to self.frags[small.wholeStr]
        if small.wholeStr not in self.frags.keys():
            smallAsFrag = Fragment(small)
            smallAsFrag.big.append(Fragment(big))
            # -------------------------
            # add small itself to small.big and small.small
            # smallAsFrag.big.append(smallAsFrag)
            # smallAsFrag.small.append(smallAsFrag)
            # -------------------------
            smallAsFrag.wholeStr = small.wholeStr
            self.frags[small.wholeStr] = smallAsFrag

        else:  # small.wholeStr in self.frags.keys():
            if big.wholeStr not in [x.wholeStr for x in self.frags[small.wholeStr].big]:
                self.frags[small.wholeStr].big.append(Fragment(big))

        # add small to self.frags[big.wholeStr]
        if big.wholeStr not in self.frags.keys():
            bigAsFrag = Fragment(big)
            bigAsFrag.small.append(Fragment(small))
            # -------------------------
            # add big itself to big.big and big.small
            # bigAsFrag.big.append(bigAsFrag)
            # bigAsFrag.small.append(bigAsFrag)
            # -------------------------
            bigAsFrag.wholeStr = big.wholeStr
            self.frags[big.wholeStr] = bigAsFrag

        else:  # big.wholeStr in self.frags.keys():
            if small.wholeStr not in [x.wholeStr for x in self.frags[big.wholeStr].small]:
                self.frags[big.wholeStr].small.append(Fragment(small))

        self.numPairs += 1

    def buildAll(self):

        '''
        June 2018

        We have 3 types of input for knowledge K:
        1. PAIRS: pairs in text format. e.g. N: dog < animal
        2. SUBSADJ: a list of subsective adjs. e.g. old, young
        3. ISA: isA sentences

        buildKnowledge():
        - allnouns = []
        - build knowledge for each pair in PAIRS. (get nouns)
        - parse sentences in ISA. (get nouns)
          X is a Y.
          extract X and Y as treelets from the CCG parse tree
          then add the following to knowledge: every Y < X < some Y
        - find all the nouns in the system.
          allnouns = nouns in PAIRS + nouns in ISA
          for every noun in allnouns:
            for every adj in SUBSADJ:
              add this to knowledge: adj + noun < noun
        '''

        self.buildPairs()
        self.buildSubsecAdj()
        pass

    def buildPairs(self):
        print('building from pairs ...\n')
        # read in pairs.txt in ./k
        with open('./k/pairs.txt') as f:
            for line in f:
                syntacticType = line[0]  # N or V

                if syntacticType == 'V':
                    # we don't know it's transitive or intransitive
                    # so make it None for now
                    # TODO but need to add this information in getMono.CCGtree.replacement()
                    syntacticType = None
                    pos = 'V'
                elif syntacticType == 'N':
                    pos = 'N'

                relationPair = line[2:].split('<')  # [' dog ', ' animal ']
                try:
                    assert len(relationPair) == 2
                except AssertionError:
                    print('wrong format in pairs.txt:')
                    print(line)
                    
                # print(relationPair)
                
                # set small and big to LeafNode.
                small = getMono.LeafNode(depth=0,
                                         cat=getMono.Cat(originalType=syntacticType,
                                                         word=relationPair[0].strip()),
                                         chunk=None, entity=None, lemma=None,
                                         pos=pos, span=None, start=None,
                                         word=relationPair[0].strip())
                big = getMono.LeafNode(depth=0,
                                         cat=getMono.Cat(originalType=syntacticType,
                                                         word=relationPair[1].strip()),
                                         chunk=None, entity=None, lemma=None,
                                         pos=pos, span=None, start=None,
                                         word=relationPair[1].strip())
                if syntacticType == 'N':
                    self.allnouns.extend([small, big])  # small and big are LeafNodes

                # change small and big to CCGtree().
                small = getMono.CCGtree(TermNode=small)
                big = getMono.CCGtree(TermNode=big)

                self.addPair((small, big))

        # print(self.frags)
        # print(self.frags['APPLE'].big)
        # print(self.allnouns)

    def buildSubsecAdj(self):
        print('building from subsective adjs ...\n')
        # read in all subsec adjs
        with open('./k/subsecAdj.txt') as f:
            for line in f:
                adj = getMono.LeafNode(depth=0,
                                       cat=getMono.Cat(originalType=r'N/N',
                                                       word=line.strip()),
                                       chunk=None, entity=None, lemma=None,
                                       pos='JJ', span=None, start=None,
                                       word=line.strip())
                self.subsecAdj.append(adj)
        # print(self.subsecAdj)

        # combine with allnouns and add to frags
        for noun in self.allnouns:
            # noun is LeafNode
            for adj in self.subsecAdj:
                # newNoun is the mother of adj + noun
                newNoun = getMono.NonTermNode(depth=0,
                                              cat=getMono.Cat(originalType='N',
                                                       word=None),
                                              ruleType='fa')
                newNoun.children = [adj, noun]
                adj.parent = newNoun; noun.parent = newNoun
                adj.sisters = [noun]; noun.sisters = [adj]
                self.addPair((getMono.CCGtree(NonTermNode=newNoun),
                              getMono.CCGtree(TermNode=noun)))

        print(self.frags['ANIMALS'].small)

    def buildISA(self):
        pass

class Fragment:
    def __init__(self, ccgtree=None):
        '''  small < frag < big;  a frag could be "chased some cat"  '''
        self.ccgtree = ccgtree  # a CCGtree
        self.wholeStr = ccgtree.wholeStr  # 'CHASED SOME CAT'
        self.small = []  # could have multiple small
        self.big = []  # could have multiple big
    def __str__(self):
        return '{}'.format(self.wholeStr)
    def __repr__(self):
        return self.__str__()

class Pair:
    ''' each pair is a relation: big dogs < animals
        small = big dogs; big = animals
        small and big are CCGtrees
    '''
    def __init__(self, small, big):
        self.small = small
        self.big = big

'''
Pipeline:

wordnet/sentences => our representation => replacement

Now we just assume we already have our representation.
In the next step, we start with wordnet/sentences

===================
Our representation (Knowledge class):

- big dogs < large animals

Both phrases should be trees. I.e. the CCGtree class from getMono.py

big   dogs
N/N   N
---------- fa
    N

===================
Replacement:

- Find in the premise a node N 1) with string 'big dogs' and
2) with the same tree structure (?this will be hard to do)

- Replace N with the node 'large animals'

We should loop every node in CCGtree.

===================
Test:
- premise: Every large animal likes vegetables.
- conc: Every big dog likes carrots.

'''

def buildKnowledgeTest():
    print('\n\n-----------\nbuilding knowledge...')
    k = Knowledge()

    '''
    I chased some cat.
    I hit every bird.
    I see some animal.
    It is black.

    chased some cat < liked every dog (small1, big1)
    see some animal < is black (small2, big2)
    old dog < dog (small3, big3)
    young man < man (s4, b4)
    cat < animal (s5, b5)
    every man < John < some man (s6, m6, b6)
    '''

    knowledgeTrees = getMono.CCGtrees()
    knowledgeTrees.readCandCxml('knowledge.candc.xml')

    # ----------------------
    small1 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[0].root.children[0].children[1]
    )
    print(small1.wholeStr)

    big1 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[1].root.children[0].children[1]
    )
    print(big1.wholeStr)

    # ----------------------
    small2 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[2].root.children[0].children[1]
    )
    print(small2.wholeStr)

    big2 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[3].root.children[0].children[1]
    )
    print(big2.wholeStr)

    # ----------------------
    small3 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[4].root.children[0].children[1]
    )
    print(small3.wholeStr)

    big3 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[5].root.children[0].children[1]
    )
    print(big3.wholeStr)

    # ----------------------
    s4 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[0].root.children[0].children[1].children[1].children[1]
    )
    print(s4.wholeStr)  # cat

    b4 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[6].root.children[0].children[1]
    )
    print(b4.wholeStr)  # animal

    # ----------------------
    s5 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[7].root.children[0].children[1]
    )
    print(s5.wholeStr)  # young man

    b5 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[7].root.children[0].children[1].children[1]
    )
    print(b5.wholeStr)  # man

    # ----------------------
    s6 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[8].root.children[0].children[0]
    )
    print(s6.wholeStr)  # every man

    m6 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[9].root.children[0].children[0]
    )
    print(m6.wholeStr)  # John

    b6 = getMono.CCGtree(
        NonTermNode=knowledgeTrees.trees[10].root.children[0].children[0]
    )
    print(b6.wholeStr)  # some man

    # add to knowledge
    k.addPair((small1, big1))
    k.addPair((small2, big2))
    k.addPair((small3, big3))
    k.addPair((s4, b4))
    k.addPair((s5, b5))
    k.addPair((s6, m6))
    k.addPair((m6, b6))
    k.addPair((s6, b6))

    print('\nknowledge built!\n--------------\n')
    return k


def getInferOld(CCGtree, premises=None, conc=None):
    # parse conclusion
    wordsRelevant = set()
    if premises:
        wordsRelevant.update( set(p.split(' ')) for p in premises )
    if conc:
        wordsRelevant.update( set(p.split(' ')) for p in conc )

    # make a new tree
    newTree = copy.deepcopy(CCGtree)

    for leafN in newTree.leafNodes:
        # nouns, verbs
        if leafN.pos[0].upper() in ['N', 'V']:
            print()
            if leafN.cat.monotonicity == 'UP':
                print('UP for:', leafN)
                # print(WN.getHypernyms(leafN.word, pos='n'))
                hyps = WN.getAllHyps('hypernym', leafN.word, pos='n')
                for hyp in hyps:
                    if hyp in wordsRelevant:
                        print(hyp)

            elif leafN.cat.monotonicity == 'DOWN':
                print('DOWN for:', leafN)
                # print(WN.getHyponyms(leafN.word, pos='n'))
                hyps = WN.getAllHyps('hyponym', leafN.word, pos='n')
                for hyp in hyps:
                    if hyp in wordsRelevant:
                        print(hyp)



if __name__ == '__main__':
    main()
