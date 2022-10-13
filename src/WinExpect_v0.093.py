import pexpect.popen_spawn as psp
import logging
from termcolor import colored
import sys
import re
import time
import datetime
import argparse
import colorama
colorama.init()

class WinExpect(object):
    def __init__(self, prompt, timeout, fileName):
        self.formatter = '\n[%(asctime)s][%(levelname)s]\n%(message)s'
        logging.basicConfig(filename='logs/{}_{}.log'.format(datetime.datetime.now().strftime('%Y%m%d-%H%M%S'), fileName),
                            level=logging.INFO, format=self.formatter)
        self.logger = logging.getLogger()
        self.wlog = open('logs/{}_{}_plain.log'.format(datetime.datetime.now().strftime('%Y%m%d-%H%M%S'), fileName), 'wb')
        self.process = psp.PopenSpawn('cmd', logfile=self.wlog)
        self.prompt = prompt
        self.timeout = timeout

        self.cmd_sendline('prompt $P[$T]$G')
        self.process.expect('>', int(timeout))
        print(self.process.before.decode('shift-jis', errors='ignore').replace('\r\n', '\n'), end='')
        print(self.process.after.decode('shift-jis', errors='ignore').replace('\r\n', '\n'), end='')

    def cmd_readline(self, exp_err=False):
        self.promptStr = "@"
        if self.cmd != 'echo %ERRORLEVEL%':
            print(colored('\n--- Execution Result ---\n> ', 'blue', attrs=['bold']), end='')
        else:
            print(colored('> ', 'blue', attrs=['bold']), end='')
        if (exp_err):
            # マッチした前の文字列
            print(self.process.before.decode('shift-jis', errors='ignore').replace('\r\n', '\n'), end='')
            msg = '{}'.format(self.process.before.decode('shift-jis', errors='ignore').replace('\r\n', '\n'))
            self.logger.info(msg)
        else:
            # マッチした前の文字列
            print(self.process.before.decode('shift-jis', errors='ignore').replace('\r\n', '\n'), end='')
            # マッチした文字
            print(colored(self.process.after.decode('shift-jis', errors='ignore').replace('\r\n', '\n'), 'magenta'))
            # マッチした後の文字列
            print(self.process.buffer.decode('shift-jis', errors='ignore').replace('\r\n', '\n'), end='')
            msg = '{}{}{}'.format(self.process.before.decode('shift-jis', errors='ignore').replace('\r\n', '\n'), self.process.after.decode('shift-jis', errors='ignore').replace('\r\n', '\n'), self.process.buffer.decode('shift-jis', errors='ignore').replace('\r\n', '\n'))
            self.logger.info(msg)
            if re.search('\)\s?\?', self.process.after.decode('shift-jis', errors='ignore')):
                self.promptStr = "?"
            else:
                self.promptStr = "@"

    def cmd_sendline(self, cmd, prompt='', timeout=''):
        self.cmd = cmd
        if prompt == '':
            prompt = self.prompt
        if timeout == '':
            timeout = self.timeout
        self.process.sendline(cmd)
        while True:
            try:
                self.process.expect(prompt, int(timeout))
            except Exception as ex:
                self.cmd_readline(True)
                print(colored('\n[TimeOutError] The prompt could not be detected.', 'red'))
                self.logger.error('The prompt could not be detected.')
                input_yn = input('[W]ait/[Q]uit/[I]nput: ').upper()
                if input_yn.upper() == 'Q':
                    sys.exit(1)
                elif input_yn.upper() == 'W':
                    print(colored('\nwait 20 seconds.', 'red'))
                    time.sleep(20)
                elif input_yn.upper() == 'I':
                    input_cmd = input('Input Command: ')
                    self.cmd_sendline(input_cmd, prompt, timeout)
                    break
            else:
                self.cmd_readline()
                break
        return(self.promptStr)

parser = argparse.ArgumentParser()
parser.add_argument('-f', help='Name of command file to execute', required=True)
args = parser.parse_args()
fileName = args.f
fileName = fileName.replace(".\\", '')

proc = WinExpect(['\>'], 3, fileName)
prompt = ['\[.[0-9]\:[0-9][0-9]\:[0-9][0-9].[0-9][0-9]\]\>', '\)\s?\?']
timeout = 20
rawLabel = []
flg1 = False
with open(fileName, 'r',encoding="utf-8") as file:
    lines = file.readlines()
    i0 = 0
    end = len(lines) - 1
    for i1, c in enumerate(lines):
        if c[:1] == '\t' and c[1:].strip() != "":
            rawLabel.append(i1)
    rs = '@'
    while True:
        if rs == '?':
            input_cmd = input('Input Command: ')
            rs = proc.cmd_sendline(input_cmd, prompt, timeout)
            if rs != '?':
                proc.cmd_sendline('echo %ERRORLEVEL%', prompt, timeout)
        else:
            flg0 = False
            if lines[i0][:1] != '\t':
                if lines[i0].strip() != '':
                    if not flg1:
                        print(colored('\n-------- Comment -------\n', 'green', attrs=['bold']), end='')
                    print(colored(lines[i0], 'green'), end='')
                    flg1 = True
            elif lines[i0][1:].strip() != "":
                flg1 = False
                cmd = lines[i0][1:].strip()
                while True:
                    print(colored('\n------------------------', 'red', attrs=['bold']))
                    print('[EXE CMD]:', colored(cmd, 'red', attrs=['bold']))
                    cmd_key = input(' -> ExecuteOn[Enter]/[S]kip/[R]eturn/[I]nput/[Q]uit: ')
                    if cmd_key == '':
                        cmd_key = 'E'
                        break
                    elif cmd_key.upper() == 'I' or cmd_key.upper() == 'S' or cmd_key.upper() == 'R' or cmd_key.upper() == 'Q':
                        break
                if cmd_key.upper() == 'E':
                    rs = proc.cmd_sendline(cmd, prompt, timeout)
                    if rs != '?':
                        proc.cmd_sendline('echo %ERRORLEVEL%', prompt, timeout)
                elif cmd_key.upper() == 'I':
                    input_cmd = input('Input Command: ')
                    rs = proc.cmd_sendline(input_cmd, prompt, timeout)
                    if rs != '?':
                        proc.cmd_sendline('echo %ERRORLEVEL%', prompt, timeout)
                elif cmd_key.upper() == 'S':
                    pass
                elif cmd_key.upper() == 'R':
                    flg0 = True
                    for i2, c in enumerate(rawLabel):
                        if c == i0 and i2 == 0:
                            i0 = c
                            print(rawLabel, i0)
                            break
                        elif c == i0:
                            i0 = rawLabel[i2 - 1]
                            break
                elif cmd_key.upper() == 'Q':
                    sys.exit()
            if i0 == end:
                break
            if not flg0:
                i0 = i0 + 1
