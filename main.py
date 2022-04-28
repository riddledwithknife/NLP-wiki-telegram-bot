import spacy
import wikipedia
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from clarifai.rest import ClarifaiApp, Image


def keyphrase(doc):
    for t in doc:
        if t.dep_ == 'pobj' and (t.pos_ == 'NOUN' or t.pos_ == 'PROPN'):
            return (' '.join([child.text for child in t.lefts]) + ' ' + t.text).lstrip()
    for t in reversed(doc):
        if t.dep_ == 'nsubj' and (t.pos_ == 'NOUN' or t.pos_ == 'PROPN'):
            return t.text + ' ' + t.head.text
    for t in reversed(doc):
        if t.dep_ == 'dobj' and (t.pos_ == 'NOUN' or t.pos_ == 'PROPN'):
            return t.head.text + 'ing' + ' ' + t.text
    return False


def photo_tags(filename):
    app = ClarifaiApp(api_key=CLARIFAI_API_KEY)
    model = app.public_models.general_model
    image = Image(file_obj=open(filename, 'rb'))
    response = model.predict([image])
    concepts = response['outputs'][0]['data']['concepts']
    for concept in concepts:
        if concept['name'] == 'food':
            food_model = app.public_models.food_model
            result = food_model.predict([image])
            first_concept = result['outputs'][0]['data']['concepts'][0]['name']
            return first_concept
    return response['outputs'][0]['data']['concepts'][1]['name']


def wiki(concept):
    nlp = spacy.load('en')
    wiki_resp = wikipedia.page(concept)
    doc = nlp(wiki_resp.content)
    if len(concept.split()) == 1:
        for sent in doc.sents:
            for t in sent:
                if t.text == concept and t.dep_ == 'dobj':
                    return sent.text
    return list(doc.sents)[0].text


def start(update):
    update.message.reply_text('Hi! This is a conversational bot. Ask me something.')


def text_msg(update):
    msg = update.message.text
    nlp = spacy.load('en')
    doc = nlp(msg)
    concept = keyphrase(doc)
    if concept:
        update.message.reply_text(wiki(concept))
    else:
        update.message.reply_text('Please rephrase your question.')


def photo(update):
    photo_file = update.message.photo[-1].get_file()
    filename = '{}.jpg'.format(photo_file.file_id)
    photo_file.download(filename)
    concept = photo_tags(filename)
    update.message.reply_text(wiki(concept))


def main():
    updater = Updater("TG_BOT_TOKEN", use_context=True)
    disp = updater.dispatcher
    disp.add_handler(CommandHandler("start", start))
    disp.add_handler(MessageHandler(Filters.text, text_msg))
    disp.add_handler(MessageHandler(Filters.photo, photo))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
