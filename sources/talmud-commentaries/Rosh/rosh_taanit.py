# -*- coding: utf8 -*-
__author__ = 'eliav'
import collections
import os
import re
import csv
import sys
import json
import urllib2
from fuzzywuzzy import fuzz
import korban_netanel as nosekelim
from sefaria.model import *
#import tiferet_shmuel
sys.path.insert(1, '../../genuzot')
import helperFunctions as Helper
import hebrew
masechet = str(sys.argv[1])
if "_" in masechet:
    mas = re.sub("_", " ", masechet)
else:
    mas = masechet
masechet_he = Index().load({"title":mas}).get_title("he")
links = []
log = open('../../../Match Logs/Talmud/{}/rosh_log_{}.txt'.format(masechet,masechet), 'w')
longlog = open('../../../Match Logs/Talmud/{}/rosh_longlog_{}.txt'.format(masechet,masechet), 'w')
misparim = {'ראשון':1, 'שני':2, 'שלישי':3, 'רביעי':4, 'חמישי':5, 'שישי':6,'ששי':6, 'שביעי':7,'שמיני':8, 'תשיעי':9,'עשירי':10, 'אחד עשר':11}


def test_depth(text):
    a= re.findall(ur'@22(.{1,2})',text)
    last_sif = 0
    if len([x for x, y in collections.Counter(a).items() if y > 1]) > 0:
           return False
    return True


def get_shas():
    url_index = 'http://' + Helper.server + '/api/index/' + '%s' % masechet
    response_index = urllib2.urlopen(url_index)
    resp_index = response_index.read()
    last_daf = json.loads(resp_index)["length"]
    amud = "a" if last_daf % 2 == 0 else "b"
    daf = (last_daf / 2) + 1
    last_daf =  str(daf) + amud
    url = 'http://' + Helper.server + '/api/texts/' + '%s' % masechet + '.2a' + '-' + last_daf
    response = urllib2.urlopen(url)
    resp = response.read()
    shas = json.loads(resp)["he"]
    return shas


def matching(tagged, shas, i, j, index, daf, amud, strings=15, ratio = False):
    short = 0
    fuzzed =0
    if len(tagged) >= 15:
                    string = " ".join(tagged[0:strings])
    else:
        short += 1
        string = " ".join(tagged[0:len(tagged)-1])
    print string, daf, amud
    string = re.sub(ur'[\[\]\*#@[0-9]', "", string)
    found = 0
    for counter, line in enumerate(shas[index], start = 1):
        if fuzz.partial_ratio(string, line) > 80:
            bingo = counter
            if ratio is True:
                if fuzz.ratio(string, line) > 60:
                    fuzzed +=1
                    found +=1
                    #print "ratio", string, daf, strings, fuzz.ratio(string, line)
            else:
                found +=1
    #if fuzzed > 0:
        #print "fuzzed", fuzzed
    if found < 1 and strings != 0:
        strings -= 1
        matching(tagged, shas, i, j, index, daf, amud, strings)
    elif found > 1:
        if ratio is True:
            error = "found too much, " + str(found) + "," + "on," + str(daf)+ "," + amud + "," + " ".join(tagged[0:15]).encode('utf-8') +"\n"
            log.write(error)
        else:
            matching(tagged, shas, i, j, index, daf,amud,strings, True)

    elif found == 1:
        roash = "Rosh on %s." % masechet + str(i+1) + "." + str(j+1)
        talmud = "%s." % masechet + str(daf) + amud + "." + str(bingo)
        links.append(link(talmud, roash))
        succes=  "found" + ", " + string.encode('utf-8') + str(daf)+ " ," + amud + "," + str(strings) +"\n"
        print succes
        log.write(succes)
    elif strings == 0:
        error = "did not find on daf,"+ str(daf) +"," + amud + "," + " ".join(tagged[0:15]).encode('utf-8') +"\n"
        log.write(error)
        print error


