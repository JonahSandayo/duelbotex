#!/usr/bin/env python3
#coding UTF-8
import discord
from os import getenv
# ダイスロールとコイントス用のランダムライブラリだよ
import random
# HTTPリクエスト用のライブラリだよ
import requests
# HTTPレスポンス解析用のライブラリだよ
import bs4
# APIのアレ
import json

TOKEN = 'ここにトークンを張り付け'

client = discord.Client()

cardList = []

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(name='helpでヘルプが出るわ', type=discord.ActivityType.watching))


@client.event
async def on_message(message):
    # グローバル変数のライフ・履歴を取得
    global Life1
    global Life2
    global Life1Hist
    global Life2Hist
    global player1
    global player2
    global cardList
    global chn
    
    if message.author.bot:
        return
    messageBody = message.content
    
    # カード名検索結果がある場合は表示処理
    if len(cardList) > 0  and chn == message.channel.id:
        index = ''
        # 先頭が1～5の数字に一致している場合は先頭文字を数字として取得
        if messageBody.startswith(
           ('1', '2', '3', '4', '5', '１', '２', '３', '４', '５')):
          index = messageBody[:1]

        # 指定した数字がカードリストのサイズ以下であればメッセージとして発言
        if index != '' and len(cardList) >= int(index):
          embed = discord.Embed(title="検索結果",description=cardList[int(index)-1],color=discord.Colour.from_rgb(171, 219, 255))
          await message.channel.send(embed = embed)
        else:
          await message.channel.send('カード名検索キャンセル')
        # 一時保持していたカード名検索結果をクリアと同時に取得したチャンネルもクリア
        cardList.clear()
        chn=0
        return

    # ヘルプテキスト
    if messageBody == 'help':
        embed = discord.Embed(title="コマンドリスト",description="coin:コイントスを行い、表/裏を表示\ndice:ダイスロールを行い、1～6を表示\nt:カード検索[tt カード名][ｔｔ カード名]も有効\nT カードNo:カードナンバー検索を行いテキスト表示\ndraw:カードをランダムに一枚ドローします\n",color=discord.Colour.from_rgb(171, 219, 255))
        await message.channel.send(embed=embed)
        return

    # コイントス
    if messageBody == 'coin':
        await message.channel.send('**コイントス：【 ' + random.choice('表裏') + ' 】**')
        return

    # ダイス
    if messageBody == 'dice':
        await message.channel.send('**ダイスロール：【 ' + random.choice('123456') + ' 】**')
        return
    
    # ドロー
    if messageBody == 'draw':
        r = requests.get("https://db.ygoprodeck.com/api/v7/randomcard.php")
        data = json.loads(r.text)
        await message.channel.send(data['card_images'][0]['image_url'])
        return

    # カードナンバー検索
    if messageBody.startswith('T '):
        cardNo = messageBody[2:]
        cardText = searchCardNo(cardNo)
        await message.channel.send(cardText)
        return

   # カード名検索
    if messageBody.startswith(('t ','tt','ｔｔ')):
        cardName = messageBody[2:]
        cardTextList = searchCardName(cardName)
        # 取得したテキストが1個のみであればそのまま出力
        if len(cardTextList) == 1:
          embed = discord.Embed(title="検索結果",description=cardTextList[0],color=discord.Colour.from_rgb(171, 219, 255))
          await message.channel.send(embed = embed)
        # 取得したテキストが複数の場合であればカード名を一時保持し、リスト表示
        else:
            cardList = cardTextList
            i = 1
            msg = 'テキスト表示対象を選択してください。\n'
            for text in cardTextList:
                msg = msg + str(i) + ':' + text.split('\n')[1] + '\n'
                i += 1
            embed = discord.Embed(title="検索結果",description=msg,color=discord.Colour.from_rgb(171, 219, 255))
            chn =message.channel.id
            await message.channel.send(embed = embed)
        return


