Twitter Profile Changer
=======================

概要
----

Twitter のプロフィールを更新します。
* アイコン画像
* ヘッダ画像

cron 等で定期実行することを想定しています。


設置方法
--------

### Python をインストール

Python 3 以上が必要です。
ここでは、適当な Python がインストールされている環境 (レンタルサーバーなど) を使うことを想定し、
手順は省略します。

### Python の必要ライブラリのセットアップ

以下の Python ライブラリが必要です。
* rauth

以下のコマンドでインストールします。

```
easy_install --user rauth
```

### 本ツール用の適当なディレクトリを作成する

本ツールを設置する適当なディレクトリを作ります。
twitter-profile-changer でも TwitterProfileChanger でもお好きなお名前をご利用ください。

以降の作業は、このディレクトリ内で行うことを前提にします。


### 実行ファイルを設置する

`TwitterProfileChanger.py` を設置し、ファイルの権限を 755 にします。

### Twitter でアプリケーションを作成する

https://apps.twitter.com/ からアプリケーションを作成します。

作成後、 Keys and Access Tokens から API Key と API Secret を記録しておきます。
秘密情報なので取り扱いに注意しましょう。

### 設定ファイルを作成する

`TwitterProfileChanger.conf.template` をコピーし、 `TwitterProfileChanger.conf` に
リネームして設置します。

**`TwitterProfileChanger.conf` の権限を 600 にします。** (重要)

`TwitterProfileChanger.conf` を編集し、 Twitter アプリケーションの API Key と API Secret を記入します。

```
[TwitterProfileChanger]
apikey=(API Key の値を書く)
apisecret=(API Secret の値を書く)
#accountsdir=accounts
```

### アカウントの連携設定を行う

あなたの Twitter アカウントにこのアプリケーションがアクセスできるようにします。

```
./TwitterProfileChanger.py (アカウント名) init
```

実際にはここで指定するアカウント名は Twitter のアカウントと直接関係ないのですが、
ややこしくなるだけなので、 Twitter のアカウント名を指定することをおすすめします。

以下のように URL が表示されるので、URL にブラウザでアクセスし、そこで表示される数字を入力してください。
```
Visit this URL in your browser: https://api.twitter.com/oauth/authorize?oauth_token=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Enter PIN from your browser:
```

accounts/(アカウント名) というディレクトリが作成されます。

### テスト実行する

以下のコマンドを入力すると、あなたのタイムラインの直近 10 件が表示されます。
アカウントの連携設定が正しく行えたことの確認にご利用ください。

```
./TwitterProfileChanger.py (アカウント名) test
```


### 画像を設置する

accounts/(アカウント名)/icons, accounts/(アカウント名)/headers というディレクトリを作成し、
各ディレクトリに使用したいアイコン画像、ヘッダ画像を置きます。


### 実行する

以下のように実行すると画像が変更されます。

```
./TwitterProfileChanger.py (アカウント名) update
```

アイコンだけを変更したい (ヘッダ画像は変更しない) 場合は以下のように実行します。

```
./TwitterProfileChanger.py (アカウント名) update --icon
```

ヘッダ画像だけを変更したい (アイコンは変更しない) 場合は以下のように実行します。

```
./TwitterProfileChanger.py (アカウント名) update --header
```


### cron を設定する

例えば以下のように cron を設定すると、毎日深夜に画像が変更されます。

0 4 * * * /path/to/twitter-profile-changer/TwitterProfileChanger.py YOURACCOUNT update >/dev/null 2>&1


設定詳細
--------

### 画像の切り替え挙動について

切り替える画像は、特定のディレクトリ直下に置いてあるから決定します。
切り替える規則は以下のいずれかです。

* 順番 (sequential)
    * ファイルをアルファベット順に使用します。
    * 途中でファイルを追加した場合、一周するまで新しいファイルは使用されないので注意。
* 完全ランダム (random)
    * 毎回ファイルをランダムで選びます。
    * 同じファイルが続けて使用されたり、あるファイルがいつまでも使われないような状況も発生します。
* ランダム並び替え (shuffle)
    * ファイルをランダムで並び替えた後、順番に使用します。
    * 一周すると再びランダムで並び替え直します。

### 標準的なファイル構成

標準的なファイル構成は以下のとおりです。

```
TwitterProfileChanger.py        実行ファイル
TwitterProfileChanger.conf      設定ファイル。必ず権限を 600 にしてください。
accounts/
    (アカウント名)/             アカウントごとの設定などが保持されるディレクトリです。
        account.conf            アカウントごとの設定ファイルです。必ず権限を 600 にしてください。
        headers/                ヘッダ画像を設置するディレクトリ
            xxx.jpg
            xxx.png
            ...
        icons/                  アイコン画像を設置するディレクトリ
            xxx.jpg
            xxx.png
            ...
```

### TwitterProfileChanger.conf

アプリケーション全体の設定を記載します。
ini ファイルフォーマットで記載します。

| セクション            | キー        | デフォルト値 | 値                            |
|:----------------------|:------------|:-------------|:------------------------------|
| TwitterProfileChanger | apikey      |              | アプリケーションの API Key    |
|                       | apisecret   |              | アプリケーションの API Secret |
|                       | accountsdir | accounts     | アカウントごとの設定等を格納する親ディレクトリ。相対パスで指定した場合、 `TwitterProfileChanger.py` が置いてあるディレクトリからの相対パスになります。 |

例)
```
[TwitterProfileChanger]
apikey=(API Key の値を書く)
apisecret=(API Secret の値を書く)
accountsdir=accounts
```

### accounts/(アカウント名)/account.conf

アカウントごとの設定を記載します。
ini ファイルフォーマットで記載します。

| セクション            | キー              | デフォルト値 | 値                               |
|:----------------------|:------------------|:-------------|:---------------------------------|
| TwitterProfileChanger | accesstoken       |              | アカウントの Access Token。連携設定時に設定された値から変更しないでください。 |
|                       | accesstokensecret |              | アカウントの Access Token Secret。連携設定時に設定された値から変更しないでください。 |
|                       | icondir           | icons        | アイコン画像を設置するディレクトリ。相対パスで指定した場合、アカウントごとのディレクトリからの相対パスになります。 |
|                       | iconstrategy      | shuffle      | アイコン画像の切り替え挙動を指定します。 |
|                       | headerdir         | headers      | ヘッダ画像を設置するディレクトリ。相対パスで指定した場合、アカウントごとのディレクトリからの相対パスになります。 |
|                       | headerstrategy    | sequential   | ヘッダ画像の切り替え挙動を指定します。 |

例)
```
[TwitterProfileChanger]
accesstoken = (アカウントの Access Token)
accesstokensecret = (アカウントの Access Token Secret)
icondir = icons
iconstrategy = shuffle
headerdir = headers
headerstrategy = sequential
```

### 起動オプション

```
TwitterProfileChanger.py -h
usage: TwitterProfileChanger.py [-h] [--verbose] [--icon] [--header]
                                ACCOUNTNAME COMMAND

Twitter profile changer updates your twitter profile (icon, header, etc.) automatically.

positional arguments:
  ACCOUNTNAME  an account name to use
  COMMAND      a command to execute

optional arguments:
  -h, --help   show this help message and exit
  --verbose    Verbose message.
  --icon       Updates only the icon.
  --header     Updates only the header.

COMMANDS:
  init  : Authenticate and initialize a configuration for a new account
  test  : Test the account. Retrieves the timeline and display.
  update: Update the profile
```
