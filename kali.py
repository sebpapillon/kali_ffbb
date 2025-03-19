#!/bin/python
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import requests
import re
import sqlite3
import json
from datetime import date
import datetime
import threading
import sys

class ffbb:
    def init(self,thr):
        print("init ffbb")
        con=sqlite3.connect("kalisport.sqlite")
        cur=con.cursor()
        cur.execute("delete from ffbb")
        con.commit()
        con.close()
        
        for champ in self.get_champs():
            thr.append(threading.Thread(target=self.get_data_from_champ, args=(champ,)))
        
        
    def get_champs(self):
        champs=[]
        url="https://resultats.ffbb.com/championnat/equipe/bcd36d30da.html"
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text,"lxml")
        mychamps = soup.find_all("option")
        
        for champ in mychamps:
            chp=[]
            chp.append(re.search("(C.*)(<.*)",str(champ))[1])
            chp.append(champ['value'])
            champs.append(chp)
            
        return(champs)    
            
    def get_data_from_champ(self,chp):
        con=sqlite3.connect("kalisport.sqlite")
        cur=con.cursor()
        response = requests.get("https://resultats.ffbb.com/championnat/equipe/division/"+chp[1]+".html")
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text,"lxml")
        mydivs = soup.find_all("tr", {"class": ["altern-2", "no-altern-2"]})
        for champ in mydivs:
            datas = BeautifulSoup(str(champ),"lxml")
            data = datas.find_all("td")
            d=[]
            if(len(data)>2):
                d.append(re.search("C.*: (.*)",chp[0])[1])
                d.append(re.search("..\/..\/....",str(data[1]))[0])
                d.append(re.search("..:..",str(data[2]))[0])
                d.append(re.search("(.*\">)(.*)(<\/a><\/td>)",str(data[3]))[2])    
                if(len(data)==7):
                    d.append(re.search("(.*\">)(.*)(<\/a><\/td>)",str(data[4]))[2])
                    d.append(re.search("<td align=\"center\">(.*)<\/td>",str(data[5]))[1])
                if(len(data)==9):
                    d.append(re.search("(.*\">)(.*)(<\/a><\/td>)",str(data[5]))[2])
                    d.append(re.search("<td align=\"center\">(.*)<\/td>",str(data[7]))[1])
                cur.execute("insert into ffbb values (?,?,?,?,?,?)",d)
        con.commit()
        con.close()        