def matching1(tagged, shas, i, j, k, index, daf, amud, strings=15, ratio = False):
    short = 0
    fuzzed =0
    original =tagged
    if len(tagged) >= 15:
                    string = " ".join(tagged[0:strings])
    else:
        short += 1
        string = " ".join(tagged[0:len(tagged)-1])
    #print string, daf, amud
    string = re.sub(ur'[\[\]\*#@[0-9]', "", string)
    found = 0
    for counter, line in enumerate(shas[index], start = 1):
        if fuzz.partial_ratio(string, line) > 80:
            bingo = counter
            if ratio is True:
                if fuzz.ratio(string, line) > 60:
                    fuzzed +=1
                    found +=1
                    #print "ratio", string, daf, strings, fuzz.ratio(string, line)
            else:
                found +=1
    #if fuzzed > 0:
        #print "fuzzed", fuzzed
    if found < 1 and strings != 0:
        strings -= 1
        matching1(tagged, shas, i, j,k,  index, daf, amud, strings)
        return
    elif found > 1:
        if ratio is True:
            error = "found too much, " + str(found) + "," + "on," + str(daf) + amud + "," + " ".join(tagged[0:15]).encode('utf-8') +"for roash" + str(k+1)+"."+ str(i+1) + "." + str(j+1) + "\n"
            log.write(error)
            longlog.write(error)
        else:
            matching1(tagged, shas, i, j, k,  index, daf,amud,strings, True)
            return

    elif found == 1:
        roash = "Rosh on %s." % masechet + str(k+1)+"."+ str(i+1) + "." + str(j+1)
        talmud = "%s." % masechet + str(daf) + amud + "." + str(bingo)
        links.append(link(talmud, roash))
        print roash, talmud
        succes=  "found" + ", " + string.encode('utf-8') + str(daf) + amud + "," + str(strings) + "for roash" + str(k+1)+"."+ str(i+1) + "." + str(j+1) + "\n"
        #print succes
        longlog.write(succes)
    elif strings == 0:
        if isinstance(amud, str):
            error = "did not find on daf,"+ str(daf) + amud + "," + " ".join(original[0:15]).encode('utf-8') +"for roash" + str(k+1)+"."+ str(i+1) + "." + str(j+1) + "\n"
            log.write(error)
            longlog.write(error)
      #  print error


def search(text, shas):
    for i, seif in enumerate(text):
        for j, siman in enumerate(seif):
            if siman.endswith(ur'5 '):
               print "yes"
            linked = re.finditer(ur'@44(.*?)@(?:55|11)(.*?)(?=(@44|$))', siman)
            if '@44' not in siman[0:10] and len(siman) > 8:
                start = re.sub('([\[\*\]]|@..|#)',"",siman)
                start_of_siman = re.split(" ", start)
       #         print "start of siman", start_of_siman[0]
                if 'index' in locals():
                 #   print "matching", index
                    if index > len(shas):
                        break

                    matching(start_of_siman, shas, i, j, index, daf, amud)
            for match in linked:
                lookfor = match.group(2)
                tagged = re.split(" ", lookfor.strip())
                daf_amud = re.split(ur' ', match.group(1).strip())
                daf = re.sub(ur'[^א-ת]',"",daf_amud[1])
                daf =  hebrew.heb_string_to_int(daf)
                if daf > len(shas) or len(daf_amud) <= 2:
         #           print "daf", daf, "is longer than needs to"
                    break
                else:
                    print daf_amud[0]
                    amud = daf_amud[2]
               # print "amud", amud
                index = ((daf-2)*2)+1
                #if index > len(shas):
                #    break
                if amud[2].strip() == ur'א':
                    amud = 'a'
                    index = index - 1
                else:
                    amud = 'b'
                #print "daf", daf, amud
                if index >= len(shas):
          #          print "short", daf, amud, lookfor
                    pass
                    #break
                else:
           #         print "else"
                    matching(tagged, shas, i, j, index, daf, amud)


