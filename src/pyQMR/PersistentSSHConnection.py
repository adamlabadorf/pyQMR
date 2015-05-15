import os
import random
import shlex
import string
import sys

from subprocess import call, Popen, PIPE

class PersistentSSHConnection(object) :
    '''This class wraps a master ssh process and allows repeated command
    execution on the same ssh connection without reentering a passphrase.
    The master connection is performed using the -M and -o ControlPath ssh
    arguments.  All ssh child processes are killed and the socket file object
    is deleted upon *close()* or garbage collection.'''

    def __init__(self,username,hostname,ssh_exec='/usr/bin/ssh',scp_exec='/usr/bin/scp') :

        noise = ''.join(random.sample(string.letters,4))
        self._socket_fn = '/tmp/master-%s@%s:22-%s'%(username,hostname,noise)
        self._master_ssh_opts = '-f -MN -o ControlPath=%s -o ControlMaster=no -o ServerAliveInterval=900'%self._socket_fn
        self._slave_ssh_opts = '-S %s'%self._socket_fn
        self._slave_scp_opts = '-r -o ControlPath=%s'%self._socket_fn
        self._ssh_exec = ssh_exec
        self._scp_exec = scp_exec

        cmd = [ssh_exec]+shlex.split(self._master_ssh_opts)+['%s@%s'%(username,hostname)]
        self._master_ssh_cmd = ' '.join(cmd)

        self._master_proc = Popen(cmd,stdin=PIPE)
        self._master_proc.communicate()
        self.username = username
        self.hostname = hostname

    def needs_socket(fn) :
        def f(self,*args) :
            if not os.path.exists(self._socket_fn) :
                raise Exception('SSH socket file cannot be found, will not send command')
            return fn(self,*args)
        return f

    @needs_socket
    def send_cmd(self,cmd) :
        '''Send an ssh command over the persistent connection and return the
        stdout and stderr of the command execution.'''
        ssh_cmd = [self._ssh_exec]+shlex.split(self._slave_ssh_opts)+['%s@%s'%(self.username,self.hostname),cmd]
        p = Popen(ssh_cmd,stdout=PIPE,stderr=PIPE)
        stdout, stderr = p.communicate()
        return stdout, stderr

    @needs_socket
    def fetch_file(self,path,lpath=None,recurse=False) :
        '''Call scp and copy path from remote host to local filesystem with the
        same name.  If *lpath* is specified the local file will be named *lpath*.
        If the remote path is a directory, mkdir the directory locally if it does
        not already exist. If *recurse* is True, directories will be downloaded
        as well as created.'''

        scp_local = lpath or path

        # check if remote path is directory
        stdout, stderr = self.send_cmd('test -d %s && echo directory || echo file'%path)

        if stdout.strip() == 'directory' :
            try :
                os.mkdir(scp_local)
                r = 0
            except (Exception) as e:
                print(e)

        if stdout.strip() == 'file' or recurse :
            scp_remote = '%s@%s:%s'%(self.username,self.hostname,path)
            scp_cmd = [self._scp_exec]+shlex.split(self._slave_scp_opts)+[scp_remote,scp_local]
            r = call(scp_cmd)

        return r

    def __del__(self) :
        try :
            self.close()
        except :
            pass

    def close(self) :
        '''Close the connection and clean up'''

        # find and kill the forked ssh process
        p = Popen('pgrep -f "^%s$"'%self._master_ssh_cmd,shell=True,stdout=PIPE,stderr=PIPE)
        stdout, stderr = p.communicate()
        if stdout is not None and stdout != '' :
            for pid in stdout.strip().split() :
                try :
                    os.kill(int(pid),signal.SIGKILL)
                except Exception as e:
                    sys.stderr.write('killing forked process %s didnt work: %s'%(pid,e))

        # remove the socket file
        try :
            os.remove(self._socket_fn)
        except : # eh, whatever
            pass

if __name__ == '__main__' :

    username = raw_input('enter username: ')
    hostname = raw_input('enter hostname: ')

    conn = PersistentSSHConnection(username,hostname)
    print('connected to %s, send ssh commands and watch yourself'%hostname)

    while True :
        cmd = raw_input('%s@%s ] '%(username,hostname))
        if cmd.strip() == 'exit' :
            break
        stdout, stderr = conn.send_cmd(cmd)
        print('stdout:')
        print(stdout)

        print('stderr:')
        print(stderr)
