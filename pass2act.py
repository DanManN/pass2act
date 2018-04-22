import spacy
import pattern.en as en
from wordinv import nouninv

nlp = spacy.load('en')

def pass2act(doc):
    parse = nlp(doc)
    newdoc = ''
    for sent in parse.sents:
        
        subjpass = ''
        verb = ''
        adverb = {'bef':'', 'aft':''}
        part = ''
        prep = ''
        agent = ''
        advcltree = None
        will = ''
        aux1 = ''
        aux2 = ''
        punc = '.'
        for word in sent:
            if word.dep_ == 'advcl':
                if word.head.dep_ in ('ROOT', 'auxpass'):
                    advcltree = word.subtree
            if word.dep_ == 'nsubjpass':
                subjpass = ''.join(w.text_with_ws.lower() if w.dep_ != 'nsubjpass' else w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'nsubj':
                if word.head.dep_ == 'auxpass':
                    subjpass = ''.join(w.text_with_ws.lower() if w.dep_ == 'nsubj' else w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'advmod':
                if word.head.dep_ == 'ROOT':
                    if verb == '':
                        adverb['bef'] = ''.join(w.text_with_ws for w in word.subtree).strip()
                    else:
                        adverb['aft'] = ''.join(w.text_with_ws for w in word.subtree).strip()
            if word.text.lower() == 'will':
                if word.head.dep_ == 'ROOT':
                    will = 'will'
            if word.dep_ == 'aux':
                if word.head.dep_ == 'ROOT':
                    aux1 = word
            if word.dep_ == 'auxpass':
                if word.head.dep_ == 'ROOT':
                    aux2 = word
            if word.dep_ == 'ROOT':
                verb = word.text_with_ws.strip()
            if word.dep_ == 'prt':
                if word.head.dep_ == 'ROOT':
                    part += ''.join(w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'prep':
                if word.head.dep_ == 'ROOT':
                    prep += ''.join(w.text_with_ws for w in word.subtree).strip()
            if word.dep_.endswith('obj'):
                if word.head.dep_ == 'agent':
                    agent = ''.join(w.text_with_ws + ',' if w.dep_=='appos' else w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'punct':
                punc = word.text

        if subjpass == '':
            newdoc += str(sent)
            continue
        
        if agent == '':
            # what am I gonna do? BITconEEEEEEECT!!!!
            newdoc += str(sent)
            continue

        if will:
            verb = en.conjugate(verb,tense=en.INFINITIVE)
        else:
            verb = en.conjugate(verb,tense=en.tenses(verb)[0][0])
        agent = nouninv(agent)
        subjpass = nouninv(subjpass)

        advcl = ''
        if advcltree:
            for w in advcltree:
                if w.pos_ == 'VERB' and en.tenses(w.text)[0][4] == en.PROGRESSIVE:
                    advcl += 'which ' + en.conjugate(w.text,tense=en.tenses(verb)[0][0]) + ' '
                else:
                    advcl += w.text_with_ws

        newdoc += ' '.join(list(filter(None, [agent,will,adverb['bef'],verb,part,subjpass,adverb['aft'],advcl,prep])))+punc
        newdoc = newdoc[0].upper() + newdoc[1:]
    return newdoc
