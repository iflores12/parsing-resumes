import argparse
import csv
import functools
import glob
import os
import re
import sys
import docx

import pandas as pd
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from io import StringIO

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_folder', required=True)
    parser.add_argument('--output_name', required=True)

    args = parser.parse_args()

    resume = compile_resumes(args.input_folder)
    print('FUCK')
    print(resume.head())
    resume.to_csv(args.output_name, quoting=csv.QUOTE_ALL, encoding='utf-8')

def pdf_to_text(pdf_path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 2
    caching = True
    pagenos = set()

    p_open = open(pdf_path, 'rb')

    for page in PDFPage.get_pages(p_open, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
        interpreter.process_page(page)

    p_open.close()
    device.close()

    pdf_text = retstr.getvalue()
    retstr.close()

    full_text = pdf_text.replace("\r", "\n")
    full_text = full_text.replace("\t", " ")
    full_text = full_text.replace("\n", " ")
    full_text = re.sub(r"\(cid:\d{0,2}\)", " ", full_text)

    return full_text.encode('utf-8', errors='ignore')

def doc_to_text(doc_path):
    doc = docx.Document(doc_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def phone(string):
    s = string.decode('utf-8')
    result = re.search('\(?(\d){3,3}\)?[\s\-\.]?(\d){3,3}[\-\.](\d){4,4}', s)
    if result is None:
        return None
    else:
        return result.group()

def email(string):
    s = string.decode('utf-8')
    result = re.search('[\w\.-]+@[\w\.-]+', s)
    if result is None:
        return None
    else:
        return result.group()

def address(string):
    s = string.decode('utf-8')
    result = re.search('\d{1,4}( \w+){1,5} (.*) ( \w+){1,5} (AZ|CA|CO|NH) [0-9]{5}(-[0-9]{4})?', s)
    if result is None:
        return None
    else:
        return result.group()


def name(string):
    result = re.search('[\/].*[$\/]', string)
    if result is None:
        return None
    else:
        return result.group()

def university(string):
    s = string.decode('utf-8')
    result = re.search('(\w+) ?(\w+) (University)', s)
    if result is None:
        result = re.search('(\w+) ?(\w+) (College)', s)
    if result is None:
        result = re.search('(University) ?(\w+) (\w+)', s)
    if result is None:
        result = re.search('(College) ?(\w+) (\w+)', s)
    if result is None:
        return None
    else:
        return result.group()

def zip1(string):
    s = string.decode('utf-8')
    result = re.search('([0-9]{5})', s)
    if result is None:
        return None
    else:
        return result.group()

def majors(string):
    s = string.decode('utf-8')
    s = s.split()
    s = [x.upper() for x in s]
    s = set(s)
    major = pd.read_csv('majors.csv')
    x = major['Major'].tolist()
    x = set(x)
    return s&x

def compile_resumes(path):
    pdf_list = []
    doc_list = []

    for root, subdirs, files in os.walk(path):
        for filename in files:
            p_glob = os.path.join(root, '*Resume*.pdf')
            pdf_list.append(glob.glob(p_glob))

            d_glob = os.path.join(root, '*Resume*.docx')
            doc_list.append(glob.glob(d_glob))

    new_pdf = [i for i in pdf_list if i]
    new_doc = [i for i in doc_list if i]

    all_resumes = pd.DataFrame()

    all_resumes['file_path_pdf'] = [new_pdf[x][0] for x in range(len(new_pdf))]
    #all_resumes['file_path_doc'] = [new_doc[x][0] for x in range(len(new_doc))]
    all_resumes['raw_text'] = all_resumes['file_path_pdf'].apply(pdf_to_text)
    all_resumes['name'] = all_resumes["file_path_pdf"].apply(name)
    all_resumes['phone'] = all_resumes["raw_text"].apply(phone)
    all_resumes['email'] = all_resumes["raw_text"].apply(email)
    all_resumes['university'] = all_resumes["raw_text"].apply(university)
    all_resumes['major'] = all_resumes["raw_text"].apply(majors)
    all_resumes['address'] = all_resumes["raw_text"].apply(address)
    all_resumes['zip'] = all_resumes["raw_text"].apply(zip1)

    return all_resumes


if __name__ == '__main__':
    main()