def search1(text, shas):
    for k, perek in enumerate(text):
        for i, seif in enumerate(perek):
            for j, siman in enumerate(seif):
                if siman.endswith(ur'5 '):
                    print "yes"
                linked = re.finditer(ur'@44(.*?)@(?:55|11)(.*?)(?=(@44|$))', siman)
                if '@44' not in siman[0:10] and len(siman) > 8:
                    start = re.sub('([\[\*\]]|@..|#)',"",siman)
                    start_of_siman = re.split(" ", start)
                    if 'index' in locals():
                        if index >= len(shas):
                            break
            #            print "line number: 203", daf, amud
                        matching1(start_of_siman, shas, i, j, k, index, daf, amud)
                for match in linked:
                    lookfor = match.group(2)
                   # print "lookfor is", lookfor
                    tagged = re.split(" ", lookfor.strip())
                    if len(tagged)<=1:
                        break
                    daf_amud = re.split(ur' ', match.group(1).strip())
                    #print daf_amud[0]
                    if len(daf_amud)  >=2:
                        daf = re.sub(ur'[^א-ת]',"",daf_amud[1])
                    else:
                     #   print "no  daf "
                        break
             #       print daf
                    daf =  hebrew.heb_string_to_int(daf)
                    if daf > len(shas) or len(daf_amud) < 3:
                        break
                    else:
                      #  print len(daf_amud)
                       # print  daf_amud
                        amud = daf_amud[2]
                    index = ((daf-2)*2)+1
                    #if index > len(shas):
                    #    break
                    if len(amud) < 3:
                        #print "short amud"
                        break
                    else:
                        #print amud
                        if amud[2].strip() == ur'א':
                            amud = 'a'
                            index = index - 1
                        else:
                            amud = 'b'
                        #print daf, amud
                        if index >= len(shas):
                            #print "short", daf, amud, lookfor
                            #return
                            pass
                        else:
                            #print "else"
                        #    print "tagged is", tagged
                            matching1(tagged, shas, i, j, k, index, daf, amud)


def link(talmud, roash):
    return {
            "refs": [
               talmud,
                roash ],
            "type": "commentary",
            "auto": True,
            "generated_by": "Rosh_%s" % masechet,
            }


def open_file():
    with open("../source/Rosh_on_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
      #  print file_text.decode('utf-8','ignore')
        ucd_text = unicode(file_text, 'utf-8', errors='ignore').strip()
        print masechet_he
        return ucd_text


def book_record():
    structs = {"nodes": [] }
    with open('../source/rosh_taanit_names .csv', 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',' )
        for row in reader:
            eng_title = row[0]
            heb_title = row[3]
            frm = row[1]
            to = row[2]
            wholeref = "Rosh on Taanit" + "." + str(frm) + "-" + str(to)
            structs["nodes"].append({
                "titles":  [{
                            "lang": "en",
                            "text": eng_title,
                            "primary": True

                            },
                            {
                            "lang": "he",
                            "text": heb_title,
                            "primary": True
                            }],
                "nodeType": "ArrayMapNode",
                "depth": 0,
                "addressTypes": [],
                "sectionNames": [],
                "wholeRef": wholeref,
                "includeSections": "true"
            })
    a = u" פסקי הראש על " + masechet_he
    return {
    "title" : "Rosh on %s" % masechet,
     "categories": [ "Commentary2",
        "Talmud","Rosh"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Rosh on %s" % masechet,
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : a,
                "primary" : True
            }
        ],
        "nodeType" : "JaggedArrayNode",
        "depth" : 2,
        "sectionNames" : [
            "Halacha",
            "Siman"
        ],
        "addressTypes" : [
           "Integer",
            "Integer"
        ],
        "key" : "Rosh on %s" % masechet
    },
         "alt_structs": {"Chapter": structs},
        "default_struct": "Chapter"
	}


def book_record1():
    a = u" פסקי הראש על " + masechet_he
    return {
    "title" : "Rosh on %s" % mas,
    "categories": [ "Commentary2",
        "Talmud","Rosh"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Rosh on %s" % mas,
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : a,
                "primary" : True
            }
        ],
        "nodeType" : "JaggedArrayNode",
        "depth" : 3,
        "sectionNames" : [
            "Perek",
            "Halacha",
            "Siman"
        ],
        "addressTypes" : [
            "Integer",
           "Integer",
            "Integer"
        ],
        "key" : "Rosh on %s" % mas
    }
    }


