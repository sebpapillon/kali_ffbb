#!/bin/python
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import requests
import re
import sqlite3

class ffbb:
    def get_champs():
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
            
    def get_data_from_champ(chp):
        print(chp)
        con=sqlite3.connect("kalisport.sqlite")
        cur=con.cursor()
        response = requests.get("https://resultats.ffbb.com/championnat/equipe/division/"+chp[1]+".html")
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text,"lxml")
        mydivs = soup.find_all("tr", {"class": "altern-2"})
        for champ in mydivs:
            datas = BeautifulSoup(str(champ),"lxml")
            data = datas.find_all("td")
            if(len(data)==7):
                d=[]
                d.append(chp[0])
                d.append(re.search("..\/..\/....",str(data[1]))[0])
                d.append(re.search("..:..",str(data[2]))[0])
                d.append(re.search("(.*\">)(.*)(<\/a><\/td>)",str(data[3]))[2])
                d.append(re.search("(.*\">)(.*)(<\/a><\/td>)",str(data[4]))[2])
                d.append(re.search("<td align=\"center\">(.*)<\/td>",str(data[5]))[1])
                cur.execute("insert into ffbb values (?,?,?,?,?,?)",d)
            if(len(data)==9):
                d=[]
                d.append(chp[0])
                d.append(re.search("..\/..\/....",str(data[1]))[0])
                d.append(re.search("..:..",str(data[2]))[0])
                d.append(re.search("(.*\">)(.*)(<\/a><\/td>)",str(data[3]))[2])
                d.append(re.search("(.*\">)(.*)(<\/a><\/td>)",str(data[5]))[2])
                d.append(re.search("<td align=\"center\">(.*)<\/td>",str(data[7]))[1])
                cur.execute("insert into ffbb values (?,?,?,?,?,?)",d)
        con.commit()
        con.close()        

class kali:
    def get_teams():
        response = requests.get("https://neuvillebasket.fr/equipes")
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text,"lxml")
        
        for ul in soup.find_all("ul"):
            print(ul)
            print("--------------------")
        
        #for li in soup.find_all("a",href=True):
            #print(li['href'])

def main():
    con=sqlite3.connect("kalisport.sqlite")
    cur=con.cursor()
    cur.execute("delete from ffbb")
    con.commit()
    con.close()
    
    #for champ in ffbb.get_champs():
        #ffbb.get_data_from_champ(champ)
        
    kali.get_teams()
    
if __name__ == "__main__":
    main()

