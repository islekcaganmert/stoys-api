from datetime import datetime

import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}
path = lambda p: 'https://login.stoys.co' + p


class STOYS:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.id = 0
        self.session = requests.session()
        if not self.refresh_token():
            for i in self.__dict__:
                self.__dict__[i] = None

    def refresh_token(self) -> bool:
        r = self.session.post(path('/auth/signin'), data={
            'username': self.username, 'password': self.password
        }, allow_redirects=False, headers=headers)
        if r.status_code == 302:
            bs = BeautifulSoup(self.session.get(path(r.headers['Location'])).content.decode(), 'html.parser')
            dropdown = str(bs.find_all(attrs={"aria-labelledby": "user-options"})[0])
            self.id = int(dropdown.split('/corporate/usersettings/index/id/')[1].split('"')[0])
            return True
        else:
            return False

    def get_user_info(self):
        r1 = self.session.get(path(f'/corporate/usersettings/index/id/{self.id}'))
        r2 = self.session.get(path(f'/academic/studentdevelopment/index/id/{self.id}'))
        bs = BeautifulSoup(r1.content.decode(), 'html.parser')
        d = {'username': self.username}
        for i in [
            ['tckn', 'TC_KIMLIK_NO'],
            ['name', 'ADI'],
            ['surname', 'SOYADI'],
            ['birthday', 'DOGUM_TARIHI'],
            ['role', 'ROL_ADI'],
            ['email', 'EPOSTA']
        ]:
            try:
                d.update({i[0]: bs.find_all(attrs={'name': i[1]})[0].get('value')})
            except IndexError:
                d.update({i[0]: None})
        for i in [
            ['school_number', 'School Number'],
            ['level', 'Level'],
            ['branch', 'Branch'],
            ['grade', 'Grade'],
            ['parent', 'Name and Surname']
        ]:
            try:
                d.update({i[0]: r2.content.decode().split(i[1])[1].split('bold">')[1].split('</')[0]})
            except IndexError:
                d.update({i[0]: None})
        return d

    def lms(self):
        l = []
        r = self.session.get(path('/lms/student/index'))
        if r.status_code == 200:
            bs = BeautifulSoup(r.content.decode(), 'html.parser')
            for i in bs.find_all('li'):
                if i.get('class') and len(i.get('class')) == 1:
                    if i.get('class')[0] in ['homework', 'weekcontent', 'book', 'announcement']:
                        l.append({
                            'type': i.get('class')[0],
                            'title': i.find_all('h4')[0].text,
                            'deadline': datetime.strptime(
                                i.find_all(attrs={'class': 'dark-text'})[0].text.split(' ')[-2],
                                '%d.%m.%Y'
                            ) if i.get('class')[0] == 'homework' else None,
                            'text': i.find_all(attrs={'class': 'dark-text'})[-1].text,
                            'added_by': (
                                i.find_all(attrs={'class': 'action-bar'})[0].text.split(' .')[0].split(' by ')[1]
                                if ' . ' in i.find_all(attrs={'class': 'action-bar'})[0].text else
                                i.find_all(attrs={'class': 'action-bar'})[0].text.split('\n  ')[1].split(' tarafından eklendi.')[0]
                            )
                        })
        return l

    def resources(self):
        r1 = self.session.get(path('/cms/lessonresources/index'))
        bs = BeautifulSoup(r1.content.decode(), 'html.parser')
        idlist = []
        for i in bs.find_all('select', attrs={'name': 'DERS_ID[]'})[0].find_all('option'):
            idlist.append(i.get('value'))
        r2 = self.session.post(
            path('/cms/lessonresources/fetchresult'),
            headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            },
            data=(
                '&'.join([f'DERS_ID[]={i}' for i in idlist]) +
                '&COLS[]=DERS_ADI&COLS[]=BASLIK&COLS[]=KAYNAK_TURU_TANIM&COLS[]=DURUM_TANIM&COLS[]=DUZEY_ID_LISTESI&COLS[]=OLUSTURMA_TARIHI'
            )
        )
        d = r2.json()['data']
        r = []
        for i in d:
            r.append({
                'title': i['BASLIK'],
                'lesson': i['DERS_ADI'],
                'filename': i['DOSYA_ADI'],
                'link': i['DOSYA_BAGLANTISI'].split('href=')[1].split('>')[0],
                'status': i['DURUM_TANIM'] == 'AKTİF',
                'level': i['DUZEY_ID_LISTESI'],
                'id': int(i['ID']),
                'date_created': datetime.strptime(
                    i['OLUSTURMA_TARIHI'],
                    '%d.%m.%Y'
                )
            })
        return r