class kali:
    def init(self,thr):
        print("init kali")
        self.teams_href=[]
        con=sqlite3.connect("kalisport.sqlite")
        cur=con.cursor()
        cur.execute("delete from kali")
        con.commit()
        con.close()
        self.get_teams()
        for href in self.teams_href:
            thr.append(threading.Thread(target=self.get_matchs_from_href, args=(href,)))

    
    def results(self,delta):
        print("\n----------\n results "+str(delta)+"\n----------")
        con=sqlite3.connect("kalisport.sqlite")
        cur=con.cursor()
        cur.execute("select * from ffbb")
        kali=cur.fetchall()
        current_date=datetime.datetime.now().isocalendar()
        current_week=str(current_date[1]) if len(str(current_date[1]))==2 else "0"+str(current_date[1])
        current_week=int(str(current_date[0])+str(current_week))
        for match in kali:
            date_of_match=datetime.datetime.strptime(match[1], "%d/%m/%Y").isocalendar()
            week_of_match=str(date_of_match[1]) if len(str(date_of_match[1]))==2 else "0"+str(date_of_match[1])
            week_of_match=int(str(date_of_match[0])+str(week_of_match))
            
            if week_of_match==current_week+delta:
                print()
                cur.execute("select team,ffbb from compet where compet=?",(match[0],))
                team=cur.fetchone()[0]
                local=team if "NEUVIL" in match[3] else match[3]
                away=team if "NEUVIL" in match[4] else match[4]
                result=re.search("(\d*) - (\d*)",match[5])
                if result:
                    nba_wins = True if (((result[1] > result[2]) and ("NEUVIL" in match[3])) or ((result[1] < result[2]) and ("NEUVIL" in match[4]))) else False
                    if nba_wins:
                        print("Victoire des ",end="")
                    else:
                        print("Défaite des ",end="")
                    if "NEUVIL" in match[3]:
                        print(local+" contre "+away)
                    else:
                        print(away+" contre "+local)
                    print(match[5])
                else:
                    print("pas de résultat pour les "+team)    
    
    def next_week(self):
        semaine=["","lundi","mardi","mercredi","jeudi","vendredi","samedi","dimanche"]
        print("\n----------\n next\n----------")
        con=sqlite3.connect("kalisport.sqlite")
        cur=con.cursor()
        cur.execute("select * from kali")
        kali=cur.fetchall()
        current_week=datetime.datetime.now().isocalendar()[1]
        for match in kali:
            isodate=datetime.datetime.strptime(match[1], "%d/%m/%Y").isocalendar()
            week_of_match=isodate[1]
            day_of_match=isodate[2]
            if week_of_match==current_week:
                print(match[0])
                cur.execute("select team,ffbb from compet where compet=?",(match[0],))
                team=cur.fetchone()[0]
                local=team if "NEUVIL" in match[3] else match[3]
                away=team if "NEUVIL" in match[4] else match[4]
                if "NEUVIL" in match[3]:
                    print(local+" contre "+away+"\nà domicile")
                else:
                    print(away+" contre "+local+"\nà l'extérieur")
                print("le "+semaine[day_of_match]+" "+match[1]+" à "+match[2]+"\n")
        
    def get_teams(self):
        response = requests.get("https://neuvillebasket.fr/equipes",timeout=2)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text,"lxml")
        
        for ul in soup.find("div",{"id": "content"}):
            soup = BeautifulSoup(str(ul),"lxml")
            for a in soup.find_all("a"):
                if "title" in a.attrs:
                    self.teams_href.append(a.attrs["href"])
        
    def get_matchs_from_href(self,href):
        con=sqlite3.connect("kalisport.sqlite")
        cur=con.cursor()
        response = requests.get(href)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text,"lxml")
        
        c = soup.find("div",{"class":"bloc-data-equipe"})
        r = re.search("(<\/div>)([\S\s]*)(<\/div>)",str(c))
        compet = r.group(2).strip()
        
        for jason in soup.find_all("script",{"type":"application/ld+json"}):
            j=json.loads(str(jason.contents[0]))
            if "@type" in j.keys():
                d=re.search("([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2})",j["startDate"])
                r=[]
                r.append(compet)
                r.append(d[3]+"/"+d[2]+"/"+d[1])
                x = datetime.datetime(int(d[1]), int(d[2]), int(d[3]))
                r.append(d[4]+":"+d[5])
                if(self.is_nba_team(j["homeTeam"]["name"])):
                    r.append(self.get_ffbb_team_name(j["homeTeam"]["name"]))
                else:
                    r.append(j["homeTeam"]["name"])
                if(self.is_nba_team(j["awayTeam"]["name"])):
                    r.append(self.get_ffbb_team_name(j["awayTeam"]["name"]))
                else:
                    r.append(j["awayTeam"]["name"])
                if(datetime.datetime.now()<x):
                    cur.execute("insert into kali values (?,?,?,?,?)",r)
        con.commit()
        con.close()
        
    def get_ffbb_team_name(self,team):
        con=sqlite3.connect("kalisport.sqlite")
        cur=con.cursor()
        cur.execute("select ffbb from compet where team=?",(team,))
        row=cur.fetchone()
        return row[0]
        
    def is_nba_team(self,team):
        con=sqlite3.connect("kalisport.sqlite")
        cur=con.cursor()
        cur.execute("select count(*) from compet where team=?",(team,))
        row=cur.fetchone()
        if row[0] > 0:
            return True

def compare():
    con=sqlite3.connect("kalisport.sqlite")
    cur=con.cursor()
    cur.execute("select * from kali")
    kali=cur.fetchall()
    for match_kali in kali:
        cur.execute("select * from ffbb where compet=? and date=? and heure=? and domicile=? and visiteur=?",(match_kali[0],match_kali[1],match_kali[2],match_kali[3],match_kali[4],))
        match_ffbb=cur.fetchone()
        if not match_ffbb:
            print("--------")
            print("kali")
            print(match_kali)
            cur.execute("select * from ffbb where compet=? and domicile=? and visiteur=?",(match_kali[0],match_kali[3],match_kali[4],))
            match_ffbb=cur.fetchone()
            print("ffbb")
            print(match_ffbb)


def main():
    thr=[]
    f=ffbb()
    f.init(thr)
    
    k=kali()
    k.init(thr)
    
    for t in thr:
        t.start()
    for t in thr:
        t.join()
    
    k.results(-1)
    k.results(0)
    k.next_week()
    
    compare()

if __name__ == "__main__":
    main()
