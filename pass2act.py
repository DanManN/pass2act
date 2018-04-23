import spacy
import pattern.en as en
from wordinv import nouninv

nlp = spacy.load('en')

def pass2act(doc):
    parse = nlp(doc)
    newdoc = ''
    for sent in parse.sents:

        # Init parts of sentence to capture:
        subjpass = ''
        subj = ''
        verb = ''
        verbaspect = ''
        verbtense = ''
        adverb = {'bef':'', 'aft':''}
        part = ''
        prep = ''
        agent = ''
        aplural = False
        advcltree = None
        aux = list(list(nlp('. .').sents)[0]) # start with 2 'null' elements
        xcomp = ''
        punc = '.'
        # Analyse dependency tree:
        for word in sent:
            if word.dep_ == 'advcl':
                if word.head.dep_ in ('ROOT', 'auxpass'):
                    advcltree = word.subtree
            if word.dep_ == 'nsubjpass':
                if word.head.dep_ == 'ROOT':
                    subjpass = ''.join(w.text_with_ws.lower() if w.tag_ not in ('NNP','NNPS') else w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'nsubj':
                subj = ''.join(w.text_with_ws.lower() if w.tag_ not in ('NNP','NNPS') else w.text_with_ws for w in word.subtree).strip()
                if word.head.dep_ == 'auxpass':
                    if word.head.head.dep_ == 'ROOT':
                        subjpass = subj
            if word.dep_ in ('advmod','npadvmod'):
                if word.head.dep_ == 'ROOT':
                    if verb == '':
                        adverb['bef'] = ''.join(w.text_with_ws for w in word.subtree).strip()
                    else:
                        adverb['aft'] = ''.join(w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'auxpass':
                if word.head.dep_ == 'ROOT':
                    if not subjpass:
                        subjpass = subj
            if word.dep_ in ('aux','auxpass','neg'):
                if word.head.dep_ == 'ROOT':
                    aux += [word]
            if word.dep_ == 'ROOT':
                verb = word.text
                if word.tag_ == 'VB':
                    verbtense = en.INFINITIVE
                elif word.tag_ == 'VBD':
                    verbtense = en.PAST
                elif word.tag_ == 'VBG':
                    verbtense = en.PRESENT
                    verbaspect = en.PROGRESSIVE
                elif word.tag_ == 'VBN':
                    verbtense = en.PAST
                else:
                    verbtense = en.tenses(word.text)[0][0]
            if word.dep_ == 'prt':
                if word.head.dep_ == 'ROOT':
                    part = ''.join(w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'prep':
                if word.head.dep_ == 'ROOT':
                    prep = ''.join(w.text_with_ws for w in word.subtree).strip()
            if word.dep_.endswith('obj'):
                if word.head.dep_ == 'agent':
                    if word.head.head.dep_ == 'ROOT':
                        agent = ''.join(w.text + ', ' if w.dep_=='appos' else w.text_with_ws for w in word.subtree).strip()
                        aplural = word.tag_ in ('NNS','NNPS')
            if word.dep_ in ('xcomp','ccomp','conj'):
                if word.head.dep_ == 'ROOT':
                    xcomp = ''.join(w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'punct':
                punc = word.text

        # exit if not passive:
        if subjpass == '':
            newdoc += str(sent) + ' '
            continue

        # if no agent is found:
        if agent == '':
            # what am I gonna do? BITconEEEEEEECT!!!!
            newdoc += str(sent) + ' '
            continue

        # invert nouns:
        agent = nouninv(agent)
        subjpass = nouninv(subjpass)

        # FUCKING CONJUGATION!!!!!!!!!!!!!:
        auxstr = ''
        num = en.SINGULAR if not aplural or agent in ('he','she') else en.PLURAL
        aux.append(aux[0])
        for (pp, p, a, n) in zip(aux,aux[1:],aux[2:],aux[3:]):
            if a.lemma_ == '.':
                continue

            if a.lemma_ == 'not':
                if p.lemma_ == 'be':
                    if n.lemma_ == 'be':
                        verbtense = en.tenses(a.text)[0][0]
                        auxstr += en.conjugate('be',tense=en.tenses(p.text)[0][0],number=num) + ' '
                        verbaspect = en.PROGRESSIVE
                    else:
                        auxstr += en.conjugate('do',tense=en.tenses(p.text)[0][0],number=num) + ' '
                        verbtense = en.INFINITIVE
                auxstr += 'not '
            elif a.lemma_ == 'be':
                if p.lemma_ == 'be':
                    verbtense = en.tenses(a.text)[0][0]
                    auxstr += en.conjugate('be',tense=en.tenses(a.text)[0][0],number=num) + ' '
                    verbaspect = en.PROGRESSIVE
            elif a.lemma_ == 'have':
                num == en.PLURAL if p.tag_ == 'MD' else num
                auxstr += en.conjugate('have',tense=en.tenses(a.text)[0][0],number=num) + ' '
                if n.lemma_ == 'be':
                    verbaspect = en.PROGRESSIVE
            else:
                auxstr += a.text_with_ws
        auxstr = auxstr.strip()

        verbaspect = None
        if auxstr.startswith('will'):
            verb = en.conjugate(verb,tense=en.INFINITIVE)
        else:
            if verbaspect:
                verb = en.conjugate(verb,tense=verbtense,aspect=verbaspect)
            else:
                verb = en.conjugate(verb,tense=verbtense)

        advcl = ''
        if advcltree:
            for w in advcltree:
                if w.pos_ == 'VERB' and en.tenses(w.text)[0][4] == en.PROGRESSIVE:
                    advcl += 'which ' + en.conjugate(w.text,tense=en.tenses(verb)[0][0]) + ' '
                else:
                    advcl += w.text_with_ws

        newsent = ' '.join(list(filter(None, [agent,auxstr,adverb['bef'],verb,part,subjpass,adverb['aft'],advcl,prep,xcomp])))+punc
        newsent = newsent[0].upper() + newsent[1:]
        newdoc += newsent + ' '
    return newdoc
