#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# The MIT License (MIT)
# 
# Copyright (c) 2015 ikedam.jp
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import argparse
import base64
import ConfigParser
import logging
import os
import os.path
import rauth
import random
import stat
import sys
import urllib

# The directory this script is put in.
# This is useful especially when launched from cron.
BASEDIR = os.path.dirname(os.path.realpath(__file__))
BASENAME = os.path.splitext(os.path.basename(__file__))[0]
CONFIG = os.path.join(BASEDIR, '%s.conf' % BASENAME)
SECTION = 'TwitterProfileChanger'

def checkPermission(file):
    """
    Checks permissions of a file containing secrets.
    Modify here if you want don't like the check (to make weak or strong).
    """
    mode = os.stat(file)[stat.ST_MODE]
    if mode & (stat.S_IRGRP | stat.ST_MODE):
        raise Exception('config file (%s) should not be exposed to non-owners' % file)

def getAbsolutePath(base, path):
    """
    Calculates the absolute path from the base directory.
    """
    if os.path.isabs(path):
        return path
    
    return os.path.join(base, path)

class TwitterProfileChanger(object):
    _AccountsDir = getAbsolutePath(BASEDIR, 'accounts')
    _DefaultConf = {
        'icondir'       : 'icons',
        'iconstrategy'  : 'shuffle',
        'headerdir'     : 'headers',
        'headerstrategy': 'sequential',
    }
    _AcceptImageExts = (
        '.jpeg',
        '.jpg',
        '.png',
    )
    
    def __init__(self, account, apikey, apisecret, accountsdir=None, logger=None):
        if logger:
            self._Logger = logger
        else:
            self._Logger = logger.getLogger()
        
        self._Account = account
        if accountsdir:
            self._AccountsDir = getAbsolutePath(BASEDIR, accountsdir)
        self._AccountDir = os.path.join(self._AccountsDir, urllib.quote(account, ''))
        self._AccountConfFile = os.path.join(self._AccountDir, 'account.conf')
        
        if os.path.exists(self._AccountConfFile):
            checkPermission(self._AccountConfFile)
            config = ConfigParser.RawConfigParser()
            config.read(self._AccountConfFile)
            self._accountConf = self._DefaultConf.copy()
            self._accountConf.update(dict(config.items(SECTION)))
        else:
            self._accountConf = None
        
        
        self._ApiKey = apikey
        self._ApiSecret = apisecret
        
        # Initizalize OAuth service.
        self._Twitter = rauth.OAuth1Service(
            # The service name, e.g. 'twitter'.
            name = 'twitter',
            consumer_key = self._ApiKey,
            consumer_secret = self._ApiSecret,
            
            # URLs for twitter services.
            request_token_url = 'https://api.twitter.com/oauth/request_token',
            access_token_url = 'https://api.twitter.com/oauth/access_token',
            authorize_url = 'https://api.twitter.com/oauth/authorize',
            base_url = 'https://api.twitter.com/1.1/'
        )
        
        # Session
        self._session = None
    
    def _initAccount(self):
        
        if not os.path.exists(self._AccountDir):
            os.makedirs(self._AccountDir)
        
        config = ConfigParser.RawConfigParser()
        config.add_section(SECTION)
        for key, value in self._accountConf.iteritems():
            config.set(SECTION, key, value)
        
        oldmask = os.umask(077)
        config.write(open(self._AccountConfFile, 'w'))
        os.umask(oldmask)
    
    def isInitialized(self):
        return self._accountConf and True
    
    def assertInitialized(self):
        if not self.isInitialized():
            raise Exception('You need to authenticate the application for the account first')
    
    def assertNotInitialized(self):
        if self.isInitialized():
            raise Exception(
                'Already initialized. Remove %s or %s and retry.'
                % (self._AccountDir, self._AccountConfFile)
            )
    
    def _initializePrepare(self):
        """
        Starts the authentication for twitter.
        Returns an URL and tokens for authentication.
        Let the user to access the URL and retrieve PIN code to authenticate.
        Call initializeComplete with that PIN code.
        """
        self.assertNotInitialized()
        
        # Get a request token and a secret.
        (requestToken, requestTokenSecret) = self._Twitter.get_request_token()
        
        return {
            'authorizeUrl': self._Twitter.get_authorize_url(requestToken),
            'requestToken': requestToken,
            'requestTokenSecret': requestTokenSecret,
        }
    
    def _initializeComplete(self, authorizeInfo, pinCode):
        """
        Completes the authentication for twitter.
        Pass the return value from initializePrepare as authorizeInfo,
        and the pin code the user see in the authentication page as pinCode
        """
        self.assertNotInitialized()
        
        # Get an access token and an access secret.
        (accessToken, accessTokenSecret) = self._Twitter.get_access_token(
            request_token=authorizeInfo['requestToken'],
            request_token_secret=authorizeInfo['requestTokenSecret'],
            method='POST',
            data={'oauth_verifier': pinCode}
        )
        
        self._accountConf = self._DefaultConf.copy()
        self._accountConf.update({
            'accesstoken': accessToken,
            'accesstokensecret': accessTokenSecret,
        })
        
        self._initAccount()
    
    def initialize(self):
        """
        Initialize the account
        """
        authorizeInfo = self._initializePrepare()
        print('Visit this URL in your browser: %s' % authorizeInfo['authorizeUrl'])
        pin = raw_input('Enter PIN from your browser: ')
        
        self._initializeComplete(authorizeInfo, pin)
    
    def _createSession(self):
        """ Creates a new session. """
        
        self.assertInitialized()
        
        if not self._session:
            # Create a session.
            self._session = rauth.OAuth1Session(
                consumer_key=self._ApiKey,
                consumer_secret=self._ApiSecret,
                access_token=self._accountConf['accesstoken'],
                access_token_secret=self._accountConf['accesstokensecret'],
                service=self._Twitter
            )
        
        return self._session
    
    def getTimeline(self, count=10):
        """
        Get timeline. 
        https://dev.twitter.com/rest/reference/get/statuses/home_timeline
        """
        
        session = self._createSession()
        
        res = session.get('statuses/home_timeline.json', params={'count': count})
        
        if not 200 <= res.status_code < 300:
            raise Exception(
                'Failed to get timeline for code %d, response: %s' % (
                    res.status_code, res.text
                )
            )
        
        return res.json()
    
    def _getImageList(self, imagedir):
        return [ p for p in os.listdir(imagedir) if os.path.splitext(p)[1].lower() in self._AcceptImageExts ]
    
    def _pickRandomImageFile(self, imagedir):
        images = self._getImageList(imagedir)
        if not images:
            raise Exception('No image files are found in %s' % imagedir)
        return random.choice(images)
    
    def _pickPreorderedImageFile(self, imagedir, orderFunc):
        listfile = os.path.join(imagedir, 'list.txt')
        if os.path.exists(listfile):
            candidates = [ x.strip() for x in open(listfile).readlines() ]
            while candidates:
                candidate = candidates.pop(0)
                if not candidate:
                    continue
                if not os.path.exists(os.path.join(imagedir, candidate)):
                    self._Logger.debug('%s is lost: ignored', os.path.join(imagedir, candidate))
                    continue
                if candidates:
                    open(listfile, 'w').write('\n'.join(candidates))
                else:
                    os.remove(listfile)
                return candidate
            os.remove(listfile)
        
        self._Logger.debug('No processing image list exists for %s', imagedir)
        images = self._getImageList(imagedir)
        if not images:
            raise Exception('No image files are found in %s' % imagedir)
        candidates = orderFunc(imagedir, images)
        self._Logger.debug('New order: %s', candidates)
        candidate = candidates.pop(0)
        if candidates:
            open(listfile, 'w').write('\n'.join(candidates))
        
        return candidate
    
    def _orderSequential(self, imagedir, images):
        images.sort()
        return images
    
    def _orderShuffle(self, imagedir, images):
        random.shuffle(images)
        return images
    
    def _pickImageFile(self, imagedir, imagestrategy):
        if not os.path.exists(imagedir):
            raise Exception('%s doesnot exist' % imagedir)
        
        if imagestrategy == 'random':
            return self._pickRandomImageFile(imagedir)
        elif imagestrategy == 'sequential':
            return self._pickPreorderedImageFile(imagedir, self._orderSequential)
        elif imagestrategy == 'shuffle':
            return self._pickPreorderedImageFile(imagedir, self._orderShuffle)
        
        raise Exception('Unknown image strategy %s' % imagestrategy)
    
    def updateIcon(self):
        """
        Updates the icon
        https://dev.twitter.com/rest/reference/post/account/update_profile_image
        """
        imagedir  = getAbsolutePath(self._AccountDir, self._accountConf['icondir'])
        imagestrategy = self._accountConf['iconstrategy']
        
        imagefile = os.path.join(imagedir, self._pickImageFile(imagedir, imagestrategy))
        
        self._Logger.debug('Upload %s for the icon image', imagefile)
        
        session = self._createSession()
        
        res = session.post('account/update_profile_image.json', data={
            'image': base64.b64encode(open(imagefile, 'rb').read()),
        })
        
        if not 200 <= res.status_code < 300:
            raise Exception(
                'Failed to upload image %s for code %d, response: %s' % (
                    imagefile, res.status_code, res.text
                )
            )
        
        return res.json()
    
    def updateHeader(self):
        """
        Updates the icon
        https://dev.twitter.com/rest/reference/post/account/update_profile_banner
        """
        imagedir  = getAbsolutePath(self._AccountDir, self._accountConf['headerdir'])
        imagestrategy = self._accountConf['headerstrategy']
        
        imagefile = os.path.join(imagedir, self._pickImageFile(imagedir, imagestrategy))
        
        self._Logger.debug('Upload %s for the header image', imagefile)
        
        session = self._createSession()
        
        res = session.post('account/update_profile_banner.json', data={
            'banner': base64.b64encode(open(imagefile, 'rb').read()),
        })
        
        if not 200 <= res.status_code < 300:
            raise Exception(
                'Failed to upload banner %s for code %d, response: %s' % (
                    imagefile, res.status_code, res.text
                )
            )

