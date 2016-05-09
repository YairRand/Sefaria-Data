# -*- coding: utf-8 -*-
import pdb
import os
import sys
import re
import codecs
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from data_utilities.util import *
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *
import glob
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from data_utilities.sanity_checks import Tag
from sefaria.model import *



def check_mishna_order():
    #checked Mishnayot for Pereks being in order and within each perek each comment is in order
    #checked Boaz for Pereks being in order but DID NOT check that each comment within each perek is in order

    count=0
    for file in glob.glob(u"*.txt"):
     file = file.replace(u"\u200f", u"")
     if file.split(" ")[0] == u"יכין":
        count += 1
        in_order_caller(file, reg_exp_tag=u'@00\u05E4(?:"|\u05E8\u05E7 )?([\u05D0-\u05EA]{1}"?[\u05D0-\u05EA]?)')


def files_exist():
    """
    Looks through the directory to ensure all files that should be there do exist. It will also take care
    of naming conventions - i.e. it will mark a file as missing if it's named in an unpredictable manner.
    """

    # get a list of all tractates
    tractates = library.get_indexes_in_category('Mishnah')
    missing = codecs.open('missing_tractates.txt', 'w', 'utf-8')

    for tractate in tractates:
        ref = Ref(tractate)
        name = ref.he_book()
        terms = [u'משניות', u'יכין', u'בועז']

        for term in terms:
            file_name = u'{}.txt'.format(name.replace(u'משנה', term))
            if not os.path.isfile(file_name):
                missing.write(u'{}\n'.format(file_name))

    missing.close()


def compare_tags_to_comments(main_tag, commentary_tag, output):
    """
    Check that their the number of comments in a commentary match the number of tags in the main text.
    Outputs errors to a file. main_tag and commentary_tag should have members added called segment_tag
    which indicate the beginning of a new segment (chapter, verse, etc.).

    :param main_tag: A Tag object associated with the main text
    :param commentary_tag: Tag associated with the commentary.
    :param output: output file for results.
    """

    text_tags = main_tag.count_tags_by_segment(main_tag.segment_tag)
    comment_tags = commentary_tag.count_tags_by_segment(commentary_tag.segment_tag)

    perfect = True

    if len(text_tags) != len(comment_tags):
        output.write(u'Major alignment mismatch between {} and {}\n'.format(main_tag.name, commentary_tag.name))
        return

    for index, appearances in enumerate(text_tags):
        if appearances != comment_tags[index]:
            output.write(u'Tag mismatch {} and {} segment {}\n'.format(main_tag.name, commentary_tag.name, index+1))
            output.write(u'{} tags in {}; {} tags in {}\n'.format(appearances, main_tag.name,
                                                                  comment_tags[index], commentary_tag.name))
            perfect = False
    if perfect:
        output.write(u'Perfect alignment {} and {}\n'.format(main_tag.name, commentary_tag.name))


def compare_mishna_to_yachin(tractate_list):

    for tractate in tractate_list:
        r = Ref(tractate)
        name = r.he_book()
        m_name = name.replace(u'משנה', u'משניות')
        y_name = name.replace(u'משנה', u'יכין')
        output = codecs.open('results.txt', 'a', 'utf-8')
        try:
            m_file = codecs.open(u'{}.txt'.format(m_name), 'r', 'utf-8')
            y_file = codecs.open(u'{}.txt'.format(y_name), 'r', 'utf-8')
        except IOError:
            output.write(u'missing file {}\n'.format(name))
            continue

        m_tag = Tag(u'@44', m_file, name=m_name)
        y_tag = Tag(u'@11', y_file, name=y_name)

        seg_tag = u'@00(פרק|פ")'
        m_tag.segment_tag = seg_tag
        y_tag.segment_tag = seg_tag

        compare_tags_to_comments(m_tag, y_tag, output)

        m_file.close()
        y_file.close()
        output.close()


def get_perakim(type, tag, tag_reg):
    """
    :param type: identifies if this is Mishnah, yachin or boaz
    :param tag: the tag to identify the start of a new perek
    :param tag_reg: regular expression for the tag
    :return: a dictionary, keys are the tractate, values are a list of perakim
    """

    # get a list of all tractates
    tractates = library.get_indexes_in_category('Mishnah')
    results = {}

    for tractate in tractates:
        ref = Ref(tractate)
        name = ref.he_book()
        name = name.replace(u'משנה', type)
        file_name = u'{}.txt'.format(name)

        # if file doesn't exist, skip
        if not os.path.isfile(file_name):
            continue

        text_file = codecs.open(file_name, 'r', 'utf-8')

        data_tag = Tag(tag, text_file, tag_reg, name)
        results[name] = data_tag.grab_by_section()

        text_file.close()


def get_tags_by_perek(srika_tag, segment_regex, capture_group=0):
    """
    Create an array of arrays, with outer arrays corresponding to chapters and inner arrays containing the
    captures of srika_tag in order.
    :param srika_tag: A Tag object
    :param segment_regex: used to find the beginning of each segment
    :return: 2D array
    """

    # set tag file to the beginning of the first segment
    srika_tag.file.seek(0)
    srika_tag.eof = False
    srika_tag.skip_to_next_segment(segment_regex)
    captures_by_segment = []

    while True:
        captures_by_segment.append(srika_tag.grab_by_section(segment_regex, capture_group))

        if srika_tag.eof:
            break

    return captures_by_segment


def he_tags_in_order(captures, seg_name, output_file):
    """
    Checks if tags properly increment by 1
    :param captures: An array of captures to be analyzed by function
    :param seg_name: Name of segment. Will be displayed in the output_file/
    :param output_file: File to output results
    :return: True if tags in order, False otherwise.
    """

    previous = getGematria(captures[0])
    in_order = True

    for index, current in enumerate(captures):

        # do nothing for first index
        if index == 0:
            previous = getGematria(current)
            continue

        else:
            if getGematria(current) - previous != 1:
                output_file.write(u'{} goes from {} to {}\n'.format(seg_name, previous, current))
                in_order = False
    return in_order