def parse(text):
    if os.path.isfile('../source/Korban_Netanel_on_{}.txt'.format(masechet)) or os.path.isfile('../source/Pilpula_Charifta_on_{}.txt'.format(masechet)):
       # print "has korban netanel 2"
        nose_kelim = nosekelim.open_file()
        fixed = nosekelim.parse(nose_kelim)
        links_netanel = []
        netanel = 0
    rosh = []
    a = re.split(ur'@22([^@]*)', text)
    for seif, cont in zip(a[1::2], a[2::2]):
        si = []
        korban =[]
        if ur'[*]' in seif and (os.path.isfile('../source/Korban_Netanel_on_{}.txt'.format(masechet) or os.path.isfile('../source/PilPula_Charifta_on_{}.txt'.format(masechet))) and netanel <= len(fixed)):
            if os.path.isfile('../source/Korban_Netanel_on_{}.txt'.format(masechet)):
                commentator = "Korban Netanel on "
            if os.path.isfile('../source/PilPula_Charifta_on_{}.txt'.format(masechet)):
                commentator = "Pilpula Charifta on "
            korban.append(fixed[netanel])
            #print len(links_netanel)
            roash = "Rosh on %s." % masechet + str(len(links_netanel)+1) + ".1"
            netanelink = commentator + masechet +"."+ str(len(links_netanel)+1) + ".1"
            links.append(link(netanelink, roash))
            netanel += 1
            #print "netanel one seif", seif, netanel
            #print fixed[netanel]
        content = re.split('@66', cont)
        seif = re.sub(ur'[^א-ת]',"", seif)
        seif = hebrew.heb_string_to_int(seif.strip())
        for num, co in enumerate(content):
            if ur'[*]' in co:
                #print co
                a = re.findall('\[\*\](.{6})', co)
                for b in a:
                    if (os.path.isfile('../source/Korban_netanel_on_{}.txt'.format(masechet)) or os.path.isfile('../source/Pilpula_Charifta_on_{}.txt'.format(masechet))) and netanel < len(fixed):
                        if os.path.isfile('../source/Korban_netanel_on_{}.txt'.format(masechet)):
                            commentator = "Korban Netanel "
                        if os.path.isfile('../source/Pilpula_Charifta_on_{}.txt'.format(masechet)):
                            commentator = "Pilpula Charifta "
                        korban.append(fixed[netanel])
                        roash = "Rosh on %s." % masechet + str(len(links_netanel)+1) + "." + str(num+1)
                        netanelink = commentator + "on " +masechet + "." + str(len(links_netanel)+1)+ "."+ str(len(korban))
                        links.append(link(netanelink, roash))
                        netanel +=1
            si.append(co)
        if os.path.isfile('../source/Korban_Netanel_on_{}.txt'.format(masechet)) or os.path.isfile('../source/Pilpula_Charifta_on_{}.txt'.format(masechet)):
            links_netanel.append(korban)
#            if len(links_netanel[len(links_netanel)-1]) > 0:
#                print links_netanel[len(links_netanel)-1][len(links_netanel[len(links_netanel)-1])-1]
        rosh.append(si)

    #print "searching"
    search(rosh,get_shas(),)
    if os.path.isfile('../source/Korban_Netanel_on_{}.txt'.format(masechet)) or os.path.isfile('../source/Pilpula_Charifta_on_{}.txt'.format(masechet)):
        nosekelim.save_parsed_text(links_netanel, commentator)
        nosekelim.run_post_to_api(commentator)
    return rosh


def clean(text):
    rosh = []
    for i, seif in enumerate(text):
        si = []
        for j, siman in enumerate(seif):
            siman = re.sub('@44.*?@(?:55|11)',"",siman)
            siman = re.sub('([\[\*\]]|@..|#)',"",siman)
            #print siman
            si.append(siman)
        rosh.append(si)
    return rosh