# カードナンバーにより検索し、結果を返す
def searchCardNo(argNo):
    baseurl = "https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&sess=1&keyword=XXNOXX&stype=4&ctype=&starfr=&starto=&pscalefr=&pscaleto=&linkmarkerfr=&linkmarkerto=&link_m=2&atkfr=&atkto=&deffr=&defto=&othercon=2"
    requesturl = baseurl.replace('XXNOXX', argNo)
    # 日本語指定
    headers = {'Accept-Language': 'ja'}

    # リクエスト送信
    response = requests.get(requesturl, headers=headers)

    # 通信エラーの場合は何もしない
    if response.status_code != 200:
        return 'カード検索失敗：通信エラー(' + str(response.status_code) + ')'

    # レスポンス解析
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    # 該当データ無しの場合は終了
    elems = soup.select('.no_data')
    for elem in elems:
        return '該当カードが見つかりません。'

    # 該当データが複数件の場合は終了
    uniqueStr = '検索結果 1件中 1～1件を表示'
    elems = soup.select('.page_num_title strong')
    for elem in elems:
        if not uniqueStr in elem.text:
            return '該当カードが複数あります。'

    # 以下にDiscord発言用のメッセージ取得
    msg = 'カードNo検索\n'

    # カードのタイトル取得
    elems = soup.select('.card_name')
    for elem in elems:
        msg = msg + elem.text + '\n'

    # カードのテキスト取得
    elems = soup.select('.box_card_text')
    for elem in elems:
        msg = msg + elem.get_text('\n').strip()

    embed = discord.Embed(title=".box_card_name strong",description=".box_card_text")
    return embed

# カード名により検索し、結果を配列で返す
def searchCardName(argName):

    # リクエスト先の遊戯王公式URL
    baseurl = "https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&sess=1&keyword=XXNAMEXX&stype=1&ctype=&starfr=&starto=&pscalefr=&pscaleto=&linkmarkerfr=&linkmarkerto=&link_m=2&atkfr=&atkto=&deffr=&defto=&othercon=2"
    requesturl = baseurl.replace('XXNAMEXX', argName)
    # 日本語指定
    headers = {'Accept-Language': 'ja'}

    # リクエスト送信
    response = requests.get(requesturl, headers=headers)

    # 通信エラーの場合は何もしない
    if response.status_code != 200:
        msg = 'カード検索失敗：通信エラー(' + str(response.status_code) + ')'
        return [msg]

    # レスポンス解析
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    # 該当データ無しの場合は終了
    elems = soup.select('.no_data')
    for elem in elems:
        msg = '該当カードが見つかりません。'
        return [msg]

    # 以下にDiscord発言用のメッセージ取得
    textList = []

    # カード名取得
    elems = soup.select('.card_name')

    # ヒットしたカード件数が5件以上の場合は終了
    if len(elems) > 5:
        textList.append('該当カードが5件超過のため表示できません')
        return textList

    for elem in elems:
        textList.append('カード名検索\n' + elem.text + '\n')

    # カードのテキスト取得
    i = 0
    elems = soup.select('.atk_power')
    for elem in elems:
        textList[i] = textList[i] + elem.get_text('\n').strip()
        i += 1

    i = 0
    elems = soup.select('.def_power')
    for elem in elems:
        textList[i] = textList[i] + elem.get_text('\n').strip()+('\n')
        i += 1
    
    i = 0
    elems = soup.select('.box_card_text')
    for elem in elems:
        textList[i] = textList[i] + elem.get_text('\n').strip()
        i += 1
    return textList


# ヘルプテキスト表示
def showHelp():
    msg = 'BOTコマンド\n'
    msg = msg + 'coin:コイントスを行い、表/裏を表示\n'
    msg = msg + 'dice:ダイスロールを行い、1～6を表示\n'
    msg = msg + '[tt カード名][ｔｔ カード名]も有効\n'
    msg = msg + 'T カードNo:カードナンバー検索を行いテキスト表示\n'
    msg = msg + 'draw:ランダムにカードを一枚ドローします'

    return msg


client.run(TOKEN)
