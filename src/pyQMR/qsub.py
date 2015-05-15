import jinja2
import uuid

from PersistentSSHConnection import PersistentSSHConnection as PSSHC

template = """\
#!/bin/bash

#$ -N {{ name }}
{{ "#$ -wd %s"%wd if wd is defined else "#$ -cwd" }}
{{ "#$ -hold_jid %s"%hold_jid if wd is defined }}

# user specified opts
{% for opt,val in qsub_opts %}
#$ -{{ opt }} {{ val }}
{% endfor %}

{{ executable }} {{ script }} {{ args }}
"""

class QJob(object) :

  def __init__(self) :
    template = jinja2.Template(template)
    qsub_script_d = {
      "name": "test",
      "wd": "",
      "qsub_opts": [["P","mlhd"]],
      "executable": "python3",
      "script": "test.py",
      "args": "some awesome args"
    }
    self.qsub_script = template.render(**qsub_script_d)

def qsub() :
  return False

def qstat() :
  return False