def parse1(text):
    old_numeri = 0
    if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)) or os.path.isfile('source/Pilpula_Charifta_on_{}.txt'.format(masechet)):
        nose_kelim = nosekelim.open_file()
        fixed = nosekelim.parse(nose_kelim)
        links_netanel = []
        netanel = 0
    rosh = []
    chapters = re.split(ur'(?:@00|@99)([^@]*)', text)
    for chapter_num, chapter in zip(chapters[1::2], chapters[2::2]):
        mispar = chapter_num.strip().split(" ")[1]
        if mispar.encode('utf-8') in misparim.keys():
            mispar_numeri = misparim[mispar.encode('utf-8')]
            print mispar_numeri
            if mispar_numeri - old_numeri > 1:
               for i in range(1,mispar_numeri-old_numeri):
                    rosh.append([])
                    #print "length of rosh", len(rosh)
            old_numeri = mispar_numeri
        print mispar
        #if len(chapter)<=1:
         #   pass
        #else:
        perek = []
        a = re.split(ur'@22([^@]*)', chapter)
        for seif, cont in zip(a[1::2], a[2::2]):
            si = []
            korban =[]
            #print seif
            if ur'[*]' in seif and (os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)) or os.path.isfile('source/Pilpula_Charifta_on_{}.txt'.format(masechet))) and netanel < len(fixed):
               # print "hello", seif, netanel, len(fixed)
                if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)):
                    commentator = "Korban Netanel"
                if os.path.isfile('source/PilPula_Charifta_on_{}.txt'.format(masechet)):
                    commentator = "Pilpula Charifta"
                korban.append(fixed[netanel])
                roash = "Rosh on %s." % masechet  +str(len(rosh)+1) + "." + str(len(perek)+1) + ".1"
                netanelink = commentator + " on " +  masechet +"."+ str(len(links_netanel)+1) + ".1"
                #print roash, netanelink
                links.append(link(netanelink, roash))
                netanel += 1
            content = re.split('@66', cont)
            seif = re.sub(ur'[^א-ת]',"", seif)
            seif = hebrew.heb_string_to_int(seif.strip())
            for num, co in enumerate(content):
                a = re.findall('\[\*\]', co)
                for b in a:
                 #   print b, seif
                    if (os.path.isfile('source/Korban_netanel_on_{}.txt'.format(masechet)) or os.path.isfile('source/Pilpula_Charifta_on_{}.txt'.format(masechet))) and netanel < len(fixed):
                        if os.path.isfile('source/Korban_netanel_on_{}.txt'.format(masechet)):
                            commentator = "Korban Netanel "
                        if os.path.isfile('source/Pilpula_Charifta_on_{}.txt'.format(masechet)):
                            commentator = "Pilpula Charifta "
                        korban.append(fixed[netanel])
                        roash = "Rosh on %s." % masechet + str(len(rosh)+1) + "." + str(len(perek)+1) + "." + str(num+1)
                        netanelink = commentator + "on " + masechet + "." + str(len(links_netanel)+1)+ "."+ str(len(korban))
                        #print roash, netanelink
                        links.append(link(netanelink, roash))
                        netanel +=1
                si.append(co)
            if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)) or os.path.isfile('source/Pilpula_Charifta_on_{}.txt'.format(masechet)):
                links_netanel.append(korban)
            perek.append(si)
        if len(perek) is not 0:
            rosh.append(perek)
           # print len(rosh)
    search1(rosh,get_shas(),)
    if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)) or os.path.isfile('source/Pilpula_Charifta_on_{}.txt'.format(masechet)):
        nosekelim.save_parsed_text(links_netanel, commentator)
        nosekelim.run_post_to_api(commentator)
        pass
    #print rosh[1][0][0]
    return rosh


def clean1(text):
    rosh = []
    for k, perek in enumerate(text, start = 0):
        #if len(perek)<=1:
         #   pass
        #else:
        prakim =[]
        for i, seif in enumerate(perek):
            si = []
            for j, siman in enumerate(seif):
                siman = re.sub('@44.*?@(?:55|11)',"",siman)
                siman = re.sub('([\[\*\]]|@..|#|!|%|[\(\)]|0)',"",siman)
                #print siman
                si.append(siman)
            prakim.append(si)
        rosh.append(prakim)
   # print rosh[0][0][0]
    return rosh


