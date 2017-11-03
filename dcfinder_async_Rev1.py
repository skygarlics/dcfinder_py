import os
import re
from bs4 import BeautifulSoup
import requests
import asyncio


search_types = {"전체": "search_all",
                "제목": "search_subject",
                "내용": "search_memo",
                "글쓴이": "search_name",
                "제목+내용": "search_subject_memo"}

검색타입 = search_types["전체"]
갤러리 = "rhythmgame"
키워드 = "로리"
깊이 = 10


def _clear():
    os.system('cls')


class DCFinder():
    base_url = "http://gall.dcinside.com"
    searchpos_regex = re.compile("search_pos=-(\d*)")
    page_regex = re.compile("page=(\d*)")

    async def findAsync(self, gallery_id, keyword, search_type, search_pos=0, search_depth=-1):
        """
        find & print list of articles
        """
        if not search_pos:
            board_url = self.base_url + "/board/lists/?id={gall_id}".format(gall_id=gallery_id)
            search_query = "&s_type={s_type}&s_keyword={s_keyword}".format(s_type=search_type, s_keyword=keyword)
            resp = requests.get(board_url + search_query)
            parser = BeautifulSoup(resp.text, "html.parser")
            next_search_url = parser.find("div", {"id": "dgn_btn_paging"}).find_all("a")[-1].get("href")
            search_pos = int(self.searchpos_regex.search(next_search_url).group(1)) + 10000
        if search_depth < 0:
            search_depth = search_pos // 10000 + 1

        # create dictionary of pagecounts
        futures = []
        for pos_idx in range(search_depth):
            pos = search_pos - (pos_idx * 10000)
            futures.append(self.get_page_counts(board_url, keyword, pos, search_type))
        pagecount_list = await asyncio.gather(*futures)

        # construct EVERY fetch
        futures = []
        for pos_idx in range(search_depth):
            pos = search_pos - (pos_idx * 10000)
            for page_num in range(1, pagecount_list[pos_idx] + 1):
                req_url = board_url + "&page={page_num}&search_pos=-{search_pos}&s_type={s_type}&s_keyword={s_keyword}"
                req_url = req_url.format(page_num=page_num, search_pos=pos, s_type=search_type, s_keyword=keyword)
                futures.append(loop.run_in_executor(None, requests.get, req_url))
        resp_lists = await asyncio.gather(*futures)

        for resp in resp_lists:
            for article in self.get_articles(BeautifulSoup(resp.text, "html.parser")):
                print(article)

    async def get_page_counts(self, board_url, keyword, search_pos, s_type):
        search_query = "&page=1&search_pos=-{search_pos}&s_type={s_type}&s_keyword={s_keyword}"
        # get last page of this search
        request_url = board_url + search_query.format(search_pos=search_pos, s_type=s_type, s_keyword=keyword)
        resp = requests.get(request_url)
        parser = BeautifulSoup(resp.text, "html.parser")
        nexts = parser.find_all('a', {'class': 'b_next'})
        if len(nexts) == 3:
            # last page btn exists
            page_len = int(self.page_regex.search(nexts[-2].get("href")).group(1))
        elif len(nexts) == 2:
            # case not happens(maybe)
            raise NotImplementedError
        else:
            page_btns = parser.find('div', {'id': 'dgn_btn_paging'})
            if page_btns:
                page_len = self.count_pages(page_btns)
        return page_len

    @staticmethod
    def count_pages(bs_parsed):
        links = bs_parsed.find_all('a')
        c = 0
        for idx in links:
            clss = idx.get('class')
            if clss in [None, ['on']]:
                c += 1
        return c

    @staticmethod
    def get_articles(bs_parsed):
        article_list = []
        tbody = bs_parsed.find('tbody')
        tr = tbody.find_all('tr')
        for idx in tr:
            notice = idx.find('td', {'class': 't_notice'}).get_text()
            subject = idx.find('td', {'class': 't_subject'}).get_text()
            writer = idx.find('td', {'class': 't_writer'}).get_text()
            date = idx.find('td', {'class': 't_date'}).get_text()
            if notice != '공지':
                article_list += [[notice, subject, writer, date]]
        return article_list


async def main():
    dcfinder = DCFinder()
    await dcfinder.findAsync(갤러리, 키워드, 검색타입, search_depth=깊이)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    input("press any key to continue...")
