#!/usr/bin/env python
# -*- coding: utf-8 -*-


#   from flask import redirect, url_for
import json
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from irtokz import tokenize_ind
from main import change_chl, save_feedback, get_feedbacks, change_weights_pratyaya_options, create_dummy_output, save_modified_words, rule_based_analyze, get_chunks, get_all_sense_gloss, get_csv_from_uni, get_all_valid_nouns
from collections import OrderedDict


# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding("utf8")


app = Flask(__name__)
app.config["TRAP_BAD_REQUEST_ERRORS"] = True
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqldb://root:ltrc@iiit@localhost/communicator_tool?charset=utf8mb4"
db = SQLAlchemy(app)


class CHL_CONVERSION(db.Model):
    """create CHL_CONVERSION Table in the communicator_tool database"""
    id = db.Column(db.Integer, primary_key=True)
    input_text = db.Column(db.Text)
    parser_words = db.Column(db.Text)
    modified_parser_words = db.Column(db.Text)
    chl_text = db.Column(db.Text)
    feedback = db.Column(db.Text)
    checked = db.Column(db.Boolean)

    def __init__(self, **kwargs):
        for name, value in kwargs.iteritems():
            self.name = value

    def __repr__(self):
        return "{}\n----------\n{}\n{}\n----------".format(self.id, self.input_text, self.chl_text)


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
    return response


@app.route("/")
def root():
    return render_template("index.html")


@app.route("/run", methods=["POST", "GET"])
def run():
    """Takes the input text from the FORM and passes it to analyze function and returns its output"""
    if request.method == "POST":
        return "Not Installed"


@app.route("/change", methods=["POST", "GET"])
def change():
    """Takes the modified words and passes it to change function and returns its output"""
    if request.method == "POST":
        # print request.form
        dbid = request.form["dbid"]
        output = request.form["result"]
        new_relation_weight = json.loads(request.form["new_relation_weight"])
        output = json.loads(output)
        dbid, output = change_chl(dbid, output)
        change_weights_pratyaya_options(new_relation_weight)
        return json.dumps((dbid, output))


@app.route("/feedback", methods=["POST", "GET"])
def feedback():
    """Takes the modified words and passes it to change function and returns its output"""
    if request.method == "POST":
        # print request.form
        dbid = request.form["dbid"]
        ifeedback = request.form["feedback"]
        save_feedback(dbid, ifeedback)
        return "successfully saved in the database"
    elif request.method == "GET":
        return get_feedbacks()


@app.route("/tokenize", methods=["POST"])
def tokenize():
    """Takes the input sentence and outputs the json of the tokens"""
    print request.method
    if request.method == "POST":
        # print request.form
        input_text = request.form["hin_text"]
        tok = tokenize_ind(lang="hin")
        tokenized_output = [ tok.tokenize(i).split() for i in input_text.split("\n")]
    # print tokenized_output
        output = json.dumps({"input_text": input_text, "tokenized_output": tokenized_output})
        return json.dumps({"input_text": input_text, "tokenized_output": tokenized_output})


@app.route("/raw_annotate", methods=["POST"])
def raw_annotate():
    """Takes raw_sentence and creates a dummy output for user to annotate the sentence"""
    print request.form
    if request.method == "POST":
        # print request
        input_text = request.form["mainInput"].strip()
        open_brackets_list = json.loads(request.form["open_brackets_list"].encode("utf-8"))
        close_brackets_list = json.loads(request.form["close_brackets_list"].encode("utf-8"))
        proper_noun_list = json.loads(request.form["proper_noun_list"].encode("utf-8"))
        dbid, output = create_dummy_output(input_text, open_brackets_list, close_brackets_list, proper_noun_list)
        return json.dumps((dbid, output))


@app.route("/rulebased_run", methods=["POST", "GET"])
def rulebased_run():
    """Takes the input text from the FORM and passes it to analyze function and returns its output"""
    if request.method == "POST":
        user_text = request.form["mainInput"].encode("utf-8")
        open_brackets_list = json.loads(request.form["open_brackets_list"].encode("utf-8"))
        close_brackets_list = json.loads(request.form["close_brackets_list"].encode("utf-8"))
        proper_noun_list = json.loads(request.form["proper_noun_list"].encode("utf-8"))
        chnk_html = request.form["chnk_html"].encode("utf-8")
        chunking_output = json.loads(request.form["chunking_output"].encode("utf-8"))
        compoundnouns = json.loads(request.form["compoundnouns"].encode("utf-8"))
        complexpredicates = json.loads(request.form["complexpredicates"].encode("utf-8"))
        dbid, output, ilparser_output = rule_based_analyze(user_text, open_brackets_list, close_brackets_list, proper_noun_list, chnk_html, chunking_output, compoundnouns, complexpredicates)
        return json.dumps((dbid, output, ilparser_output))


@app.route("/get_chunking", methods=["POST"])
def get_chunking():
    """Takes the input text from the form and passes it to get_chunk module and return its output"""
    if request.method == "POST":
        user_text = request.form["hin_input"].encode("utf-8")
        tokenized_text = json.loads(request.form["tokenized_text"].encode("utf-8"))
        output = get_chunks(user_text, tokenized_text)
        return json.dumps(output)


@app.route("/save_modified_words", methods=["POST"])
def modified_words():
    """Takes modified words and updates them in the database"""
    if request.method == "POST":
        uni = json.loads(request.form["uni"])
        dbid = request.form["dbid"]
        return save_modified_words(uni, dbid)


@app.route("/get_gloss", methods=["POST"])
def get_gloss():
    """takes modified words and inserts gloss in them"""
    if request.method == "POST":
        uni = json.loads(request.form["uni"])
        dbid = request.form["dbid"]
        uni, dbid = get_all_sense_gloss(uni, dbid)
        return json.dumps(uni)


@app.route("/store_morph", methods=["POST"])
def store_morph():
    """takes new morph given by user and stores it """
    if request.method == "POST":
        uni = json.loads(request.form["uni"])
        dbid = request.form["dbid"]
        # do something
        return json.dumps(uni)


@app.route("/get_csv", methods=["POST"])
def get_csv():
    """get csv from uni"""
    result = []
    if request.method == "POST":
        uni = json.loads(request.form["uni"], object_pairs_hook=OrderedDict)
        all_mass = json.loads(request.form["mass"], object_pairs_hook=OrderedDict)
        all_definite = json.loads(request.form["definite"], object_pairs_hook=OrderedDict)
        all_chunks = json.loads(request.form["chunking_output"], object_pairs_hook=OrderedDict)
        for index, each_sent in enumerate(uni):
            result.append(get_csv_from_uni(each_sent, all_mass[index], all_definite[index], all_chunks[index]))
    return json.dumps(result)


@app.route("/get_nouns", methods=["POST"])
def get_nouns():
    user_text = request.form["hin_input"].encode("utf-8")
    valid_nouns = get_all_valid_nouns(user_text)
    return json.dumps(valid_nouns)


if __name__ == "__main__":
    app.debug = True
    app.run("0.0.0.0", port=9004)