def save_parsed_text(text):
    text_whole = {
        "title": 'Rosh on %s' % masechet,
        "versionTitle": "Vilna Edition",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": text,
        "digitizedBySefaria": True,
        "license": "Public Domain",
        "licenseVetted": True,
        "status": "locked",
    }
    #save
    Helper.mkdir_p("../preprocess_json/")
    with open("../preprocess_json/Rosh_on_%s.json" % masechet, 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
   # Helper.createBookRecord(book_record())
    with open("../preprocess_json/Rosh_on_%s.json" % masechet, 'r') as filep:
        file_text = filep.read()
    Helper.postText("Rosh on %s" % masechet, file_text, False)


def link_tiferet_shmuel(parsed_text):
    shmuellinks = []
    count = 0
    file = tiferet_shmuel.open_file()
    parsed = tiferet_shmuel.parse(file)
    Helper.createBookRecord(tiferet_shmuel.book_record())
    tiferet_shmuel.save_parsed_text(parsed)
    tiferet_shmuel.run_post_to_api()
    for k, perek in enumerate(parsed_text):
        for i, seif in enumerate(perek):
            for j, siman in enumerate(seif):
                #if re.match('\(.\)', siman):
                 if ur'(*)' in siman:
                    #print ur"הגעתי לכאן!"
                    a = re.findall('\(\*\)', siman)
                    for b in a:
                        #print siman
                        count +=1
                        roash = "Rosh on %s." % masechet + str(k+1) + "." + str(i+1) + "." + str(j+1)
                        shmuel = "Tiferet Shmuel on " + masechet + "." + str(count)
                        shmuellinks.append(link(roash, shmuel))
                        #print count
                        #print roash, shmuel
    Helper.postLink(shmuellinks)


def maadaney_yom_tov(parsed_text):
    yomtovlinks = []
    count = 0
    file = tiferet_shmuel.open_file1()
    parsed = tiferet_shmuel.parse(file)
    Helper.createBookRecord(tiferet_shmuel.book_record(record = "yomtov"))
    tiferet_shmuel.save_parsed_text(parsed, record = "yomtov")
    tiferet_shmuel.run_post_to_api(record = "yomtov")
    for k, perek in enumerate(parsed_text):
        for i, seif in enumerate(perek):
            for j, siman in enumerate(seif):
                #print siman
                #if re.match('\(.\)', siman):
                if ur'[*]' in siman:
                    #print ur"הגעתי לכאן!"
                    a = re.findall('\[\*\]', siman)
                    for b in a:
                       # print siman
                        count +=1
                        roash = "Rosh on %s." % masechet + str(k+1) + "." + str(i+1) + "." + str(j+1)
                        shmuel = "Maadaney Yom Tov on " + masechet + "." + str(count)
                        yomtovlinks.append(link(roash, shmuel))
                        #print count
                        #print roash, shmuel
    #Helper.postLink(yomtovlinks)


def divrey_chamuot(parsed_text):
    chamudotlinks = []
    count = 0
    file = tiferet_shmuel.open_file(record = "chamudot")
    parsed = tiferet_shmuel.parse(file)
    Helper.createBookRecord(tiferet_shmuel.book_record(record = "chamudot"))
    tiferet_shmuel.save_parsed_text(parsed, record = "chamudot")
    tiferet_shmuel.run_post_to_api(record = "chamudot")
    for k, perek in enumerate(parsed_text):
        for i, seif in enumerate(perek):
            for j, siman in enumerate(seif):
                #if re.match('\(.\)', siman):
                 if ur'(*)' in siman:
                    print ur"הגעתי לכאן!"
                    a = re.findall('\(\*\)', siman)
                    for b in a:
                        print siman
                        count +=1
                        roash = "Rosh on %s." % masechet + str(k+1) + "." + str(i+1) + "." + str(j+1)
                        shmuel = "Divrey Chamudot on " + masechet + "." + str(count)
                        chamudotlinks.append(link(roash, shmuel))
                        print count
                        print roash, shmuel
    Helper.postLink(chamudotlinks)


def divrey_chamuot2(text):
    chamudotlinks = []
    count = 0
    file = tiferet_shmuel.open_file(record = "chamudot")
    parsed = tiferet_shmuel.parse(file)
    Helper.createBookRecord(tiferet_shmuel.book_record(record = "chamudot"))
    tiferet_shmuel.save_parsed_text(parsed, record = "chamudot")
    tiferet_shmuel.run_post_to_api(record = "chamudot")
    commentator = "Divrey Chamudot"
    rosh = []
    chapters = re.split(ur'(?:@00|@99)', text)
    for chapter_num, chapter in zip(chapters[1::2], chapters[2::2]):
        print chapter_num
        if len(chapter)<=1:
            pass
        else:
            perek = []
            a = re.split(ur'@22([^@]*)', chapter)
            for seif, cont in zip(a[1::2], a[2::2]):
                si = []
                print seif
                if ur'(*)' in seif:
                    print "hello1"
                if ur'(*)' in seif:

                    count+=1
                    roash = "Rosh on %s." % masechet  +str(len(rosh)+1) + "." + str(len(perek)+1) + ".1"
                    shmuel = commentator + " on " +  masechet +"."+ str(count)
                    chamudotlinks.append(link(roash, shmuel))
                    print roash, shmuel
                content = re.split('@66', cont)
                seif = re.sub(ur'[^א-ת]',"", seif)
                seif = hebrew.heb_string_to_int(seif.strip())
                for num, co in enumerate(content):
                    a = re.findall('\(\*\)', co)
                    for b in a:
                        count+=1
                        roash = "Rosh on %s." % masechet + str(len(rosh)+1) + "." + str(len(perek)+1) + "." + str(num+1)
                        shmuel = commentator + " on " + masechet + "." + str(count)
                        print roash, shmuel
                        chamudotlinks.append(link(shmuel, roash))
                    #print parsed[count]
                    si.append(co)
                perek.append(si)
            rosh.append(perek)

    Helper.postLink(chamudotlinks)


def yomtov2(text):
    chamudotlinks = []
    count = 0
    file = tiferet_shmuel.open_file(record = "yomtov")
    parsed = tiferet_shmuel.parse(file)
    Helper.createBookRecord(tiferet_shmuel.book_record(record = "yomtov"))
    tiferet_shmuel.save_parsed_text(parsed, record = "yomtov")
    tiferet_shmuel.run_post_to_api(record = "yomtov")
    commentator = "Maadaney Yom Tov"
    rosh = []
    chapters = re.split(ur'(?:@00|@99)', text)
    for chapter_num, chapter in enumerate(chapters):
        if len(chapter)<=1:
            pass
        else:
            perek = []
            a = re.split(ur'@22([^@]*)', chapter)
            for seif, cont in zip(a[1::2], a[2::2]):
                si = []
                print seif
                if ur'[*]' in seif:
                    print "hello1"
                if ur'[*]' in seif:

                    count+=1
                    roash = "Rosh on %s." % masechet  +str(len(rosh)+1) + "." + str(len(perek)+1) + ".1"
                    shmuel = commentator + " on " +  masechet +"."+ str(count)
                    chamudotlinks.append(link(roash, shmuel))
                    print roash, shmuel
                content = re.split('@66', cont)
                seif = re.sub(ur'[^א-ת]',"", seif)
                seif = hebrew.heb_string_to_int(seif.strip())
                for num, co in enumerate(content):
                    a = re.findall('\[\*\]', co)
                    for b in a:
                        count+=1
                        roash = "Rosh on %s." % masechet + str(len(rosh)+1) + "." + str(len(perek)+1) + "." + str(num+1)
                        shmuel = commentator + " on " + masechet + "." + str(count)
                        print roash, shmuel
                        chamudotlinks.append(link(shmuel, roash))
                    #print parsed[count]
                    si.append(co)
                perek.append(si)
            rosh.append(perek)

    Helper.postLink(chamudotlinks)

if __name__ == '__main__':
    if os.path.isfile('../source/Korban_Netanel_on_{}.txt'.format(masechet)):
       print "has Korban 1"
       Helper.createBookRecord(nosekelim.book_record(commentator="Korban Netanel"))
    if os.path.isfile('../source/Pilpula_Charifta_on_{}.txt'.format(masechet)):
       print "has Pilpula 1" + masechet
       Helper.createBookRecord(nosekelim.book_record(commentator="Pilpula Charifta"))
    text = open_file()
    print masechet
    if test_depth(text) == True:
        print "true"
        parsed_text = parse(text)
        upload_text = clean(parsed_text)
        Helper.createBookRecord(book_record())
    else:
        print "false"
        parsed_text = parse1(text)
        upload_text = clean1(parsed_text)
        Helper.createBookRecord(book_record1())
    print "cleaning"
    save_parsed_text(upload_text)
    run_post_to_api()
    #link_tiferet_shmuel(parsed_text)
    #yomtov2(text)
#    divrey_chamuot(parsed_text)
#    divrey_chamuot2(text)
    Helper.postLink(links)