def readConfig(file):
    if not os.path.exists(file):
        raise Exception('config file (%s) does not exist' % file)
    
    checkPermission(file)
    
    config = ConfigParser.RawConfigParser()
    config.read(file)
    return dict(config.items(SECTION))

if __name__ == '__main__':
    config = readConfig(CONFIG)
    
    parser = argparse.ArgumentParser(
        description='Twitter profile changer updates your twitter profile (icon, header, etc.) automatically.',
        epilog='\n'.join([
            'COMMANDS:',
            '  init  : Authenticate and initialize a configuration for a new account',
            '  test  : Test the account. Retrieves the timeline and display.',
            '  update: Update the profile',
        ]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--verbose', 
        dest='verbose', 
        action='store_true',
        help='Verbose message.'
    )
    parser.add_argument(
        '--icon', 
        dest='icon', 
        action='store_true',
        help='Updates only the icon.'
    )
    parser.add_argument(
        '--header', 
        dest='header', 
        action='store_true',
        help='Updates only the header.'
    )
    parser.add_argument('account', type=str,
        metavar='ACCOUNTNAME', help='an account name to use')
    parser.add_argument('command', type=str,
        metavar='COMMAND', help='a command to execute')
    
    args = parser.parse_args()
    
    logging.basicConfig()
    logger = logging.getLogger()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    changer = TwitterProfileChanger(account=args.account, logger=logger, **config)
    
    if args.command in ('init'):
        changer.initialize()
    elif args.command in ('test'):
        tweets = changer.getTimeline()
        for tweet in tweets:
          print(('%s: %s' % (tweet['user']['name'], tweet['text'])).encode('UTF-8'))
    elif args.command in ('update'):
        doAll = not args.icon and not args.header
        if doAll or args.icon:
            changer.updateIcon()
        if doAll or args.header:
            changer.updateHeader()
    else:
        raise Exception('Unknown command: %s' % args.command)
    
    sys.exit(0)
